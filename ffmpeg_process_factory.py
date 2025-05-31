from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Union
from utils import Logger

log = Logger("factory")


@dataclass
class EncoderOptions:
    encoder: str
    options: Optional[str] = None
    av1_cpu_used: Optional[str] = None


@dataclass
class EncodingArguments:
    original_video_path: Union[str, Path]
    encoder_options: EncoderOptions
    output_path: Union[str, Path]
    parameter: Optional[str] = None
    value: Optional[str] = None
    combination: Optional[List[str]] = None

    def __post_init__(self) -> None:
        self.original_video_path = Path(self.original_video_path)
        self.output_path = Path(self.output_path)

        self._base_ffmpeg_arguments = [
            "ffmpeg",
            "-y",
            "-i",
            str(self.original_video_path),
            "-map",
            "0",
            "-c:a",
            "copy",
            "-c:s",
            "copy",
            "-c:v",
            self.encoder_options.encoder,
        ]

        if self.encoder_options.options is not None:
            self._base_ffmpeg_arguments.extend(self.encoder_options.options.split())

    def get_arguments(self) -> List[str]:
        if self.output_path is None:
            raise ValueError("Output path must be specified")

        if self.encoder_options.encoder == "libaom-av1":
            if self.encoder_options.av1_cpu_used is None:
                raise ValueError(
                    "av1_cpu_used must be specified for libaom-av1 encoder"
                )
            encoding_arguments = [
                "-b:v",
                "0",
                "-cpu-used",
                self.encoder_options.av1_cpu_used,
                str(self.output_path),
            ]
        elif self.combination:
            self.combination.append(str(self.output_path))
            encoding_arguments = self.combination
        elif self.parameter and self.value:
            encoding_arguments = [
                f"-{self.parameter}",
                self.value,
                str(self.output_path),
            ]
        else:
            raise ValueError("Invalid encoding configuration")

        return self._base_ffmpeg_arguments + encoding_arguments


@dataclass
class LibVmafArguments:
    original_video: Union[str, Path]
    distorted_video: Union[str, Path]
    vmaf_options: str
    video_filters: Optional[str] = None
    transcoded_video_scaling: Optional[str] = None

    def __post_init__(self) -> None:
        self.original_video = Path(self.original_video)
        self.distorted_video = Path(self.distorted_video)
        self._video_filters = (
            f"{self.video_filters}," if self.video_filters is not None else ""
        )

    def _get_scaling_filter(self) -> str:
        if self.transcoded_video_scaling is None:
            return ""
        return f"scale={self.transcoded_video_scaling.replace('x', ':')}:flags=bicubic,"

    def get_arguments(self) -> List[str]:
        scaling_filter = self._get_scaling_filter()

        filtergraph = (
            f"[0:V]{self._video_filters}setpts=PTS-STARTPTS[reference];"
            f"[1:V]{scaling_filter}setpts=PTS-STARTPTS[distorted];"
            f"[distorted][reference]libvmaf={self.vmaf_options}"
        )

        return [
            "ffmpeg",
            "-r",
            "24",
            "-i",
            str(self.original_video),
            "-r",
            "24",
            "-i",
            str(self.distorted_video),
            "-map",
            "0:V",
            "-map",
            "1:V",
            "-lavfi",
            filtergraph,
            "-f",
            "null",
            "-",
        ]
