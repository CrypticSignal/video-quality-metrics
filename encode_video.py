from ffmpeg_process_factory import EncodingArguments, FfmpegProcessFactory
from utils import Timer

factory = FfmpegProcessFactory()
timer = Timer()


def encode_video(args, crf, preset, output_path, message):
    arguments = EncodingArguments(args.video_encoder)
    
    arguments.infile = args.original_video_path

    if args.video_encoder == 'av1':
        arguments.av1_cpu_used = str(args.av1_cpu_used)

    arguments.crf = str(crf)
    arguments.preset = preset
    arguments.filterchain = args.filterchain if args.filterchain else None
    arguments.outfile = output_path

    process = factory.create_process(arguments, args)
    
    print(f'Transcoding the video with {message}...')
    timer.start()
    process.run()
    time_taken = timer.stop(args.decimal_places)
    print(f'Done! Time taken: {time_taken} seconds.')

    return factory, time_taken
