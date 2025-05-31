import os
from pathlib import Path
import re
import sys
from typing import List, Optional, Tuple

import numpy as np
from prettytable import PrettyTable

from args import parser
from arguments_validator import ArgumentsValidator
from transcode_video import transcode_video
from libvmaf import run_libvmaf
from metrics import process_metrics
from overview import create_overview_video
from utils import (
    cut_video,
    exit_program,
    force_decimal_places,
    line,
    Logger,
    plot_graph,
    VideoInfoProvider,
    write_table_info,
    get_metrics_list,
    Timer,
)

log = Logger("main.py")


def validate_args(args) -> None:
    validator = ArgumentsValidator()
    result, errors = validator.validate(args)
    if not result:
        for error in errors:
            log.info(f"Error: {error}")
        exit_program("Argument validation failed.")


def get_video_info(
    input_video: str, decimal_places: int, output_folder: Optional[str] = None
) -> Tuple[str, str, str, str, float, str]:
    filename = Path(input_video).name
    output_folder = output_folder or filename
    # Replace any character that is not a letter, digit, underscore or hyphen with an underscore
    output_folder = re.sub(r"[^a-zA-Z0-9_-]", "_", output_folder)

    os.makedirs(output_folder, exist_ok=True)

    provider = VideoInfoProvider(input_video)

    return (
        input_video,
        filename,
        provider.get_framerate_fraction(),
        provider.get_framerate_float(),
        provider.get_bitrate(decimal_places),
        output_folder,
    )


def initialize_table(args) -> PrettyTable:
    table = PrettyTable()
    metrics_list = get_metrics_list(args)
    column_names = [
        "Combination" if args.combinations else args.parameter,
        "Encoding Time (s)",
        "Size",
        "Bitrate",
    ] + metrics_list
    table.field_names = column_names
    return table


def handle_video_filters(args) -> None:
    if args.video_filters:
        log.info("The following filter(s) will be used:")
        log.info(args.video_filters)
        line()


def prepare_video(video_path: str, filename: str, output_folder: str, args) -> str:
    if args.transcode_length:
        video_path = cut_video(
            filename,
            args,
            ".mkv",
            output_folder,
            os.path.join(output_folder, "metrics_table.txt"),
        )

    if args.interval is not None:
        result, concatenated_video = create_overview_video(
            video_path, output_folder, args.interval, str(args.clip_length)
        )
        if result:
            video_path = concatenated_video
        else:
            exit_program("Failed to create overview video.")

    return video_path


def transcode_and_analyse(
    video_path: str,
    output_path: str,
    output_folder: str,
    args,
    combination_list: Optional[List[str]],
    description: str,
    value: Optional[str] = None,
) -> Tuple[float, str]:
    time_taken = transcode_video(
        video_path,
        args,
        value,
        output_path,
        f"Transcoding the video using {description}",
        combination_list,
    )

    json_file_path = Path(output_folder) / "per_frame_metrics.json"

    run_libvmaf(
        output_path,
        args,
        json_file_path,
        video_path,
        f" achieved with {description}",
    )

    return time_taken, json_file_path


def process_combination(
    combination: str,
    video_path: str,
    output_folder: str,
    args,
    table: PrettyTable,
    vmaf_scores: List[float],
) -> float:
    current_output_folder = os.path.join(output_folder, combination.replace(" ", "_"))
    os.makedirs(current_output_folder, exist_ok=True)

    output_path = os.path.join(
        current_output_folder, f"{combination.replace(' ', '_')}.mkv"
    )

    combination_list = combination.split(" ")

    for i in range(0, len(combination_list), 2):
        combination_list[i] = f"-{combination_list[i]}"

    combination_string = " ".join(combination_list)

    time_taken, json_file_path = transcode_and_analyse(
        video_path,
        output_path,
        current_output_folder,
        args,
        combination_list,
        f"combination '{combination_string}'",
    )

    vmaf_score = update_metrics(
        output_folder,
        current_output_folder,
        output_path,
        json_file_path,
        time_taken,
        combination_string,
        args,
        table,
    )
    vmaf_scores.append(vmaf_score)
    return vmaf_score


def process_parameter_value(
    value: str,
    video_path: str,
    output_folder: str,
    args,
    table: PrettyTable,
    vmaf_scores: List[float],
) -> float:
    current_output_folder = os.path.join(output_folder, f"{args.parameter}_{value}")
    os.makedirs(current_output_folder, exist_ok=True)

    output_path = os.path.join(current_output_folder, f"{value}.mkv")

    time_taken, json_file_path = transcode_and_analyse(
        video_path,
        output_path,
        current_output_folder,
        args,
        None,
        f"'-{args.parameter} {value}'",
        value,
    )

    vmaf_score = update_metrics(
        output_folder,
        current_output_folder,
        output_path,
        json_file_path,
        time_taken,
        value,
        args,
        table,
    )
    vmaf_scores.append(vmaf_score)
    return vmaf_score


def update_metrics(
    output_folder: str,
    current_output_folder: str,
    output_path: str,
    json_file_path: str,
    time_taken: float,
    value: str,
    args,
    table: PrettyTable,
) -> float:
    provider = VideoInfoProvider(output_path)
    size = force_decimal_places(
        os.path.getsize(output_path) / 1_000_000, args.decimal_places
    )
    bitrate = provider.get_bitrate(args.decimal_places)

    return process_metrics(
        os.path.join(output_folder, "metrics_table.txt"),
        json_file_path,
        args,
        args.decimal_places,
        [f"{size} MB", bitrate],
        table,
        current_output_folder,
        time_taken,
        value,
    )


def finalise(
    filename: str,
    output_folder: str,
    original_bitrate: str,
    args,
    vmaf_scores: List[float],
) -> None:
    mean_vmaf = force_decimal_places(np.mean(vmaf_scores), args.decimal_places)
    write_table_info(
        os.path.join(output_folder, "metrics_table.txt"),
        filename,
        original_bitrate,
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
        os.path.join(output_folder, f"{parameter} vs VMAF"),
        bar_graph=True,
    )


def main():
    if len(sys.argv) == 1:
        line()
        log.info(
            'For more details about the available arguments, enter "python main.py -h"'
        )
        line()
        return

    args = parser.parse_args()
    validate_args(args)

    video_path, filename, fps, fps_float, original_bitrate, output_folder = (
        get_video_info(args.input_video, args.decimal_places, args.output_folder)
    )
    table = initialize_table(args)
    timer = Timer()
    vmaf_scores = []

    line()
    log.info("Video Quality Metrics")
    log.info("Version Date: 11th October 2024")
    line()
    log.info("Here's some information about the original video:")
    log.info(f"Filename: {filename}")
    log.info(f"Bitrate: {original_bitrate}")
    log.info(f"Framerate: {fps} ({fps_float}) FPS")
    line()

    timer.start()
    handle_video_filters(args)
    video_path = prepare_video(video_path, filename, output_folder, args)

    if args.combinations:
        log.info("Combination Mode activated.")
        for combination in args.combinations.split(","):
            process_combination(
                combination, video_path, output_folder, args, table, vmaf_scores
            )
    else:
        log.info(
            f"Values of {args.encoder}'s '-{args.parameter}' parameter will be compared."
        )
        log.info(
            f"The following values will be compared: {', '.join(str(value) for value in args.values)}"
        )
        for value in args.values:
            process_parameter_value(
                value, video_path, output_folder, args, table, vmaf_scores
            )

    line()
    log.info(f"Total Time Taken: {timer.stop(args.decimal_places)}s")

    finalise(filename, output_folder, original_bitrate, args, vmaf_scores)

    line()
    log.info(f"All done! Check out the contents of the '{output_folder}' folder.")
    log.close()


main()
