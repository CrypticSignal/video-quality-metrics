import time, os, subprocess, sys
from argparse import ArgumentParser, RawTextHelpFormatter
from prettytable import PrettyTable
from save_metrics import create_table_plot_metrics, force_decimal_places

from overview import create_movie_overview
from utils import VideoInfoProvider, is_list, line, exit_program
from ffmpeg_process_factory import Encoder, EncodingArguments, \
    FfmpegProcessFactory


METRICS_EXPLANATION = 'PSNR/SSIM/VMAF values are in the format: Min | Standard Deviation | Mean\n'

def main():
    if len(sys.argv) == 1:
        line()
        print("To see more details about the available arguments, enter 'python main.py -h'")
        line()
    parser = ArgumentParser(formatter_class=RawTextHelpFormatter)
    # Original video path.
    parser.add_argument('-ovp', '--original-video-path', type=str, required=True,
                        help='Enter the path of the original '
                             'video. A relative or absolute path can be specified. '
                             'If the path contains a space, it must be surrounded in double quotes.\n'
                             'Example: -ovp "C:/Users/H/Desktop/file 1.mp4"')
    # Which video encoder to use.
    parser.add_argument('-e', '--video-encoder', type=str, default='x264', choices=['x264', 'x265'],
                        help='Specify the encoder to use (default: x264).\nExample: -e x265')
    # CRF value(s).
    parser.add_argument('-crf', '--crf-value', nargs='+', type=int, choices=range(0, 51),
                        default=23, help='Specify the CRF value(s) to use.', metavar='CRF_VALUE(s)')
    # Preset(s).
    parser.add_argument('-p', '--preset', nargs='+', choices=[
                        'veryslow', 'slower', 'slow', 'medium', 'fast', 'faster', 'veryfast', 'superfast', 'ultrafast'],
                        default='medium', help='Specify the preset(s) to use.', metavar='PRESET(s)')
    # The time interval to use when creating the overview video.
    parser.add_argument('-i', '--interval', type=int, choices=range(1, 600), default=0,
                        help='Create a lossless overview video by grabbing a <cliplength> seconds long segment '
							  'every <interval> seconds from the original video and use this overview video '
							  'as the "original" video that the transcodes are compared with.\nExample: -i 30',
						metavar='<an integer between 1 and 600>')
    # The length of each clip.
    parser.add_argument('-cl', '--clip-length', type=int, choices=range(1, 60), default=1,
                        help='Defines the length of the clips. Only applies when used with -i > 0. Default: 1.\n'
							 'Example: -cl 10', 
						metavar='<an integer between 1 and 60>')
    # Use only the first x seconds of the original video.
    parser.add_argument('-t', '--encoding-time', type=str,
                        help='Create a lossless version of the original video that is just the first x seconds of the '
                        'video, use the cut version as the reference and for all encodes. '
                        'You cannot use this option in conjunction with the -i or -cl arguments.'
                        'Example: -t 60')
    # Enable phone model?
    parser.add_argument('-pm', '--phone-model', action='store_true', help='Enable VMAF phone model.')
    # Number of decimal places to use for the data.
    parser.add_argument('-dp', '--decimal-places', default=2, help='The number of decimal places to use for the data '
                                                                   'in the table (default: 2).\nExample: -dp 3')
    # Calculate SSIM?
    parser.add_argument('-ssim', '--calculate-ssim', action='store_true', help='Calculate SSIM in addition to VMAF.')
    # Calculate psnr?
    parser.add_argument('-psnr', '--calculate-psnr', action='store_true', help='Calculate PSNR in addition to VMAF.')
    # Disable quality calculation?
    parser.add_argument('-dqm', '--disable-quality-metrics', action='store_true',
                        help='Disable calculation of '
                             'PSNR, SSIM and VMAF; only show encoding time and filesize (improves completion time).')
    # No transcoding mode.
    parser.add_argument('-ntm', '--no-transcoding-mode', action='store_true',
                        help='Use this mode if you\'ve already transcoded a video and would like its VMAF and '
                             '(optionally) the SSIM and PSNR to be calculated.\n'
                             'Example: -ntm -tvp transcoded.mp4 -ovp original.mp4 -ssim -psnr')
    # Transcoded video path (only applicable when using the -ntm mode).
    parser.add_argument('-tvp', '--transcoded-video-path',
                        help='The path of the transcoded video (only applicable when using the -ntm mode).')

    args = parser.parse_args()

    decimal_places = args.decimal_places
    # The path of the original video.
    original_video = args.original_video_path
    # Just the filename.
    filename = original_video.split('/')[-1]
    # The file extension of the video.
    output_ext = os.path.splitext(original_video)[-1][1:]
	# The value of the --interval argument.
    clip_interval = args.interval

    # Use class VideoInfoProvider  to get the framerate, bitrate and duration
    provider = VideoInfoProvider(original_video)
    fps = provider.get_framerate_fraction()
    fps_float = provider.get_framerate_float()
    original_bitrate = provider.get_bitrate()
    original_duration = round(float(provider.get_duration()), 1)
    
    line()
    print('Here\'s some information about the original video:')
    print(f'Filename: {filename}')
    print(f'Bitrate: {original_bitrate}')
    print(f'Framerate: {fps} ({fps_float}) FPS')
    print(f'Duration: {original_duration} seconds')
    line()

    # Create a PrettyTable object.
    table = PrettyTable()
    # Base template for the column names.
    table_column_names = ['Encoding Time (s)', 'Size', 'Bitrate']

    if not args.disable_quality_metrics:
        table_column_names.append('VMAF')
        if args.calculate_ssim:
            table_column_names.append('SSIM')
        if args.calculate_psnr:
            table_column_names.append('PSNR')
        if args.no_transcoding_mode:
            del table_column_names[0]

    if clip_interval > 0:
        clip_length = args.clip_length
        output_folder = os.path.join(f'({filename})', 'clips')
        os.makedirs(output_folder, exist_ok=True)
        
        result, concatenated_video = create_movie_overview(original_video, output_folder, clip_interval, clip_length)
        if result:
            original_video = concatenated_video
        else:
            exit_program('Something went wrong when trying to create the overview video.')

    if not args.no_transcoding_mode:
        # If no CRF or preset is specified, the default data types are as int and str, respectively.
        if isinstance(args.crf_value, int) and isinstance(args.preset, str):
            exit_program('No CRF value(s) or preset(s) specified. Exiting.')
        elif is_list(args.crf_value) and len(args.crf_value) > 1 and is_list(args.preset) and len(args.preset) > 1:
            exit_program(f'More than one CRF value AND more than one preset specified. No suitable mode found. '
                         f'Exiting.')

        # args.crf_value is a list when more than one CRF value is specified.
        elif is_list(args.crf_value) and len(args.crf_value) > 1:
            print('CRF comparison mode activated.')
            crf_values = args.crf_value
            crf_values_string = ', '.join(str(crf) for crf in crf_values)
            preset = args.preset[0] if is_list(args.preset) else args.preset
            print(f'CRF values {crf_values_string} will be compared and the {preset} preset will be used.')
            video_encoder = args.video_encoder
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
            if args.encoding_time and clip_interval == 0:
                original_video = cut_video(filename, args, output_ext, output_folder, comparison_table)

            # Transcode the video with each CRF value.
            for crf in crf_values:
                transcode_output_path = os.path.join(output_folder, f'CRF {crf} at preset {preset}.{output_ext}')
                graph_filename = f'CRF {crf} at preset {preset}'

                factory = FfmpegProcessFactory()
                arguments = EncodingArguments()
                arguments.infile = original_video
                arguments.encoder = Encoder[video_encoder]
                arguments.crf = crf
                arguments.preset = preset
                arguments.outfile = transcode_output_path

                process = factory.create_process(arguments)

                line()
                print(f'Transcoding the video with CRF {crf}...')
                start_time = time.time()
                process.run()
                end_time = time.time()
                print('Done!')
                time_to_convert = end_time - start_time
                time_rounded = force_decimal_places(round(time_to_convert, decimal_places), decimal_places)
                transcode_size = os.path.getsize(transcode_output_path) / 1_000_000
                transcoded_bitrate = provider.get_bitrate(transcode_output_path)
                size_rounded = force_decimal_places(round(transcode_size, decimal_places), decimal_places)
                data_for_current_row = [f'{size_rounded} MB', transcoded_bitrate]

                if not args.disable_quality_metrics:
                    os.makedirs(os.path.join(output_folder, 'Raw JSON Data'), exist_ok=True)
                    # os.path.join doesn't work with libvmaf's log_path option so we're manually defining the path with
                    # slashes.
                    json_file_path = f'{output_folder}/Raw JSON Data/CRF {crf}.json'
                    preset_string = ','.join(args.preset)
                    # The first line of Table.txt:
                    with open(comparison_table, 'w') as f:
                        f.write(METRICS_EXPLANATION)
                        f.write(f'Chosen preset: {preset_string}\n')
                        f.write(f'Original video bitrate: {original_bitrate}\n')
                    
                    run_libvmaf(transcode_output_path, args, json_file_path, fps, original_video)
                
                    create_table_plot_metrics(json_file_path, args, decimal_places, data_for_current_row, graph_filename,
                                            table, output_folder, time_rounded, crf)

                # --disable-quality-metrics argument specified
                else:
                    table.add_row([preset, f'{time_rounded}', f'{size_rounded} MB'])

        # args.preset is a list when more than one preset is specified.
        elif is_list(args.preset):
            print('Presets comparison mode activated.')
            chosen_presets = args.preset
            presets_string = ', '.join(chosen_presets)
            crf = args.crf_value[0] if is_list(args.crf_value) else args.crf_value
            video_encoder = args.video_encoder
            print(f'Presets {presets_string} will be compared at a CRF of {crf}.')
            # Cannot use os.path.join for output_folder as this gives an error like the following:
            # No such file or directory: '(2.mkv)\\Presets comparison at CRF 23/Raw JSON Data/superfast.json'
            output_folder = f'({filename})/Presets comparison at CRF {crf}'
            os.makedirs(output_folder, exist_ok=True)
            comparison_table = os.path.join(output_folder, 'Table.txt')
            table_column_names.insert(0, 'Preset')
            # Set the names of the columns
            table.field_names = table_column_names

            # The user only wants to transcode the first x seconds of the video.
            if args.encoding_time:
                original_video = cut_video(filename, args, output_ext, output_folder, comparison_table)

            # Transcode the video with each preset.
            for preset in chosen_presets:
                transcode_output_path = os.path.join(output_folder, f'{preset}.{output_ext}')
                graph_filename = f"Preset '{preset}'"
                
                factory = FfmpegProcessFactory()
                arguments = EncodingArguments()
                arguments.infile = original_video
                arguments.encoder = Encoder[video_encoder]
                arguments.crf = crf
                arguments.preset = preset
                arguments.outfile = transcode_output_path

                process = factory.create_process(arguments)
                
                line()
                print(f'Transcoding the video with preset {preset}...')
                start_time = time.time()
                process.run()
                end_time = time.time()
                print('Done!')
                time_to_convert = end_time - start_time
                time_rounded = force_decimal_places(round(time_to_convert, decimal_places), decimal_places)
                transcode_size = os.path.getsize(transcode_output_path) / 1_000_000
                transcoded_bitrate = provider.get_bitrate(transcode_output_path)
                size_rounded = force_decimal_places(round(transcode_size, decimal_places), decimal_places)
                data_for_current_row = [f'{size_rounded} MB', transcoded_bitrate]

                if not args.disable_quality_metrics:
                    os.makedirs(os.path.join(output_folder, 'Raw JSON Data'), exist_ok=True)
                    # os.path.join doesn't work with libvmaf's log_path option so we're manually defining the path with
                    # slashes.
                    json_file_path = f'{output_folder}/Raw JSON Data/{preset}.json'
                    # The first line of Table.txt:
                    with open(comparison_table, 'w') as f:
                        f.write(METRICS_EXPLANATION)
                        f.write(f'Chosen CRF: {crf}\n')
                        f.write(f'Original video bitrate: {original_bitrate}\n')

                    run_libvmaf(transcode_output_path, args, json_file_path, fps, original_video)
        
                    create_table_plot_metrics(json_file_path, args, decimal_places, data_for_current_row, graph_filename,
                                            time_rounded, table, output_folder, preset)

                # --disable-quality-metrics argument specified.
                else:
                    table.add_row([preset, f'{time_rounded}', f'{size_rounded} MB'])

    # -ntm argument was specified.
    else:
        
        line()
        output_folder = f'({filename})'
        os.makedirs(output_folder, exist_ok=True)
        comparison_table = os.path.join(output_folder, 'Table.txt')
        with open(comparison_table, 'w') as f:
            f.write(METRICS_EXPLANATION)
            f.write(f'Original video bitrate: {original_bitrate}\n')
        table.field_names = table_column_names
        # os.path.join doesn't work with libvmaf's log_path option so we're manually defining the path with slashes.
        json_file_path = f'{output_folder}/QualityMetrics.json'
        # Run libvmaf to get the quality metric(s).
        run_libvmaf(args.transcoded_video_path, args, json_file_path, fps, original_video)
        transcode_size = os.path.getsize(args.transcoded_video_path) / 1_000_000
        size_rounded = force_decimal_places(round(transcode_size, decimal_places), decimal_places)
        transcoded_bitrate = provider.get_bitrate(args.transcoded_video_path)
        data_for_current_row = [f'{size_rounded} MB', transcoded_bitrate]
        print(data_for_current_row)
        graph_filename = 'The variation of the quality of the transcoded video throughout the video'
        # Create the table and plot the metrics if -dqm was not specified.
        create_table_plot_metrics(json_file_path, args, decimal_places, data_for_current_row, graph_filename,
                                            table, output_folder, time_rounded=None, crf_or_preset=None)

    # Write the table to the Table.txt file.
    with open(comparison_table, 'a') as f:
        f.write(table.get_string())
    
    line()
    print(f'All done! Check out the ({filename}) folder.')


def cut_video(filename, args, output_ext, output_folder, comparison_table):
    cut_version_filename = f'{os.path.splitext(filename)[0]} [{args.encoding_time}s].{output_ext}'
    # Output path for the cut video.
    output_file_path = os.path.join(output_folder, cut_version_filename)
    # The reference file will be the cut version of the video.
    # Create the cut version.
    print(f'Cutting the video to a length of {args.encoding_time} seconds...')
    os.system(f'ffmpeg -loglevel warning -y -i {args.original_video_path} -t {args.encoding_time} '
              f'-map 0 -c copy "{output_file_path}"')
    print('Done!')

    time_message = f' for {args.encoding_time} seconds' if int(args.encoding_time) > 1 else 'for 1 second'

    with open(comparison_table, 'w') as f:
        f.write(f'You chose to encode {filename}{time_message} using {args.video_encoder}.\n' +
                {METRICS_EXPLANATION})

    return output_file_path


def run_libvmaf(transcode_output_path, args, json_file_path, fps, original_video):
    vmaf_options = {
        "model_path": "vmaf_v0.6.1.pkl",
        "phone_model": "1" if args.phone_model else "0",
        "psnr": "1" if args.calculate_psnr else "0",
        "ssim": "1" if args.calculate_ssim else "0",
        "log_path": json_file_path,
        "log_fmt": "json"
    }
    vmaf_options = ":".join(f'{key}={value}' for key, value in vmaf_options.items())

    subprocess_args = [
        "ffmpeg", "-loglevel", "error", "-stats", "-r", fps, "-i", transcode_output_path,
        "-r", fps, "-i", original_video,
        "-lavfi", "[0:v]setpts=PTS-STARTPTS[dist];[1:v]setpts=PTS-STARTPTS[ref];[dist][ref]"
        f'libvmaf={vmaf_options}', "-f", "null", "-"
    ]

    if args.calculate_psnr and args.calculate_ssim:
        end_of_computing_message = ', PSNR and SSIM'
    elif args.calculate_psnr:
        end_of_computing_message = ' and PSNR'
    elif args.calculate_ssim:
        end_of_computing_message = ' and SSIM'
    else:
        end_of_computing_message = ''

    print(f'Computing the VMAF{end_of_computing_message}...')
    subprocess.run(subprocess_args)
    print('Done!')


if __name__ == "__main__":
    main()