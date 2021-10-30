import os
from pathlib import Path
import sys

import numpy as np
from prettytable import PrettyTable

from args import parser
from arguments_validator import ArgumentsValidator
from encode_video import encode_video
from ffmpeg_process_factory import FfmpegProcessFactory
from libvmaf import run_libvmaf
from metrics import get_metrics_save_table
from overview import create_movie_overview
from utils import cut_video, exit_program, force_decimal_places, is_list, line, Logger, \
                  plot_graph, VideoInfoProvider, write_table_info

log = Logger('main.py')

if len(sys.argv) == 1:
    line()
    log.info('For more details about the available arguments, enter "python main.py -h"')
    line()

args = parser.parse_args()
original_video_path = args.original_video_path
filename = Path(original_video_path).name
video_encoder = args.video_encoder

args_validator = ArgumentsValidator()
validation_result, validation_errors = args_validator.validate(args)

if not validation_result:
    for error in validation_errors:
        log.info(f'Error: {error}')
    exit_program('Argument validation failed.')


def create_output_folder_initialise_table(crf_or_preset):
    if args.output_folder:
        output_folder = f'{args.output_folder}/{crf_or_preset} Comparison'
    else:
        output_folder = f'({filename})/{crf_or_preset} Comparison'

    comparison_table = os.path.join(output_folder, 'Table.txt')
    table_column_names.insert(0, crf_or_preset)
    # Set the names of the columns
    table.field_names = table_column_names

    output_ext = Path(args.original_video_path).suffix
    # The M4V container does not support the H.265 codec.
    if output_ext == '.m4v' and args.video_encoder == 'x265':
        output_ext = '.mp4'
    
    return output_folder, comparison_table, output_ext

# Use the VideoInfoProvider class to get the framerate, bitrate and duration.
provider = VideoInfoProvider(args.original_video_path)
duration = provider.get_duration()
fps = provider.get_framerate_fraction()
fps_float = provider.get_framerate_float()
original_bitrate = provider.get_bitrate(args.decimal_places)

line()
log.info('Video Quality Metrics\nGitHub.com/CrypticSignal/video-quality-metrics')
line()
log.info('Here\'s some information about the original video:')
log.info(f'Filename: {filename}')
log.info(f'Bitrate: {original_bitrate}')
log.info(f'Framerate: {fps} ({fps_float}) FPS')
line()

if args.video_filters:
    log.info('The -vf/--video-filters argument has been supplied. The following filter(s) will be used:')
    log.info(args.video_filters)
    line()

table = PrettyTable()
table_column_names = ['Encoding Time (s)', 'Size', 'Bitrate', 'VMAF']

if args.no_transcoding_mode:
    del table_column_names[0]
if args.calculate_ssim:
    table_column_names.append('SSIM')
if args.calculate_psnr:
    table_column_names.append('PSNR')

if args.interval is not None:
    output_folder = f'({filename})'
    clip_length = str(args.clip_length)
    result, concatenated_video = create_movie_overview(original_video_path, output_folder, args.interval, clip_length)
    if result:
        original_video_path = concatenated_video
    else:
        exit_program('Something went wrong when trying to create the overview video.')

# The -ntm argument was not specified.
if not args.no_transcoding_mode:
    vmaf_scores = []
    if video_encoder == 'x264':
        crf = '23'
    elif video_encoder == 'x265':
        crf = '28'
    elif video_encoder == 'libaom-av1':
        crf = '32'

    # CRF comparison mode.
    if is_list(args.crf) and len(args.crf) > 1:
        log.info('CRF comparison mode activated.')
        crf_values = args.crf
        crf_values_string = ', '.join(str(crf) for crf in crf_values)
        preset = args.preset[0] if is_list(args.preset) else args.preset
        log.info(f'CRF values {crf_values_string} will be compared and the {preset} preset will be used.')
        line()

        prev_output_folder, comparison_table, output_ext = create_output_folder_initialise_table('CRF')

        # The user only wants to transcode the first x seconds of the video.
        if args.encode_length:
            original_video_path = cut_video(filename, args, output_ext, prev_output_folder, comparison_table)

        for crf in crf_values:
            log.info(f'| CRF {crf} |')
            line()
            output_folder = f'{prev_output_folder}/CRF {crf}'
            os.makedirs(output_folder, exist_ok=True)
            transcode_output_path = os.path.join(output_folder, f'CRF {crf}{output_ext}')

            # Encode the video.
            factory, time_taken = encode_video(original_video_path, args, crf, preset, transcode_output_path, f'CRF {crf}', duration)
            
            transcode_size = os.path.getsize(transcode_output_path) / 1_000_000
            transcoded_bitrate = provider.get_bitrate(args.decimal_places, transcode_output_path)
            size_rounded = force_decimal_places(transcode_size, args.decimal_places)
            data_for_current_row = [f'{size_rounded} MB', transcoded_bitrate]

            # Save the output of libvmaf to the following path.
            json_file_path = f'{output_folder}/Metrics of each frame.json'
             # Run the libvmaf filter.
            run_libvmaf(transcode_output_path, args, json_file_path, fps, original_video_path, factory, duration, crf)

            vmaf_scores.append(get_metrics_save_table(comparison_table, json_file_path, args, args.decimal_places, 
                               data_for_current_row, table, output_folder, time_taken, crf))

            mean_vmaf = force_decimal_places(np.mean(vmaf_scores), args.decimal_places)

            write_table_info(comparison_table, filename, original_bitrate, args, f'Preset {preset}')

        # Plot a bar graph showing the average VMAF score of each CRF value.
        plot_graph('CRF vs VMAF', 'CRF', 'VMAF', crf_values, vmaf_scores, mean_vmaf, f'{prev_output_folder}/CRF vs VMAF', 
                   bar_graph=True)
            
    # Presets comparison mode.
    elif is_list(args.preset):
        log.info('Presets comparison mode activated.')
        chosen_presets = args.preset
        presets_string = ', '.join(chosen_presets)
        crf = args.crf[0] if is_list(args.crf) else crf
        log.info(f'Presets {presets_string} will be compared at a CRF of {crf}.')
        line()

        prev_output_folder, comparison_table, output_ext = create_output_folder_initialise_table('Preset')

        # The -t/--encode-length argument was specified.
        if args.encode_length:
            original_video_path = cut_video(filename, args, output_ext, prev_output_folder, comparison_table)

        for preset in chosen_presets:
            log.info(f'| Preset {preset} |')
            line()
            output_folder = f'{prev_output_folder}/Preset {preset}'
            os.makedirs(output_folder, exist_ok=True)
            transcode_output_path = os.path.join(output_folder, f'{preset}{output_ext}')

            # Encode the video.
            factory, time_taken = encode_video(original_video_path, args, crf, preset, transcode_output_path, f'preset {preset}', duration)

            transcode_size = os.path.getsize(transcode_output_path) / 1_000_000
            transcoded_bitrate = provider.get_bitrate(args.decimal_places, transcode_output_path)
            size_rounded = force_decimal_places(transcode_size, args.decimal_places)
            data_for_current_row = [f'{size_rounded} MB', transcoded_bitrate]

            # Save the output of libvmaf to the following path.
            json_file_path = f'{output_folder}/Metrics of each frame.json'
            # Run the libvmaf filter.
            run_libvmaf(transcode_output_path, args, json_file_path, fps, original_video_path, factory, duration, 
                        preset)

            vmaf_scores.append(get_metrics_save_table(comparison_table, json_file_path, args, args.decimal_places, 
                               data_for_current_row, table, output_folder, time_taken, preset))

            mean_vmaf = force_decimal_places(np.mean(vmaf_scores), args.decimal_places)

            write_table_info(comparison_table, original_video_path, original_bitrate, args, f'CRF {crf}')

        # Plot a bar graph showing the average VMAF score of each preset.
        plot_graph('Preset vs VMAF', 'Preset', 'VMAF', chosen_presets, vmaf_scores, mean_vmaf, f'{prev_output_folder}/Preset vs VMAF', bar_graph=True)

# -ntm mode.
else:
    if args.output_folder:
        output_folder = args.output_folder
    else:
        output_folder = f'[VQM] {Path(args.transcoded_video_path).name}'

    os.makedirs(output_folder, exist_ok=True)

    table_path = os.path.join(output_folder, 'Table.txt')
    table.field_names = table_column_names

    json_file_path = f'{output_folder}/Metrics of each frame.json'

    factory = FfmpegProcessFactory()
    run_libvmaf(args.transcoded_video_path, args, json_file_path, fps, original_video_path, factory, duration)

    transcode_size = os.path.getsize(args.transcoded_video_path) / 1_000_000
    size_rounded = force_decimal_places(transcode_size, args.decimal_places)
    transcoded_bitrate = provider.get_bitrate(args.decimal_places, args.transcoded_video_path)
    data_for_current_row = [f'{size_rounded} MB', transcoded_bitrate]

    get_metrics_save_table(table_path, json_file_path, args, args.decimal_places, data_for_current_row, 
                           table, output_folder, time_taken=None)

    with open(table_path, 'a') as f:
        f.write(f'\nOriginal Bitrate: {original_bitrate}')


output_directory = output_folder if args.no_transcoding_mode else Path(output_folder).parent
log.info(f'All done! Check out the contents of the "{output_directory}" directory.')
