from ffmpeg_process_factory import NewFfmpegProcess, FFmpegCommand
from utils import line, Logger, Timer

log = Logger("transcode_video.py")


def transcode_video(
    video_path, args, value, output_path, message, vmaf_options=None, fps=None
):
    arguments = FFmpegCommand(
        video_path, args.encoder, args.parameter, value, output_path, vmaf_options, fps
    )

    if args.encoder == "libaom-av1":
        arguments.av1_cpu_used(str(args.av1_cpu_used))

    video_filters = args.video_filters if args.video_filters else None
    arguments.video_filters(video_filters)

    process = NewFfmpegProcess(arguments.get_arguments())

    line()
    log.info(f"Transcoding the video using {message}...\n")
    timer = Timer()
    timer.start()
    process.run()
    time_taken = timer.stop(args.decimal_places)
    log.info(f"Output file: {output_path}")
    return time_taken
