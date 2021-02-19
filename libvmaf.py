from utils import Logger
from ffmpeg_process_factory import LibVmafArguments

log = Logger('libmaf')

# Change this if you want to use a different VMAF model file.
vmaf_model_file_path = 'vmaf_models/vmaf_v0.6.1.json'


def run_libvmaf(transcode_output_path, args, json_file_path, fps, original_video_path, factory, crf_or_preset, duration):
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
        "n_threads": args.n_threads
    }
    vmaf_options = ":".join(f'{key}={value}' for key, value in vmaf_options.items())

    libvmaf_arguments = LibVmafArguments(fps, transcode_output_path, original_video_path, vmaf_options)
    video_filters = args.video_filters if args.video_filters else None
    libvmaf_arguments.video_filters(video_filters)

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
        if isinstance(args.crf, list) and len(args.crf) > 1:
            end_of_computing_message += f' achieved with CRF {crf_or_preset}'
        else:
            end_of_computing_message += f' achieved with preset {crf_or_preset}'

    print(f'Calculating the VMAF{end_of_computing_message}...')
    process.run(duration)
    log.info('Done!')
