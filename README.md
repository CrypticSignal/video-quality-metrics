# Video Quality Metrics (VQM)
VQM is a command line program that has two main modes:

- **Transcoding Mode**
  - Details about **Transcoding Mode**, as well as example commands, can be found in the [Transcoding Mode](#transcoding-mode) section.

- **No Transcoding Mode (`-ntm`)**
  - VQM will calculate the VMAF and PSNR of a transcoded video as long as you have the original video as well.

To see an example of how to use **No Transcoding Mode**, check out the [Getting Started](#getting-started) section.

# Quick Links
- [What does VQM produce?](#what-does-vqm-produce)
- [Getting Started](#getting-started)
- [Transcoding Mode](#transcoding-mode)
- [Overview Mode](#overview-mode)
- [Combination Mode](#combination-mode)
- [Available Arguments](#available-arguments)
- [Requirements](#requirements)
- [FFmpeg Builds](#ffmpeg-builds)
- [About the model files](#about-the-model-files)

# What does VQM produce?
VQM produces a table to show the metrics, and graphs that show the per-frame VMAF and PSNR.

The table can be found in a file named `metrics_table.txt` and it contains the following:
- Encoder parameter (only applicable if using **Transcoding Mode**)
- Time taken to transcode the video (only applicable if using **Transcoding Mode**)
- Filesize (MB)
- Bitrate (Mbps)
- [Video Multimethod Assessment Fusion (VMAF)](https://github.com/Netflix/vmaf) values. VMAF is a perceptual video quality assessment algorithm developed by Netflix.
- Peak Signal-to-Noise-Ratio (PSNR).

In **No Transcoding Mode**, per-frame VMAF and PSNR graphs are created.

In **Transcoding Mode**, two types of graphs are created:

- A graph (type 1) for each encoder parameter value, showing the per-frame VMAF and PSNR.
- A graph (type 2) where the average VMAF is plotted against the value of the encoder parameter.

Here's an example of graph type 1, which shows the per-frame VMAF score:

![Per-frame VMAF](https://github.com/CrypticSignal/video-quality-metrics/blob/master/example_graphs/VMAF.png)

_An example of the per-frame PSNR graph can be found in the [example_graphs folder](https://github.com/CrypticSignal/video-quality-metrics/tree/master/example_graphs)._

Here's an example of graph type 2 if you opt to compare the effects of different CRF values:

![CRF vs VMAF graph](https://github.com/CrypticSignal/video-quality-metrics/blob/master/example_graphs/CRF%20vs%20VMAF.png)

# Getting Started
Clone this repository. Then, navigate to the root of this repository in your terminal and run `pip install -r requirements.txt --upgrade`.
VQM is now ready to be used.

If you would like to test VQM without using your own video(s), you can use the videos in the `test_videos` folder.

`Seeking_30_480_1050.mp4` is the original video and `Seeking_10_288_375.mp4` is the distorted video.

There is also `ForBiggerFun.mp4`, which is a video that is exactly 1 minute long.

To test **No Transcoding Mode**, you can run:
```
python main.py -ntm -i test_videos/Seeking_30_480_1050.mp4 -tv test_videos/Seeking_10_288_375.mp4 -s 720x480
```
_Note: If using the `Seeking_...` videos in the test_videos folder, `-s 720x480` is necessary to scale the distorted video to match the resolution of the original video (720x480) before calculating VMAF scores. This is the best practice as per Netflix's tech blog. Here is a quote from [their blog](https://netflixtechblog.com/vmaf-the-journey-continues-44b51ee9ed12):_

_"A typical encoding pipeline for adaptive streaming introduces two types of artifacts — compression artifacts (due to lossy compression) and scaling artifacts (for low bitrates, source video is downsampled before compression, and later upsampled on the display device). When using VMAF to evaluate perceptual quality, both types of artifacts must be taken into account. For example, when a source is 1080p but the encode is 480p, the correct way of calculating VMAF on the pair is to upsample the encode to 1080p to match the source’s resolution. If, instead, the source is downsampled to 480p to match the encode, the obtained VMAF score will not capture the scaling artifacts."_

_If the transcoded file is the same resolution as the original file, using the `-s` argument is not necessary._

To test **Transcoding Mode**, you can run:
```
python main.py -i test_videos/Seeking_30_480_1050.mp4 -e libx264 -p preset -v slow medium
```
Alternatively, you can use `test_videos/ForBiggerFun.mp4`.

# Transcoding Mode
In this mode, VQM will compare the VMAF and PSNR achieved with different values of the chosen encoder parameter.

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
Here is  an example of the table that is produced when comparing presets:
```
VMAF/PSNR values are in the format: Min | Standard Deviation | Mean
+--------+-------------------+---------+-----------+----------------------+----------------------+
| Preset | Encoding Time (s) |   Size  |  Bitrate  |         VMAF         |         PSNR         |
+--------+-------------------+---------+-----------+----------------------+----------------------+
|  slow  |        2.75       | 4.23 MB | 2.15 Mbps | 90.56 | 1.13 | 94.09 | 46.24 | 0.91 | 48.30 |
| medium |        2.14       | 4.33 MB | 2.20 Mbps | 90.65 | 1.07 | 93.95 | 46.17 | 0.92 | 48.24 |
+--------+-------------------+---------+-----------+----------------------+----------------------+
```
Here is  an example of the table that is produced when comparing CRF values:
```
VMAF/PSNR values are in the format: Min | Standard Deviation | Mean
+-----+-------------------+---------+-----------+----------------------+----------------------+
| CRF | Encoding Time (s) |   Size  |  Bitrate  |         VMAF         |         PSNR         |
+-----+-------------------+---------+-----------+----------------------+-----------------------
|  20 |        2.43       | 6.70 MB | 3.40 Mbps | 92.90 | 1.13 | 95.77 | 47.80 | 1.08 | 50.44 |
|  23 |        2.13       | 4.33 MB | 2.20 Mbps | 90.65 | 1.07 | 93.95 | 46.17 | 0.92 | 48.24 |
+-----+-------------------+---------+-----------+----------------------+----------------------+
```
# Overview Mode
Overview Mode can be used with **Transcoding Mode** by specifying the `--interval` and `--clip-length` arguments. The benefit of this mode is especially apparent with long videos, such as movies. What this mode does is create a lossless "overview video" by grabbing a `<clip length>` seconds long segment every `<interval>` seconds from the original video. The transcodes and computation of the quality metrics are done using this overview video instead of the original video. As the overview video can be much shorter than the original, the process of trancoding and computing the quality metrics is much quicker, while still being a fairly accurate representation of the original video as the program goes through the whole video and grabs, say, a two-second-long segment every 60 seconds.

Example: `python main.py -i test_videos/Seeking_30_480_1050.mp4 -crf 17 18 19 --interval 60 --clip-length 2`

In the example above, we're grabbing a two-second-long clip (`--clip-length 2`) every minute (`--interval 60`) in the video. These 2-second long clips are concatenated to make the overview video. A 1-hour long video is turned into an overview video that is 1 minute and 58 seconds long. The benefit of overview mode should now be clear - transcoding and computing the quality metrics of a <2 minutes long video is **much** quicker than doing so with an hour long video.

_An alternative method of reducing the execution time of this program is by only using the first x seconds of the original video (you can do this with the `-t` argument), but **Overview Mode** provides a better representation of the whole video._

# Combination Mode
Instead of comparing the quality achieved with various values of one encoder parameter, Combination Mode allows you to compare the quality achieved with a combination of two or more parameters.

To activate Combination Mode, specify the `-c` or `--combinations` argument, followed by a list of combinations you wish to compare. The list of combinations must be surrounded in quotes, and each combination must be separated by a comma.

For example, if you want to compare the quality achieved with:
- The combination of preset `veryslow` and a CRF value of `18`
- The combination of preset `slower` and CRF value of `16`

You would run something like:
```
python main.py -i "test_videos/ForBiggerFun.mp4" -e libx265 -c "preset veryslow crf 18,preset slower crf 16"
```
The table produced will look something like this:
```
VMAF values are in the format: Min | Standard Deviation | Mean
+--------------------------+-------------------+----------+-----------+----------------------+
|       Combination        | Encoding Time (s) |   Size   |  Bitrate  |         VMAF         |
+--------------------------+-------------------+----------+-----------+----------------------+
| -preset veryslow -crf 18 |       325.79      | 19.13 MB | 2.55 Mbps | 94.99 | 1.27 | 99.06 |
|  -preset slower -crf 16  |       211.81      | 24.06 MB | 3.20 Mbps | 95.62 | 1.14 | 99.23 |
+--------------------------+-------------------+----------+-----------+----------------------+
```
- Combination Mode can be used alongside Overview Mode.
- You need to decide whether you want to use the regular mode, which compares the quality metrics achieved with various values of **one** particular encoder parameter (using the `-p` and `-v` arguments), OR Combination Mode. You cannot do both.

# Available Arguments
You can see a list of the available arguments with `python main.py -h`:

```
usage: main.py [-h] [--disable-psnr] [-dp DECIMAL_PLACES] -i INPUT_VIDEO [-t TRANSCODE_LENGTH] [-ntm] [-o OUTPUT_FOLDER] [-tv TRANSCODED_VIDEO] [-vf VIDEO_FILTERS] [--av1-cpu-used <1-8>] [-e ENCODER] [-eo ENCODER_OPTIONS] [-p PARAMETER] [-v VALUES [VALUES ...]]
               [-c COMBINATIONS] [-cl <1-60>] [--interval <1-600>] [-n <x>] [--n-threads N_THREADS] [--phone-model] [-s SCALE]

options:
  -h, --help            show this help message and exit

General Arguments:
  --disable-psnr        Disable PSNR calculation.
  -dp DECIMAL_PLACES, --decimal-places DECIMAL_PLACES
                        The number of decimal places to use for the data in the table
  -i INPUT_VIDEO, --input-video INPUT_VIDEO
                        Input video. Can be a relative or absolute path, or a URL.
                        If the path contains a space, it must be surrounded in double quotes.
  -t TRANSCODE_LENGTH, --transcode-length TRANSCODE_LENGTH
                        Create a lossless version of the original video that is just the first x seconds of the video.
                        This cut version of the original video is what will be transcoded and used as the reference video.
                        You cannot use this option in conjunction with the --interval or -cl argument.
  -ntm, --no-transcoding-mode
                        Enable 'No Transcoding Mode', which allows you to calculate the VMAF/PSNR for a video that you have already transcoded.
                        The original and transcoded video paths must be specified using the -i and -tv arguments, respectively.
                        Example: python main.py -ntm -i original.mp4 -tv transcoded.mp4
  -o OUTPUT_FOLDER, --output-folder OUTPUT_FOLDER
                        Use this argument if you want a specific name for the output folder. If you want the name of the output folder to contain a space, the string must be surrounded in double quotes
  -tv TRANSCODED_VIDEO, --transcoded-video TRANSCODED_VIDEO
                        Transcoded video. Can be a relative or absolute path, or an URL. Only applicable when using the -ntm mode.
  -vf VIDEO_FILTERS, --video-filters VIDEO_FILTERS
                        Apply video filter(s) to the original video before calculating quality metrics. Each filter must be separated by a comma.
                        Example: -vf bwdif=mode=0,crop=1920:800:0:140

Encoder Arguments:
  --av1-cpu-used <1-8>  Only applicable if the libaom-av1 (AV1) encoder is chosen. Set the quality/encoding speed tradeoff.
                        Lower values mean slower encoding but better quality, and vice-versa
  -e ENCODER, --encoder ENCODER
                        Specify an ffmpeg video encoder.
                        Examples: libx265, h264_amf, libaom-av1
  -eo ENCODER_OPTIONS, --encoder-options ENCODER_OPTIONS
                        Set general encoder options to use for all transcodes.
                        Use FFmpeg syntax. Must be surronded in quotes. Example:
                        --encoder-options='-crf 18 -x264-params keyint=123:min-keyint=20'
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
  -s SCALE, --scale SCALE
                        Scale the transcoded video to match the resolution of the original video.
                        To ensure accurate VMAF scores, this is necessary if the transcoded video has a different resolution.
                        For example, if the original video is 1920x1980 and the transcoded video is 1280x720, you should specify:
                        -s 1920x1080
```

# Requirements
1. Python **3.7+** installed and in your PATH.
2. `pip install -r requirements.txt --upgrade`
3. FFmpeg and FFprobe installed and in your PATH (or in the same directory as this program). Your build of FFmpeg must have v2.1.1 (or above) of the `libvmaf` filter. FFmpeg must also be built with support for the encoders you wish you test.

You can check which encoders your build of FFmpeg supports by running `ffmpeg -buildconf -hide_banner` in the terminal. If `--enable-libvmaf` is not printed, your build of FFmpeg is not sufficient as VQM needs the `libvmaf` filter.

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
