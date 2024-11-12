from ffmpeg_process_factory import LibVmafArguments, NewFfmpegProcess
from utils import line, Logger, get_metrics_list, Timer

log = Logger("libvmaf")

# Change this if you want to use a different VMAF model file.
model_file_path = "vmaf_models/vmaf_v0.6.1.json"


def run_libvmaf(
    transcode_output_path,
    args,
    json_file_path,
    original_video_path,
    parameter_value=None,
):
    n_subsample = args.n_subsample if args.n_subsample else "1"

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

    vmaf_options = f"{model_string}:log_fmt=json:log_path='{json_file_path}':n_subsample={n_subsample}:n_threads={args.n_threads}{feature_string}"

    libvmaf_arguments = LibVmafArguments(
        original_video_path,
        args.video_filters,
        transcode_output_path,
        vmaf_options,
        args.scale,
    )

    process = NewFfmpegProcess(log_file="calculate_metrics_log.txt")

    metrics_list = get_metrics_list(args)

    metric_types = metrics_list[0]
    if len(metrics_list) > 1:
        metric_types = f"{', '.join(metrics_list[:-1])} and {metrics_list[-1]}"

    message_transcoding_mode = ""
    if not args.no_transcoding_mode:
        message_transcoding_mode += (
            f" achieved with '-{args.parameter} {parameter_value}'"
        )

    line()
    log.info(f"Calculating the {metric_types}{message_transcoding_mode}...\n")

    timer = Timer()
    timer.start()
    process.run(libvmaf_arguments.get_arguments())
    print(f"Time Taken: {timer.stop(args.decimal_places)}s")
