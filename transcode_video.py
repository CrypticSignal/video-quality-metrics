import os
from typing import Any, Optional

from better_ffmpeg_progress import FfmpegProcess

from ffmpeg_process_factory import EncoderOptions, EncodingArguments
from utils import Logger, Timer, force_decimal_places, line

log = Logger("transcode_video.py")


def transcode_video(
    original_video_path: str,
    args: Any,
    value: Optional[str],
    output_path: str,
    message: str,
    combination: Optional[list[str]] = None,
) -> float:
    encoder_opts = EncoderOptions(
        encoder=args.encoder,
        av1_cpu_used=args.av1_cpu_used,
    )

    encoding_args = EncodingArguments(
        original_video_path,
        encoder_opts,
        output_path,
        args.parameter,
        value,
        combination,
        input_options=args.input_options,
        output_options=args.output_options,
    )

    process = FfmpegProcess(encoding_args.get_arguments(), print_detected_duration=False)

    line()
    log.info(f"{message}...\n")
    timer = Timer()
    timer.start()
    process.run(print_command=args.debug)
    time_taken = timer.stop(args.decimal_places)
    log.info(f"Time Taken: {force_decimal_places(time_taken, args.decimal_places)}s")
    log.info(f"Output file: {output_path}")

    return time_taken
