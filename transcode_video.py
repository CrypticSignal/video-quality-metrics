from ffmpeg_process_factory import EncodingArguments, EncoderOptions
from utils import line, Logger, Timer

from better_ffmpeg_progress import FfmpegProcess

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
    )

    process = FfmpegProcess(
        encoding_args.get_arguments(), print_detected_duration=False
    )

    line()
    log.info(f"{message}...\n")
    timer = Timer()
    timer.start()
    process.run(progress_bar_description="")
    time_taken = timer.stop(args.decimal_places)
    print(f"Time Taken: {time_taken}s")
    log.info(f"Output file: {output_path}")
    return time_taken
