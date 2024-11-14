from utils import Logger

from better_ffmpeg_progress import FfmpegProcess

log = Logger("factory")


class EncodingArguments:
    def __init__(
        self,
        original_video_path,
        encoder,
        encoder_options,
        parameter,
        value,
        output_path,
        combination,
    ):
        self._encoder = encoder
        self._combination = combination
        self._parameter = parameter
        self._value = value
        self._output_path = output_path

        self._base_ffmpeg_arguments = [
            "-i",
            original_video_path,
            "-map",
            "0",
            "-c:a",
            "copy",
            "-c:s",
            "copy",
            "-c:v",
            self._encoder,
        ]

        if encoder_options:
            self._base_ffmpeg_arguments += encoder_options.split(" ")

    # libaom-av1 "cpu-used" option.
    def av1_cpu_used(self, value):
        self._av1_cpu_used = value

    def get_arguments(self):
        if self._encoder == "libaom-av1":
            encoding_arguments = [
                "-b:v",
                "0",
                "-cpu-used",
                self._av1_cpu_used,
                self._output_path,
            ]
        elif self._combination:
            self._combination.append(self._output_path)
            encoding_arguments = self._combination
        else:
            encoding_arguments = [
                f"-{self._parameter}",
                self._value,
                self._output_path,
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
