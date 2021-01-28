import subprocess


class BaseFfmpegArguments:
    _fps = None

    @property
    def infile(self):
        return self._infile

    @infile.setter
    def infile(self, value):
        self._infile = value

    @property
    def fps(self):
        return self._fps

    @fps.setter
    def fps(self, value):
        self._fps = value

    def get_arguments(self):
        base_ffmpeg_arguments = ["-i", self._infile]
        if self._fps is not None:
            base_ffmpeg_arguments = ["-r", self._fps, "-i", self._infile]
        return base_ffmpeg_arguments


class EncodingArguments(BaseFfmpegArguments):
    def __init__(self, encoder):
        self._encoder = encoder

    # libaom-av1 "cpu-used" option.

    @property
    def av1_cpu_used(self):
        return self._av1_cpu_used

    @av1_cpu_used.setter
    def av1_cpu_used(self, value):
        self._av1_cpu_used = value

    # Preset

    @property
    def preset(self):
        return self._preset

    @preset.setter
    def preset(self, value):
        self._preset = value

    # CRF

    @property
    def crf(self):
        return self._crf

    @crf.setter
    def crf(self, value):
        self._crf = value

    # Filterchain

    @property
    def filterchain(self):
        return self._filterchain

    @filterchain.setter
    def filterchain(self, value):
        if value is not None:
            self._filterchain = ['-vf', value]
        else:
            self._filterchain = ''

    # Output file
    
    @property
    def outfile(self):
        return(self._outfile)

    @outfile.setter
    def outfile(self, value):
        self._outfile = value


    def get_arguments(self):
        transcode_arguments = [
                "-map", "0:V",
                "-c:v", "libaom-av1" if self._encoder == 'av1' else f'lib{self._encoder}',
                "-crf", self._crf
        ]

        if self._encoder == 'av1':
            transcode_arguments += ['-b:v', '0', '-cpu-used', self._av1_cpu_used, *self._filterchain, self._outfile]
        else:
            transcode_arguments += ['-preset', self._preset, *self._filterchain, self._outfile]
            
        return super().get_arguments() + transcode_arguments
    

class LibVmafArguments(BaseFfmpegArguments):
    @property
    def second_infile(self):
        return self._second_infile

    @second_infile.setter
    def second_infile(self, value):
        self._second_infile = value

    @property
    def filterchain(self):
        return self._filterchain

    @filterchain.setter
    def filterchain(self, value):
        if value is not None:
            self._filterchain = f',{value}'
        else:
            self._filterchain = ''

    @property
    def vmaf_options(self):
        return self._vmaf_options

    @vmaf_options.setter
    def vmaf_options(self, value):
        self._vmaf_options = value

    def get_arguments(self):
        return super().get_arguments() + \
            [
                "-r", self._fps, "-i", self._second_infile,
                "-map", "0:V", "-map", "1:V",
                "-lavfi", f'[0:v]setpts=PTS-STARTPTS[dist];'
                          f'[1:v]setpts=PTS-STARTPTS{self._filterchain}[ref];'
                          f'[dist][ref]libvmaf={self._vmaf_options}',
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
        self._arguments = arguments

        if args.show_commands:
            from utils import subprocess_printer
            subprocess_printer('The following command will run', self._arguments)

    def run(self):
        subprocess.run(self._arguments)
