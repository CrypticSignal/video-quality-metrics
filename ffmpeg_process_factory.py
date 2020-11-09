import subprocess
from enum import Enum


class Encoder(Enum):
    x264 = 1
    x265 = 2


class FfmpegArguments:
    _fps = int(0)
    _infile = str()

    def get_arguments(self):
        result = []
        if self._fps != 0:
            result = result + ["-r", self._fps]

        result = result + ["-i", self._infile]

        return result

    def get_fps(self):
        return self._fps

    def set_fps(self, value):
        self._fps = value

    def get_infile(self):
        return self._infile

    def set_infile(self, value):
        self._infile = value

    fps = property(get_fps, set_fps)
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
                "-map", "0",
                "-c:v", "lib" + self._encoder.name,
                "-crf", str(self._crf),
                "-preset", self._preset,
                "-an", "-sn", self._outfile
            ]

    crf = property(get_crf, set_crf)
    preset = property(get_preset, set_preset)
    encoder = property(get_encoder, set_encoder)
    outfile = property(get_outfile, set_outfile)


class LibVmafArguments(FfmpegArguments):
    _vmaf_options = str()
    _second_infile = str()

    def get_second_infile(self):
        return self._second_infile

    def set_second_infile(self, value):
        self._second_infile = value

    def get_vmaf_options(self):
        return self._vmaf_options

    def set_vmaf_options(self, value):
        self._vmaf_options = value

    def get_arguments(self):
        return super().get_arguments() + \
            [
                "-r", str(self._fps),
                "-i", self._second_infile,
                "-lavfi", "[0:v]setpts=PTS-STARTPTS[dist];[1:v]setpts="
                          "PTS-STARTPTS[ref];[dist][ref]"
                          f'libvmaf={self._vmaf_options}', "-f", "null", "-"
            ]

    second_infile = property(get_second_infile, set_second_infile)
    vmaf_options = property(get_vmaf_options, set_vmaf_options)


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
