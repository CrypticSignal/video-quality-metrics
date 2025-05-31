import os

from ffmpeg_process_factory import LibVmafArguments
from utils import line, Logger, get_metrics_list, Timer

from better_ffmpeg_progress import FfmpegProcess

log = Logger("libvmaf.py")

# Change this if you want to use a different VMAF model file.
model_file_path = "vmaf_models/vmaf_v0.6.1.json"


def run_libvmaf(
    transcode_output_path,
    args,
    json_file_path,
    original_video_path,
    message,
):
    n_subsample = args.n_subsample if args.n_subsample else "1"

    model_params = [
        f"path={model_file_path}",
    ]

    if args.phone_model:
        model_params.append("enable_transform=true")

    model_string = f"model={'|'.join(model_params)}"

    json_file_path_str = str(json_file_path).replace("\\", "/")
    # Escape any single quotes
    json_file_path_escaped = json_file_path_str.replace("'", "\\'")

    features = [
        "name=psnr" if not args.disable_psnr else None,
        "name=float_ssim" if not args.disable_ssim else None,
    ]
    feature_string = f":feature={'|'.join(features)}"

    # On Windows, escape the pipe character
    if os.name == "nt":
        feature_string = feature_string.replace("|", "^|")

    vmaf_options = f"{model_string}:log_fmt=json:log_path='{json_file_path_escaped}':n_subsample={n_subsample}:n_threads={args.n_threads}{feature_string}"

    libvmaf_arguments = LibVmafArguments(
        original_video_path,
        transcode_output_path,
        vmaf_options,
        args.video_filters,
        args.scale,
    )

    process = FfmpegProcess(
        libvmaf_arguments.get_arguments(),
        print_detected_duration=False,
    )

    metrics_list = get_metrics_list(args)

    metric_types = metrics_list[0]
    if len(metrics_list) > 1:
        metric_types = f"{', '.join(metrics_list[:-1])} and {metrics_list[-1]}"

    line()
    log.info(
        f"Calculating the {metric_types}{message if not args.no_transcoding_mode else ''}...\n"
    )

    timer = Timer()
    timer.start()
    process.run()
    log.info(f"Time Taken: {timer.stop(args.decimal_places)}s")
