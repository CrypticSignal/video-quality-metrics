"""The FFmpeg commands that transcode the video and calculate the quality metrics."""

import shlex
import subprocess
from argparse import Namespace
from pathlib import Path
from time import perf_counter

from better_ffmpeg_progress import FfmpegProcess, FfmpegProcessError

from metrics import enabled_metrics
from utils import exit_program, fail, line, log

# The model files are relative to this file so that the program works from any directory.
VMAF_MODELS_FOLDER = Path(__file__).parent / "vmaf_models"


def vmaf_model_path(args: Namespace) -> Path:
    """Return the path of the VMAF model file to use."""
    model_file = "vmaf_4k_v0.6.1.json" if args.four_k_model else "vmaf_v0.6.1.json"
    return VMAF_MODELS_FOLDER / model_file


def check_ffmpeg() -> None:
    """Exit if FFmpeg or FFprobe can't be run, or if FFmpeg doesn't have the libvmaf filter."""
    for program in ("ffmpeg", "ffprobe"):
        try:
            subprocess.run([program, "-version"], capture_output=True, check=True)
        except (OSError, subprocess.CalledProcessError):
            exit_program(
                f"Unable to run {program}. Make sure that it is installed and in your PATH."
            )

    filters = subprocess.run(
        ["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True
    ).stdout
    # Each line is e.g. " ... libvmaf  VV->V  Calculate the VMAF between two video streams."
    if not any(line.split()[1:2] == ["libvmaf"] for line in filters.splitlines()):
        exit_program(
            "Your build of FFmpeg does not have the libvmaf filter.\n"
            "Builds that have it are listed in the FFmpeg Builds section of the README."
        )


def backslash_escape(value: str, special_characters: str) -> str:
    """Put a backslash before each backslash and each of the special characters."""
    for character in "\\" + special_characters:
        value = value.replace(character, f"\\{character}")
    return value


def quote_filter_option(value: str) -> str:
    """Quote and escape a filter option's value so that FFmpeg reads it unchanged.

    FFmpeg parses the value twice: once as part of the filtergraph and then
    as one of the filter's colon-separated options. In the quotes, each
    apostrophe must end the quote, be escaped and then start a new quote.
    """
    escaped = backslash_escape(value, "':")
    return "'" + escaped.replace("'", "'\\''") + "'"


def run_ffmpeg(command: list[str], message: str, args: Namespace) -> float:
    """Run an FFmpeg command with a progress bar and return the time taken in seconds."""
    line()
    log.info(f"{message}...\n")

    start_time = perf_counter()
    try:
        FfmpegProcess(command).run(print_command=args.debug)
    except FfmpegProcessError as error:
        # The error names the log file that contains FFmpeg's output.
        fail(str(error))
    time_taken = round(perf_counter() - start_time, args.decimal_places)

    log.info(f"Time Taken: {time_taken:.{args.decimal_places}f}s")
    return time_taken


def transcode_command(
    reference_video: str | Path, encoder_options: list[str], output_path: Path, args: Namespace
) -> list[str]:
    """Return the FFmpeg command that transcodes the video using the encoder options."""
    command = ["ffmpeg", "-y"]
    if args.input_options:
        command += shlex.split(args.input_options)
    # The audio is copied rather than re-encoded, so that the time taken is only the video
    # encoder's. FFmpeg uses the last value of an option, so an audio codec (or -an) in
    # --output-options replaces "-c:a copy".
    command += ["-i", str(reference_video), "-c:v", args.encoder, "-c:a", "copy"]
    if args.output_options:
        command += shlex.split(args.output_options)
    if args.encoder == "libaom-av1":
        command += ["-b:v", "0", "-cpu-used", str(args.av1_cpu_used)]
    return command + encoder_options + [str(output_path)]


# The containers that a transcode can be saved in if the original video is in one, so that the
# Size column compares like with like. Other formats are raw streams without timestamps (e.g.
# .h264) or can't hold compressed video (e.g. .y4m), so MKV is used for them. AVI isn't
# included because it can't store the timestamps of B-frames, which most encoders use.
CONTAINERS = {".mp4", ".m4v", ".mov", ".mkv", ".webm", ".ts", ".m2ts", ".mts"}


def choose_container(
    original_video: str | Path,
    reference_video: str | Path,
    encoder_options: list[str],
    folder: Path,
    args: Namespace,
) -> str:
    """Return the file extension to save the transcode with, e.g. ".mp4".

    This is the original video's extension if its container can hold the transcode's streams,
    otherwise ".mkv", which can hold almost any codec. FFmpeg doesn't have a way of asking
    whether a container supports a codec, so a test transcode of the first frame is made.
    """
    extension = Path(original_video).suffix.lower()
    if extension == ".mkv":
        return extension
    if extension not in CONTAINERS:
        name = extension or "a file without an extension"
        log.info(
            f"The transcode will be saved as MKV, because {name} is not one of the containers "
            "that transcodes can be saved in."
        )
        return ".mkv"

    test_path = folder / f"container_test{extension}"
    command = transcode_command(reference_video, encoder_options, test_path, args)
    # -frames:v and -t go just before the output path, so that they replace any in the options.
    command[-1:-1] = ["-frames:v", "1", "-t", "1"]
    result = subprocess.run(
        command[:1] + ["-v", "error"] + command[1:], capture_output=True, text=True
    )
    test_path.unlink(missing_ok=True)

    if result.returncode == 0:
        return extension
    log.info(
        f"The transcode will be saved as MKV, because FFmpeg could not save a test transcode as "
        f"{extension}. Its error was:\n{result.stderr.strip()}"
    )
    return ".mkv"


def transcode(
    reference_video: str | Path,
    encoder_options: list[str],
    output_path: Path,
    args: Namespace,
) -> float:
    """Transcode the video using the encoder options, e.g. ["-crf", "23"].

    Returns the time taken in seconds.
    """
    command = transcode_command(reference_video, encoder_options, output_path, args)
    description = " ".join(encoder_options)
    time_taken = run_ffmpeg(command, f"Transcoding {reference_video} using '{description}'", args)
    log.info(f"Output file: {output_path}")
    return time_taken


def calculate_quality_metrics(
    reference_video: str | Path,
    distorted_video: Path,
    json_path: Path,
    reference_resolution: tuple[int, int] | None,
    args: Namespace,
) -> None:
    """Use libvmaf to compare the distorted video against the reference video.

    The per-frame scores are saved to json_path. reference_resolution is the reference video's
    resolution after the -vf filters, or None if it couldn't be found.
    """
    # The model option is parsed again by libvmaf, as key=value pairs separated by colons.
    # This matters for absolute paths, e.g. "C:/Users" or "/Users/Sam's Mac".
    model_path = backslash_escape(vmaf_model_path(args).as_posix(), "':=")
    model = f"path={model_path}"
    if args.phone_model:
        # A colon adds an option to the same model, whereas "|" would start a second model.
        model += ":enable_transform=true"

    # libvmaf expects forward slashes in the log path.
    log_path = quote_filter_option(json_path.as_posix())

    vmaf_options = (
        f"model={quote_filter_option(model)}:log_fmt=json:log_path={log_path}"
        f":n_subsample={args.n_subsample}:n_threads={args.n_threads}"
    )

    features = []
    if not args.disable_psnr:
        features.append("name=psnr")
    if not args.disable_ssim:
        features.append("name=float_ssim")
    if features:
        vmaf_options += f":feature={'|'.join(features)}"

    video_filters = f"{args.video_filters}," if args.video_filters else ""
    # libvmaf needs both videos to have the same resolution, so if the transcode was scaled
    # (e.g. with --output-options), scale it back. This does nothing if they already match.
    # The scale2ref filter isn't used for this because it has two outputs, and a filter with
    # several outputs can make FFmpeg 7 fail with "Assertion best_input >= 0 failed".
    scale = ""
    if reference_resolution:
        width, height = reference_resolution
        scale = f"scale={width}:{height}:flags=bicubic,"
    filtergraph = (
        f"[0:V]{video_filters}setpts=PTS-STARTPTS[reference];"
        f"[1:V]{scale}setpts=PTS-STARTPTS[distorted];"
        f"[distorted][reference]libvmaf={vmaf_options}[vmaf]"
    )

    # As an input option, -r makes FFmpeg ignore the timestamps in the file and give the frames
    # evenly spaced timestamps at that frame rate. Doing this to both videos means that libvmaf
    # pairs the frames by their order, even if the timestamps differ (e.g. a variable frame rate
    # or a different start time). The value itself doesn't matter, as long as both are the same.
    command = [
        "ffmpeg",
        "-r",
        "24",
        "-i",
        str(reference_video),
        "-r",
        "24",
        "-i",
        str(distorted_video),
        "-lavfi",
        filtergraph,
        # Only libvmaf's output is mapped. Mapping the input videos as well (-map 0:V -map 1:V)
        # adds each of them as an extra output stream, so they are decoded twice, and the extra
        # outputs can make FFmpeg 7 fail with "Assertion best_input >= 0 failed".
        "-map",
        "[vmaf]",
        "-f",
        "null",
        "-",
    ]

    metrics = enabled_metrics(args)
    run_ffmpeg(command, f"Calculating the {'/'.join(metrics)} of {distorted_video}", args)
