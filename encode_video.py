from ffmpeg_process_factory import EncodingArguments, FfmpegProcessFactory
from utils import Timer


def encode_video(args, crf, preset, output_path, message):
    arguments = EncodingArguments(args.original_video_path, args.video_encoder, output_path)
    
    arguments.infile = args.original_video_path

    if args.video_encoder == 'av1':
        arguments.av1_cpu_used(str(args.av1_cpu_used))

    arguments.crf(str(crf))
    arguments.preset(preset)
    video_filters = args.video_filters if args.video_filters else None
    arguments.video_filters(video_filters)

    factory = FfmpegProcessFactory()
    process = factory.create_process(arguments, args)
    
    print(f'Transcoding the video with {message}...\n')
    timer = Timer()
    timer.start()
    process.run()
    time_taken = timer.stop(args.decimal_places)
    print(f'Done! Time taken: {time_taken} seconds.\n')

    return factory, time_taken
