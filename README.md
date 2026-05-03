# Video Quality Metrics (VQM)
VQM will compare the VMAF, SSIM and PSNR achieved with different values of the specified encoder parameter.

# Quick Links
- [What does VQM produce?](#what-does-vqm-produce)
- [Requirements](#requirements)
- [Usage](#usage)
- [Overview Mode](#overview-mode)
- [Combination Mode](#combination-mode)
- [Available Arguments](#available-arguments)
- [FFmpeg Builds](#ffmpeg-builds)
- [About the model files](#about-the-model-files)

# What does VQM produce?
VQM produces a table to show the metrics, and graphs that show the per-frame VMAF, SSIM and PSNR.

The table is written to a file named `metrics_table.txt` and it contains the following for each value of the specified encoder parameter:
- Parameter value
- Time taken to transcode the video (seconds)
- Filesize (MB)
- Bitrate (Mbps)
- [Video Multimethod Assessment Fusion (VMAF)](https://github.com/Netflix/vmaf)
- Structural Similarity Index (SSIM)
- Peak Signal-to-Noise-Ratio (PSNR)

Here's an example:
```
VMAF/PSNR/SSIM values are in the format: Min | Standard Deviation | Mean
+----------------+---------+--------------------+-----------+----------------------------------------+----------+-------------------------+-------------------------+-----------------------+
|     preset     | Encoder | Transcode Time (s) |    Size   |  Video Bitrate | Confidence | Method   | Duration |           VMAF          |           PSNR          |          SSIM         |
+----------------+---------+--------------------+-----------+----------------------------------------+----------+-------------------------+-------------------------+-----------------------+
| Original Video |   h264  |         -          | 12.917 MB | 1.526 Mbps | High | Video Packet Sizes | 60.070 s |            -            |            -            |           -           |
|    veryslow    | libx264 |       23.073       | 11.016 MB | 1.358 Mbps | High | Video Packet Sizes | 60.073 s | 89.514 | 2.488 | 97.371 | 40.715 | 4.063 | 47.691 | 0.992 | 0.001 | 0.997 |
|     slower     | libx264 |       15.238       | 11.877 MB | 1.473 Mbps | High | Video Packet Sizes | 60.073 s | 88.464 | 2.463 | 97.401 | 40.644 | 4.041 | 47.844 | 0.993 | 0.001 | 0.998 |
|      slow      | libx264 |       6.144        | 11.755 MB | 1.456 Mbps | High | Video Packet Sizes | 60.073 s | 89.348 | 2.506 | 97.342 | 40.871 | 4.041 | 47.800 | 0.993 | 0.001 | 0.998 |
|     medium     | libx264 |       4.360        | 12.163 MB | 1.511 Mbps | High | Video Packet Sizes | 60.073 s | 89.529 | 2.414 | 97.490 | 40.927 | 4.023 | 47.958 | 0.993 | 0.001 | 0.998 |
|      fast      | libx264 |       3.904        | 12.632 MB | 1.573 Mbps | High | Video Packet Sizes | 60.073 s | 89.882 | 2.465 | 97.460 | 40.954 | 3.983 | 48.016 | 0.994 | 0.001 | 0.998 |
|     faster     | libx264 |       2.999        | 12.487 MB | 1.554 Mbps | High | Video Packet Sizes | 60.073 s | 88.592 | 2.603 | 97.257 | 40.877 | 3.989 | 48.006 | 0.994 | 0.001 | 0.998 |
|    veryfast    | libx264 |       2.303        | 11.107 MB | 1.370 Mbps | High | Video Packet Sizes | 60.073 s | 83.313 | 3.698 | 95.400 | 39.779 | 4.071 | 46.612 | 0.992 | 0.002 | 0.997 |
|   superfast    | libx264 |       1.705        | 15.967 MB | 2.017 Mbps | High | Video Packet Sizes | 60.073 s | 86.385 | 2.687 | 96.859 | 40.207 | 4.335 | 47.502 | 0.992 | 0.001 | 0.997 |
|   ultrafast    | libx264 |       1.185        | 23.969 MB | 3.083 Mbps | High | Video Packet Sizes | 60.073 s | 88.579 | 2.067 | 97.982 | 40.093 | 4.811 | 46.288 | 0.989 | 0.002 | 0.996 |
+----------------+---------+--------------------+-----------+----------------------------------------+----------+-------------------------+-------------------------+-----------------------+
Original File: ForBiggerFun.mp4
FFmpeg output options: None
libvmaf n_subsample: 1
```
_Command used: `python main.py -i ForBiggerFun.mp4 -e libx264 -p preset -v veryslow slower slow medium fast faster veryfast superfast ultrafast`_

In addition to the table, two types of graphs are created:
- A graph (type 1) for each encoder parameter value, showing the per-frame VMAF, SSIM and PSNR.
- A graph (type 2) where the average VMAF is plotted against the value of the encoder parameter.

Here's an example of graph type 1:

![Per-frame VMAF](https://github.com/CrypticSignal/video-quality-metrics/blob/master/example_graphs/Per-frame%20VMAF.png?raw=true)

_This particular graph shows the per-frame VMAF score. An example of the per-frame SSIM graph and per-frame PSNR graph can be found in the [example_graphs folder](https://github.com/CrypticSignal/video-quality-metrics/tree/master/example_graphs)._

Here's an example of graph type 2 if you opt to compare CRF values:

![CRF vs VMAF graph](https://github.com/CrypticSignal/video-quality-metrics/blob/master/example_graphs/CRF%20vs%20VMAF.png?raw=true)

# Usage
You must specify an encoder (using the `-e` argument), an FFmpeg encoder parameter (using the `-p` argument, e.g. `-p preset`, `-p crf` or `-p quality`) and the values you want to compare (using the `-v` argument).

If you would like to test VQM without using your own video(s), you can use `ForBiggerFun.mp4`.

Examples: 
```
python main.py -i ForBiggerFun.mp4 -e libx264 -p preset -v veryfast superfast ultrafast
```
```
python main.py -i ForBiggerFun.mp4 -e libx264 -p crf -v 22 23 24
```
```
python main.py -i ForBiggerFun.mp4 -e h264_amf -p quality -v balanced speed quality
```

# Overview Mode
Overview Mode can be activated by specifying the `--interval` and `--clip-length` arguments. The benefit of this mode is especially apparent with long videos, such as movies. What this mode does is create an overview video by grabbing a `<clip length>` seconds long segment every `<interval>` seconds from the original video. As the overview video can be much shorter than the original, the process of transcoding and calculating the quality metrics is quicker.

Example: `python main.py -i ForBiggerFun.mp4 -p crf -v 17 18 19 --interval 5 --clip-length 2`

In the example above, an overview video is created by concatenating 2-second-long* clips (`--clip-length 2`) every 5s* (`--interval 5`) from the original video. In this example, a one-minute-long video is turned into an overview video that is 20 seconds long. Transcoding and calculating the quality metrics of a video that is 20 seconds long is quicker than doing so with a one-minute-long video.

_Sections marked with an asterisk will not be exact as FFmpeg will use the closest I-frames._

_An alternative method of reducing the execution time of this program is by only using the first x seconds of the original video (you can do this with the `-t` argument), but **Overview Mode** provides a better representation of the whole video._

# Combination Mode
Instead of comparing the quality achieved with various values of one encoder parameter, Combination Mode allows you to compare the quality achieved with a combination of two or more parameters.

To activate Combination Mode, specify the `-c` or `--combinations` argument, followed by a list of combinations you wish to compare. The list of combinations must be surrounded in quotes, and each combination must be separated by a comma.

For example, if you want to compare the quality achieved with:
- The combination of preset `veryslow` and a CRF value of `18`
- The combination of preset `slower` and CRF value of `16`

You would run something like:
```
python main.py -i "ForBiggerFun.mp4" -e libx265 -c "preset slow crf 24,preset medium crf 23"
```
The table produced will look something like this:
```
VMAF/PSNR/SSIM values are in the format: Min | Standard Deviation | Mean
+------------------------+---------+--------------------+-----------+----------------------------------------+----------+-------------------------+-------------------------+-----------------------+
|      Combination       | Encoder | Transcode Time (s) |    Size   |  Video Bitrate | Confidence | Method   | Duration |           VMAF          |           PSNR          |          SSIM         |
+------------------------+---------+--------------------+-----------+----------------------------------------+----------+-------------------------+-------------------------+-----------------------+
|     Original Video     |   h264  |         -          | 12.917 MB | 1.526 Mbps | High | Video Packet Sizes | 60.070 s |            -            |            -            |           -           |
|  -preset slow -crf 24  | libx265 |       36.423       |  9.114 MB | 1.104 Mbps | High | Video Packet Sizes | 60.073 s | 90.631 | 2.206 | 97.704 | 41.371 | 4.015 | 47.687 | 0.991 | 0.001 | 0.997 |
| -preset medium -crf 23 | libx265 |       14.131       |  9.364 MB | 1.138 Mbps | High | Video Packet Sizes | 60.073 s | 89.330 | 2.635 | 97.069 | 41.001 | 4.017 | 47.380 | 0.991 | 0.002 | 0.997 |
+------------------------+---------+--------------------+-----------+----------------------------------------+----------+-------------------------+-------------------------+-----------------------+
```
A graph will also be produced, comparing each combination:

![Combination vs VMAF](https://github.com/CrypticSignal/video-quality-metrics/blob/master/example_graphs/Combination%20vs%20VMAF.png?raw=true)

- Combination Mode can be used alongside Overview Mode.
- You need to decide whether you want to use the regular mode, which compares the quality metrics achieved with various values of **one** particular encoder parameter (using the `-p` and `-v` arguments), OR Combination Mode. You cannot do both.

# Available Arguments
You can see a list of the available arguments with `python main.py -h`:

```
usage: main.py [-h] [--disable-psnr] [--disable-ssim] [-dp DECIMAL_PLACES] -i INPUT_VIDEO [-t TRANSCODE_LENGTH] [-o OUTPUT_FOLDER] [-vf VIDEO_FILTERS] [-sl] [-st] [-d] [-P] [--input-options INPUT_OPTIONS] [--output-options OUTPUT_OPTIONS] [--av1-cpu-used <1-8>] [-e ENCODER]
               [-p PARAMETER] [-v VALUES [VALUES ...]] [-c COMBINATIONS] [-cl <1-60>] [--interval <1-600>] [-n <x>] [--n-threads N_THREADS] [--phone-model]

options:
  -h, --help            show this help message and exit

General Arguments:
  --disable-psnr        Disable PSNR calculation.
  --disable-ssim        Disable SSIM calculation.
  -dp DECIMAL_PLACES, --decimal-places DECIMAL_PLACES
                        The number of decimal places to use for the data in the table
  -i INPUT_VIDEO, --input-video INPUT_VIDEO
                        Input video. Must be a relative/absolute path or a glob pattern.
                        If the path contains a space, it must be surrounded in double quotes.
  -t TRANSCODE_LENGTH, --transcode-length TRANSCODE_LENGTH
                        Create a lossless version of the original video that is just the first x seconds of the video.
                        This cut version of the original video is what will be transcoded and used as the reference video.
                        You cannot use this option in conjunction with the --interval or -cl argument.
  -o OUTPUT_FOLDER, --output-folder OUTPUT_FOLDER
                        Use this argument if you want a specific name for the output folder. If you want the name of the output folder to contain a space, the string must be surrounded in double quotes
  -vf VIDEO_FILTERS, --video-filters VIDEO_FILTERS
                        Apply video filter(s) to the original video before calculating quality metrics. Each filter must be separated by a comma.
                        Example: -vf bwdif=mode=0,crop=1920:800:0:140
  -sl, --skip-libvmaf   Skip libvmaf if output file exists.
  -st, --skip-transcoding
                        Skip encoding if output file exists.
  -d, --debug           Print debug message and command line.
  -P, --print           Print metrics table.
  --input-options INPUT_OPTIONS
                        Set general FFmpeg input options.
                        Use FFmpeg syntax and wrap it in double quotes. Example:
                        --input-options="-hwaccel d3d11va"
  --output-options OUTPUT_OPTIONS
                        Set general FFmpeg output options.
                        Use FFmpeg syntax and wrap it in double quotes. Examples:
                        --output-options="-c:a aac -b:a 128k"--output-options="-x264-params keyint=123:min-keyint=20"

Encoder Arguments:
  --av1-cpu-used <1-8>  Only applicable if the libaom-av1 (AV1) encoder is chosen. Set the quality/encoding speed tradeoff.
                        Lower values mean slower encoding but better quality, and vice-versa
  -e ENCODER, --encoder ENCODER
                        Specify an ffmpeg video encoder.
                        Examples: libx265, h264_amf, libaom-av1
  -p PARAMETER, --parameter PARAMETER
                        The encoder parameter to compare, e.g. preset, crf, quality.
                        Example: -p preset
  -v VALUES [VALUES ...], --values VALUES [VALUES ...]
                        The values of the specified encoder parameter to compare. Must be used alongside the -p option. Examples:
                        Compare presets: -p preset -v slow fast
                        Compare CRF values: -p crf -v 22 23
                        Compare h264_amf quality levels: -p quality -v balanced speed
  -c COMBINATIONS, --combinations COMBINATIONS
                        Use this mode if you want to compare the quality achieved with a combination of two or more parameters.
                        The list of combinations must be surrounded in quotes, and each combination must be separated by a comma.
                        For example, if you want to compare the combination of preset veryslow and CRF 18, with the combination of preset slower and CRF 16:
                        -c 'preset veryslow crf 18,preset slower crf 16'

Overview Mode Arguments:
  -cl <1-60>, --clip-length <1-60>
                        When using Overview Mode, a X seconds long segment is taken from the original video every --interval seconds and these segments are concatenated to create the overview video.
                        Specify a value for X (in the range 1-60)
  --interval <1-600>    To activate Overview Mode, this argument must be specified.
                        Overview Mode creates a lossless overview video by grabbing a --clip-length long segment every X seconds from the original video.
                        Specify a value for X (in the range 1-600)

VMAF Arguments:
  -n <x>, --n-subsample <x>
                        Set a value for libvmaf's n_subsample option if you only want the VMAF/PSNR to be calculated for every nth frame.
                        Without this argument, VMAF/PSNR scores will be calculated for every frame.
  --n-threads N_THREADS
                        Specify the number of threads to use when calculating VMAF
  --phone-model         Enable VMAF phone model
```

# Requirements
1. Python **3.7+** installed and in your PATH.
2. `pip install -r requirements.txt --upgrade`
3. FFmpeg and FFprobe installed and in your PATH (or in the same directory as this program). Your build of FFmpeg must support v2.1.1 (or above) of the `libvmaf` filter and the encoders you wish you test.

You can check what your build of FFmpeg supports by running `ffmpeg -buildconf -hide_banner` in the terminal. If `--enable-libvmaf` is not printed, your build of FFmpeg is not sufficient as VQM needs the `libvmaf` filter.

FFmpeg builds that support the `libvmaf` filter can be found in the [FFmpeg Builds](#ffmpeg-builds) section.

# FFmpeg Builds
For convenience, below are links to FFmpeg builds that support the `libvmaf` filter. 

**Windows:** https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-essentials.7z

**macOS:** https://evermeet.cx/ffmpeg - download both ffmpeg and ffprobe and add the binaries to your PATH.

Alternatively, you can install FFmpeg using Homebrew - `brew install ffmpeg`

**Linux (kernels 3.2.0+):** https://johnvansickle.com/ffmpeg.

Download the _git master_ build. Installation instructions, as well as how to add FFmpeg and FFprobe to your PATH, can be found [here](https://www.johnvansickle.com/ffmpeg/faq/).

# About the model files
Two model files are provided, `vmaf_v0.6.1.json` and `vmaf_4k_v0.6.1.json`. There is also the phone model that can be enabled by using the `-pm` argument.

This program uses the `vmaf_v0.6.1.json` model file by default, which is "based on the assumption that the viewers sit in front of a 1080p display in a living room-like environment with the viewing distance of 3x the screen height (3H)."

The phone model was created because the original model "did not accurately reflect how a viewer perceives quality on a phone. In particular, due to smaller screen size and longer viewing distance relative to the screen height (>3H), viewers perceive high-quality videos with smaller noticeable differences. For example, on a mobile phone, there is less distinction between 720p and 1080p videos compared to other devices. With this in mind, we trained and released a VMAF phone model."

The 4K model (`vmaf_4k_v0.6.1.json`) "predicts the subjective quality of video displayed on a 4K TV and viewed from a distance of 1.5H. A viewing distance of 1.5H is the maximum distance for the average viewer to appreciate the sharpness of 4K content. The 4K model is similar to the default model in the sense that both models capture quality at the critical angular frequency of 1/60 degree/pixel. However, the 4K model assumes a wider viewing angle, which affects the foveal vs peripheral vision that the subject uses."

The source of the quoted text, plus additional information about VMAF (such as the correct way to calculate VMAF), can be found [here](https://netflixtechblog.com/vmaf-the-journey-continues-44b51ee9ed12).

**Notes:**
- If you are transcoding a video that will be viewed on a mobile phone, you can add the `-pm` argument which will enable the [phone model](https://github.com/Netflix/vmaf/blob/master/resource/doc/models.md/#predict-quality-on-a-cellular-phone-screen).

- If you are transcoding a video that will be viewed on a 4K display, the default model (`vmaf_v0.6.1.json`) is fine if you are only interested in relative VMAF scores, i.e. the score differences between different encoder parameter values, but if you are interested in absolute scores, it may be better to use the 4K model file which predicts the subjective quality of video displayed on a 4K screen at a distance of 1.5x the height of the screen. To use the 4K model, replace the value of the `model_file_path` variable in libvmaf.py with `'vmaf_models/vmaf_4k_v0.6.1.json'`.