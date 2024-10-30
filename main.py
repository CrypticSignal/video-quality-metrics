import os
from pathlib import Path
import sys

import numpy as np
from prettytable import PrettyTable

from args import parser
from arguments_validator import ArgumentsValidator
from transcode_video import transcode_video
from libvmaf import run_libvmaf
from metrics import get_metrics_save_table
from overview import create_movie_overview
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
)

log = Logger("main.py")

if len(sys.argv) == 1:
    line()
    log.info(
        'For more details about the available arguments, enter "python main.py -h"'
    )
    line()

args = parser.parse_args()
original_video_path = args.input_video
filename = Path(original_video_path).name
encoder = args.encoder

args_validator = ArgumentsValidator()
validation_result, validation_errors = args_validator.validate(args)

if not validation_result:
    for error in validation_errors:
        log.info(f"Error: {error}")
    exit_program("Argument validation failed.")


def create_output_folder_initialise_table(crf_or_preset):
    if args.output_folder:
        output_folder = f"{args.output_folder}/{crf_or_preset} Comparison"
    else:
        output_folder = f"({filename})/{crf_or_preset} Comparison"

    comparison_table = os.path.join(output_folder, "metrics_table.txt")
    table_column_names.insert(0, crf_or_preset)
    # Set the names of the columns
    table.field_names = table_column_names

    output_ext = ".mkv"

    return output_folder, comparison_table, output_ext


# Use the VideoInfoProvider class to get the framerate, bitrate and duration.
provider = VideoInfoProvider(original_video_path)
duration = provider.get_duration()
fps = provider.get_framerate_fraction()
fps_float = provider.get_framerate_float()
original_bitrate = provider.get_bitrate(args.decimal_places)

line()
log.info("Video Quality Metrics\nGitHub.com/CrypticSignal/video-quality-metrics")
line()
log.info("Here's some information about the original video:")
log.info(f"Filename: {filename}")
log.info(f"Bitrate: {original_bitrate}")
log.info(f"Framerate: {fps} ({fps_float}) FPS")
line()

if args.video_filters:
    log.info(
        "The -vf/--video-filters argument has been supplied. The following filter(s) will be used:"
    )
    log.info(args.video_filters)
    line()

if args.interval is not None:
    output_folder = f"({filename})"
    clip_length = str(args.clip_length)
    result, concatenated_video = create_movie_overview(
        original_video_path, output_folder, args.interval, clip_length
    )
    if result:
        original_video_path = concatenated_video
    else:
        exit_program("Something went wrong when trying to create the overview video.")

table = PrettyTable()
metrics_list = get_metrics_list(args)
table_column_names = ["Encoding Time (s)", "Size", "Bitrate"] + metrics_list

# No Transcoding Mode
if args.no_transcoding_mode:
    print("No Transcoding Mode activated.")
    del table_column_names[0]

    if args.output_folder:
        output_folder = args.output_folder
    else:
        output_folder = f"[VQM] {Path(args.transcoded_video).name}"

    os.makedirs(output_folder, exist_ok=True)

    table_path = os.path.join(output_folder, "metrics_table.txt")
    table.field_names = table_column_names

    json_file_path = f"{output_folder}/per_frame_metrics.json"

    run_libvmaf(
        args.transcoded_video,
        args,
        json_file_path,
        fps,
        original_video_path,
    )

    transcode_size = os.path.getsize(args.transcoded_video) / 1_000_000
    size_rounded = force_decimal_places(transcode_size, args.decimal_places)
    transcoded_bitrate = provider.get_bitrate(
        args.decimal_places, args.transcoded_video
    )
    data_for_current_row = [f"{size_rounded} MB", transcoded_bitrate]

    get_metrics_save_table(
        table_path,
        json_file_path,
        args,
        args.decimal_places,
        data_for_current_row,
        table,
        output_folder,
        time_taken=None,
    )

    with open(table_path, "a") as f:
        f.write(f"\nOriginal Bitrate: {original_bitrate}")

    sys.exit()

# Transcoding Mode

vmaf_scores = []

log.info(f"Values of {args.encoder}'s '-{args.parameter}' parameter will be compared.")
log.info(
    f"The following values will be compared: {", ".join(str(value) for value in args.values)}"
)

prev_output_folder, comparison_table, output_ext = (
    create_output_folder_initialise_table(args.parameter)
)

# The user only wants to transcode the first x seconds of the video.
if args.transcode_length:
    original_video_path = cut_video(
        filename, args, output_ext, prev_output_folder, comparison_table
    )

for value in args.values:
    output_folder = f"{prev_output_folder}/{args.parameter} {value}"
    os.makedirs(output_folder, exist_ok=True)
    transcode_output_path = os.path.join(output_folder, f"{value}{output_ext}")

    # Transcode the video.
    time_taken = transcode_video(
        original_video_path,
        args,
        value,
        transcode_output_path,
        f"'-{args.parameter} {value}'",
    )

    transcode_size = os.path.getsize(transcode_output_path) / 1_000_000
    transcoded_bitrate = provider.get_bitrate(
        args.decimal_places, transcode_output_path
    )
    size_rounded = force_decimal_places(transcode_size, args.decimal_places)
    data_for_current_row = [f"{size_rounded} MB", transcoded_bitrate]

    # Save the output of libvmaf to the following path.
    json_file_path = f"{output_folder}/per_frame_metrics.json"
    # Run the libvmaf filter.
    run_libvmaf(
        transcode_output_path,
        args,
        json_file_path,
        fps,
        original_video_path,
        value,
    )

    vmaf_scores.append(
        get_metrics_save_table(
            comparison_table,
            json_file_path,
            args,
            args.decimal_places,
            data_for_current_row,
            table,
            output_folder,
            time_taken,
            value,
        )
    )

    mean_vmaf = force_decimal_places(np.mean(vmaf_scores), args.decimal_places)

    write_table_info(comparison_table, filename, original_bitrate, args)

# Plot a bar graph showing the average VMAF score of each CRF value.
plot_graph(
    "CRF vs VMAF",
    "CRF",
    "VMAF",
    args.values,
    vmaf_scores,
    mean_vmaf,
    f"{prev_output_folder}/CRF vs VMAF",
    bar_graph=True,
)

output_directory = (
    output_folder if args.no_transcoding_mode else Path(output_folder).parent
)
line()
log.info(f"All done! Check out the contents of the '{output_directory}' folder.")
