from ffmpeg_process_factory import EncodingArguments, NewFfmpegProcess
from utils import line, Logger, Timer

log = Logger("transcode_video.py")


def transcode_video(
    original_video_path, args, value, output_path, message, combination=None
):
    arguments = EncodingArguments(
        original_video_path,
        args.encoder,
        args.encoder_options,
        args.parameter,
        value,
        output_path,
        combination,
    )

    if args.encoder == "libaom-av1":
        arguments.av1_cpu_used(str(args.av1_cpu_used))

    process = NewFfmpegProcess(log_file="transcode_video_log.txt")

    line()
    log.info(f"{message}...\n")
    timer = Timer()
    timer.start()
    process.run(arguments.get_arguments())
    time_taken = timer.stop(args.decimal_places)
    print(f"Time Taken: {time_taken}s")
    log.info(f"Output file: {output_path}")
    return time_taken
