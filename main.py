import glob
import json
import re
import sys
from argparse import Namespace
from dataclasses import dataclass
from pathlib import Path
from statistics import fmean

from args import parser
from ffmpeg_tasks import (
    calculate_quality_metrics,
    check_ffmpeg,
    quality_metrics_settings,
    transcode,
)
from graphs import plot_mean_vmaf_graph, plot_per_frame_graph
from metrics import enabled_metrics, read_per_frame_scores
from reference_video import create_overview_video, cut_video
from report import write_report
from results import ResultRow, describe_bitrate_sources, print_results
from utils import line, log, setup_logging
from video_info import (
    count_video_frames,
    get_duration,
    get_filtered_resolution,
    get_frame_rate,
    get_resolution,
    get_video_bitrate,
    get_video_stream,
    probe,
)

# Update this whenever the program is changed.
VERSION_DATE = "31st October 2026"


def sanitise(name: str) -> str:
    """Replace any character that may not be valid in a file or folder name."""
    return re.sub(r"[^a-zA-Z0-9_-]", "_", name)


@dataclass
class Comparison:
    """One set of encoder options to test, e.g. "-crf 23" or "-preset slow -crf 24"."""

    label: str  # Shown in the table and the bar graph.
    encoder_options: list[str]
    name: str  # Used to name the output folder and the transcoded video.


def get_comparisons(args: Namespace) -> list[Comparison]:
    if args.combinations:
        comparisons = []
        # e.g. "preset slow crf 24,preset medium crf 23"
        for combination in args.combinations.split(","):
            words = combination.split()
            # e.g. ["preset", "slow", "crf", "24"] -> ["-preset", "slow", "-crf", "24"]
            options = [f"-{word}" if i % 2 == 0 else word for i, word in enumerate(words)]
            name = "_".join(words)
            comparisons.append(
                Comparison(" ".join(options), options, sanitise(f"{args.encoder}_{name}"))
            )
        return comparisons

    return [
        Comparison(
            value,
            [f"-{args.parameter}", value],
            sanitise(f"{args.encoder}_{args.parameter}_{value}"),
        )
        for value in args.values
    ]


def get_folder_names(input_videos: list[str]) -> dict[str, str]:
    """Return the name to base each video's output folder on.

    This is the filename, unless another input video has the same filename (e.g. a/clip.mp4 and
    b/clip.mp4), in which case the whole path is used so that the results don't overwrite each
    other.
    """
    filenames = [Path(video).name for video in input_videos]
    return {
        video: filename if filenames.count(filename) == 1 else video
        for video, filename in zip(input_videos, filenames)
    }


def get_output_folder(filename: str, args: Namespace, multiple_inputs: bool) -> Path:
    if args.interval:
        name = f"{filename}_overview_mode"
    elif args.combinations:
        name = f"{filename}_combination_mode"
    else:
        name = filename

    # The user's own folder is used as given, so that it can be a path or contain spaces.
    # Only the names that this program generates are sanitised.
    if not args.output_folder:
        output_folder = Path(sanitise(name))
    elif multiple_inputs:
        # Give each video its own subfolder so that the results don't overwrite each other.
        output_folder = Path(args.output_folder) / sanitise(name)
    else:
        output_folder = Path(args.output_folder)

    output_folder.mkdir(parents=True, exist_ok=True)
    return output_folder


def video_row(
    label: str, encoder: str, video_path: str | Path, info: dict, args: Namespace
) -> ResultRow:
    """Return the table row of a video, without any quality metrics."""
    bitrate, bitrate_source = get_video_bitrate(video_path, info, args.decimal_places)
    return ResultRow(
        label, encoder, int(info["format"]["size"]), bitrate, bitrate_source, get_duration(info)
    )


def get_codec(info: dict) -> str:
    video_stream = get_video_stream(info)
    return video_stream.get("codec_name", "N/A") if video_stream else "N/A"


def get_notes(filename: str, rows: list[ResultRow], args: Namespace) -> list[str]:
    """Return the notes that go underneath the table."""
    notes = describe_bitrate_sources(rows) + [f"Original File: {filename}"]
    if args.transcode_length:
        notes.append(f"Only the first {args.transcode_length:g}s was used.")
    if args.interval:
        notes.append(
            f"Overview Mode: a {args.clip_length}s clip was taken every {args.interval}s."
        )
    notes.append(f"FFmpeg output options: {args.output_options}")
    if args.video_filters:
        notes.append(
            "Filter(s) applied to original video before quality metrics calculation: "
            f"{args.video_filters}"
        )
    notes.append(f"libvmaf n_subsample: {args.n_subsample}")
    return notes


# The key that the settings used to calculate the quality metrics are saved under, in libvmaf's
# JSON log.
SETTINGS_KEY = "vqm_settings"


def save_settings(json_path: Path, settings: dict) -> None:
    """Add the settings used to calculate the quality metrics to libvmaf's JSON log."""
    data = json.loads(json_path.read_text(encoding="utf-8"))
    data[SETTINGS_KEY] = settings
    json_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def reason_to_recalculate(json_path: Path, transcoded_video: Path, settings: dict) -> str | None:
    """Return why the saved quality metrics can't be reused, or None if they can."""
    if not json_path.exists():
        return "it does not exist"
    if json_path.stat().st_mtime <= transcoded_video.stat().st_mtime:
        return "it is older than the transcoded video"
    try:
        saved_settings = json.loads(json_path.read_text(encoding="utf-8")).get(SETTINGS_KEY)
    except (OSError, ValueError):
        return "it could not be read"
    if saved_settings is None:
        return "the settings used to calculate it are unknown"
    if saved_settings != settings:
        return "it was calculated with different settings"
    return None


def run_comparison(
    comparison: Comparison,
    reference_video: str | Path,
    reference_frame_count: int | None,
    reference_resolution: tuple[int, int] | None,
    output_folder: Path,
    metrics: list[str],
    args: Namespace,
) -> ResultRow:
    """Transcode the reference video, calculate the quality metrics and return the table row."""
    folder = output_folder / comparison.name
    folder.mkdir(exist_ok=True)
    transcoded_video = folder / f"{comparison.name}.mkv"
    json_path = folder / "per_frame_metrics.json"

    if args.skip_transcoding and transcoded_video.exists():
        log.info(f"{transcoded_video} exists. Skipping transcoding.")
        transcode_time = None
    else:
        transcode_time = transcode(
            reference_video, comparison.encoder_options, transcoded_video, args
        )

    # libvmaf compares the frames in order, so a frame that was dropped or duplicated when
    # transcoding means that every frame after it is compared against the wrong frame.
    frame_count = count_video_frames(transcoded_video)
    if reference_frame_count and frame_count and frame_count != reference_frame_count:
        log.warning(
            f"Warning: {transcoded_video} has {frame_count} frames but the reference video has "
            f"{reference_frame_count}, so the quality metrics may be inaccurate."
        )

    # The transcode is scaled to the reference's resolution so that libvmaf can compare them.
    # This is expected if the transcode was scaled on purpose, but it also happens if e.g. the
    # reference was cropped with -vf and the transcode wasn't, which makes the scores meaningless.
    transcoded_info = probe(transcoded_video)
    resolution = get_resolution(transcoded_info)
    if reference_resolution and resolution and resolution != reference_resolution:
        log.warning(
            f"Warning: {transcoded_video} is {resolution[0]}x{resolution[1]} but the reference "
            f"video is {reference_resolution[0]}x{reference_resolution[1]}"
            + (" after the -vf filter(s)" if args.video_filters else "")
            + ", so the transcode will be scaled to that resolution before the quality metrics "
            "are calculated. If you didn't intend to change the resolution, check that the "
            "same filters were applied to the transcode (e.g. with --output-options)."
        )

    # The scores are only reused if they were calculated after the video was last transcoded,
    # and with the same settings. Otherwise, e.g. a metric that was disabled last time would be
    # missing, or scores calculated with a different model would be shown.
    settings = quality_metrics_settings(args)
    reason = None
    if args.skip_libvmaf:
        reason = reason_to_recalculate(json_path, transcoded_video, settings)
    if args.skip_libvmaf and reason is None:
        log.info(f"{json_path} exists. Skipping quality metrics calculation.")
    else:
        if reason:
            log.info(f"Not reusing {json_path} because {reason}.")
        calculate_quality_metrics(reference_video, transcoded_video, json_path, args)
        save_settings(json_path, settings)

    frame_numbers, scores = read_per_frame_scores(json_path, metrics)
    row = video_row(comparison.label, args.encoder, transcoded_video, transcoded_info, args)
    row.transcode_time = transcode_time
    for metric in metrics:
        row.mean_scores[metric] = fmean(scores[metric])
        row.per_frame_graphs[metric] = plot_per_frame_graph(
            metric,
            frame_numbers,
            scores[metric],
            f"{row.mean_scores[metric]:.{args.decimal_places}f}",
            args.n_subsample,
        )
    return row


def process_video(
    input_video: str, folder_name: str, args: Namespace, multiple_inputs: bool
) -> None:
    filename = Path(input_video).name
    metrics = enabled_metrics(args)

    line()
    log.info(f"Here's some information about {filename}:")
    info = probe(input_video)
    rows = [video_row("Original Video", get_codec(info), input_video, info, args)]
    log.info(f"Frame rate: {get_frame_rate(info)} FPS")
    for stream in info["streams"]:
        log.info(
            f"Stream {stream['index']} | {stream['codec_type']} | "
            f"Codec: {stream.get('codec_long_name', 'N/A')}"
        )
    line()

    if args.video_filters:
        log.info(f"The following filter(s) will be used:\n{args.video_filters}")
        line()

    output_folder = get_output_folder(folder_name, args, multiple_inputs)

    # The reference video is what gets transcoded and what the transcodes are compared against.
    reference_video = input_video
    if args.transcode_length:
        reference_video = cut_video(input_video, output_folder, args.transcode_length)
    if args.interval:
        log.info("Overview Mode activated.")
        reference_video = create_overview_video(
            input_video, output_folder, args.interval, args.clip_length
        )

    if reference_video != input_video:
        # The transcodes are made from the cut or overview video, so their size and duration
        # should be compared with it rather than with the whole original video.
        reference_info = probe(reference_video)
        rows.append(
            video_row(
                "Reference Video", get_codec(reference_info), reference_video, reference_info, args
            )
        )

    first_column = "Combination" if args.combinations else args.parameter
    title = f"Video Quality Metrics: {filename}"
    report_path = output_folder / "report.html"

    def write_results(mean_vmaf_graph: str | None = None) -> None:
        write_report(
            report_path,
            title,
            first_column,
            metrics,
            rows,
            get_notes(filename, rows, args),
            mean_vmaf_graph,
            args.decimal_places,
        )

    reference_frame_count = count_video_frames(reference_video)
    if args.video_filters:
        reference_resolution = get_filtered_resolution(reference_video, args.video_filters)
    else:
        reference_resolution = get_resolution(probe(reference_video))
    comparisons = get_comparisons(args)
    log.info(f"Comparing: {', '.join(c.label for c in comparisons)}")
    for comparison in comparisons:
        rows.append(
            run_comparison(
                comparison,
                reference_video,
                reference_frame_count,
                reference_resolution,
                output_folder,
                metrics,
                args,
            )
        )
        # Write the results after each comparison so that they are kept if the program stops.
        write_results()

    transcodes = [row for row in rows if row.is_transcode]
    mean_vmaf_graph = plot_mean_vmaf_graph(
        first_column,
        [row.label for row in transcodes],
        [row.mean_scores["VMAF"] for row in transcodes],
        args.decimal_places,
    )
    write_results(mean_vmaf_graph)

    line()
    log.info(f"Open {report_path} in a web browser to see the results.")

    if args.print:
        print_results(
            first_column, metrics, rows, get_notes(filename, rows, args), args.decimal_places
        )


def main() -> None:
    if len(sys.argv) == 1:
        print('For details about the available arguments, enter "python main.py -h"')
        return

    args = parser.parse_args()
    if not args.combinations and not (args.parameter and args.values):
        parser.error(
            "You must specify either combinations (-c) or a parameter (-p) and values (-v)."
        )
    if args.phone_model and args.four_k_model:
        # The phone model is a transform defined in the default model file, which the 4K
        # model file does not have.
        parser.error("You cannot use --phone-model together with --4k-model.")
    if args.transcode_length and args.interval:
        parser.error("You cannot use -t/--transcode-length together with Overview Mode.")
    if args.interval and args.clip_length > args.interval:
        # The clips would overlap, so some frames would be in the overview video twice.
        parser.error(
            f"The clip length ({args.clip_length}s) may not be longer than the interval "
            f"({args.interval}s)."
        )

    # The input can be a path or a glob pattern.
    if Path(args.input_video).exists():
        input_videos = [args.input_video]
    else:
        # recursive=True makes "**" match any number of subfolders, e.g. "videos/**/*.mp4".
        input_videos = sorted(
            path for path in glob.glob(args.input_video, recursive=True) if Path(path).is_file()
        )
    if not input_videos:
        parser.error(f"No file(s) found at the specified path or glob pattern: {args.input_video}")

    setup_logging()
    line()
    log.info("Video Quality Metrics")
    log.info(f"Version Date: {VERSION_DATE}")
    check_ffmpeg()

    folder_names = get_folder_names(input_videos)
    for input_video in input_videos:
        process_video(input_video, folder_names[input_video], args, len(input_videos) > 1)


if __name__ == "__main__":
    main()
