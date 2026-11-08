"""Tests for Video Quality Metrics. Run them with: python -m unittest tests -v

The end-to-end tests run main.py on ForBiggerFun.mp4, so they need FFmpeg with the libvmaf
filter. They are skipped if FFmpeg doesn't have it. The other tests only need the requirements.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

from main import get_comparisons, get_folder_names, reason_to_recalculate
from results import ResultRow, describe_bitrate_sources, get_columns, is_best
from utils import format_si

REPO_FOLDER = Path(__file__).parent
VIDEO = REPO_FOLDER / "ForBiggerFun.mp4"


def run_main(*arguments: str) -> subprocess.CompletedProcess:
    """Run main.py with the arguments. Its output (stdout and stderr) is in .stdout."""
    return subprocess.run(
        [sys.executable, str(REPO_FOLDER / "main.py"), *arguments],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        # On Windows, Python writes to a pipe in the legacy cp1252 encoding by default, which
        # can't write some of the characters in the progress bars (e.g. "✓"). UTF-8 mode can.
        env={**os.environ, "PYTHONUTF8": "1"},
        encoding="utf-8",
    )


def ffmpeg_has_libvmaf() -> bool:
    """Return whether FFmpeg is installed and has the libvmaf filter."""
    try:
        filters = subprocess.run(
            ["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True
        ).stdout
    except OSError:
        return False
    return any(line.split()[1:2] == ["libvmaf"] for line in filters.splitlines())


class TestComparisons(unittest.TestCase):
    """How the -p/-v and -c arguments are turned into the encoder options to compare."""

    def test_parameter_mode(self):
        """-p crf -v 23 24 gives one comparison per value, e.g. "-crf 23"."""
        args = Namespace(
            combinations=None, encoder="libx264", parameter="crf", values=["23", "24"]
        )
        comparisons = get_comparisons(args)
        self.assertEqual([c.label for c in comparisons], ["23", "24"])
        self.assertEqual(comparisons[0].encoder_options, ["-crf", "23"])
        self.assertEqual(comparisons[0].name, "libx264_crf_23")

    def test_combination_mode(self):
        """-c gives one comparison per combination, with a "-" added before each option name."""
        args = Namespace(combinations="preset slow crf 24,preset medium crf 23", encoder="libx264")
        comparisons = get_comparisons(args)
        self.assertEqual(
            [c.label for c in comparisons], ["-preset slow -crf 24", "-preset medium -crf 23"]
        )
        self.assertEqual(comparisons[0].encoder_options, ["-preset", "slow", "-crf", "24"])
        self.assertEqual(comparisons[0].name, "libx264_preset_slow_crf_24")

    def test_folder_names_only_use_the_path_when_filenames_clash(self):
        """Videos with the same filename get different folders, so results aren't overwritten."""
        # a/clip.mp4 and b/clip.mp4 have the same filename, so their whole paths are used.
        # other.mp4 is the only video with its filename, so just the filename is used.
        folder_names = get_folder_names(["a/clip.mp4", "b/clip.mp4", "c/other.mp4"])
        self.assertEqual(
            folder_names,
            {"a/clip.mp4": "a/clip.mp4", "b/clip.mp4": "b/clip.mp4", "c/other.mp4": "other.mp4"},
        )


class TestResults(unittest.TestCase):
    """How the values in the results table and the notes underneath it are shown."""

    def test_format_si(self):
        """Sizes and bitrates are shown with an SI prefix, e.g. 1.235 MB."""
        # Values below 1000 have no prefix and no decimal places.
        self.assertEqual(format_si(999, "B", 3), "999 B")
        self.assertEqual(format_si(1234567, "B", 3), "1.235 MB")
        self.assertEqual(format_si(1_500_000, "bps", 1), "1.5 Mbps")

    def test_only_the_highest_metric_of_the_transcodes_is_best(self):
        """Only the transcode with the highest VMAF/PSNR/SSIM is highlighted as the best."""
        original = ResultRow("Original Video", "h264", 100, None, None)
        worse = ResultRow("30", "h264", 50, None, None, mean_scores={"VMAF": 90.0})
        better = ResultRow("20", "h264", 80, None, None, mean_scores={"VMAF": 95.0})
        rows = [original, worse, better]
        columns = {column.name: column for column in get_columns("crf", ["VMAF"], 3)}
        size_column, vmaf_column = columns["Size"], columns["VMAF"]

        self.assertTrue(is_best(vmaf_column, better, rows))
        self.assertFalse(is_best(vmaf_column, worse, rows))
        # The original video has no scores, so it is never the best.
        self.assertFalse(is_best(vmaf_column, original, rows))
        # Sizes are never highlighted, because a bigger file isn't better.
        self.assertFalse(is_best(size_column, better, rows))
        # Nothing is the best if there is only one transcode.
        self.assertFalse(is_best(vmaf_column, better, [original, better]))

    def test_bitrate_sources_are_listed_per_row_only_if_they_differ(self):
        """The note about how the bitrates were found lists each row only if they differ."""
        # If every row's bitrate was found the same way, a single line is enough.
        same = [
            ResultRow("a", "h264", 1, 1, "confidence = high"),
            ResultRow("b", "h264", 1, 1, "confidence = high"),
        ]
        self.assertEqual(describe_bitrate_sources(same), ["Video bitrate confidence = high"])

        # Otherwise each row is listed, so that a less reliable bitrate stands out.
        different = [same[0], ResultRow("b", "h264", 1, 1, "confidence = low")]
        self.assertEqual(
            describe_bitrate_sources(different),
            ["Video bitrate:", "  a: confidence = high", "  b: confidence = low"],
        )


class TestReusingSavedScores(unittest.TestCase):
    """When -sl reuses the scores saved by a previous run instead of calculating them again."""

    def setUp(self):
        # Each test gets an empty transcoded video in a temporary folder, deleted afterwards.
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.video = Path(folder.name) / "video.mkv"
        self.json_path = Path(folder.name) / "per_frame_metrics.json"
        self.video.write_text("")

    def save(self, data: dict, newer_than_video: bool = True) -> None:
        """Save data as the scores file, 10s newer (or older) than the transcoded video."""
        self.json_path.write_text(json.dumps(data))
        # Set the modification times explicitly, because they can be equal if set by writing.
        offset = 10 if newer_than_video else -10
        os.utime(self.json_path, (1000 + offset, 1000 + offset))
        os.utime(self.video, (1000, 1000))

    def reason(self) -> str | None:
        """Return why the saved scores can't be reused, if the current settings are these."""
        return reason_to_recalculate(self.json_path, self.video, {"n_subsample": 1})

    def test_reused_if_newer_and_calculated_with_the_same_settings(self):
        """Scores newer than the transcode, calculated with the same settings, are reused."""
        self.save({"vqm_settings": {"n_subsample": 1}})
        self.assertIsNone(self.reason())

    def test_not_reused(self):
        """Each reason that the saved scores are calculated again instead of being reused."""
        # Nothing has been saved yet.
        self.assertEqual(self.reason(), "it does not exist")
        # The video was transcoded again after the scores were saved, so they are out of date.
        self.save({"vqm_settings": {"n_subsample": 1}}, newer_than_video=False)
        self.assertEqual(self.reason(), "it is older than the transcoded video")
        # The scores were saved without their settings, e.g. by an older version of VQM.
        self.save({})
        self.assertEqual(self.reason(), "the settings used to calculate it are unknown")
        # The scores were calculated with a different -n value than the current one.
        self.save({"vqm_settings": {"n_subsample": 2}})
        self.assertEqual(self.reason(), "it was calculated with different settings")


class TestArgumentErrors(unittest.TestCase):
    """Invalid arguments are rejected with an error message.

    These exit before FFmpeg is used, so they don't need FFmpeg.
    """

    def assert_error(self, message: str, *arguments: str) -> None:
        """Check that main.py exits with argparse's error code (2) and the message."""
        result = run_main("-i", str(VIDEO), *arguments)
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn(message, result.stdout)

    def test_errors(self):
        """Arguments that can't be used together, or are missing, are rejected."""
        # -p without -v (or -c) doesn't say what to compare.
        self.assert_error("You must specify either combinations", "-p", "crf")
        # The phone model only exists in the default model file, not the 4K one.
        self.assert_error(
            "--phone-model together with --4k-model",
            "-p",
            "crf",
            "-v",
            "23",
            "--phone-model",
            "--4k-model",
        )
        # -t and Overview Mode are both ways of making a shorter reference video.
        self.assert_error(
            "-t/--transcode-length together with Overview Mode",
            "-p",
            "crf",
            "-v",
            "23",
            "-t",
            "1",
            "--interval",
            "5",
        )
        # 3s clips taken every 2s would overlap.
        self.assert_error(
            "may not be longer than the interval",
            "-p",
            "crf",
            "-v",
            "23",
            "--interval",
            "2",
            "-cl",
            "3",
        )

    def test_missing_input_video(self):
        """An input video that doesn't exist is rejected."""
        result = run_main("-i", "does_not_exist.mp4", "-p", "crf", "-v", "23")
        self.assertEqual(result.returncode, 2)
        self.assertIn("No file(s) found", result.stdout)


@unittest.skipUnless(ffmpeg_has_libvmaf(), "FFmpeg does not have the libvmaf filter")
class TestEndToEnd(unittest.TestCase):
    """Run the whole program on 1 second of ForBiggerFun.mp4 and check its output."""

    def setUp(self):
        # Each test saves its results in a temporary folder, which is deleted afterwards.
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        # The space and apostrophe check that paths are escaped correctly for libvmaf.
        self.output_folder = Path(folder.name) / "Sam's results"

    def run_vqm(self, *arguments: str) -> str:
        """Run VQM on ForBiggerFun.mp4, check that it succeeded and return its output."""
        result = run_main("-i", str(VIDEO), "-o", str(self.output_folder), *arguments)
        self.assertEqual(result.returncode, 0, result.stdout)
        return result.stdout

    def assert_scores(self, comparison_name: str, metrics: list[str]) -> None:
        """Check that libvmaf saved a score for each frame, for each of the metrics, and that
        the disabled metrics weren't calculated."""
        json_path = self.output_folder / comparison_name / "per_frame_metrics.json"
        frames = json.loads(json_path.read_text())["frames"]
        self.assertGreater(len(frames), 0)
        disabled_metrics = {"vmaf", "psnr_y", "float_ssim"} - set(metrics)
        for frame in frames:
            # libvmaf also logs other values (e.g. "integer_adm2"), which VQM doesn't use.
            for metric in metrics:
                self.assertIn(metric, frame["metrics"])
            for metric in disabled_metrics:
                self.assertNotIn(metric, frame["metrics"])

    def assert_report(self, *expected_text: str) -> None:
        """Check that report.html has the mean VMAF graph and the expected text."""
        report = (self.output_folder / "report.html").read_text(encoding="utf-8")
        self.assertIn("Mean VMAF", report)
        for text in expected_text:
            self.assertIn(text, report)

    def test_parameter_mode(self):
        """-p crf -v 30 40 compares two CRF values, using the first second of the video (-t 1)."""
        output = self.run_vqm("-p", "crf", "-v", "30", "40", "-t", "1", "-P")
        for crf in ("30", "40"):
            self.assert_scores(f"libx264_crf_{crf}", ["vmaf", "psnr_y", "float_ssim"])
        # -t 1 cuts the video, so the report has a row for the cut "Reference Video".
        self.assert_report("Reference Video", "Only the first 1s was used.")
        # -P prints the table.
        self.assertIn("Time Taken (s)", output)

    def test_combination_mode(self):
        """-c compares two combinations of presets and CRF values."""
        self.run_vqm("-c", "preset ultrafast crf 30,preset veryfast crf 40", "-t", "1")
        self.assert_scores("libx264_preset_ultrafast_crf_30", ["vmaf", "psnr_y", "float_ssim"])
        self.assert_scores("libx264_preset_veryfast_crf_40", ["vmaf", "psnr_y", "float_ssim"])
        self.assert_report("-preset ultrafast -crf 30")

    def test_overview_mode(self):
        """Overview Mode takes a 1s clip every 20s and compares the transcodes of them."""
        self.run_vqm("-p", "crf", "-v", "40", "--interval", "20", "-cl", "1")
        self.assertTrue((self.output_folder / "Overview_Video.mkv").exists())
        self.assert_scores("libx264_crf_40", ["vmaf", "psnr_y", "float_ssim"])
        self.assert_report("Overview Mode: a 1s clip was taken every 20s.")

    def test_options(self):
        """Disabled metrics, the 4K model, n_subsample and a video filter, used together."""
        self.run_vqm(
            "-p",
            "crf",
            "-v",
            "40",
            "-t",
            "1",
            "--disable-psnr",
            "--disable-ssim",
            "--4k-model",
            "-n",
            "2",
            "-vf",
            "hflip",
        )
        # PSNR and SSIM are disabled, so only VMAF is calculated.
        self.assert_scores("libx264_crf_40", ["vmaf"])
        self.assert_report("libvmaf n_subsample: 2", "Filter(s) applied")

    def test_phone_model(self):
        """The phone model works. It is passed to libvmaf as an extra model option."""
        self.run_vqm("-p", "crf", "-v", "40", "-t", "1", "--phone-model")
        self.assert_scores("libx264_crf_40", ["vmaf", "psnr_y", "float_ssim"])

    def test_rotated_video(self):
        """A video with a rotation, e.g. from a phone, is compared at its rotated resolution."""
        # A copy of the first second, stored as 1280x720 with a rotation of 90 degrees. FFmpeg
        # rotates it when decoding, so its frames are 720x1280.
        rotated_video = self.output_folder.parent / "rotated.mp4"
        subprocess.run(
            [
                "ffmpeg",
                "-loglevel",
                "error",
                "-display_rotation",
                "90",
                "-i",
                str(VIDEO),
                "-t",
                "1",
                "-c",
                "copy",
                str(rotated_video),
            ],
            check=True,
        )
        result = run_main(
            "-i", str(rotated_video), "-o", str(self.output_folder), "-p", "crf", "-v", "40"
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assert_scores("libx264_crf_40", ["vmaf", "psnr_y", "float_ssim"])
        # Both videos are 720x1280 when decoded, so there is no resolution mismatch.
        self.assertNotIn("Warning", result.stdout)

    def test_skipping_transcoding_and_reusing_scores(self):
        """-st and -sl reuse the previous run's transcode and scores, if they are still valid."""
        # The first run transcodes the video and calculates the scores.
        self.run_vqm("-p", "crf", "-v", "40", "-t", "1")

        # Running again with the same settings reuses both.
        output = self.run_vqm("-p", "crf", "-v", "40", "-t", "1", "-st", "-sl")
        self.assertIn("Skipping transcoding", output)
        self.assertIn("Skipping quality metrics calculation", output)

        # The scores are recalculated if the settings change.
        output = self.run_vqm("-p", "crf", "-v", "40", "-t", "1", "-st", "-sl", "--disable-ssim")
        self.assertIn("calculated with different settings", output)
        self.assert_scores("libx264_crf_40", ["vmaf", "psnr_y"])


if __name__ == "__main__":
    unittest.main()
