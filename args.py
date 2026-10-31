import math
import os
from argparse import ArgumentParser, ArgumentTypeError, RawTextHelpFormatter
from collections.abc import Callable


def number(number_type: type, minimum: float, exclusive: bool = False) -> Callable[[str], float]:
    """Return an argparse type that converts the value to number_type and checks its minimum.

    If exclusive is True, the value must be greater than the minimum rather than at least it.
    """

    def parse(value: str) -> float:
        try:
            converted = number_type(value)
        except ValueError:
            kind = "whole number" if number_type is int else "number"
            raise ArgumentTypeError(f"'{value}' is not a {kind}") from None
        if not math.isfinite(converted):
            raise ArgumentTypeError(f"'{value}' is not a finite number")
        if converted < minimum or (exclusive and converted == minimum):
            comparison = "greater than" if exclusive else "at least"
            raise ArgumentTypeError(f"must be {comparison} {minimum}, not {value}")
        return converted

    return parse


parser = ArgumentParser(formatter_class=RawTextHelpFormatter)

general_args = parser.add_argument_group("General Arguments")
encoder_args = parser.add_argument_group("Encoder Arguments")
overview_mode_args = parser.add_argument_group("Overview Mode Arguments")
vmaf_args = parser.add_argument_group("VMAF Arguments")

general_args.add_argument(
    "--disable-psnr",
    action="store_true",
    help="Disable PSNR calculation.",
)

general_args.add_argument(
    "--disable-ssim",
    action="store_true",
    help="Disable SSIM calculation.",
)

general_args.add_argument(
    "-dp",
    "--decimal-places",
    type=number(int, 0),
    default=3,
    help="The number of decimal places to use for the data in the table",
)

general_args.add_argument(
    "-i",
    "--input-video",
    type=str,
    required=True,
    help="Input video. Must be a relative/absolute path or a glob pattern.\n"
    "If the path contains a space, it must be surrounded in double quotes.",
)

general_args.add_argument(
    "-t",
    "--transcode-length",
    type=number(float, 0, exclusive=True),
    help="Create a lossless version of the original video that is just the first x seconds of the video.\n"
    "This cut version of the original video is what will be transcoded and used as the reference video.\n"
    "You cannot use this option in conjunction with Overview Mode (--interval).",
)

general_args.add_argument(
    "-o",
    "--output-folder",
    type=str,
    help="The folder to save the results in. It can be a relative or absolute path, e.g. results/run1\n"
    "If the path contains a space, it must be surrounded in double quotes.\n"
    "If the input is a glob pattern that matches multiple videos, each video's results are saved in a subfolder of this folder.",
)

general_args.add_argument(
    "-vf",
    "--video-filters",
    type=str,
    help="Apply video filter(s) to the original video before calculating quality metrics. Each filter must be separated by a comma.\nExample: -vf bwdif=mode=0,crop=1920:800:0:140",
)

general_args.add_argument(
    "-sl",
    "--skip-libvmaf",
    action="store_true",
    default=False,
    help="Skip quality metrics calculation if its output file exists, is newer than the transcoded video\n"
    "and was calculated with the same settings (metrics, model, -n and -vf).",
)

general_args.add_argument(
    "-st",
    "--skip-transcoding",
    action="store_true",
    default=False,
    help="Skip transcoding if output file exists.",
)

general_args.add_argument(
    "-d",
    "--debug",
    action="store_true",
    default=False,
    help="Print debug message and command line.",
)

general_args.add_argument(
    "-P",
    "--print",
    action="store_true",
    default=False,
    help="Print metrics table.",
)

general_args.add_argument(
    "--input-options",
    type=str,
    help="Set general FFmpeg input options.\n"
    "Use FFmpeg syntax and wrap it in double quotes. Example:\n"
    '--input-options="-hwaccel d3d11va"',
)

general_args.add_argument(
    "--output-options",
    type=str,
    help="Set general FFmpeg output options.\n"
    "Use FFmpeg syntax and wrap it in double quotes. Examples:\n"
    '--output-options="-c:a aac -b:a 128k"\n'
    '--output-options="-x264-params keyint=123:min-keyint=20"',
)

encoder_args.add_argument(
    "--av1-cpu-used",
    type=int,
    default=5,
    choices=range(1, 9),
    metavar="<1-8>",
    help="Only applicable if the libaom-av1 (AV1) encoder is chosen. Set the quality/encoding speed tradeoff.\n"
    "Lower values mean slower encoding but better quality, and vice-versa",
)

encoder_args.add_argument(
    "-e",
    "--encoder",
    type=str,
    default="libx264",
    help="Specify an ffmpeg video encoder.\nExamples: libx265, h264_amf, libaom-av1",
)

encoder_args.add_argument(
    "-p",
    "--parameter",
    type=str,
    help="The encoder parameter to compare, e.g. preset, crf, quality.\nExample: -p preset",
)

encoder_args.add_argument(
    "-v",
    "--values",
    nargs="+",
    help="The values of the specified encoder parameter to compare. Must be used alongside the -p option. Examples:\n"
    "Compare presets: -p preset -v slow fast\n"
    "Compare CRF values: -p crf -v 22 23\n"
    "Compare h264_amf quality levels: -p quality -v balanced speed",
)

encoder_args.add_argument(
    "-c",
    "--combinations",
    type=str,
    help="Use this mode if you want to compare the quality achieved with a combination of two or more parameters.\n"
    "The list of combinations must be surrounded in quotes, and each combination must be separated by a comma.\n"
    "For example, if you want to compare the combination of preset veryslow and CRF 18, with the combination of preset slower and CRF 16:\n"
    "-c 'preset veryslow crf 18,preset slower crf 16'",
)

overview_mode_args.add_argument(
    "-cl",
    "--clip-length",
    type=int,
    default=1,
    choices=range(1, 61),
    metavar="<1-60>",
    help="When using Overview Mode, a X seconds long segment is taken from the original video every --interval seconds and these segments are concatenated to create the overview video.\n"
    "Specify a value for X (in the range 1-60)",
)

overview_mode_args.add_argument(
    "--interval",
    type=int,
    default=None,
    choices=range(1, 601),
    metavar="<1-600>",
    help="To activate Overview Mode, this argument must be specified.\n"
    "Overview Mode creates a lossless overview video by grabbing a --clip-length long segment every X seconds from the original video.\nSpecify a value for X (in the range 1-600)",
)

vmaf_args.add_argument(
    "-n",
    "--n-subsample",
    type=number(int, 1),
    default=1,
    metavar="<x>",
    help="Set a value for libvmaf's n_subsample option if you only want the VMAF/PSNR to be calculated for every nth frame.\nWithout this argument, VMAF/PSNR scores will be calculated for every frame.",
)

vmaf_args.add_argument(
    "--n-threads",
    type=number(int, 1),
    # os.cpu_count() returns None if the number of CPUs can't be determined.
    default=os.cpu_count() or 1,
    help="Specify the number of threads to use when calculating VMAF",
)

vmaf_args.add_argument("--phone-model", action="store_true", help="Enable VMAF phone model")

vmaf_args.add_argument(
    "--4k-model",
    dest="four_k_model",
    action="store_true",
    help="Use the VMAF 4K model, which predicts the quality of video viewed on a 4K display.\n"
    "It cannot be used with --phone-model.",
)
