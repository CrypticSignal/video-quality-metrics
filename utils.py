from ffmpeg import probe
import math, sys


def get_framerate_fraction(video_path):
    r_frame_rate = [stream for stream in probe(video_path)['streams'] if stream['codec_type'] == 'video'][0][
        'r_frame_rate']
    return r_frame_rate


def get_framerate_float(video_path):
    numerator, denominator = get_framerate_fraction(video_path).split('/')
    return round((int(numerator) / int(denominator)), 3)


def get_bitrate(video_path):
    bitrate = probe(video_path)['format']['bit_rate']
    return f'{math.trunc(int(bitrate) / 1000)} kbit/s'


def get_duration(video_path):
    return probe(video_path)['format']['duration']


def separator():
    print('-----------------------------------------------------------------------------------------------------------')


def exit_program(message):
    separator()
    print(message)
    separator()
    sys.exit()


def is_list(argument_object):
    return isinstance(argument_object, list)
