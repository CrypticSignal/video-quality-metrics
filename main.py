import os
import sys
from pathlib import Path
from prettytable import PrettyTable

from args import parser
from save_metrics import create_table_plot_metrics, force_decimal_places
from overview import create_movie_overview
from utils import line, is_list, cut_video, exit_program, VideoInfoProvider, Timer
from ffmpeg_process_factory import Encoder, EncodingArguments, FfmpegProcessFactory
from libvmaf import run_libvmaf
from arguments_validator import ArgumentsValidator

if len(sys.argv) == 1:
    line()
    print("To see more details about the available arguments, enter 'python main.py -h'")
    line()

args = parser.parse_args()

if args.calculate_psnr:
    exit_program('PSNR calculation is currently unavailable due to a change that was made in libvmaf v2.0.0.\n'
                 'Visit https://github.com/Netflix/vmaf/issues/787 for more information.\n'
                 'You can re-run your command without the psnr argument, but PSNR values will not be calculated.')

args_validator = ArgumentsValidator()
validation_result, validation_errors = args_validator.validate(args)

if not validation_result:
    for error in validation_errors:
        print(f'Error: {error}')
    exit_program('Argument validation failed.')

decimal_places = args.decimal_places
original_video_path = args.original_video_path
filename = Path(original_video_path).name
output_folder = f'({filename})'
os.makedirs(output_folder, exist_ok=True)

# this includes the dot eg '.mp4'
output_ext = Path(original_video_path).suffix
# The M4V container does not support the H.265 codec.
if output_ext == '.m4v' and args.video_encoder == 'x265':
    output_ext = '.mp4'

# Use class VideoInfoProvider  to get the framerate, bitrate and duration
provider = VideoInfoProvider(original_video_path)
fps = provider.get_framerate_fraction()
fps_float = provider.get_framerate_float()
original_bitrate = provider.get_bitrate()

line()
print('Video Quality Metrics\nGitHub.com/BassThatHertz/video-quality-metrics')
line()
print('Here\'s some information about the original video:')
print(f'Filename: {filename}')
print(f'Bitrate: {original_bitrate}')
print(f'Framerate: {fps} ({fps_float}) FPS')
line()

if args.filterchain:
    print('The -fc/--filterchain argument has been supplied. The following filter(s) will be used:')
    print(args.filterchain)
    line()

table = PrettyTable()
table_column_names = ['Encoding Time (s)', 'Size', 'Bitrate', 'VMAF']

if args.calculate_ssim:
    table_column_names.append('SSIM')
if args.calculate_psnr:
    table_column_names.append('PSNR')
if args.no_transcoding_mode:
    del table_column_names[0]

if args.interval > 0:
    clip_length = str(args.clip_length)
    result, concatenated_video = create_movie_overview(original_video_path, output_folder, args.interval, clip_length)
    if result:
        original_video_path = concatenated_video
    else:
        exit_program('Something went wrong when trying to create the overview video.')
    
factory = FfmpegProcessFactory()
timer = Timer()

if not args.no_transcoding_mode:
    # args.crf_value is a list when more than one CRF value is specified.
    if is_list(args.crf_value) and len(args.crf_value) > 1:
        print('CRF comparison mode activated.')

        crf_values = args.crf_value
        crf_values_string = ', '.join(str(crf) for crf in crf_values)
        preset = args.preset[0] if is_list(args.preset) else args.preset
        print(f'CRF values {crf_values_string} will be compared and the {preset} preset will be used.')
        line()

        # Cannot use os.path.join for output_folder as this gives an error like the following:
        # No such file or directory: '(2.mkv)\\Presets comparison at CRF 23/Raw JSON Data/superfast.json'
        output_folder = f'({filename})/CRF comparison at preset {preset}'
        os.makedirs(output_folder, exist_ok=True)

        # The comparison table will be in the following path:
        comparison_table = os.path.join(output_folder, 'Table.txt')
        # Add a CRF column.
        table_column_names.insert(0, 'CRF')
        # Set the names of the columns
        table.field_names = table_column_names

        # The user only wants to transcode the first x seconds of the video.
        if args.encode_length and args.interval == 0:
            original_video_path = cut_video(filename, args, output_ext, output_folder, comparison_table)

        # Transcode the video with each CRF value.
        for crf in crf_values:
            transcode_output_path = os.path.join(output_folder, f'CRF {crf}{output_ext}')
            graph_filename = f'CRF {crf} at preset {preset}'

            arguments = EncodingArguments()

            arguments.infile = original_video_path
            arguments.encoder = Encoder[args.video_encoder]

            if args.video_encoder == 'av1':
                arguments.av1_cpu_used = str(args.av1_cpu_used)

            arguments.crf = str(crf)
            arguments.preset = preset
            arguments.filterchain = args.filterchain if args.filterchain else None
            arguments.outfile = transcode_output_path

            process = factory.create_process(arguments, args)
                
            print(f'Transcoding the video with CRF {crf}...\n')
            timer.start()
            process.run()
            time_taken = timer.end(decimal_places)
            print(f'Done! Time taken: {time_taken} seconds.')
            
            transcode_size = os.path.getsize(transcode_output_path) / 1_000_000
            transcoded_bitrate = provider.get_bitrate(transcode_output_path)
            size_rounded = force_decimal_places(round(transcode_size, decimal_places), decimal_places)
            data_for_current_row = [f'{size_rounded} MB', transcoded_bitrate]
            
            os.makedirs(os.path.join(output_folder, 'Raw JSON Data'), exist_ok=True)
            # os.path.join doesn't work with libvmaf's log_path option so we're manually defining the path with
            # slashes.
            json_file_path = f'{output_folder}/Raw JSON Data/CRF {crf}.json'

            run_libvmaf(transcode_output_path, args, json_file_path, fps, original_video_path, factory, crf)
        
            create_table_plot_metrics(comparison_table, json_file_path, args, decimal_places, data_for_current_row,
                                        graph_filename, table, output_folder, time_taken, crf)

            with open(comparison_table, 'a') as f:
                f.write(
                    f'\nFile Transcoded: {filename}\n'
                    f'Bitrate: {original_bitrate}\n'
                    f'Encoder used for the transcodes: {args.video_encoder}\n'
                    f'Preset used for the transcodes: {preset}\n'
                    f'Filter(s) used: {"None" if not args.filterchain else args.filterchain}\n'
                    f'n_subsample: {args.subsample}')
            
    # args.preset is a list when more than one preset is specified.
    elif is_list(args.preset):
        print('Presets comparison mode activated.')

        chosen_presets = args.preset
        presets_string = ', '.join(chosen_presets)
        crf = args.crf_value[0] if is_list(args.crf_value) else args.crf_value
        print(f'Presets {presets_string} will be compared at a CRF of {crf}.')
        line()

        # Cannot use os.path.join for output_folder as this gives an error like the following:
        # No such file or directory: '(2.mkv)\\Presets comparison at CRF 23/Raw JSON Data/superfast.json'
        output_folder = f'({filename})/Presets comparison at CRF {crf}'
        os.makedirs(output_folder, exist_ok=True)

        comparison_table = os.path.join(output_folder, 'Table.txt')
        table_column_names.insert(0, 'Preset')
        # Set the names of the columns
        table.field_names = table_column_names

        # The user only wants to transcode the first x seconds of the video.
        if args.encode_length:
            original_video_path = cut_video(filename, args, output_ext, output_folder, comparison_table)

        # Transcode the video with each preset.
        for preset in chosen_presets:
            transcode_output_path = os.path.join(output_folder, f'{preset}{output_ext}')
            graph_filename = f"Preset '{preset}'"
            
            arguments = EncodingArguments()
            
            arguments.infile = original_video_path
            arguments.encoder = Encoder[args.video_encoder]

            if args.video_encoder == 'av1':
                arguments.av1_cpu_used = str(args.cpu_used)

            arguments.crf = str(crf)
            arguments.preset = preset
            arguments.filterchain = args.filterchain if args.filterchain else None
            arguments.outfile = transcode_output_path

            process = factory.create_process(arguments)
            
            print(f'Transcoding the video with preset {preset}...')
            timer.start()
            process.run()
            time_taken = timer.end(decimal_places)
            print(f'Done! Time taken: {time_taken} seconds.')

            transcode_size = os.path.getsize(transcode_output_path) / 1_000_000
            transcoded_bitrate = provider.get_bitrate(transcode_output_path)
            size_rounded = force_decimal_places(round(transcode_size, decimal_places), decimal_places)
            data_for_current_row = [f'{size_rounded} MB', transcoded_bitrate]
        
            os.makedirs(os.path.join(output_folder, 'Raw JSON Data'), exist_ok=True)
            # os.path.join doesn't work with libvmaf's log_path option so we're manually defining the path with
            # slashes.
            json_file_path = f'{output_folder}/Raw JSON Data/{preset}.json'

            run_libvmaf(transcode_output_path, args, json_file_path, fps, original_video_path, factory, preset)

            create_table_plot_metrics(comparison_table, json_file_path, args, decimal_places, data_for_current_row, 
                                        graph_filename, table, output_folder, time_taken, preset)

        with open(comparison_table, 'a') as f:
            f.write(
                f'\nFile Transcoded: {filename}\n'
                f'Bitrate: {original_bitrate}\n'
                f'Encoder used for the transcodes: {args.video_encoder}\n'
                f'CRF value used for the transcodes: {crf}\n'
                f'Filter(s) used: {"None" if not args.filterchain else args.filterchain}\n'
                f'n_subsample: {args.subsample}'  
            )

# -ntm argument was specified.
else:
    line()
    output_folder = f'({filename})'
    os.makedirs(output_folder, exist_ok=True)
    comparison_table = os.path.join(output_folder, 'Table.txt')
    table.field_names = table_column_names
    # os.path.join doesn't work with libvmaf's log_path option so we're manually defining the path with slashes.
    json_file_path = f'{output_folder}/QualityMetrics.json'
    # Run libvmaf to get the quality metric(s).
    run_libvmaf(args.transcoded_video_path, args, json_file_path, fps, original_video_path, factory, crf_or_preset=None)

    transcode_size = os.path.getsize(args.transcoded_video_path) / 1_000_000
    size_rounded = force_decimal_places(round(transcode_size, decimal_places), decimal_places)
    transcoded_bitrate = provider.get_bitrate(args.transcoded_video_path)
    data_for_current_row = [f'{size_rounded} MB', transcoded_bitrate]
    
    graph_filename = 'The variation of the quality of the transcoded video throughout the video'
    # Create the table and plot the metrics if -dqm was not specified.
    create_table_plot_metrics(json_file_path, args, decimal_places, data_for_current_row, graph_filename,
                                        table, output_folder, time_rounded=None, crf_or_preset=None)

line()
print(f'All done! Check out the ({filename}) folder.')
