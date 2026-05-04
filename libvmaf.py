import os
from typing import Any

from better_ffmpeg_progress import FfmpegProcess

from ffmpeg_process_factory import LibVmafArguments
from utils import Logger, Timer, force_decimal_places, get_metrics_list, line

log = Logger("libvmaf.py")

# Change this if you want to use a different VMAF model file.
model_file_path = "vmaf_models/vmaf_v0.6.1.json"


def run_libvmaf(
    transcode_output_path: str,
    args: Any,
    json_file_path: str,
    original_video_path: str,
    message: str = "",
) -> None:
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

    features = []
    if not args.disable_psnr:
        features.append("name=psnr")
    if not args.disable_ssim:
        features.append("name=float_ssim")

    if features:
        feature_string = f":feature={'|'.join(features)}"
        # On Windows, escape the pipe character
        if os.name == "nt":
            feature_string = feature_string.replace("|", "^|")
    else:
        feature_string = ""

    vmaf_options = f"{model_string}:log_fmt=json:log_path='{json_file_path_escaped}':n_subsample={n_subsample}:n_threads={args.n_threads}{feature_string}"

    libvmaf_arguments = LibVmafArguments(
        original_video_path, transcode_output_path, vmaf_options, args.video_filters
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
    log.info(f"Calculating the {metric_types}{message}...\n")
    timer = Timer()
    timer.start()
    process.run(print_command=args.debug)
    time_taken = timer.stop(args.decimal_places)
    log.info(f"Time Taken: {force_decimal_places(time_taken, args.decimal_places)}s")
