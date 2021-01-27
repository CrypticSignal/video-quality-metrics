import os
from argparse import ArgumentParser, RawTextHelpFormatter

parser = ArgumentParser(formatter_class=RawTextHelpFormatter)

# Set AV1 speed/quality ratio
parser.add_argument(
    '--av1-cpu-used',
    type=int,
    default=1,
    choices=range(1, 9),
    help='Only applicable if choosing the AV1 encoder. Set speed/quality ratio. Value Range: 1-8\n'
         'Lower values mean slower encoding but better quality, and vice-versa.'
)

# The length of each clip for Overview Mode.
parser.add_argument(
    '-cl', '--clip-length',
    type=int,
    default=1, 
    choices=range(1, 60), 
    metavar='<an integer between 1 and 60>',
    help='Defines the length of the clips (default: 1). Only applies when used with -i > 0.\nExample: -cl 2'
)

# CRF value(s).
parser.add_argument(
    '-crf', '--crf-value', 
    type=int, 
    default=23,
    choices=range(0, 52),
    nargs='+',
    metavar='CRF_VALUE(s)',
    help='Specify the CRF value(s) to use.', 
)

# Number of decimal places to use for the data.
parser.add_argument(
    '-dp', '--decimal-places', 
    type=int,
    default=2, 
    help='The number of decimal places to use for the data in the table (default: 2).\nExample: -dp 3'
)

# Video Encoder
parser.add_argument(
    '-e', '--video-encoder', 
    type=str, 
    default='x264', 
    choices=['x264', 'x265', 'av1'],
    help='Specify the encoder to use (default: x264).'
)

# FFmpeg Video Filter(s)
parser.add_argument(
    '-fc', '--filterchain',
    type=str,
    help='Add FFmpeg video filter(s). Each filter must be separated by a comma.\n'
         'Example: -fc bwdif=mode=0,crop=1920:800:0:140'
)

# The time interval for Overview Mode.
parser.add_argument(
    '-i', '--interval', 
    type=int, 
    default=0,
    choices=range(1, 600),
    metavar='<an integer between 1 and 600>',
    help='Create a lossless overview video by grabbing a <cliplength> seconds long segment '
         'every <interval> seconds from the original video and use this overview video '
         'as the "original" video that the transcodes are compared with.\nExample: -i 30'
)

# n_subsample
parser.add_argument(
    '-n', '--subsample',
    type=str, 
    default='1',
    metavar='x',
    help='Set a value for libvmaf\'s n_subsample option if you only want the VMAF/SSSIM to be calculated for every nth '
         'frame.\nWithout this argument, VMAF/SSIM scores will be calculated for every frame.\nExample: -n 24'
)

# -ntm mode
parser.add_argument(
    '-ntm', '--no-transcoding-mode', 
    action='store_true',
    help='Enable "no transcoding mode", which allows you to '
         'calculate the VMAF/SSIM/PSNR for a video that you have already transcoded.\n'
         'The original and transcoded video paths must be specified using the -ovp and -tvp arguments, respectively.\n'
         'Example: python main.py -ntm -ovp original.mp4 -tvp transcoded.mp4 -ssim'
)

# Original Video Path
parser.add_argument(
    '-ovp', '--original-video-path', 
    type=str, 
    required=True,
    help='Enter the path of the original '
         'video. A relative or absolute path can be specified. '
         'If the path contains a space, it must be surrounded in double quotes.\n'
         'Example: -ovp "C:/Users/H/Desktop/file 1.mp4"'
)

# Phone Model
parser.add_argument(
    '-pm', '--phone-model',
    action='store_true', 
    help='Enable VMAF phone model.'
)

# Preset(s).
parser.add_argument(
    '-p', '--preset',
    type=str, 
    default='medium',
    choices=[
        'veryslow', 'slower', 'slow', 'medium', 'fast', 'faster', 'veryfast', 'superfast', 'ultrafast'
    ],
    nargs='+', 
    metavar='PRESET(s)',
    help='Specify the preset(s) to use.'
)

# PSNR
parser.add_argument(
    '-psnr', '--calculate-psnr', 
    action='store_true', 
    help='Enable PSNR calculation in addition to VMAF (default: disabled).'
)

# SSIM
parser.add_argument(
    '-ssim', '--calculate-ssim', 
    action='store_true', 
    help='Enable SSIM calculation in addition to VMAF (default: disabled).'
)

# Use only the first x seconds of the original video.
parser.add_argument(
    '-t', '--encode-length',
    type=str,
    metavar='x',
    help='Create a lossless version of the original video that is just the first x seconds of the video. '
         'This cut version of the original video is what will be transcoded and used as the reference video. '
         'You cannot use this option in conjunction with the -i or -cl arguments.\nExample: -t 60'
)

# Set the number of threads to be used when computing VMAF.
parser.add_argument(
    '--threads',
    type=str,
    default=str(os.cpu_count()),
    metavar='x',
    help='Set the number of threads to be used when computing VMAF.\n'
         'The default is set to what Python\'s os.cpu_count() method returns. '
         'For example, on a dual-core Intel CPU with hyperthreading, the default will be set to 4.\n'
         'Example: --threads 2'
)

# Transcoded video path (only applicable when using the -ntm mode).
parser.add_argument(
    '-tvp', '--transcoded-video-path',
    help='The path of the transcoded video (only applicable when using the -ntm mode).'
)