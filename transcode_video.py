from ffmpeg_process_factory import EncodingArguments, NewFfmpegProcess
from utils import line, Logger, Timer

log = Logger("transcode_video.py")


def transcode_video(original_video_path, args, value, output_path, message):
    arguments = EncodingArguments(
        original_video_path, args.encoder, args.parameter, value, output_path
    )

    if args.encoder == "libaom-av1":
        arguments.av1_cpu_used(str(args.av1_cpu_used))

    process = NewFfmpegProcess()

    line()
    log.info(f"Transcoding the video using {message}...\n")
    timer = Timer()
    timer.start()
    process.run(arguments.get_arguments())
    time_taken = timer.stop(args.decimal_places)
    print(f"Transcoding with {args.parameter} '{value}' took {time_taken}s")
    log.info(f"Output file: {output_path}")
    return time_taken
