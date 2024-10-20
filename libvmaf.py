from ffmpeg_process_factory import LibVmafArguments
from utils import line, Logger, get_metrics_list

log = Logger("libvmaf")

# Change this if you want to use a different VMAF model file.
model_file_path = "vmaf_models/vmaf_v0.6.1.json"


def run_libvmaf(
    transcode_output_path,
    args,
    json_file_path,
    fps,
    original_video_path,
    factory,
    crf_or_preset=None,
):
    characters_to_escape = ["'", ":", ",", "[", "]"]
    for character in characters_to_escape:
        if character in json_file_path:
            json_file_path = json_file_path.replace(character, f"\{character}")

    n_subsample = "1" if not args.subsample else args.subsample

    model_params = filter(
        None,
        [
            f"path={model_file_path}",
            "enable_transform=true" if args.phone_model else "",
        ],
    )
    model_string = f"model='{'|'.join(model_params)}'"

    features = filter(
        None,
        [
            "name=psnr" if args.calculate_psnr else "",
            "name=float_ssim" if args.calculate_ssim else "",
            "name=float_ms_ssim" if args.calculate_msssim else "",
        ],
    )
    feature_string = f":feature='{'|'.join(features)}'"

    vmaf_options = f"""
    {model_string}:log_fmt=json:log_path='{json_file_path}':n_subsample={n_subsample}:n_threads={args.n_threads}{feature_string}
    """

    libvmaf_arguments = LibVmafArguments(
        fps, transcode_output_path, original_video_path, vmaf_options
    )
    video_filters = args.video_filters if args.video_filters else None
    libvmaf_arguments.video_filters(video_filters)

    process = factory.create_process(libvmaf_arguments)

    metrics_list = get_metrics_list(args)

    metric_types = metrics_list[0]
    if len(metrics_list) > 1:
        metric_types = f"{', '.join(metrics_list[:-1])} and {metrics_list[-1]}"

    message_transcoding_mode = ""
    if not args.no_transcoding_mode:
        if isinstance(args.crf, list) and len(args.crf) > 1:
            message_transcoding_mode += f" achieved with CRF {crf_or_preset}"
        else:
            message_transcoding_mode += f" achieved with preset {crf_or_preset}"

    line()
    log.info(f"Calculating the {metric_types}{message_transcoding_mode}...")

    process.run()
