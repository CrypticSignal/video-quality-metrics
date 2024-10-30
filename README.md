# Video Quality Metrics (VQM)
VQM is a command line program that has 2 main modes:

**[1] Transcoding Mode**

Details about **Transcoding Mode**, as well as example commands, can be found in the [Transcoding Mode](#transcoding-mode) section.

**[2] No Transcoding Mode (`-ntm`)** 

VQM will calculate the VMAF (and optionally) the SSIM and PSNR of a transcoded video as long as you have the original video as well. To calculate SSIM and PSNR in addition to VMAF, you must use the `-ssim` and `-psnr` arguments.

To see an example of how to use **No Transcoding Mode**, check out the [Getting Started](#getting-started) section.

# What does VQM produce?
VQM produces a table to show the metrics, and graphs that show the variation of the value of the quality metric throughout the video (on a per-frame basis).

The table can be found in a file named `metrics_table.txt` and it contains the following:
- Encoder parameter (only applicable if using **Transcoding Mode**)
- Time taken to transcode the video (only applicable if using **Transcoding Mode**)
- Filesize (MB)
- Bitrate (Mbps)
- [Video Multimethod Assessment Fusion (VMAF)](https://github.com/Netflix/vmaf) values. VMAF is a perceptual video quality assessment algorithm developed by Netflix.
- [Optional] Peak Signal-to-Noise-Ratio (PSNR). _You must use the `-psnr` argument._
- [Optional] Structural Similarity Index (SSIM). _You must use the `-ssim` argument._
- [Optional] Multi-Scale Structural Similarity Index (MS-SSIM). _You must use the `-msssim` argument._
```
VMAF/PSNR/SSIM values are in the format: Min | Standard Deviation | Mean
+-----------+-------------------+---------+-----------+----------------------+----------------------+--------------------+
|   preset  | Encoding Time (s) |   Size  |  Bitrate  |         VMAF         |         PSNR         |        SSIM        |
+-----------+-------------------+---------+-----------+----------------------+----------------------+--------------------+
|  veryslow |        2.10       | 1.29 MB | 1.73 Mbps | 90.48 | 1.02 | 99.70 | 35.33 | 0.80 | 38.34 | 0.98 | 0.00 | 0.99 |
|   slower  |        1.21       | 1.36 MB | 1.81 Mbps | 91.56 | 0.91 | 99.75 | 35.52 | 0.79 | 38.52 | 0.98 | 0.00 | 0.99 |
|    slow   |        0.65       | 1.55 MB | 2.06 Mbps | 91.38 | 1.30 | 99.35 | 35.18 | 1.20 | 37.97 | 0.98 | 0.00 | 0.99 |
|   medium  |        0.40       | 1.56 MB | 2.08 Mbps | 90.92 | 1.46 | 99.23 | 35.14 | 1.19 | 37.91 | 0.98 | 0.00 | 0.99 |
|    fast   |        0.34       | 1.59 MB | 2.13 Mbps | 90.82 | 1.70 | 99.01 | 35.08 | 1.19 | 37.83 | 0.98 | 0.00 | 0.99 |
|   faster  |        0.26       | 1.57 MB | 2.09 Mbps | 90.09 | 1.82 | 98.90 | 35.01 | 1.20 | 37.87 | 0.98 | 0.00 | 0.99 |
|  veryfast |        0.21       | 1.57 MB | 2.09 Mbps | 88.10 | 3.15 | 96.82 | 34.18 | 1.17 | 36.81 | 0.97 | 0.00 | 0.98 |
| superfast |        0.15       | 1.87 MB | 2.50 Mbps | 87.64 | 3.60 | 95.11 | 33.39 | 1.24 | 35.71 | 0.97 | 0.00 | 0.98 |
| ultrafast |        0.11       | 3.72 MB | 4.97 Mbps | 92.80 | 1.65 | 98.60 | 34.50 | 0.98 | 35.94 | 0.97 | 0.00 | 0.98 |
+-----------+-------------------+---------+-----------+----------------------+----------------------+--------------------+
Original File: Seeking_30_480_1050.mp4
Original Bitrate: 1.04 Mbps
VQM transcoded the file with the libx264 encoder
libvmaf n_subsample: 1
```
The following command was used to produce such a table:
```
python main.py -i test_videos/Seeking_30_480_1050.mp4 -e libx264 -p preset -v veryslow slower slow medium fast faster veryfast superfast ultrafast -ssim -psnr
```

In **No Transcoding Mode**, a graph is created which shows the variation of the VMAF/SSIM/PSNR throughout the video. [1]

In **Transcoding Mode**, two types of graphs are created:

- A graph where the average VMAF is plotted against the value of the encoder parameter. [1]
- A graph for each encoder parameter value, showing the variation of the VMAF/SSIM/PSNR throughout the video. [2]

Here's an example of graph type [1]. This graph shows the variation of the VMAF score throughout the video:

![VMAF variation graph](https://github.com/CrypticSignal/video-quality-metrics/blob/master/example_graphs/VMAF.png)

_An example of the per-frame SSIM graph and per-frame PSNR graph can be found in the [example_graphs folder](https://github.com/CrypticSignal/video-quality-metrics/tree/master/example_graphs)._

Here's an example of graph type [2]. This is the kind of graph that will be produced if you opted to compare the effects of different CRF values:

![CRF vs VMAF graph](https://github.com/CrypticSignal/video-quality-metrics/blob/master/example_graphs/CRF%20vs%20VMAF.png)

# Quick Links
- [Getting Started](#getting-started)
- [Transcoding Mode](#transcoding-mode)
- [Overview Mode](#overview-mode)
- [Available Arguments](#available-arguments)
- [Requirements](#requirements)
- [FFmpeg Builds](#ffmpeg-builds)
- [About the model files](#about-the-model-files)

# Getting Started
Clone this repository. Then, navigate to the root of this repository in your terminal and run `pip install -r requirements.txt --upgrade`.
VQM is now ready to be used.

If you would like to test VQM without using your own video(s), you can use the videos in the `test_videos` folder.

To test **No Transcoding Mode**, you can run:
```
python main.py -ntm -i test_videos/Seeking_30_480_1050.mp4 -tv test_videos/Seeking_10_288_375.mp4 -s 720x480
```
_Note: `-s 720x480` was necessary to scale the transcoded video to match the resolution of the original video (720x480) before calculating VMAF scores. This is the best practice as per Netflix's tech blog. Here is a quote from [their blog](https://netflixtechblog.com/vmaf-the-journey-continues-44b51ee9ed12):_

_"A typical encoding pipeline for adaptive streaming introduces two types of artifacts — compression artifacts (due to lossy compression) and scaling artifacts (for low bitrates, source video is downsampled before compression, and later upsampled on the display device). When using VMAF to evaluate perceptual quality, both types of artifacts must be taken into account. For example, when a source is 1080p but the encode is 480p, the correct way of calculating VMAF on the pair is to upsample the encode to 1080p to match the source’s resolution. If, instead, the source is downsampled to 480p to match the encode, the obtained VMAF score will not capture the scaling artifacts."_

_If the transcoded file is the same resolution as the original file, using the `-s` argument is not necessary._

To test **Transcoding Mode**, you can run:
```
python main.py -i test_videos/Seeking_30_480_1050.mp4 -e libx264 -p preset -v slow medium -ssim -psnr
```

# Transcoding Mode
In this mode, VQM will compare the VMAF (and optionally) the SSIM and PSNR achieved with different values of the chosen encoder parameter.

You must specify an encoder (using the `-e` argument. If not specified, `libx264` will be used), a FFmpeg encoder parameter (e.g. `-preset`, `-crf`, `-quality`) and the values you want to compare (using the `-v` argument). 

Examples: 

```
python main.py -i test_videos/Seeking_30_480_1050.mp4 -e libx265 -p preset -v slow medium
```
```
python main.py -i test_videos/Seeking_30_480_1050.mp4 -e libx264 -p crf -v 22 23 24
```
```
python main.py -i test_videos/Seeking_30_480_1050.mp4 -e h264_amf -p quality -v balanced speed quality
```

VQM will automatically transcode the video with each value. To calculate SSIM and PSNR in addition to VMAF, you must include the `-ssim` and `-psnr` arguments.

Here is  an example of the table that is produced when comparing presets:
```
VMAF/PSNR/SSIM values are in the format: Min | Standard Deviation | Mean
+--------+-------------------+---------+-----------+----------------------+----------------------+--------------------+
| Preset | Encoding Time (s) |   Size  |  Bitrate  |         VMAF         |         PSNR         |        SSIM        |
+--------+-------------------+---------+-----------+----------------------+----------------------+--------------------+
|  slow  |        2.75       | 4.23 MB | 2.15 Mbps | 90.56 | 1.13 | 94.09 | 46.24 | 0.91 | 48.30 | 1.00 | 0.00 | 1.00 |
| medium |        2.14       | 4.33 MB | 2.20 Mbps | 90.65 | 1.07 | 93.95 | 46.17 | 0.92 | 48.24 | 1.00 | 0.00 | 1.00 |
+--------+-------------------+---------+-----------+----------------------+----------------------+--------------------+
```

Here is  an example of the table that is produced when comparing CRF values:
```
VMAF/PSNR/SSIM values are in the format: Min | Standard Deviation | Mean
+-----+-------------------+---------+-----------+----------------------+----------------------+--------------------+
| CRF | Encoding Time (s) |   Size  |  Bitrate  |         VMAF         |         PSNR         |        SSIM        |
+-----+-------------------+---------+-----------+----------------------+----------------------+--------------------+
|  20 |        2.43       | 6.70 MB | 3.40 Mbps | 92.90 | 1.13 | 95.77 | 47.80 | 1.08 | 50.44 | 1.00 | 0.00 | 1.00 |
|  23 |        2.13       | 4.33 MB | 2.20 Mbps | 90.65 | 1.07 | 93.95 | 46.17 | 0.92 | 48.24 | 1.00 | 0.00 | 1.00 |
+-----+-------------------+---------+-----------+----------------------+----------------------+--------------------+
```

# Overview Mode
A recent addition to this program is "overview mode", which can be used with **Transcoding Mode** by specifying the `--interval` and `--clip-length` arguments. The benefit of this mode is especially apparent with long videos, such as movies. What this mode does is create a lossless "overview video" by grabbing a `<clip length>` seconds long segment every `<interval>` seconds from the original video. The transcodes and computation of the quality metrics are done using this overview video instead of the original video. As the overview video can be much shorter than the original, the process of trancoding and computing the quality metrics is much quicker, while still being a fairly accurate representation of the original video as the program goes through the whole video and grabs, say, a two-second-long segment every 60 seconds.

Example: `python main.py -i test_videos/Seeking_30_480_1050.mp4 -crf 17 18 19 --interval 60 --clip-length 2`

In the example above, we're grabbing a two-second-long clip (`--clip-length 2`) every minute (`--interval 60`) in the video. These 2-second long clips are concatenated to make the overview video. A 1-hour long video is turned into an overview video that is 1 minute and 58 seconds long. The benefit of overview mode should now be clear - transcoding and computing the quality metrics of a <2 minutes long video is **much** quicker than doing so with an hour long video.

_An alternative method of reducing the execution time of this program is by only using the first x seconds of the original video (you can do this with the `-t` argument), but **Overview Mode** provides a better representation of the whole video._

# Available Arguments
You can see a list of the available arguments with `python main.py -h`:

```
usage: main.py [-h] [-dp DECIMAL_PLACES] -i INPUT_VIDEO [-t TRANSCODE_LENGTH] [-ntm] [-o OUTPUT_FOLDER] [-tv TRANSCODED_VIDEO] [-vf VIDEO_FILTERS] [--av1-cpu-used <1-8>] [-e ENCODER] [-p PARAMETER] [-v VALUES [VALUES ...]] [-cl <1-60>] [--interval <1-600>] [-n <x>]
               [--n-threads N_THREADS] [--phone-model] [-s SCALE] [-psnr] [-ssim] [-msssim]

options:
  -h, --help            show this help message and exit

General Arguments:
  -dp, --decimal-places DECIMAL_PLACES
                        The number of decimal places to use for the data in the table
  -i, --input-video INPUT_VIDEO
                        Input video. Can be a relative or absolute path, or a URL.
                        If the path contains a space, it must be surrounded in double quotes.
  -t, --transcode-length TRANSCODE_LENGTH
                        Create a lossless version of the original video that is just the first x seconds of the video.
                        This cut version of the original video is what will be transcoded and used as the reference video.
                        You cannot use this option in conjunction with the --interval or -cl argument.
  -ntm, --no-transcoding-mode
                        Enable 'No Transcoding Mode', which allows you to calculate the VMAF/SSIM/PSNR for a video that you have already transcoded.
                        The original and transcoded video paths must be specified using the -i and -tv arguments, respectively.
                        Example: python main.py -ntm -i original.mp4 -tv transcoded.mp4
  -o, --output-folder OUTPUT_FOLDER
                        Use this argument if you want a specific name for the output folder. If you want the name of the output folder to contain a space, the string must be surrounded in double quotes
  -tv, --transcoded-video TRANSCODED_VIDEO
                        Transcoded video. Can be a relative or absolute path, or an URL. Only applicable when using the -ntm mode.
  -vf, --video-filters VIDEO_FILTERS
                        Apply video filter(s) to the original video before calculating quality metrics. Each filter must be separated by a comma.
                        Example: -vf bwdif=mode=0,crop=1920:800:0:140

Transcoding Arguments:
  --av1-cpu-used <1-8>  Only applicable if the libaom-av1 (AV1) encoder is chosen. Set the quality/encoding speed tradeoff.
                        Lower values mean slower encoding but better quality, and vice-versa
  -e, --encoder ENCODER
                        Specify an ffmpeg video encoder.
                        Examples: libx265, h264_amf, libaom-av1
  -p, --parameter PARAMETER
                        The encoder parameter to compare, e.g. preset, crf, quality.
                        Example: -p preset
  -v, --values VALUES [VALUES ...]
                        The values of the specified encoder parameter to compare. Must be used alongside the -p option. Examples:
                        Compare presets: -p preset -v slow fast
                        Compare CRF values: -p crf -v 22 23
                        Compare h264_amf quality levels: -p quality -v balanced speed

Overview Mode Arguments:
  -cl, --clip-length <1-60>
                        When using Overview Mode, a X seconds long segment is taken from the original video every --interval seconds and these segments are concatenated to create the overview video.
                        Specify a value for X (in the range 1-60)
  --interval <1-600>    To activate Overview Mode, this argument must be specified.
                        Overview Mode creates a lossless overview video by grabbing a --clip-length long segment every X seconds from the original video.
                        Specify a value for X (in the range 1-600)

VMAF Arguments:
  -n, --n-subsample <x>
                        Set a value for libvmaf's n_subsample option if you only want the VMAF/SSIM/PSNR to be calculated for every nth frame.
                        Without this argument, VMAF/SSIM/PSNR scores will be calculated for every frame.
  --n-threads N_THREADS
                        Specify the number of threads to use when calculating VMAF
  --phone-model         Enable VMAF phone model
  -s, --scale SCALE     Scale the transcoded video to match the resolution of the original video.
                        To ensure accurate VMAF scores, this is necessary if the transcoded video has a different resolution.
                        For example, if the original video is 1920x1980 and the transcoded video is 1280x720, you should specify:
                        -s 1920x1080

Optional Metrics:
  -psnr, --calculate-psnr
                        Enable PSNR calculation in addition to VMAF
  -ssim, --calculate-ssim
                        Enable SSIM calculation in addition to VMAF
  -msssim, --calculate-msssim
                        Enable MS-SSIM calculation in addition to VMAF
```

# Requirements
1. Python **3.7+** installed and in your PATH.
2. `pip install -r requirements.txt --upgrade`
3. FFmpeg and FFprobe installed and in your PATH (or in the same directory as this program). Your build of FFmpeg must have v2.1.1 (or above) of the `libvmaf` filter. FFmpeg must also be built with support for the encoders you wish you test.

You can check which encoders your build of FFmpeg supports by running `ffmpeg -buildconf` in the terminal.

If `--enable-libvmaf` is not printed when running `ffmpeg -buildconf`, your build of FFmpeg is not sufficient as VQM needs the `libvmaf` filter.

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
