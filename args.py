from argparse import ArgumentParser, RawTextHelpFormatter
import os

parser = ArgumentParser(formatter_class=RawTextHelpFormatter)

general_args = parser.add_argument_group("General Arguments")
encoder_args = parser.add_argument_group("Encoder Arguments")
overview_mode_args = parser.add_argument_group("Overview Mode Arguments")
vmaf_args = parser.add_argument_group("VMAF Arguments")

# Disable PSNR calculation.
general_args.add_argument(
    "--disable-psnr",
    action="store_true",
    help="Disable PSNR calculation.",
)

# Disable SSIM calculation.
general_args.add_argument(
    "--disable-ssim",
    action="store_true",
    help="Disable SSIM calculation.",
)

# Number of decimal places to use for the data.
general_args.add_argument(
    "-dp",
    "--decimal-places",
    type=int,
    default=3,
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
    help="Enable 'No Transcoding Mode', which allows you to calculate the VMAF/PSNR for a video that you have already transcoded.\n"
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
    help="Apply video filter(s) to the original video before calculating quality metrics. Each filter must be separated by a comma.\nExample: -vf bwdif=mode=0,crop=1920:800:0:140",
)

# Set AV1 speed/quality ratio
encoder_args.add_argument(
    "--av1-cpu-used",
    type=int,
    default=5,
    choices=range(1, 9),
    metavar="<1-8>",
    help="Only applicable if the libaom-av1 (AV1) encoder is chosen. Set the quality/encoding speed tradeoff.\n"
    "Lower values mean slower encoding but better quality, and vice-versa",
)

# Encoder
encoder_args.add_argument(
    "-e",
    "--encoder",
    type=str,
    default="libx264",
    help="Specify an ffmpeg video encoder.\nExamples: libx265, h264_amf, libaom-av1",
)

# Encoder Options
encoder_args.add_argument(
    "-eo",
    "--encoder-options",
    type=str,
    help="Set general encoder options to use for all transcodes.\n"
    "Use FFmpeg syntax. Must be surronded in quotes. Example:\n"
    "--encoder-options='-crf 18 -x264-params keyint=123:min-keyint=20'",
)

# Encoder Parameter
encoder_args.add_argument(
    "-p",
    "--parameter",
    type=str,
    help="The encoder parameter to compare, e.g. preset, crf, quality.\nExample: -p preset",
)

# Encoder Parameter Values
encoder_args.add_argument(
    "-v",
    "--values",
    nargs="+",
    help="The values of the specified encoder parameter to compare. Must be used alongside the -p option. Examples:\n"
    "Compare presets: -p preset -v slow fast\n"
    "Compare CRF values: -p crf -v 22 23\n"
    "Compare h264_amf quality levels: -p quality -v balanced speed",
)

# Combination Mode
encoder_args.add_argument(
    "-c",
    "--combinations",
    type=str,
    help="Use this mode if you want to compare the quality achieved with a combination of two or more parameters.\n"
    "The list of combinations must be surrounded in quotes, and each combination must be separated by a comma.\n"
    "For example, if you want to compare the combination of preset veryslow and CRF 18, with the combination of preset slower and CRF 16:\n"
    "-c 'preset veryslow crf 18,preset slower crf 16'",
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

# libvmaf n_subsample
vmaf_args.add_argument(
    "-n",
    "--n-subsample",
    type=str,
    default="1",
    metavar="<x>",
    help="Set a value for libvmaf's n_subsample option if you only want the VMAF/PSNR to be calculated for every nth frame.\nWithout this argument, VMAF/PSNR scores will be calculated for every frame.",
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

vmaf_args.add_argument(
    "-s",
    "--scale",
    type=str,
    help="Scale the transcoded video to match the resolution of the original video.\n"
    "To ensure accurate VMAF scores, this is necessary if the transcoded video has a different resolution.\n"
    "For example, if the original video is 1920x1980 and the transcoded video is 1280x720, you should specify:\n"
    "-s 1920x1080",
)
