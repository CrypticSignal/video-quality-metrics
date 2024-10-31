from utils import Logger

from better_ffmpeg_progress import FfmpegProcess

log = Logger("factory")


class FFmpegCommand:
    def __init__(
        self, infile, encoder, parameter, value, output_file, vmaf_options, fps
    ):
        self._infile = infile
        self._encoder = encoder
        self._parameter = parameter
        self._value = value
        self._output_file = output_file
        self._vmaf_options = vmaf_options
        self._fps = fps

        self._base_ffmpeg_arguments = [
            "-i",
            self._infile,
            "-map",
            "0:v",
        ]

    # libaom-av1 "cpu-used" option.
    def av1_cpu_used(self, value):
        self._av1_cpu_used = value

    def preset(self, value):
        self._preset = value

    def crf(self, value):
        self._crf = value

    def video_filters(self, filters):
        if filters is not None:
            self._video_filters = ["-vf", filters]
        else:
            self._video_filters = ""

    def outfile(self, value):
        self._outfile = value

    def get_arguments(self):
        base_encoding_arguments = [
            "-c:v",
            self._encoder,
        ]

        if self._encoder == "libaom-av1":
            encoding_arguments = base_encoding_arguments + [
                "-b:v",
                "0",
                "-cpu-used",
                self._av1_cpu_used,
                *self._video_filters,
                # "-flush_packets",
                # "1",
            ]
        else:
            encoding_arguments = base_encoding_arguments + [
                f"-{self._parameter}",
                self._value,
                *self._video_filters,
                # "-flush_packets",
                # "1",
            ]

        libvmaf = [
            "ffmpeg",
            "-r",
            self._fps,
            "-i",
            "pipe:0",
            "-r",
            self._fps,
            "-i",
            self._infile,
            "-lavfi",
            f"[0:v]setpts=PTS-STARTPTS[dist];[1:v]setpts=PTS-STARTPTS{self._video_filters}[ref];[dist][ref]libvmaf={self._vmaf_options.strip()}",
            # "-flush_packets",
            # "1",
            "-f",
            "null",
            "-",
        ]

        return (
            self._base_ffmpeg_arguments
            + encoding_arguments
            + [
                "-f",
                "rawvideo",
                # "-pix_fmt",
                # "yuv420p",
                "-",  # Output to pipe
                "-f",
                "matroska",
                self._output_file,  # Output to file
                "|",
            ]
            + libvmaf
        )


class EncodingArguments:
    def __init__(self, infile, encoder, parameter, value, outfile):
        self._infile = infile
        self._encoder = encoder
        self._parameter = parameter
        self._value = value
        self._outfile = outfile

        self._base_ffmpeg_arguments = ["-i", self._infile]

    # libaom-av1 "cpu-used" option.
    def av1_cpu_used(self, value):
        self._av1_cpu_used = value

    def preset(self, value):
        self._preset = value

    def crf(self, value):
        self._crf = value

    def video_filters(self, filters):
        if filters is not None:
            self._video_filters = ["-vf", filters]
        else:
            self._video_filters = ""

    def outfile(self, value):
        self._outfile = value

    def get_arguments(self):
        base_encoding_arguments = [
            "-c:v",
            self._encoder,
            "-c:a",
            "copy",
            "-c:s",
            "copy",
        ]

        if self._encoder == "libaom-av1":
            encoding_arguments = base_encoding_arguments + [
                "-b:v",
                "0",
                "-cpu-used",
                self._av1_cpu_used,
                *self._video_filters,
                self._outfile,
            ]
        else:
            encoding_arguments = base_encoding_arguments + [
                f"-{self._parameter}",
                self._value,
                *self._video_filters,
                self._outfile,
            ]

        return self._base_ffmpeg_arguments + encoding_arguments


class NewFfmpegProcess:
    def __init__(self, arguments):
        self._arguments = arguments

        self._process_base_arguments = [
            # "stdbuf",
            # "-oL",
            # "-eL",
            "ffmpeg",
            "-progress",
            "-",
            "-nostats",
            "-loglevel",
            "warning",
            "-y",
        ]

    def run(
        self,
    ):
        process = FfmpegProcess(
            [*self._process_base_arguments, *self._arguments],
            print_detected_duration=False,
        )

        process.run(progress_bar_description="")
