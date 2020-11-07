from ffmpeg import probe
import math, sys, os


def line():
    print('-----------------------------------------------------------------------------------------------------------')


def get_bitrate(video_path):
    bitrate = probe(video_path)['format']['bit_rate']
    return f'{math.trunc(int(bitrate) / 1000)} kbit/s'

def get_framerate_fraction(video_path):
    r_frame_rate = [stream for stream in probe(video_path)['streams'] if stream['codec_type'] == 'video'][0][
        'r_frame_rate']
    return r_frame_rate


def get_framerate_float(video_path):
    numerator, denominator = get_framerate_fraction(video_path).split('/')
    return round((int(numerator) / int(denominator)), 3)


def get_duration(video_path):
    return probe(video_path)['format']['duration']


def exit_program(message):
    line()
    print(message)
    line()
    sys.exit()


def is_list(argument_object):
    return isinstance(argument_object, list)
