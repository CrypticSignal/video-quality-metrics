# Video Quality Metrics (VQM)

VQM is a command line program that has 2 main modes:

**[1] Transcoding Mode**

Details about **Transcoding Mode**, as well as example commands, can be found in the [Transcoding Mode](#transcoding-mode) section.

**[2] No Transcoding Mode (`-ntm`)** 

VQM will calculate the VMAF (and optionally) the SSIM and PSNR of a transcoded video as long as you have the original video as well. To calculate SSIM and PSNR in addition to VMAF, you must use the `-ssim` and `-psnr` arguments.

Here is an example:

`python main.py -ntm -iv example_video/original.mp4 -tv example_video/transcoded.mp4 -ssim -psnr`

# Table of Contents

- [Example Table](#example-table)
- [Example Graphs](#example-graphs)
- [Transcoding Mode](#transcoding-mode)
- [Overview Mode](#overview-mode)
- [Available Arguments](#available-arguments)
- [Requirements](#requirements)
- [Recommended FFmpeg Builds](#recommended-ffmpeg-builds)
- [About the model files](#about-the-model-files)

# Example Table

VQM creates a table in a file named `Table.txt`, and it contains the following:
- Preset/CRF value
- Time taken to transcode the video (in seconds)
- Filesize (MB)
- Bitrate (Mbps)
- [Video Multimethod Assessment Fusion (VMAF)](https://github.com/Netflix/vmaf) values. VMAF is a perceptual video quality assessment algorithm developed by Netflix.
- [Optional] Peak Signal-to-Noise-Ratio (PSNR). _You must use the `-psnr` argument._
- [Optional] Structural Similarity Index (SSIM). _You must use the `-ssim` argument._
- [Optional] Multi-Scale Structural Similarity Index (MS-SSIM). _You must use the `-msssim` argument._
```
VMAF values are in the format: Min | Standard Deviation | Mean
+-----------+-------------------+----------+-----------+----------------------+
|   Preset  | Encoding Time (s) |   Size   |  Bitrate  |         VMAF         |
+-----------+-------------------+----------+-----------+----------------------+
|    slow   |        2.78       | 4.23 MB  | 2.15 Mbps | 90.56 | 1.13 | 94.09 |
|   medium  |        2.14       | 4.33 MB  | 2.20 Mbps | 90.65 | 1.07 | 93.95 |
|    fast   |        1.89       | 4.87 MB  | 2.47 Mbps | 90.66 | 1.19 | 93.60 |
|   faster  |        1.48       | 4.37 MB  | 2.22 Mbps | 90.08 | 1.18 | 93.11 |
|  veryfast |        0.97       | 3.30 MB  | 1.67 Mbps | 86.75 | 1.78 | 90.02 |
| superfast |        0.82       | 8.34 MB  | 4.23 Mbps | 90.90 | 1.13 | 93.70 |
+-----------+-------------------+----------+-----------+----------------------+
File Transcoded: example_video/original.mp4
Bitrate: 3.78 Mbps
Encoder used for the transcodes: x264
CRF 23 was used.
Filter(s) used: None
n_subsample: 1
```
The following command was used to produce such a table:

`python main.py -iv example_video/original.mp4 -p slow medium fast faster veryfast superfast`

*If **No Transcoding Mode** is used, the first two columns will not exist as they are not applicable.*

# Example Graphs

In **Transcoding Mode**, two types of graphs are created:

- A graph where the average VMAF is plotted against the presets/CRF values. If one opts to compare CRF values, the following type of graph will produced:

![CRF vs VMAF graph](https://github.com/CrypticSignal/video-quality-metrics/blob/master/example_graphs/CRF%20vs%20VMAF.png)

- A graph for each preset/CRF value, showing the variation of the VMAF/SSIM/PSNR throughout the video. An example is shown below.

![VMAF variation graph](https://github.com/CrypticSignal/video-quality-metrics/blob/master/example_graphs/VMAF.png)

_Example SSIM and PSNR graphs can be found in the [example_graphs folder](https://github.com/CrypticSignal/video-quality-metrics/tree/master/example_graphs)._

# Transcoding Mode

In this mode, you compare the VMAF (and optionally) the SSIM and PSNR with different presets **or** CRF values. You must specify multiple CRF values or presets and VQM will automatically transcode the video with each preset/CRF value. To calculate SSIM and PSNR, you must use the `-ssim` and `-psnr` arguments.

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
Command used:

`python main.py -iv example_video/original.mp4 -p slow medium -ssim -psnr`

_You specify the presets that you want to compare and (optionally) **one** CRF value. If you do not specify a CRF value, the CRF will be set to 23._


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
Command used:

`python main.py -iv example_video/original.mp4 -crf 20 23 -ssim -psnr`

_You specify the CRF values that you want to compare and (optionally) **one** preset. If you do not specify a preset, the `medium` preset will be used._

# Overview Mode

A recent addition to this program is "overview mode", which can be used with **Transcoding Mode** by specifying the `--interval` and `--clip-length` arguments. The benefit of this mode is especially apparent with long videos, such as movies. What this mode does is create a lossless "overview video" by grabbing a `<clip length>` seconds long segment every `<interval>` seconds from the original video. The transcodes and computation of the quality metrics are done using this overview video instead of the original video. As the overview video can be much shorter than the original, the process of trancoding and computing the quality metrics is much quicker, while still being a fairly accurate representation of the original video as the program goes through the whole video and grabs, say, a two-second-long segment every 60 seconds.

Example: `python main.py -iv original.mp4 -crf 17 18 19 --interval 60 --clip-length 2`

In the example above, we're grabbing a two-second-long clip (`--clip-length 2`) every minute (`--interval 60`) in the video. These 2-second long clips are concatenated to make the overview video. A 1-hour long video is turned into an overview video that is 1 minute and 58 seconds long. The benefit of overview mode should now be clear - transcoding and computing the quality metrics of a <2 minutes long video is **much** quicker than doing so with an hour long video.

_An alternative method of reducing the execution time of this program is by only using the first x seconds of the original video (you can do this with the `-t` argument), but **Overview Mode** provides a better representation of the whole video._

# Available Arguments

You can check the available arguments with `python main.py -h`:

```
usage: main.py [-h] [--av1-cpu-used <1-8>] [-cl <1-60>] [-crf <0-51> [<0-51> ...]] [-dp DECIMAL_PLACES] [-e {x264,x265,libaom-av1}] [-i <1-600>] [-subsample SUBSAMPLE]
               [--n-threads N_THREADS] [-ntm] [-o OUTPUT_FOLDER] -iv INPUT_VIDEO [-p <preset/s> [<preset/s> ...]] [--phone-model] [-sc] [-psnr] [-ssim] [-msssim]
               [-t SECONDS] [-tv TRANSCODED_VIDEO] [-vf VIDEO_FILTERS]

optional arguments:
  -h, --help            show this help message and exit

Encoding Arguments:
  --av1-cpu-used <1-8>  Only applicable if the libaom-av1 (AV1) encoder is chosen. Set the quality/encoding speed tradeoff. Lower values mean slower encoding but better
                        quality, and vice-versa (default: 5)
  -crf <0-51> [<0-51> ...]
                        Specify the CRF value(s) to use
  -e {x264,x265,libaom-av1}, --video-encoder {x264,x265,libaom-av1}
                        Specify whether to use the x264 (H.264), x265 (H.265) or libaom-av1 (AV1) encoder (default: x264)
  -p <preset/s> [<preset/s> ...], --preset <preset/s> [<preset/s> ...]
                        Specify the preset(s) to use (default: medium)

VMAF Arguments:
  -subsample SUBSAMPLE  Set a value for libvmaf's n_subsample option if you only want the VMAF/SSIM/PSNR to be calculated for every nth frame. Without this argument,
                        VMAF/SSIM/PSNR scores will be calculated for every frame (default: 1)
  --n-threads N_THREADS
                        Specify the number of threads to use when calculating VMAF
  --phone-model         Enable VMAF phone model (default: False)

Overview Mode Arguments:
  -cl <1-60>, --clip-length <1-60>
                        When using Overview Mode, a X seconds long segment is taken from the original video every --interval seconds and these segments are concatenated to
                        create the overview video. Specify a value for X (in the range 1-60) (default: 1)
  -i <1-600>, --interval <1-600>
                        To activate Overview Mode, this argument must be specified. Overview Mode creates a lossless overview video by grabbing a --clip-length long segment
                        every X seconds from the original video. Specify a value for X (in the range 1-600) (default: None)

General Arguments:
  -dp DECIMAL_PLACES, --decimal-places DECIMAL_PLACES
                        The number of decimal places to use for the data in the table (default: 2)
  -ntm, --no-transcoding-mode
                        Enable "no transcoding mode", which allows you to calculate the VMAF/SSIM/PSNR for a video that you have already transcoded. The original and
                        transcoded video paths must be specified using the -iv and -tv arguments, respectively. Example: python main.py -ntm -iv original.mp4 -tv
                        transcoded.mp4 (default: False)
  -o OUTPUT_FOLDER, --output-folder OUTPUT_FOLDER
                        Use this argument if you want a specific name for the output folder. If you want the name of the output folder to contain a space, the string must
                        be surrounded in double quotes (default: None)
  -iv INPUT_VIDEO, --input-video INPUT_VIDEO
                        Input video. Can be a relative or absolute path, or an URL. If the path contains a space, it must be surrounded in double
                        quotes (default: None)
  -t SECONDS, --encode-length SECONDS
                        Create a lossless version of the original video that is just the first x seconds of the video. This cut version of the original video is what will
                        be transcoded and used as the reference video. You cannot use this option in conjunction with the -i or -cl arguments (default: None)
  -tv TRANSCODED_VIDEO, --transcoded-video TRANSCODED_VIDEO
                        Transcoded video. Can be a relative or absolute path, or an URL. Only applicable when using the -ntm mode.
  -vf VIDEO_FILTERS, --video-filters VIDEO_FILTERS
                        Add FFmpeg video filter(s). Each filter must be separated by a comma. Example: -vf bwdif=mode=0,crop=1920:800:0:140 (default: None)

Optional Metrics:
  -psnr, --calculate-psnr
                        Enable PSNR calculation in addition to VMAF (default: False)
  -ssim, --calculate-ssim
                        Enable SSIM calculation in addition to VMAF (default: False)
  -msssim, --calculate-msssim
                        Enable MS-SSIM calculation in addition to VMAF (default: False)
```

# Requirements

1. Python **3.7+**
2. `pip install -r requirements.txt`
3. FFmpeg and FFprobe installed and in your PATH (or in the same directory as this program). Your build of FFmpeg must have v2.1.1 (or above) of the libvmaf filter. Depending on the encoder(s) that you wish to test, FFmpeg must also be built with libx264, libx265 and libaom.

You can check whether your build of FFmpeg has libvmaf/libx264/libx265/libaom with `ffmpeg -buildconf`.

Look for `--enable-libvmaf`, `--enable-libx265`, `--enable-libx264` and `--enable-libaom`.

# Recommended FFmpeg Builds

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

- If you are transcoding a video that will be viewed on a mobile phone, you can add the `-pm` argument which will enable the [phone model](https://github.com/Netflix/vmaf/blob/master/resource/doc/models.md/#predict-quality-on-a-cellular-phone-screen).

- If you are transcoding a video that will be viewed on a 4K display, the default model (`vmaf_v0.6.1.json`) is fine if you are only interested in relative VMAF scores, i.e. the score differences between different presets/CRF values, but if you are interested in absolute scores, it may be better to use the 4K model file which predicts the subjective quality of video displayed on a 4K screen at a distance of 1.5x the height of the screen. To use the 4K model, replace the value of the `model_file_path` variable in libvmaf.py with `'vmaf_models/vmaf_4k_v0.6.1.json'`.
