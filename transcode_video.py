from ffmpeg_process_factory import EncodingArguments, EncoderOptions
from utils import line, Logger, Timer

from better_ffmpeg_progress import FfmpegProcess
import os

log = Logger("transcode_video.py")


def transcode_video(
    original_video_path, args, value, output_path, message, combination=None
):
    encoder_opts = EncoderOptions(
        encoder=args.encoder,
        options=args.encoder_options,
        av1_cpu_used=args.av1_cpu_used,
    )

    encoding_args = EncodingArguments(
        original_video_path,
        encoder_opts,
        output_path,
        args.parameter,
        value,
        combination,
        args.leading,
    )

    process = FfmpegProcess(
        encoding_args.get_arguments(), print_detected_duration=False
    )

    line()
    if os.path.exists(output_path) or args.skip_transcoding:
        log.info(f"{output_path} exists. Skipping transcoding.")
        return 0
    else:
        log.info(f"{message}...\n")
        timer = Timer()
        timer.start()
        process.run(print_command=args.debug)
        time_taken = timer.stop(args.decimal_places)
        print(f"Time Taken: {time_taken}s")
        log.info(f"Output file: {output_path}")
        return time_taken
        
