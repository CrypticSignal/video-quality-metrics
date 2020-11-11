import sys
import math
from time import time

from ffmpeg import probe


def line():
    print('-----------------------------------------------------------------------------------------------------------')


def is_list(argument_object):
    return isinstance(argument_object, list)


def force_decimal_places(value, decimal_places):
	return '{:0.{dp}f}'.format(value, dp=decimal_places)


def exit_program(message):
    line()
    print(f'[Exiting Program] {message}')
    line()
    sys.exit()


class VideoInfoProvider:
    def __init__(self, video_path):
        self._video_path = video_path

    def get_bitrate(self, video_path=None):
        if video_path:
            bitrate = probe(video_path)['format']['bit_rate']
        else:
            bitrate = probe(self._video_path)['format']['bit_rate']
        return f'{math.trunc(int(bitrate) / 1000)} kbit/s'

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
        self.__start_time = time()

    def end(self, decimal_places):
        time_to_convert = time() - self.__start_time
        time_rounded = force_decimal_places(round(time_to_convert, decimal_places), decimal_places)
        return time_rounded
