import subprocess
from enum import Enum


class Encoder(Enum):
    x264 = 1
    x265 = 2
    av1 = 3


class FfmpegArguments:
    _fps = None

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

    def get_arguments(self):
        base_ffmpeg_arguments = ["-i", self.__infile]
        if self._fps is not None:
            base_ffmpeg_arguments = ["-r", self._fps, "-i", self.__infile]
        return base_ffmpeg_arguments


class EncodingArguments(FfmpegArguments):
    def __init__(self):
        self.__encoder = Encoder.x264

    # Encoder

    @property
    def encoder(self):
        return self.__encoder

    @encoder.setter
    def encoder(self, value):
        self.__encoder = value

    # AV1 compression

    @property
    def av1_compression(self):
        return self.__av1_compression

    @av1_compression.setter
    def av1_compression(self, value):
        self.__av1_compression = value

    # Preset

    @property
    def preset(self):
        return self.__preset

    @preset.setter
    def preset(self, value):
        self.__preset = value

    # CRF

    @property
    def crf(self):
        return self.__crf

    @crf.setter
    def crf(self, value):
        self.__crf = value

    # Filterchain

    @property
    def filterchain(self):
        return self.__filterchain

    @filterchain.setter
    def filterchain(self, value):
        if value is not None:
            self.__filterchain = ['-vf', value]
        else:
            self.__filterchain = ''

    # Output file
    
    @property
    def outfile(self):
        return(self.__outfile)

    @outfile.setter
    def outfile(self, value):
        self.__outfile = value


    def get_arguments(self):
        transcode_arguments = [
                "-map", "0:V",
                "-c:v", "libaom-av1" if self.__encoder.name == 'av1' else f'lib{self.__encoder.name}',
                "-crf", self.__crf
        ]

        if self.__encoder.name == 'av1':
            transcode_arguments += ['-b:v', '0', '-cpu-used', self.__av1_compression, *self.__filterchain, self.__outfile]
        else:
            transcode_arguments += ['-preset', self.__preset, *self.__filterchain, self.__outfile]
            
        return super().get_arguments() + transcode_arguments
    

class LibVmafArguments(FfmpegArguments):
    @property
    def second_infile(self):
        return self.__second_infile

    @second_infile.setter
    def second_infile(self, value):
        self.__second_infile = value

    @property
    def filterchain(self):
        return self.__filterchain

    @filterchain.setter
    def filterchain(self, value):
        if value is not None:
            self.__filterchain = f',{value}'
        else:
            self.__filterchain = ''

    @property
    def vmaf_options(self):
        return self.__vmaf_options

    @vmaf_options.setter
    def vmaf_options(self, value):
        self.__vmaf_options = value

    def get_arguments(self):
        return super().get_arguments() + \
            [
                "-r", self._fps, "-i", self.__second_infile, "-an", "-sn",
                "-lavfi", f"[0:v]setpts=PTS-STARTPTS[dist];"
                          f"[1:v]setpts=PTS-STARTPTS{self.__filterchain}[ref];"
                          f'[dist][ref]libvmaf={self.__vmaf_options}',
                "-f", "null", "-"
            ]


class FfmpegProcessFactory:
    def create_process(self, arguments, args):
        __process_base_arguments = [
            "ffmpeg", "-loglevel", "warning", "-stats", "-y"
        ]

        process = FfmpegProcess(
            __process_base_arguments + arguments.get_arguments(), args)

        return process


class FfmpegProcess:
    def __init__(self, arguments, args):
        self.__arguments = arguments

        if args.show_commands:
            from utils import subprocess_printer
            subprocess_printer('The following command will run', self.__arguments)

    def run(self):
        subprocess.run(self.__arguments)
