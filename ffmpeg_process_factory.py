import subprocess
from enum import Enum


class Encoder(Enum):
    x264 = 1
    x265 = 2


class FfmpegArguments:
    _fps = 0

    def get_arguments(self):
        base_ffmpeg_arguments = ["-i", self.__infile]
        if self._fps != 0:
            base_ffmpeg_arguments = ["-r", self._fps, "-i", self.__infile]
        return base_ffmpeg_arguments

    @property
    def infile(self):
        return self.__infile

    @infile.setter
    def infile(self, value):
        self.__infile = value

    @property
    def fps(self):
        return self._fps

    @fps.setter
    def fps(self, value):
        self._fps = value


class EncodingArguments(FfmpegArguments):
    def __init__(self):
        self.__encoder = Encoder.x264

    @property
    def encoder(self):
        return self.__encoder

    @encoder.setter
    def encoder(self, value):
        self.__encoder = value

    @property
    def preset(self):
        return self.__preset

    @preset.setter
    def preset(self, value):
        self.__preset = value

    @property
    def crf(self):
        return self.__crf

    @crf.setter
    def crf(self, value):
        self.__crf = value

    @property
    def outfile(self):
        return(self.__outfile)

    @outfile.setter
    def outfile(self, value):
        self.__outfile = value

    def get_arguments(self):
        return super().get_arguments() + \
            [
                "-map", "0:V",
                "-c:v", "lib" + self.__encoder.name,
                "-crf", self.__crf,
                "-preset", self.__preset,
                self.__outfile
            ]


class LibVmafArguments(FfmpegArguments):
    @property
    def second_infile(self):
        return self.__second_infile

    @second_infile.setter
    def second_infile(self, value):
        self.__second_infile = value

    @property
    def vmaf_options(self):
        return self.__vmaf_options

    @vmaf_options.setter
    def vmaf_options(self, value):
        self.__vmaf_options = value

    def get_arguments(self):
        return super().get_arguments() + \
            [
                "-r", self._fps,
                "-i", self.__second_infile,
                "-lavfi", "[0:v]setpts=PTS-STARTPTS[dist];[1:v]setpts="
                          "PTS-STARTPTS[ref];[dist][ref]"
                          f'libvmaf={self.__vmaf_options}', "-f", "null", "-"
            ]


class FfmpegProcessFactory:
    def create_process(self, arguments):
        __process_base_arguments = [
            "ffmpeg", "-loglevel", "warning", "-stats", "-y",
        ]

        process = FfmpegProcess(
            __process_base_arguments + arguments.get_arguments())

        return process


class FfmpegProcess:
    def __init__(self, arguments):
        self.__arguments = arguments

    def run(self):
        subprocess.run(self.__arguments)
