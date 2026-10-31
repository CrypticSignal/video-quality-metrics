"""The FFmpeg commands that transcode the video and calculate the quality metrics."""

import shlex
import subprocess
from argparse import Namespace
from pathlib import Path
from time import perf_counter

from better_ffmpeg_progress import FfmpegProcess, FfmpegProcessError

from metrics import enabled_metrics
from utils import exit_program, line, log

# The model files are relative to this file so that the program works from any directory.
VMAF_MODELS_FOLDER = Path(__file__).parent / "vmaf_models"


def vmaf_model_path(args: Namespace) -> Path:
    """Return the path of the VMAF model file to use."""
    model_file = "vmaf_4k_v0.6.1.json" if args.four_k_model else "vmaf_v0.6.1.json"
    return VMAF_MODELS_FOLDER / model_file


def check_ffmpeg() -> None:
    """Exit if FFmpeg or FFprobe can't be run, or if FFmpeg doesn't have the libvmaf filter."""
    for program in ("ffmpeg", "ffprobe"):
        try:
            subprocess.run([program, "-version"], capture_output=True, check=True)
        except (OSError, subprocess.CalledProcessError):
            exit_program(
                f"Unable to run {program}. Make sure that it is installed and in your PATH."
            )

    filters = subprocess.run(
        ["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True
    ).stdout
    # Each line is e.g. " ... libvmaf  VV->V  Calculate the VMAF between two video streams."
    if not any(line.split()[1:2] == ["libvmaf"] for line in filters.splitlines()):
        exit_program(
            "Your build of FFmpeg does not have the libvmaf filter.\n"
            "Builds that have it are listed in the FFmpeg Builds section of the README."
        )


def backslash_escape(value: str, special_characters: str) -> str:
    """Put a backslash before each backslash and each of the special characters."""
    for character in "\\" + special_characters:
        value = value.replace(character, f"\\{character}")
    return value


def quote_filter_option(value: str) -> str:
    """Quote and escape a filter option's value so that FFmpeg reads it unchanged.

    FFmpeg parses the value twice: once as part of the filtergraph and then
    as one of the filter's colon-separated options. In the quotes, each
    apostrophe must end the quote, be escaped and then start a new quote.
    """
    escaped = backslash_escape(value, "':")
    return "'" + escaped.replace("'", "'\\''") + "'"


def run_ffmpeg(command: list[str], message: str, args: Namespace) -> float:
    """Run an FFmpeg command with a progress bar and return the time taken in seconds."""
    line()
    log.info(f"{message}...\n")

    start_time = perf_counter()
    try:
        FfmpegProcess(command).run(print_command=args.debug)
    except FfmpegProcessError as error:
        # The error names the log file that contains FFmpeg's output.
        exit_program(str(error))
    time_taken = round(perf_counter() - start_time, args.decimal_places)

    log.info(f"Time Taken: {time_taken:.{args.decimal_places}f}s")
    return time_taken


def transcode(
    reference_video: str | Path,
    encoder_options: list[str],
    output_path: Path,
    args: Namespace,
) -> float:
    """Transcode the video using the encoder options, e.g. ["-crf", "23"].

    Returns the time taken in seconds.
    """
    command = ["ffmpeg", "-y"]
    if args.input_options:
        command += shlex.split(args.input_options)
    command += ["-i", str(reference_video), "-c:v", args.encoder]
    if args.output_options:
        command += shlex.split(args.output_options)
    if args.encoder == "libaom-av1":
        command += ["-b:v", "0", "-cpu-used", str(args.av1_cpu_used)]
    command += encoder_options + [str(output_path)]

    description = " ".join(encoder_options)
    time_taken = run_ffmpeg(command, f"Transcoding {reference_video} using '{description}'", args)
    log.info(f"Output file: {output_path}")
    return time_taken


def quality_metrics_settings(args: Namespace) -> dict:
    """Return the settings that affect the quality metrics, so that saved scores are only
    reused if they were calculated with the same settings."""
    return {
        "metrics": enabled_metrics(args),
        "model": vmaf_model_path(args).name,
        "phone_model": args.phone_model,
        "n_subsample": args.n_subsample,
        "video_filters": args.video_filters,
    }


def calculate_quality_metrics(
    reference_video: str | Path,
    distorted_video: Path,
    json_path: Path,
    args: Namespace,
) -> None:
    """Use libvmaf to compare the distorted video against the reference video.

    The per-frame scores are saved to json_path.
    """
    # The model option is parsed again by libvmaf, as key=value pairs separated by colons.
    # This matters for absolute paths, e.g. "C:/Users" or "/Users/Sam's Mac".
    model_path = backslash_escape(vmaf_model_path(args).as_posix(), "':=")
    model = f"path={model_path}"
    if args.phone_model:
        # A colon adds an option to the same model, whereas "|" would start a second model.
        model += ":enable_transform=true"

    # libvmaf expects forward slashes in the log path.
    log_path = quote_filter_option(json_path.as_posix())

    vmaf_options = (
        f"model={quote_filter_option(model)}:log_fmt=json:log_path={log_path}"
        f":n_subsample={args.n_subsample}:n_threads={args.n_threads}"
    )

    features = []
    if not args.disable_psnr:
        features.append("name=psnr")
    if not args.disable_ssim:
        features.append("name=float_ssim")
    if features:
        vmaf_options += f":feature={'|'.join(features)}"

    video_filters = f"{args.video_filters}," if args.video_filters else ""
    filtergraph = (
        f"[0:V]{video_filters}setpts=PTS-STARTPTS[reference];"
        f"[1:V]setpts=PTS-STARTPTS[distorted];"
        # libvmaf needs both videos to have the same resolution, so if the transcode was scaled
        # (e.g. with --output-options), scale it back. This does nothing if they already match.
        f"[distorted][reference]scale2ref=flags=bicubic[distorted_scaled][reference_scaled];"
        f"[distorted_scaled][reference_scaled]libvmaf={vmaf_options}[vmaf]"
    )

    # As an input option, -r makes FFmpeg ignore the timestamps in the file and give the frames
    # evenly spaced timestamps at that frame rate. Doing this to both videos means that libvmaf
    # pairs the frames by their order, even if the timestamps differ (e.g. a variable frame rate
    # or a different start time). The value itself doesn't matter, as long as both are the same.
    command = [
        "ffmpeg",
        "-r",
        "24",
        "-i",
        str(reference_video),
        "-r",
        "24",
        "-i",
        str(distorted_video),
        "-lavfi",
        filtergraph,
        # Only libvmaf's output is mapped. Mapping the input videos as well (-map 0:V -map 1:V)
        # adds each of them as an extra output stream, so they are decoded twice, and the extra
        # outputs can make FFmpeg 7 fail with "Assertion best_input >= 0 failed".
        "-map",
        "[vmaf]",
        "-f",
        "null",
        "-",
    ]

    metrics = enabled_metrics(args)
    run_ffmpeg(command, f"Calculating the {'/'.join(metrics)} of {distorted_video}", args)
