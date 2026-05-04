import glob
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from prettytable import PrettyTable

from args import parser
from libvmaf import run_libvmaf
from metrics import extract_mean_vmaf, process_metrics
from overview import create_overview_video
from transcode_video import transcode_video
from utils import (
    Logger,
    Timer,
    VideoInfoProvider,
    cut_video,
    exit_program,
    force_decimal_places,
    format_value,
    get_metrics_list,
    line,
    plot_graph,
    write_supplementary_info,
)

log = Logger("main.py")


def get_video_info(
    input_video: str, decimal_places: int
) -> Tuple[str, str, float, str, Dict[str, Any]]:
    provider = VideoInfoProvider(input_video)

    return (
        input_video,
        provider.get_framerate_fraction(),
        provider.get_framerate_float(),
        provider.get_video_bitrate_str(decimal_places),
        provider.get_all_info(),
    )


def initialize_table(args: Any) -> PrettyTable:
    table = PrettyTable()
    metrics_list = get_metrics_list(args)

    column_names = [
        "Combination" if args.combinations else args.parameter,
        "Encoder",
        "Transcode Time (s)",
        "Size",
        "Video Bitrate | Confidence | Method",
        "Duration",
    ] + metrics_list

    table.field_names = column_names
    return table


def build_output_paths(output_folder: str, subfolder: str, filename: str) -> Tuple[str, str]:
    current_output_folder = str(Path(output_folder) / subfolder)
    os.makedirs(current_output_folder, exist_ok=True)

    output_path = str(Path(current_output_folder) / filename)

    return current_output_folder, output_path


def transcode_and_analyse(
    video_path: str,
    output_path: str,
    json_file_path: str,
    args: Any,
    value: Optional[str],
    combination_list: Optional[List[str]],
    description: str,
) -> Tuple[float, str]:
    if os.path.exists(output_path) and args.skip_transcoding:
        log.info(f"{output_path} exists. Skipping transcoding.")  #
        return 0.0

    time_taken_to_transcode = transcode_video(
        video_path,
        args,
        value,
        output_path,
        f"Transcoding {video_path} using {description}",
        combination_list,
    )

    if os.path.exists(json_file_path) and args.skip_libvmaf:
        log.info(f"{json_file_path} exists. Skipping quality metrics calculation.")
        return time_taken_to_transcode

    run_libvmaf(
        output_path,
        args,
        json_file_path,
        video_path,
        f" achieved with {description}",
    )

    return time_taken_to_transcode


def update_metrics(
    output_folder: str,
    current_output_folder: str,
    output_path: str,
    json_file_path: str,
    time_taken: float,
    value: str,
    args: Any,
    table: PrettyTable,
) -> float:
    provider = VideoInfoProvider(output_path)

    try:
        size_bytes = os.path.getsize(output_path)
    except OSError:
        size_bytes = 0

    size = format_value(size_bytes, args.decimal_places)
    bitrate = provider.get_video_bitrate_str(args.decimal_places)
    duration = provider.get_duration_str(args.decimal_places)

    process_metrics(
        str(Path(output_folder) / "metrics_table.txt"),
        json_file_path,
        args,
        args.decimal_places,
        [size, bitrate, duration],
        table,
        current_output_folder,
        time_taken,
        value,
    )

    vmaf_mean = extract_mean_vmaf(json_file_path)
    return float(vmaf_mean) if vmaf_mean != "N/A" else 0.0


def run_pipeline(
    video_path: str,
    output_path: str,
    current_output_folder: str,
    args: Any,
    value: Optional[str],
    combination_list: Optional[List[str]],
    description: str,
    output_folder: str,
    table: PrettyTable,
) -> float:
    json_file_path = str(Path(output_folder) / "per_frame_metrics.json")

    time_taken, json_file_path = transcode_and_analyse(
        video_path,
        output_path,
        json_file_path,
        args,
        value,
        combination_list,
        description,
    )

    vmaf_score = update_metrics(
        output_folder,
        current_output_folder,
        output_path,
        json_file_path,
        time_taken,
        description,
        args,
        table,
    )

    return float(vmaf_score)


def process_combination(
    combination: str,
    video_path: str,
    output_folder: str,
    args: Any,
    table: PrettyTable,
    vmaf_scores: List[float],
) -> float:
    # Filter out empty strings in case of multiple spaces
    parts = [p for p in combination.split(" ") if p]
    combination_list = [f"-{v}" if i % 2 == 0 else v for i, v in enumerate(parts)]
    combination_str = "_".join(parts)

    subfolder = f"{args.encoder}_" + combination_str
    filename = f"{combination_str}.mkv"

    current_output_folder, output_path = build_output_paths(output_folder, subfolder, filename)

    description = f"combination '{' '.join(combination_list)}'"

    vmaf_score = run_pipeline(
        video_path,
        output_path,
        current_output_folder,
        args,
        None,
        combination_list,
        description,
        output_folder,
        table,
    )

    vmaf_scores.append(vmaf_score)
    return vmaf_score


def process_parameter_value(
    value: str,
    video_path: str,
    output_folder: str,
    args: Any,
    table: PrettyTable,
    vmaf_scores: List[float],
) -> float:
    subfolder = f"{args.encoder}_{args.parameter}_{value}"
    filename = f"{value}.mkv"

    current_output_folder, output_path = build_output_paths(output_folder, subfolder, filename)

    description = f"'-{args.parameter} {value}'"

    vmaf_score = run_pipeline(
        video_path,
        output_path,
        current_output_folder,
        args,
        value,
        None,
        description,
        output_folder,
        table,
    )

    vmaf_scores.append(vmaf_score)
    return vmaf_score


def prepare_video(video_path: str, filename: str, output_folder: str, args: Any) -> str:
    if args.transcode_length:
        video_path = cut_video(
            video_path,
            filename,
            args,
            ".mkv",
            output_folder,
            str(Path(output_folder) / "metrics_table.txt"),
        )

    if args.interval is not None:
        log.info("Overview mode activated.")

        result, concatenated_video = create_overview_video(
            video_path, output_folder, args.interval, str(args.clip_length)
        )
        if result:
            video_path = concatenated_video
        else:
            exit_program("Failed to create overview video.")

    return video_path


def define_output_folder(filename: str, args: Any) -> str:
    if args.output_folder:
        output_folder = args.output_folder
    elif args.interval:
        output_folder = f"{filename}_overview_mode"
    elif args.combinations:
        output_folder = f"{filename}_combination_mode"
    else:
        output_folder = filename

    output_folder = re.sub(r"[^a-zA-Z0-9_-]", "_", output_folder)
    os.makedirs(output_folder, exist_ok=True)

    return output_folder


def finalise(
    filename: str,
    output_folder: str,
    original_video_bitrate: str,
    args: Any,
    vmaf_scores: List[float],
) -> str:
    mean_vmaf = "0.000"
    if vmaf_scores:
        mean_vmaf = force_decimal_places(np.mean(vmaf_scores), args.decimal_places)

    supplementary_info = write_supplementary_info(
        str(Path(output_folder) / "metrics_table.txt"),
        filename,
        args,
    )

    parameter = args.parameter if args.parameter else "Combination"
    values = args.values if args.values else args.combinations.split(",")

    plot_graph(
        f"{parameter} vs VMAF",
        parameter,
        "VMAF",
        values,
        vmaf_scores,
        mean_vmaf,
        str(Path(output_folder) / f"{parameter} vs VMAF"),
        bar_graph=True,
    )

    return supplementary_info


def begin(args: Any, input_video: str) -> None:
    video_path, fps, fps_float, original_video_bitrate, input_video_info = get_video_info(
        input_video, args.decimal_places
    )

    table = initialize_table(args)

    duration = 0.0
    try:
        duration = float(input_video_info.get("format", {}).get("duration", 0.0))
    except (ValueError, TypeError):
        pass

    size = 0
    try:
        size = int(input_video_info.get("format", {}).get("size", 0))
    except (ValueError, TypeError):
        pass

    streams = input_video_info.get("streams", [])
    codec_name = streams[0].get("codec_name", "N/A") if streams else "N/A"

    row = [
        "Original Video",
        codec_name,
        "-",
        format_value(size, args.decimal_places),
        original_video_bitrate,
        f"{duration:.{args.decimal_places}f} s",
        "-",
        "-",
        "-",
    ]

    table.add_row(row)

    vmaf_scores: List[float] = []

    filename = Path(input_video).name

    line()
    log.info("Here's some information about the original video:")
    log.info(f"Filename: {filename}")
    log.info(f"Video Bitrate | Confidence | Method:\n{original_video_bitrate}")
    log.info(f"Frame rate: {fps} ({fps_float}) FPS")

    for stream in streams:
        log.info(
            f"Stream {stream.get('index', 'N/A')} | {stream.get('codec_type', 'N/A')} | Codec: {stream.get('codec_long_name', 'N/A')}"
        )

    line()
    timer = Timer()

    if args.video_filters:
        log.info("The following filter(s) will be used:")
        log.info(args.video_filters)
        line()

    output_folder = define_output_folder(filename, args)
    video_path = prepare_video(video_path, filename, output_folder, args)

    if args.combinations:
        log.info("Combination Mode activated.")
        for combination in args.combinations.split(","):
            process_combination(combination, video_path, output_folder, args, table, vmaf_scores)
    else:
        log.info(f"Values of {args.encoder}'s '-{args.parameter}' parameter will be compared.")
        log.info(
            f"The following values will be compared: {', '.join(str(v) for v in args.values)}"
        )

        for value in args.values:
            process_parameter_value(value, video_path, output_folder, args, table, vmaf_scores)

    line()
    time_taken = timer.stop(args.decimal_places)
    log.info(f"Total Time Taken: {force_decimal_places(time_taken, args.decimal_places)}s")

    supplementary_info = finalise(
        filename, output_folder, original_video_bitrate, args, vmaf_scores
    )

    line()
    log.info(f"Check out the contents of the '{output_folder}' folder.")

    if args.print:
        print(table.get_string())
        print(supplementary_info)


def resolve_input_videos(input_path: str) -> List[str]:
    if os.path.exists(input_path):
        return [input_path]

    return glob.glob(input_path)


def main() -> None:
    if len(sys.argv) == 1:
        line()
        log.info('For more details about the available arguments, enter "python main.py -h"')
        line()
        return

    line()
    log.info("Video Quality Metrics")
    log.info("Version Date: 3rd May 2026")

    # Clear previous logs if they exist
    if os.path.exists("logs.log"):
        try:
            with open("logs.log", "w", encoding="utf-8") as f:
                f.truncate(0)
        except OSError:
            pass

    args = parser.parse_args()

    if not args.combinations and not (args.parameter and args.values):
        log.info(
            "Error: You must specify either combinations (-c) or a parameter (-p) with values (-v)."
        )
        return

    input_videos = resolve_input_videos(args.input_video)

    if not input_videos:
        log.info(f"No file(s) found at the specified path or glob pattern: {args.input_video}")
        return

    for input_video in input_videos:
        begin(args, input_video)

    log.close()


if __name__ == "__main__":
    main()
