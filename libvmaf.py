from ffmpeg_process_factory import LibVmafArguments
from utils import Timer

# Change this if you want to use a different VMAF model file.
vmaf_model_file_path = 'vmaf_models/vmaf_v0.6.1.json'


def run_libvmaf(transcode_output_path, args, json_file_path, fps, original_video_path, factory, crf_or_preset):
    characters_to_escape = ["'", ":", ",", "[", "]"]
    for character in characters_to_escape:
        if character in json_file_path:
            json_file_path = json_file_path.replace(character, f'\{character}')    

    vmaf_options = {
        "log_fmt": "json",
        "log_path": json_file_path,
        "model_path": vmaf_model_file_path,
        "n_subsample": "1" if not args.subsample else args.subsample,
        "phone_model": "1" if args.phone_model else "0",
        "psnr": "1" if args.calculate_psnr else "0",
        "ssim": "1" if args.calculate_ssim else "0",
        "n_threads": args.threads
    }
    vmaf_options = ":".join(f'{key}={value}' for key, value in vmaf_options.items())

    libvmaf_arguments = LibVmafArguments()

    libvmaf_arguments.infile = transcode_output_path
    libvmaf_arguments.fps = fps
    libvmaf_arguments.second_infile = original_video_path
    libvmaf_arguments.filterchain = args.filterchain if args.filterchain else None
    libvmaf_arguments.vmaf_options = vmaf_options

    process = factory.create_process(libvmaf_arguments, args)

    if args.calculate_psnr and args.calculate_ssim:
        end_of_computing_message = ', PSNR and SSIM'
    elif args.calculate_psnr:
        end_of_computing_message = ' and PSNR'
    elif args.calculate_ssim:
        end_of_computing_message = ' and SSIM'
    else:
        end_of_computing_message = ''

    if not args.no_transcoding_mode:
        if isinstance(args.crf_value, list) and len(args.crf_value) > 1:
            end_of_computing_message += f' achieved with CRF {crf_or_preset}'
        else:
            end_of_computing_message += f' achieved with preset {crf_or_preset}'

    print(f'\nComputing the VMAF{end_of_computing_message}...\n')
    timer = Timer()
    timer.start()
    process.run()
    time_taken = timer.stop(args.decimal_places)
    print(f'Done! Time taken: {time_taken} seconds.')