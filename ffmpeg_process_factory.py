from utils import Logger

from better_ffmpeg_progress import FfmpegProcess

log = Logger("factory")


class EncodingArguments:
    def __init__(self, infile, encoder, parameter, value, outfile):
        self._infile = infile
        self._encoder = encoder
        self._parameter = parameter
        self._value = value
        self._outfile = outfile

        self._base_ffmpeg_arguments = [
            "-i",
            self._infile,
            "-map",
            "0",
            "-c:a",
            "copy",
            "-c:s",
            "copy",
            "-c:v",
        ]

    # libaom-av1 "cpu-used" option.
    def av1_cpu_used(self, value):
        self._av1_cpu_used = value

    def preset(self, value):
        self._preset = value

    def crf(self, value):
        self._crf = value

    def outfile(self, value):
        self._outfile = value

    def get_arguments(self):
        if self._encoder == "libaom-av1":
            encoding_arguments = [
                self._encoder,
                "-b:v",
                "0",
                "-cpu-used",
                self._av1_cpu_used,
                self._outfile,
            ]
        else:
            encoding_arguments = [
                self._encoder,
                f"-{self._parameter}",
                self._value,
                self._outfile,
            ]

        return self._base_ffmpeg_arguments + encoding_arguments


class LibVmafArguments:
    def __init__(
        self,
        original_video,
        video_filters,
        distorted_video,
        vmaf_options,
        transcoded_video_scaling=None,
    ):
        self._original_video = original_video
        self._distorted_video = distorted_video
        self._video_filters = f"{video_filters}," if video_filters else ""
        self._transcoded_video_scaling = (
            f"scale={transcoded_video_scaling.replace("x", ":")}:flags=bicubic,"
            if transcoded_video_scaling
            else ""
        )
        self._vmaf_options = vmaf_options

    def get_arguments(self):
        return [
            "-r",
            "24",
            "-i",
            self._original_video,
            "-r",
            "24",
            "-i",
            self._distorted_video,
            "-map",
            "0:V",
            "-map",
            "1:V",
            "-lavfi",
            f"[0:V]{self._video_filters}setpts=PTS-STARTPTS[reference];"
            f"[1:V]{self._transcoded_video_scaling}setpts=PTS-STARTPTS[distorted];"
            f"[distorted][reference]libvmaf={self._vmaf_options}",
            "-f",
            "null",
            "-",
        ]


class NewFfmpegProcess:
    def __init__(self, log_file):
        self._process_base_arguments = [
            "ffmpeg",
            "-y",
        ]
        self._log_file = log_file

    def run(self, arguments):
        process = FfmpegProcess(
            [*self._process_base_arguments, *arguments],
            print_detected_duration=False,
            ffmpeg_loglevel="debug",
        )
        process.run(progress_bar_description="", log_file=self._log_file)
