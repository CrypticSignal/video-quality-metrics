from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import os

parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)

encoding_args = parser.add_argument_group('Encoding Arguments')
vmaf_args = parser.add_argument_group('VMAF Arguments')
overview_mode_args = parser.add_argument_group('Overview Mode Arguments')
general_args = parser.add_argument_group('General Arguments')
optional_metrics_args = parser.add_argument_group('Optional Metrics')

# Set AV1 speed/quality ratio
encoding_args.add_argument(
    '--av1-cpu-used',
    type=int,
    default=5,
    choices=range(1, 9),
    metavar='<1-8>',
    help='Only applicable if the libaom-av1 (AV1) encoder is chosen. Set the quality/encoding speed tradeoff. '
         'Lower values mean slower encoding but better quality, and vice-versa'
)

# The length of each clip for Overview Mode.
overview_mode_args.add_argument(
    '-cl', '--clip-length',
    type=int,
    default=1, 
    choices=range(1, 61),
    metavar='<1-60>',
    help='When using Overview Mode, a X seconds long segment is taken from the original video every --interval seconds '
         'and these segments are concatenated to create the overview video. '
         'Specify a value for X (in the range 1-60)'
)

# CRF value(s).
encoding_args.add_argument(
    '-crf',
    type=int,
    choices=range(0, 52),
    nargs='+',
    metavar='<0-51>',
    help='Specify the CRF value(s) to use', 
)

# Number of decimal places to use for the data.
general_args.add_argument(
    '-dp', '--decimal-places', 
    type=int,
    default=2, 
    help='The number of decimal places to use for the data in the table'
)

# Video Encoder
encoding_args.add_argument(
    '-e', '--video-encoder', 
    type=str, 
    default='x264', 
    choices=['x264', 'x265', 'libaom-av1'],
    help='Specify whether to use the x264 (H.264), x265 (H.265) or libaom-av1 (AV1) encoder'
)

# The time interval for Overview Mode.
overview_mode_args.add_argument(
    '-i', '--interval', 
    type=int, 
    default=None,
    choices=range(1, 601),
    metavar='<1-600>',
    help='To activate Overview Mode, this argument must be specified. '
         'Overview Mode creates a lossless overview video by grabbing a --clip-length long segment every X seconds '
         'from the original video. Specify a value for X (in the range 1-600)'
)

# n_subsample
vmaf_args.add_argument(
    '-subsample',
    type=str, 
    default='1',
    #metavar='x',
    help='Set a value for libvmaf\'s n_subsample option if you only want the VMAF/SSIM/PSNR to be calculated for every nth '
         'frame. Without this argument, VMAF/SSIM/PSNR scores will be calculated for every frame'
)

# Set the number of threads to be used when computing VMAF.
vmaf_args.add_argument(
    '--n-threads',
    type=str,
    default=str(os.cpu_count()),
    help='Specify the number of threads to use when calculating VMAF'
)

# -ntm mode
general_args.add_argument(
    '-ntm', '--no-transcoding-mode', 
    action='store_true',
    help='Enable "no transcoding mode", which allows you to '
         'calculate the VMAF/SSIM/PSNR for a video that you have already transcoded. '
         'The original and transcoded video paths must be specified using the -ovp and -tvp arguments, respectively. '
         'Example: python main.py -ntm -ovp original.mp4 -tvp transcoded.mp4'
)

general_args.add_argument(
    '-o', '--output-folder',
    type=str,
    help='Use this argument if you want a specific name for the output folder. '
         'If you want the name of the output folder to contain a space, the string must be surrounded in double quotes'
)

# Original Video Path
general_args.add_argument(
    '-ovp', '--original-video-path', 
    type=str, 
    required=True,
    help='Enter the path of the original '
         'video. A relative or absolute path can be specified. '
         'If the path contains a space, it must be surrounded in double quotes'
)

# Preset(s).
encoding_args.add_argument(
    '-p', '--preset',
    type=str, 
    default='medium',
    choices=[
        'veryslow', 'slower', 'slow', 'medium', 'fast', 'faster', 'veryfast', 'superfast', 'ultrafast'
    ],
    nargs='+', 
    metavar='<preset/s>',
    help='Specify the preset(s) to use'
)

# Phone Model
vmaf_args.add_argument(
    '--phone-model',
    action='store_true', 
    help='Enable VMAF phone model'
)

# PSNR
optional_metrics_args.add_argument(
    '-psnr', '--calculate-psnr', 
    action='store_true', 
    help='Enable PSNR calculation in addition to VMAF'
)

# Show the commands being run.
general_args.add_argument(
    '-sc', '--show-commands',
    action='store_true',
    help="Show the FFmpeg commands that are being run."
)

# SSIM
optional_metrics_args.add_argument(
    '-ssim', '--calculate-ssim', 
    action='store_true',
    help='Enable SSIM calculation in addition to VMAF'
)

# Use only the first x seconds of the original video.
general_args.add_argument(
    '-t', '--encode-length',
    type=str,
    metavar='SECONDS',
    help='Create a lossless version of the original video that is just the first x seconds of the video. '
         'This cut version of the original video is what will be transcoded and used as the reference video. '
         'You cannot use this option in conjunction with the -i or -cl arguments'
)

# Transcoded video path (only applicable when using the -ntm mode).
general_args.add_argument(
    '-tvp', '--transcoded-video-path',
    help='The path of the transcoded video (only applicable when using the -ntm mode)'
)

# FFmpeg Video Filter(s)
general_args.add_argument(
    '-vf', '--video-filters',
    type=str,
    help='Add FFmpeg video filter(s). Each filter must be separated by a comma. '
         'Example: -vf bwdif=mode=0,crop=1920:800:0:140'
)