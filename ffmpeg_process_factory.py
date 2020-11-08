import subprocess
from enum import Enum


class Encoder(Enum):
    x264 = 1
    x265 = 2


class FfmpegArguments:
    def get_arguments(self):
        return ["-i", self._infile, "-map", "0"]

    def get_infile(self):
        return self._infile

    def set_infile(self, value):
        self._infile = value

    infile = property(get_infile, set_infile)


class EncodingArguments(FfmpegArguments):
    def __init__(self):
        self._encoder = Encoder.x264

    def get_crf(self):
        return self._crf

    def set_crf(self, value):
        self._crf = value

    def get_encoder(self):
        return(self._encoder)

    def set_encoder(self, value):
        self._encoder = value

    def get_outfile(self):
        return(self._outfile)

    def set_outfile(self, value):
        self._outfile = value

    def get_preset(self):
        return self._preset

    def set_preset(self, value):
        self._preset = value

    def get_arguments(self):
        return super().get_arguments() + \
            [
                "-c:v", "lib" + self._encoder.name,
                "-crf", str(self._crf),
                "-preset", self._preset,
                "-an", "-sn", self._outfile
            ]

    crf = property(get_crf, set_crf)
    preset = property(get_preset, set_preset)
    encoder = property(get_encoder, set_encoder)
    outfile = property(get_outfile, set_outfile)


class FfmpegProcessFactory:
    def create_process(self, arguments):
        _process_base_arguments = [
            "ffmpeg", "-loglevel", "warning", "-stats", "-y",
        ]

        process = FfmpegProcess(
            _process_base_arguments + arguments.get_arguments())

        return process


class FfmpegProcess:
    def __init__(self, arguments):
        self._arguments = arguments

    def run(self):
        subprocess.run(self._arguments)
