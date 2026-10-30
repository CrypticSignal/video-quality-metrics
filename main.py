import glob
import re
import sys
from argparse import Namespace
from dataclasses import dataclass
from pathlib import Path
from statistics import fmean

from prettytable import PrettyTable

from args import parser
from ffmpeg_tasks import calculate_quality_metrics, check_ffmpeg, transcode
from graphs import plot_mean_vmaf_graph, plot_per_frame_graph
from metrics import enabled_metrics, read_per_frame_scores, summarise
from reference_video import create_overview_video, cut_video
from utils import format_si, line, log, setup_logging
from video_info import (
    describe_video_bitrate,
    get_duration,
    get_frame_rate,
    get_video_stream,
    probe,
)


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


def get_output_folder(filename: str, args: Namespace, multiple_inputs: bool) -> Path:
    if args.interval:
        name = f"{filename}_overview_mode"
    elif args.combinations:
        name = f"{filename}_combination_mode"
    else:
        name = filename

    if not args.output_folder:
        output_folder = Path(sanitise(name))
    elif multiple_inputs:
        # Give each video its own subfolder so that the results don't overwrite each other.
        output_folder = Path(sanitise(args.output_folder)) / sanitise(name)
    else:
        output_folder = Path(sanitise(args.output_folder))

    output_folder.mkdir(parents=True, exist_ok=True)
    return output_folder


def describe_video(video_path: str | Path, info: dict, args: Namespace) -> list[str]:
    """Return the size, bitrate and duration of the video, for the table."""
    size = format_si(int(info["format"]["size"]), "B", args.decimal_places)
    bitrate = describe_video_bitrate(video_path, info, args.decimal_places)
    duration = f"{get_duration(info):.{args.decimal_places}f} s"
    return [size, bitrate, duration]


def write_table(table: PrettyTable, table_path: Path, metrics: list[str]) -> None:
    with open(table_path, "w", encoding="utf-8") as f:
        f.write(f"{'/'.join(metrics)} values are in the format: Min | Standard Deviation | Mean\n")
        f.write(table.get_string())


def run_comparison(
    comparison: Comparison,
    reference_video: str | Path,
    output_folder: Path,
    metrics: list[str],
    args: Namespace,
) -> tuple[list, float]:
    """Transcode the reference video and calculate the quality metrics.

    Returns the table row and the mean VMAF.
    """
    folder = output_folder / comparison.name
    folder.mkdir(exist_ok=True)
    transcoded_video = folder / f"{comparison.name}.mkv"
    json_path = folder / "per_frame_metrics.json"

    if args.skip_transcoding and transcoded_video.exists():
        log.info(f"{transcoded_video} exists. Skipping transcoding.")
        transcode_time = "-"
    else:
        transcode_time = transcode(
            reference_video, comparison.encoder_options, transcoded_video, args
        )

    if args.skip_libvmaf and json_path.exists():
        log.info(f"{json_path} exists. Skipping quality metrics calculation.")
    else:
        calculate_quality_metrics(reference_video, transcoded_video, json_path, args)

    frame_numbers, scores = read_per_frame_scores(json_path, metrics)
    for metric in metrics:
        mean_score = f"{fmean(scores[metric]):.{args.decimal_places}f}"
        plot_per_frame_graph(
            metric, frame_numbers, scores[metric], mean_score, args.n_subsample, folder / metric
        )

    row = (
        [comparison.label, args.encoder, transcode_time]
        + describe_video(transcoded_video, probe(transcoded_video), args)
        + [summarise(scores[metric], args.decimal_places) for metric in metrics]
    )
    return row, fmean(scores["VMAF"])


def process_video(input_video: str, args: Namespace, multiple_inputs: bool) -> None:
    filename = Path(input_video).name
    metrics = enabled_metrics(args)

    line()
    log.info(f"Here's some information about {filename}:")
    info = probe(input_video)
    video_stream = get_video_stream(info)
    codec = video_stream.get("codec_name", "N/A") if video_stream else "N/A"
    original_video_details = describe_video(input_video, info, args)
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

    output_folder = get_output_folder(filename, args, multiple_inputs)

    # The reference video is what gets transcoded and what the transcodes are compared against.
    reference_video = input_video
    if args.transcode_length:
        reference_video = cut_video(input_video, output_folder, args.transcode_length)
    if args.interval:
        log.info("Overview Mode activated.")
        reference_video = create_overview_video(
            input_video, output_folder, args.interval, args.clip_length
        )

    table = PrettyTable()
    table.field_names = [
        "Combination" if args.combinations else args.parameter,
        "Encoder",
        "Transcode Time (s)",
        "Size",
        "Video Bitrate | Confidence | Method",
        "Duration",
    ] + metrics
    table.add_row(["Original Video", codec, "-"] + original_video_details + ["-"] * len(metrics))
    table_path = output_folder / "metrics_table.txt"

    comparisons = get_comparisons(args)
    log.info(f"Comparing: {', '.join(c.label for c in comparisons)}")
    mean_vmafs = []
    for comparison in comparisons:
        row, mean_vmaf = run_comparison(comparison, reference_video, output_folder, metrics, args)
        table.add_row(row)
        mean_vmafs.append(mean_vmaf)
        # Write the table after each comparison so that results are kept if the program stops.
        write_table(table, table_path, metrics)

    supplementary_info = (
        f"\nOriginal File: {filename}\n"
        + (
            f"Only the first {args.transcode_length:g}s was used.\n"
            if args.transcode_length
            else ""
        )
        + f"FFmpeg output options: {args.output_options}\n"
        + (
            f"Filter(s) applied to original video before quality metrics calculation: "
            f"{args.video_filters}\n"
            if args.video_filters
            else ""
        )
        + f"libvmaf n_subsample: {args.n_subsample}"
    )
    with open(table_path, "a", encoding="utf-8") as f:
        f.write(supplementary_info)

    x_label = "Combination" if args.combinations else args.parameter
    plot_mean_vmaf_graph(
        x_label,
        [c.label for c in comparisons],
        mean_vmafs,
        args.decimal_places,
        output_folder / f"{x_label} vs VMAF",
    )

    line()
    log.info(f"Check out the contents of the '{output_folder}' folder.")

    if args.print:
        print(table.get_string())
        print(supplementary_info)


def main() -> None:
    if len(sys.argv) == 1:
        print('For details about the available arguments, enter "python main.py -h"')
        return

    args = parser.parse_args()
    if not args.combinations and not (args.parameter and args.values):
        parser.error(
            "You must specify either combinations (-c) or a parameter (-p) and values (-v)."
        )
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
        input_videos = sorted(glob.glob(args.input_video))
    if not input_videos:
        parser.error(f"No file(s) found at the specified path or glob pattern: {args.input_video}")

    setup_logging()
    line()
    log.info("Video Quality Metrics")
    log.info("Version Date: 3rd May 2026")
    check_ffmpeg()

    for input_video in input_videos:
        process_video(input_video, args, len(input_videos) > 1)


if __name__ == "__main__":
    main()
