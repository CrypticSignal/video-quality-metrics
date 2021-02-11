import logging
import os
import sys
from pathlib import Path
from time import time, sleep

from ffmpeg import probe


class VideoInfoProvider:
    def __init__(self, video_path):
        self._video_path = video_path

    def get_bitrate(self, decimal_places, video_path=None):
        if video_path:
            bitrate = probe(video_path)['format']['bit_rate'] 
        else:
            bitrate = probe(self._video_path)['format']['bit_rate']
        return f'{force_decimal_places((int(bitrate) / 1_000_000), decimal_places)} Mbps'

    def get_framerate_fraction(self):
        r_frame_rate = [stream for stream in probe(self._video_path)['streams']
                        if stream['codec_type'] == 'video'][0]['r_frame_rate']
        return r_frame_rate

    def get_framerate_float(self):
        numerator, denominator = self.get_framerate_fraction().split('/')
        return round((int(numerator) / int(denominator)), 3)

    def get_duration(self):
        return probe(self._video_path)['format']['duration']


class Timer:
    def start(self):
        self._start_time = time()

    def stop(self, decimal_places):
        time_to_convert = time() - self._start_time
        time_rounded = force_decimal_places(round(time_to_convert, decimal_places), decimal_places)
        return time_rounded


class Logger():
    def __init__(self, name, filename='logs.log', print_to_terminal=True):
        with open(filename, 'w'): pass
        
        logger = logging.getLogger(name)
        logger.setLevel(10)

        file_handler = logging.FileHandler(filename)
        logger.addHandler(file_handler)
        self._file_handler = file_handler
        
        if print_to_terminal:
            logger.addHandler(logging.StreamHandler())

        self._logger = logger

    def info(self, msg):
        self._file_handler.setFormatter(logging.Formatter('[%(name)s] %(message)s'))
        self._logger.info(msg)

    def warning(self, msg):
        self._file_handler.setFormatter(logging.Formatter('[%(name)s] [WARNING] %(message)s'))
        self._logger.warning(msg)

    def debug(self, msg):
        self._file_handler.setFormatter(logging.Formatter('[%(name)s] [DEBUG] %(message)s'))
        self._logger.debug(msg)


log = Logger('utils')


def line():
    log.info('-----------------------------------------------------------------------------------------------------------')


def show_progress_bar(progress, total, dp, extra_info=''):
    sleep(0.1)
    width, height = os.get_terminal_size()
    extra_info_len = len(extra_info)
    bar_length = width - extra_info_len - 10
    filled_length = int(bar_length * (progress / total))

    bar = ('█' * filled_length) + ('-' * (bar_length - filled_length))
    percentage_complete = round(100.0 * (progress / total), dp)

    sys.stdout.write(f'|{bar}| {percentage_complete}% {extra_info}\r')
    sys.stdout.flush() 


def is_list(argument_object):
    return isinstance(argument_object, list)


def force_decimal_places(value, decimal_places):
    return f'{value:.{decimal_places}f}'


def cut_video(filename, args, output_ext, output_folder, comparison_table):
    cut_version_filename = f'{Path(filename).stem} [{args.encode_length}s]{output_ext}'
    # Output path for the cut video.
    output_file_path = os.path.join(output_folder, cut_version_filename)
    # The reference file will be the cut version of the video.
    # Create the cut version.
    log.info(f'Cutting the video to a length of {args.encode_length} seconds...')
    os.system(f'ffmpeg -loglevel warning -y -i {args.original_video_path} -t {args.encode_length} '
              f'-map 0 -c copy "{output_file_path}"')
    log.info('Done!')

    time_message = f' for {args.encode_length} seconds' if int(args.encode_length) > 1 else 'for 1 second'

    with open(comparison_table, 'w') as f:
        f.write(f'You chose to encode {filename}{time_message} using {args.video_encoder}.')

    return output_file_path


def write_table_info(table_path, video_filename, original_bitrate, args, crf_or_preset):
    with open(table_path, 'a') as f:
        f.write(
            f'\nFile Transcoded: {video_filename}\n'
            f'Bitrate: {original_bitrate}\n'
            f'Encoder used for the transcodes: {args.video_encoder}\n'
            f'{crf_or_preset} was used.\n'
            f'Filter(s) used: {"None" if not args.video_filters else args.video_filters}\n'
            f'n_subsample: {args.subsample}')


def exit_program(message):
    line()
    log.info(f'{message}\nThis program will now exit.')
    line()
    sys.exit()
