from argparse import ArgumentParser, RawTextHelpFormatter
import os

parser = ArgumentParser(formatter_class=RawTextHelpFormatter)

general_args = parser.add_argument_group("General Arguments")
transcoding_args = parser.add_argument_group("Transcoding Arguments")
overview_mode_args = parser.add_argument_group("Overview Mode Arguments")
vmaf_args = parser.add_argument_group("VMAF Arguments")
optional_metrics_args = parser.add_argument_group("Optional Metrics")

# Number of decimal places to use for the data.
general_args.add_argument(
    "-dp",
    "--decimal-places",
    type=int,
    default=2,
    help="The number of decimal places to use for the data in the table",
)

# Input Video
general_args.add_argument(
    "-i",
    "--input-video",
    type=str,
    required=True,
    help="Input video. Can be a relative or absolute path, or a URL.\n"
    "If the path contains a space, it must be surrounded in double quotes.",
)

# Use only the first x seconds of the original video.
general_args.add_argument(
    "-t",
    "--transcode-length",
    type=str,
    help="Create a lossless version of the original video that is just the first x seconds of the video.\n"
    "This cut version of the original video is what will be transcoded and used as the reference video.\n"
    "You cannot use this option in conjunction with the --interval or -cl argument.",
)

# -ntm mode
general_args.add_argument(
    "-ntm",
    "--no-transcoding-mode",
    action="store_true",
    help="Enable 'No Transcoding Mode', which allows you to calculate the VMAF/SSIM/PSNR for a video that you have already transcoded.\n"
    "The original and transcoded video paths must be specified using the -i and -tv arguments, respectively.\n"
    "Example: python main.py -ntm -i original.mp4 -tv transcoded.mp4",
)

general_args.add_argument(
    "-o",
    "--output-folder",
    type=str,
    help="Use this argument if you want a specific name for the output folder. "
    "If you want the name of the output folder to contain a space, the string must be surrounded in double quotes",
)

# Transcoded Video (only applicable when using the -ntm mode).
general_args.add_argument(
    "-tv",
    "--transcoded-video",
    help="Transcoded video. Can be a relative or absolute path, or an URL. "
    "Only applicable when using the -ntm mode.",
)

# FFmpeg Video Filter(s)
general_args.add_argument(
    "-vf",
    "--video-filters",
    type=str,
    help="Add FFmpeg video filter(s). Each filter must be separated by a comma. "
    "Example: -vf bwdif=mode=0,crop=1920:800:0:140",
)

# Set AV1 speed/quality ratio
transcoding_args.add_argument(
    "--av1-cpu-used",
    type=int,
    default=5,
    choices=range(1, 9),
    metavar="<1-8>",
    help="Only applicable if the libaom-av1 (AV1) encoder is chosen. Set the quality/encoding speed tradeoff.\n"
    "Lower values mean slower encoding but better quality, and vice-versa",
)

# Encoder
transcoding_args.add_argument(
    "-e",
    "--encoder",
    type=str,
    default="libx264",
    help="Specify an ffmpeg video encoder.\nExamples: libx265, h264_amf, libaom-av1",
)

# Encoder Parameter
transcoding_args.add_argument(
    "-p",
    "--parameter",
    type=str,
    help="The encoder parameter to compare, e.g. preset, crf, quality.\nExample: -p preset",
)

# Encoder Parameter Values
transcoding_args.add_argument(
    "-v",
    "--values",
    nargs="+",
    help="The values of the specified encoder parameter to compare. Must be used alongside the -p option. Examples:\nCompare presets: -p preset -v slow fast\nCompare CRF values: -p crf -v 22 23\nCompare h264_amf quality levels: -p quality -v balanced speed",
)

# The length of each clip for Overview Mode.
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

# The time interval for Overview Mode.
overview_mode_args.add_argument(
    "--interval",
    type=int,
    default=None,
    choices=range(1, 601),
    metavar="<1-600>",
    help="To activate Overview Mode, this argument must be specified.\n"
    "Overview Mode creates a lossless overview video by grabbing a --clip-length long segment every X seconds from the original video.\nSpecify a value for X (in the range 1-600)",
)

# Set the number of threads to be used when computing VMAF.
vmaf_args.add_argument(
    "--n-threads",
    type=str,
    default=str(os.cpu_count()),
    help="Specify the number of threads to use when calculating VMAF",
)

# Phone Model
vmaf_args.add_argument(
    "--phone-model", action="store_true", help="Enable VMAF phone model"
)

# n_subsample
vmaf_args.add_argument(
    "-s",
    "--subsample",
    type=str,
    default="1",
    metavar="<x>",
    help="Set a value for libvmaf's n_subsample option if you only want the VMAF/SSIM/PSNR to be calculated for every nth frame.\nWithout this argument, VMAF/SSIM/PSNR scores will be calculated for every frame.",
)

# PSNR
optional_metrics_args.add_argument(
    "-psnr",
    "--calculate-psnr",
    action="store_true",
    help="Enable PSNR calculation in addition to VMAF",
)

# SSIM
optional_metrics_args.add_argument(
    "-ssim",
    "--calculate-ssim",
    action="store_true",
    help="Enable SSIM calculation in addition to VMAF",
)

# MS-SSIM
optional_metrics_args.add_argument(
    "-msssim",
    "--calculate-msssim",
    action="store_true",
    help="Enable MS-SSIM calculation in addition to VMAF",
)
