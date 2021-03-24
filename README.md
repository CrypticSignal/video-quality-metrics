# Video Quality Metrics (VQM)
VQM is a command line program that has two main features. These features are outlined in [**Section Two: Features**](https://github.com/CrypticSignal/video-quality-metrics#section-two-features), and they are referred to as **[1]** and **[2]**, respectively.

**What kind of data does this program produce?**

This program provides you with two types of data. Graphs (saved as PNG files) and a table (saved in a .txt file) showing various information such as the average [VMAF](https://github.com/Netflix/vmaf) score. VMAF is a perceptual video quality assessment algorithm developed by Netflix.

**What kind of graphs are created?**

When using feature **[2]**, two types of graphs are created:
- A graph where the average VMAF is plotted against the presets/CRF values. If one opts to compare CRF values, the following type of graph will produced:

![CRF vs VMAF graph example](https://github.com/CrypticSignal/video-quality-metrics/blob/master/Example%20Graphs/CRF%20vs%20VMAF.png)

- A graph for each preset/CRF value, showing the variation of the VMAF/SSIM/PSNR throughout the video. An example is shown below.

![Example Graph](https://github.com/BassThatHertz/video-quality-metrics/blob/master/Example%20Graphs/VMAF.png)

*Example SSIM and PSNR graphs can be found in the [Example Graphs folder](https://github.com/BassThatHertz/video-quality-metrics/tree/master/Example%20Graphs).*

**What data is shown in the table?**
- Filesize (MB)
- Bitrate (Mbps)
- Filesize compared to the original video (as a percentage)
- [Video Multimethod Assessment Fusion (VMAF)](https://github.com/Netflix/vmaf) values. VMAF is a perceptual video quality assessment algorithm developed by Netflix.
- [Optional] Structural Similarity Index (SSIM). *You must use the `-ssim` argument.*
- [Optional] Peak Signal-to-Noise-Ratio (PSNR). *You must use the `-psnr` argument.*

If feature **[2]** is used, in addition to the above, the following colums are present:
- Preset/CRF value
- Time taken to transcode the video (in seconds)

You can find an example table below. Please note that when feature **[1]** is used, the first two columns will not exist as they are not applicable.
```
+-----------+-------------------+----------+-----------+----------------------+
|   Preset  | Encoding Time (s) |   Size   |  Bitrate  |         VMAF         |
+-----------+-------------------+----------+-----------+----------------------+
|  veryslow |       68.12       | 18.70 MB | 2.48 Mbps | 89.75 | 2.51 | 97.62 |
|   slower  |       32.57       | 20.43 MB | 2.71 Mbps | 89.54 | 2.44 | 97.72 |
|    slow   |       17.84       | 20.62 MB | 2.74 Mbps | 89.08 | 2.55 | 97.58 |
|   medium  |       12.16       | 21.24 MB | 2.82 Mbps | 88.88 | 2.56 | 97.57 |
|    fast   |       10.39       | 22.85 MB | 3.04 Mbps | 88.59 | 2.72 | 97.37 |
|   faster  |        8.37       | 21.11 MB | 2.80 Mbps | 88.66 | 2.83 | 97.18 |
|  veryfast |        5.78       | 17.71 MB | 2.35 Mbps | 84.75 | 4.00 | 95.18 |
| superfast |        3.83       | 34.95 MB | 4.64 Mbps | 88.52 | 3.19 | 96.71 |
| ultrafast |        2.34       | 49.38 MB | 6.56 Mbps | 90.03 | 2.11 | 98.24 |
+-----------+-------------------+----------+-----------+----------------------+
File Transcoded: aqp60.mkv
Bitrate: 12.34 Mbps
Encoder used for the transcodes: x264
CRF 23 was used.
Filter(s) used: None
n_subsample: 1
```
The following command was used to produce such a table:

`python main.py -ovp aqp60.mkv -p veryslow slower slow medium fast faster veryfast superfast ultrafast`

# Section Two: Features

**[1]:**

You already have a transcoded video (and the original) and you want the quality of the transcoded version to be calculated using the VMAF and (optionally) the SSIM and PSNR metrics. The values of the aforementioned quality metrics are saved in a table, in a file named *Table.txt*. VMAF/SSIM/PSNR graphs are created, which show the variation of the VMAF/SSIM/PSNR throughout the video.

Example: `python main.py -ntm -ovp original.mp4 -tvp transcoded.mp4 -ssim -psnr`

**[2]:**

Transcode a video using the x264 or x265 encoder and see the VMAF/SSIM/PSNR values that you get with the specified presets or CRF values. There are two modes; CRF comparison mode and presets comparison mode. You must specify multiple CRF values OR presets and this program will automatically transcode the video with each preset/CRF value, and the quality of each transcode is calculated using the VMAF and (optionally) the SSIM and PSNR metrics. 

**[2] CRF Comparison Mode Example:**

`python main.py -ovp original.mp4 -crf 18 19 20 -p veryfast -ssim -psnr`

*You must specify the CRF values that you want to compare and (optionally) **one** preset. If you do not specify a preset, the `medium` preset will be used.*

**[2] Presets Comparison Mode Example:**

`python main.py -ovp original.mp4 -p medium fast faster -crf 18 -ssim -psnr`

*You must specify the presets that you want to compare and (optionally) **one** CRF value. If you do specify a CRF value, a CRF of 23 will be used.*

**[2] Overview Mode:**

A recent addition to this program is "overview mode", which can be used with feature [2] by specifying the `--interval` and `--clip-length` arguments. The benefit of this mode is especially apparent with long videos, such as movies. What this mode does is create a lossless "overview video" by grabbing a `<clip length>` seconds long segment every `<interval>` seconds from the original video. The transcodes and computation of the quality metrics are done using this overview video instead of the original video. As the overview video can be much shorter than the original, the process of trancoding and computing the quality metrics is much quicker, while still being a fairly accurate representation of the original video as the program goes through the whole video and grabs, say, a two-second-long segment every 60 seconds. 
  
Example: `python main.py -ovp original.mp4 -crf 17 18 19 --interval 60 --clip-length 2`

In the example above, we're grabbing a two-second-long clip (`--clip-length 2`) every minute (`--interval 60`) in the video. These 2-second long clips are concatenated to make the overview video. A 1-hour long video is turned into an overview video that is 1 minute and 58 seconds long. The benefit of overview mode should now be clear - transcoding and computing the quality metrics of a <2 minutes long video is **much** quicker than doing so with an hour long video.

*An alternative method of reducing the execution time of this program is by only using the first x seconds of the original video (you can do this with the `-t` argument), but **Overview Mode** provides a better representation of the whole video.*

# Requirements
1. Python **3.6+**
2. `pip install -r requirements.txt`
3. FFmpeg and FFprobe installed and in your PATH (or in the same directory as this program). Your build of FFmpeg must have v2.1.1 (or above) of the libvmaf filter, and depending on the encoders that you wish to test, libx264, libx265 and libaom. You can check whether your build of FFmpeg has libvmaf/libx264/libx265/libaom by entering `ffmpeg -buildconf` in the terminal and looking for `--enable-libvmaf`, `--enable-libx265`, `--enable-libx264` and `--enable-libaom` under "configuration:".

FFmpeg builds that support all features of VQM:

**Windows:** https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-essentials.7z

**macOS:** https://evermeet.cx/ffmpeg/. You must download the snapshot build rather than the release build.

**Linux (kernels 3.2.0+):** https://johnvansickle.com/ffmpeg/. Download the **git** build. Installation instructions, as well as how to add FFmpeg and FFprobe to your PATH, can be found [here](https://www.johnvansickle.com/ffmpeg/faq/).

# Usage
You can find the output of `python main.py -h` below:
```
usage: main.py [-h] [--av1-cpu-used <1-8>] [-cl <1-60>] [-crf <0-51> [<0-51> ...]] [-dp DECIMAL_PLACES] [-e {x264,x265,libaom-av1}] [-i <1-600>] [-subsample SUBSAMPLE]
               [--n-threads N_THREADS] [-ntm] [-o OUTPUT_FOLDER] -ovp ORIGINAL_VIDEO_PATH [-p <preset/s> [<preset/s> ...]] [--phone-model] [-psnr] [-sc] [-ssim]
               [-t SECONDS] [-tvp TRANSCODED_VIDEO_PATH] [-vf VIDEO_FILTERS]

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
                        transcoded video paths must be specified using the -ovp and -tvp arguments, respectively. Example: python main.py -ntm -ovp original.mp4 -tvp
                        transcoded.mp4 (default: False)
  -o OUTPUT_FOLDER, --output-folder OUTPUT_FOLDER
                        Use this argument if you want a specific name for the output folder. If you want the name of the output folder to contain a space, the string must
                        be surrounded in double quotes (default: None)
  -ovp ORIGINAL_VIDEO_PATH, --original-video-path ORIGINAL_VIDEO_PATH
                        Enter the path of the original video. A relative or absolute path can be specified. If the path contains a space, it must be surrounded in double
                        quotes (default: None)
  -sc, --show-commands  Show the FFmpeg commands that are being run. (default: False)
  -t SECONDS, --encode-length SECONDS
                        Create a lossless version of the original video that is just the first x seconds of the video. This cut version of the original video is what will
                        be transcoded and used as the reference video. You cannot use this option in conjunction with the -i or -cl arguments (default: None)
  -tvp TRANSCODED_VIDEO_PATH, --transcoded-video-path TRANSCODED_VIDEO_PATH
                        The path of the transcoded video (only applicable when using the -ntm mode) (default: None)
  -vf VIDEO_FILTERS, --video-filters VIDEO_FILTERS
                        Add FFmpeg video filter(s). Each filter must be separated by a comma. Example: -vf bwdif=mode=0,crop=1920:800:0:140 (default: None)

Optional Metrics:
  -psnr, --calculate-psnr
                        Enable PSNR calculation in addition to VMAF (default: False)
  -ssim, --calculate-ssim
                        Enable SSIM calculation in addition to VMAF (default: False)
```

# About the model files
Two model files are provided, `vmaf_v0.6.1.json` and `vmaf_4k_v0.6.1.json`. There is also the phone model that can be enabled by using the `-pm` argument.

This program uses the `vmaf_v0.6.1.json` model file by default, which is "based on the assumption that the viewers sit in front of a 1080p display in a living room-like environment with the viewing distance of 3x the screen height (3H)."

The phone model was created because the original model "did not accurately reflect how a viewer perceives quality on a phone. In particular, due to smaller screen size and longer viewing distance relative to the screen height (>3H), viewers perceive high-quality videos with smaller noticeable differences. For example, on a mobile phone, there is less distinction between 720p and 1080p videos compared to other devices. With this in mind, we trained and released a VMAF phone model."

The 4K model (`vmaf_4k_v0.6.1.json`) "predicts the subjective quality of video displayed on a 4K TV and viewed from a distance of 1.5H. A viewing distance of 1.5H is the maximum distance for the average viewer to appreciate the sharpness of 4K content. The 4K model is similar to the default model in the sense that both models capture quality at the critical angular frequency of 1/60 degree/pixel. However, the 4K model assumes a wider viewing angle, which affects the foveal vs peripheral vision that the subject uses."

The source of the quoted text, plus additional information about VMAF (such as the correct way to calculate VMAF), can be found [here](https://netflixtechblog.com/vmaf-the-journey-continues-44b51ee9ed12).

- If you are transcoding a video that will be viewed on a mobile phone, you can add the `-pm` argument which will enable the [phone model](https://github.com/Netflix/vmaf/blob/master/resource/doc/models.md/#predict-quality-on-a-cellular-phone-screen).
- If you are transcoding a video that will be viewed on a 4K display, the default model (`vmaf_v0.6.1.json`) is fine if you are only interested in relative VMAF scores, i.e. the score differences between different presets/CRF values, but if you are interested in absolute scores, it may be better to use the 4K model file which was predicts the subjective quality of video displayed on a 4K screen at a distance of 1.5x the height of the screen. To use the 4K model, replace the value of the `vmaf_model_file_path` variable in libvmaf.py with `'vmaf_models/vmaf_4k_v0.6.1.json'`.
