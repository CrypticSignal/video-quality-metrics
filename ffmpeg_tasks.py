"""The FFmpeg commands that transcode the video and calculate the quality metrics."""

import shlex
from argparse import Namespace
from pathlib import Path
from time import perf_counter

from better_ffmpeg_progress import FfmpegProcess

from metrics import enabled_metrics
from utils import line, log

# Change this if you want to use a different VMAF model file.
# It is relative to this file so that the program works from any directory.
VMAF_MODEL_PATH = Path(__file__).parent / "vmaf_models" / "vmaf_v0.6.1.json"


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
    FfmpegProcess(command).run(print_command=args.debug)
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
    model_path = backslash_escape(VMAF_MODEL_PATH.as_posix(), "':=")
    model = f"path={model_path}"
    if args.phone_model:
        model += "|enable_transform=true"

    # libvmaf expects forward slashes and escaped single quotes in the log path.
    log_path = str(json_path).replace("\\", "/").replace("'", "\\'")

    vmaf_options = (
        f"model={quote_filter_option(model)}:log_fmt=json:log_path='{log_path}'"
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
        f"[distorted][reference]libvmaf={vmaf_options}"
    )

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
        "-map",
        "0:V",
        "-map",
        "1:V",
        "-lavfi",
        filtergraph,
        "-f",
        "null",
        "-",
    ]

    metrics = enabled_metrics(args)
    run_ffmpeg(command, f"Calculating the {'/'.join(metrics)} of {distorted_video}", args)
