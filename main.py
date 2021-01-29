import os
import sys
from pathlib import Path
from prettytable import PrettyTable

from args import parser
from save_metrics import create_table_plot_metrics, force_decimal_places
from overview import create_movie_overview
from utils import line, is_list, cut_video, exit_program, VideoInfoProvider, write_table_info
from ffmpeg_process_factory import FfmpegProcessFactory
from encode_video import encode_video
from libvmaf import run_libvmaf
from arguments_validator import ArgumentsValidator

if len(sys.argv) == 1:
    line()
    print('For more details about the available arguments, enter "python main.py -h"')
    line()

args = parser.parse_args()
original_video_path = args.original_video_path
filename = Path(original_video_path).name

args_validator = ArgumentsValidator()
validation_result, validation_errors = args_validator.validate(args)

if not validation_result:
    for error in validation_errors:
        print(f'Error: {error}')
    exit_program('Argument validation failed.')


def create_output_folder_initialise_table(crf_or_preset):
    # Cannot use os.path.join for output_folder as this gives an error like the following:
    # No such file or directory: '(2.mkv)\\Presets comparison at CRF 23/Metrics for each frame/superfast.json'
    output_folder = f'({filename})/{crf_or_preset} Comparison'
    os.makedirs(output_folder, exist_ok=True)

    comparison_table = os.path.join(output_folder, 'Table.txt')
    table_column_names.insert(0, crf_or_preset)
    # Set the names of the columns
    table.field_names = table_column_names

    output_ext = Path(args.original_video_path).suffix
    # The M4V container does not support the H.265 codec.
    if output_ext == '.m4v' and args.video_encoder == 'x265':
        output_ext = '.mp4'
    
    return output_folder, comparison_table, output_ext

# Use class VideoInfoProvider  to get the framerate, bitrate and duration
provider = VideoInfoProvider(args.original_video_path)
fps = provider.get_framerate_fraction()
fps_float = provider.get_framerate_float()
original_bitrate = provider.get_bitrate(args.decimal_places)

line()
print('Video Quality Metrics\nGitHub.com/BassThatHertz/video-quality-metrics')
line()
print('Here\'s some information about the original video:')
print(f'Filename: {filename}')
print(f'Bitrate: {original_bitrate}')
print(f'Framerate: {fps} ({fps_float}) FPS')
line()

if args.video_filters:
    print('The -vf/--video-filters argument has been supplied. The following filter(s) will be used:')
    print(args.video_filters)
    line()

table = PrettyTable()
table_column_names = ['Encoding Time (s)', 'Size', 'Bitrate', 'VMAF']

if args.no_transcoding_mode:
    del table_column_names[0]
if args.calculate_ssim:
    table_column_names.append('SSIM')
if args.calculate_psnr:
    table_column_names.append('PSNR')

# args.interval will be greater than 0 if the -i/--interval argument was specified.
if args.interval > 0:
    output_folder = f'({filename})'
    clip_length = str(args.clip_length)
    result, concatenated_video = create_movie_overview(original_video_path, output_folder, args.interval, clip_length)
    if result:
        original_video_path = concatenated_video
    else:
        exit_program('Something went wrong when trying to create the overview video.')


if not args.no_transcoding_mode:
    # CRF comparison mode.
    if is_list(args.crf_value) and len(args.crf_value) > 1:
        print('CRF comparison mode activated.')

        crf_values = args.crf_value
        crf_values_string = ', '.join(str(crf) for crf in crf_values)
        preset = args.preset[0] if is_list(args.preset) else args.preset
        print(f'CRF values {crf_values_string} will be compared and the {preset} preset will be used.')
        line()
    

        output_folder, comparison_table, output_ext = create_output_folder_initialise_table('Presets')

        # The user only wants to transcode the first x seconds of the video.
        if args.encode_length:
            original_video_path = cut_video(filename, args, output_ext, output_folder, comparison_table)

        # Transcode the video with each CRF value.
        for crf in crf_values:
            print(f'| CRF {crf} |')
            line()
            transcode_output_path = os.path.join(output_folder, f'CRF {crf}{output_ext}')
            # Encode the video.
            factory, time_taken = encode_video(args, crf, preset, transcode_output_path, 'CRF {crf}')
            
            transcode_size = os.path.getsize(transcode_output_path) / 1_000_000
            transcoded_bitrate = provider.get_bitrate(args.decimal_places, transcode_output_path)
            size_rounded = force_decimal_places(transcode_size, args.decimal_places)
            data_for_current_row = [f'{size_rounded} MB', transcoded_bitrate]
            
            os.makedirs(os.path.join(output_folder, 'Metrics for each frame'), exist_ok=True)
            json_file_path = f'{output_folder}/Metrics for each frame/CRF {crf}.json'

            run_libvmaf(transcode_output_path, args, json_file_path, fps, original_video_path, factory, crf)

            graph_filename = f'CRF {crf} at preset {preset}'
            create_table_plot_metrics(comparison_table, json_file_path, args, args.decimal_places, data_for_current_row,
                                        graph_filename, table, output_folder, time_taken, crf)

            write_table_info(comparison_table, filename, original_bitrate, args, f'Preset {preset}')
            
    # Presets comparison mode.
    elif is_list(args.preset):
        print('Presets comparison mode activated.')

        chosen_presets = args.preset
        presets_string = ', '.join(chosen_presets)
        crf = args.crf_value[0] if is_list(args.crf_value) else args.crf_value
        print(f'Presets {presets_string} will be compared at a CRF of {crf}.')
        line()

        output_folder, comparison_table, output_ext = create_output_folder_initialise_table('Preset')

        # The user only wants to transcode the first x seconds of the video.
        if args.encode_length:
            original_video_path = cut_video(filename, args, output_ext, output_folder, comparison_table)

        # Transcode the video with each preset.
        for preset in chosen_presets:
            print(f'| Preset {preset} |')
            line()
            transcode_output_path = os.path.join(output_folder, f'{preset}{output_ext}')
            # Encode the video.
            factory, time_taken = encode_video(args, crf, preset, transcode_output_path, f'preset {preset}')

            transcode_size = os.path.getsize(transcode_output_path) / 1_000_000
            transcoded_bitrate = provider.get_bitrate(args.decimal_places, transcode_output_path)
            size_rounded = force_decimal_places(transcode_size, args.decimal_places)
            data_for_current_row = [f'{size_rounded} MB', transcoded_bitrate]
        
            os.makedirs(os.path.join(output_folder, 'Metrics for each frame'), exist_ok=True)
            json_file_path = f'{output_folder}/Metrics for each frame/{preset}.json'

            run_libvmaf(transcode_output_path, args, json_file_path, fps, original_video_path, factory, preset)

            graph_filename = f'Preset {preset} at CRF {crf}'
            create_table_plot_metrics(comparison_table, json_file_path, args, args.decimal_places, data_for_current_row, 
                                        graph_filename, table, output_folder, time_taken, preset)

            write_table_info(comparison_table, filename, original_bitrate, args, f'CRF {crf}')


# -ntm mode
else:
    output_folder = f'({args.transcoded_video_path})'
    os.makedirs(output_folder, exist_ok=True)

    comparison_table = os.path.join(output_folder, 'Table.txt')
    table.field_names = table_column_names

    # os.path.join doesn't work with libvmaf's log_path option so we're manually defining the path with slashes.
    json_file_path = f'{output_folder}/QualityMetrics.json'

    factory = FfmpegProcessFactory()
    run_libvmaf(args.transcoded_video_path, args, json_file_path, fps, original_video_path, factory, crf_or_preset=None)

    transcode_size = os.path.getsize(args.transcoded_video_path) / 1_000_000
    size_rounded = force_decimal_places(round(transcode_size, args.decimal_places), args.decimal_places)
    transcoded_bitrate = provider.get_bitrate(args.transcoded_video_path)
    data_for_current_row = [f'{size_rounded} MB', transcoded_bitrate]

    graph_name = 'VMAF'
    if args.calculate_psnr and args.calculate_ssim:
        graph_name += ', PSNR and SSIM'
    elif args.calculate_psnr:
        graph_name += ' and PSNR'
    elif args.calculate_ssim:
        graph_name += ' and SSIM'
 
    create_table_plot_metrics(comparison_table, json_file_path, args, args.decimal_places, data_for_current_row, 
                              graph_name, table, output_folder, time_taken=None)


line()
output_folder = f'({filename})' if not args.no_transcoding_mode else f'({args.transcoded_video_path})'
print(f'All done! Check out the {output_folder} folder.')
