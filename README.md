# Video Quality Metrics

**What kind of graph does this program produce?**

Graph(s) are created and saved as PNG files which show the variation of the VMAF/SSIM/PSNR values throughout the video. Here's an example:

![Example Graph](https://github.com/BassThatHertz/video-quality-metrics/blob/master/CRF%2023.png?raw=true)

**This program has two main features, and they will be referred to as [1] and [2].**

**[1]:**

You already have a transcoded video (and the original) and you want the quality of the transcoded version to be calculated using the VMAF and (optionally) the SSIM and PSNR metrics. The data is saved in a file named **Table.txt**, and a graph is also created which shows the variation of the VMAF/SSIM/PSNR throughout the video. The graph is saved as a PNG file.

Example: `python main.py -ntm -ovp original.mp4 -tvp transcoded.mp4 -ssim -psnr`

**[2]:**

Transcode a video using the x264 or x265 encoder and see the VMAF/SSIM/PSNR values that you get with different presets or CRF values. There are two modes; CRF comparison mode and presets comparison mode. You must specify multiple CRF values OR presets and this program will automatically transcode the video with each preset/CRF value, and the quality of each transcode is calculated using the VMAF and (optionally) the SSIM and PSNR metrics. Other factors such as the time taken to transcode the video and the resulting filesize are also shown in a table (Table.txt). [Here's](https://github.com/BassThatHertz/video-quality-metrics#example-table) an example. In addition to this, a graph is created for each preset/CRF value, showing the variation of the SSIM, PSNR and VMAF throughout the transcoded video.

**[2] (CRF comparison mode):**

You want to know the quality (VMAF/SSIM/PSNR) achieved with certain CRF values. The program will automatically transcode the original video with every CRF value that you specify (using the `-crf` argument) without having to manually start a new transcode with a different CRF value. You must specify the CRF values that you want to compare and (optionally) **one** preset (if you don't want the default preset (medium) to be used).

Example: `python main.py -ovp original.mp4 -crf 18 19 20 -p veryfast -ssim -psnr`

**[2] (presets comparison mode):**

You want to know the quality (VMAF/SSIM/PSNR) achieved with certain presets. The program will automatically transcode the original video with every preset that you specify (using the `-p` argument) without having to manually start a new encode with each preset. You must specify the presets that you want to compare and (optionally) **one** CRF value (if you don't want the default CRF value of 23 to be used).

Example: `python main.py -ovp original.mp4 -p medium fast faster -crf 18 -ssim -psnr`

# [2] Overview Mode:
A recent addition to this program is "overview mode", which can be used by specifying the `--interval` and `--clip-length` arguments. The benefit of this mode is especially apparent with long videos, such as movies. What this mode does is create a lossless "overview video" by grabbing a `<clip length>` seconds long segment every `<interval>` seconds from the original video. The transcodes and computation of the quality metrics are done using this overview video instead of the original video. As the overview video can be much shorter than the original, the process of trancoding and computing the quality metrics is much quicker, while still being a fairly accurate representation of the original video as the program goes through the whole video and grabs, say, a 2 seconds long segment every 60 seconds. 
  
Example: `python main.py -ovp original.mp4 -crf 17 18 19 --interval 60 --clip-length 2`

In the example above, we're grabbing 2 seconds (`--clip-length 2`) every minute (`--interval 60`) in the video. These 2-second long clips are concatenated to make the overview video. A 1-hour long video is turned into an overview video that is 1 minute and 58 seconds long. The benefit of overview mode should now be clear - transcoding and computing the quality metrics of a <2 minutes long video is **much** quicker than doing so with an hour long video.

*An alternative method of reducing the execution time of this program is by only using the first x seconds of the original video (you can do this with the `-t` argument), but **Overview Mode** provides a better representation of the whole video.*

# What data is shown in the table?
The following data is presented in a table and saved as a file named **Table.txt**:
- Time taken to transcode the video (in seconds). *Applicable to [2] only.*
- Filesize (MB).
- Filesize compared to the original video (as a percentage).
- [Video Multimethod Assessment Fusion (VMAF)](https://github.com/Netflix/vmaf) - a perceptual video quality assessment algorithm developed by Netflix.
- [Optional] Structural Similarity Index (SSIM). *You must use the `-ssim` argument.*
- [Optional] Peak Signal-to-Noise-Ratio (PSNR). *You must use the `-psnr` argument.*

# Requirements:
- Python **3.6+**
- `pip install -r requirements.txt`
- FFmpeg and FFprobe installed and in your PATH. Your build of FFmpeg must have `--enable-libvmaf` in the configuration (unless you don't care about the quality metrics and you specify `-dqm` when running this program). If you're on Windows, you can download an FFmpeg binary which has `--enable-libvmaf` in the configuration by clicking on [this](http://learnffmpeg.s3.amazonaws.com/ffmpeg-vmaf-static-bin.zip) link (FFprobe also included).

# Usage:
```
usage: main.py [-h] -ovp ORIGINAL_VIDEO_PATH [-e {x264,x265}] [-crf CRF_VALUEs) [CRF_VALUE(s) ...]]
               [-p PRESET(s) [PRESET(s ...]] [-i <an integer between 1 and 600>] [-cl <an integer between 1 and 60>]
               [-t ENCODING_TIME] [-pm] [-dp DECIMAL_PLACES] [-ssim] [-psnr] [-dqm] [-ntm]
               [-tvp TRANSCODED_VIDEO_PATH]
                          
Available arguments:
  -h, --help            show this help message and exit
  -ovp ORIGINAL_VIDEO_PATH, --original-video-path ORIGINAL_VIDEO_PATH
                        Enter the path of the original video. A relative or absolute path can be specified. If the path contains a space, it must be surrounded in double quotes.
                        Example: -ovp "C:/Users/H/Desktop/file 1.mp4"
  -e {x264,x265}, --video-encoder {x264,x265}
                        Specify the encoder to use (default: x264).
                        Example: -e x265
  -crf CRF_VALUE(s) [CRF_VALUE(s) ...], --crf-value CRF_VALUE(s) [CRF_VALUE(s) ...]
                        Specify the CRF value(s) to use.
  -p PRESET(s) [PRESET(s) ...], --preset PRESET(s) [PRESET(s) ...]
                        Specify the preset(s) to use.
  -i <an integer between 1 and 600>, --interval <an integer between 1 and 600>
                        Create a lossless overview video by grabbing a <cliplength> seconds long segment every <interval> seconds from the original video and use this overview video as the "original" video that the transcodes are compared with.
                        Example: -i 30
  -cl <an integer between 1 and 60>, --clip-length <an integer between 1 and 60>
                        Defines the length of the clips. Only applies when used with -i > 0. Default: 1.
                        Example: -cl 10
  -t ENCODING_TIME, --encoding-time ENCODING_TIME
                        Encode this many seconds of the video. If not specified, the whole video will get encoded. Only applies when -i is not set.Example: -t 60
  -pm, --phone-model    Enable VMAF phone model.
  -dp DECIMAL_PLACES, --decimal-places DECIMAL_PLACES
                        The number of decimal places to use for the data in the table (default: 2).
                        Example: -dp 3
  -ssim, --calculate-ssim
                        Calculate SSIM in addition to VMAF.
  -psnr, --calculate-psnr
                        Calculate PSNR in addition to VMAF.
  -dqm, --disable-quality-metrics
                        Disable calculation of PSNR, SSIM and VMAF; only show encoding time and filesize (improves completion time).
  -ntm, --no-transcoding-mode
                        Use this mode if you've already transcoded a video and would like its VMAF and (optionally) the SSIM and PSNR to be calculated.
                        Example: -ntm -tvp transcoded.mp4 -ovp original.mp4 -ssim -psnr
  -tvp TRANSCODED_VIDEO_PATH, --transcoded-video-path TRANSCODED_VIDEO_PATH
                        The path of the transcoded video (only applicable when using the -ntm mode).
```

# Example Table:
The table is saved as a file named **Table.txt**. Here's an example of the table that is created when opting to compare presets:
```
PSNR/SSIM/VMAF values are in the format: Min | Standard Deviation | Mean
Chosen CRF: 23
Original video bitrate: 12339 kbit/s
+-----------+-------------------+----------+-------------+----------------------+--------------------+----------------------+
|   Preset  | Encoding Time (s) |   Size   |   Bitrate   |         VMAF         |        SSIM        |         PSNR         |
+-----------+-------------------+----------+-------------+----------------------+--------------------+----------------------+
|    slow   |       20.64       | 25.44 MB | 3379 kbit/s | 88.79 | 2.56 | 97.58 | 0.99 | 0.00 | 0.99 | 38.10 | 1.66 | 42.89 |
|   medium  |       12.96       | 26.04 MB | 3458 kbit/s | 88.77 | 2.55 | 97.58 | 0.99 | 0.00 | 0.99 | 38.11 | 1.70 | 42.98 |
|    fast   |       11.50       | 27.65 MB | 3672 kbit/s | 88.66 | 2.71 | 97.38 | 0.99 | 0.00 | 0.99 | 38.14 | 1.72 | 43.07 |
|   faster  |        9.09       | 25.93 MB | 3444 kbit/s | 88.78 | 2.84 | 97.18 | 0.99 | 0.00 | 0.99 | 38.02 | 1.72 | 43.02 |
|  veryfast |        5.89       | 22.53 MB | 2993 kbit/s | 84.33 | 4.00 | 95.17 | 0.99 | 0.00 | 0.99 | 37.10 | 1.75 | 42.16 |
| superfast |        3.96       | 39.77 MB | 5282 kbit/s | 88.55 | 3.19 | 96.72 | 0.99 | 0.00 | 0.99 | 36.54 | 2.05 | 43.03 |
| ultrafast |        2.50       | 54.20 MB | 7198 kbit/s | 90.04 | 2.10 | 98.26 | 0.99 | 0.00 | 0.99 | 36.35 | 1.92 | 42.17 |
+-----------+-------------------+----------+-------------+----------------------+--------------------+----------------------+
```
*A 60 seconds long video was transcoded. Command: `python main.py -ovp aqp60.mkv -p slow medium fast faster veryfast superfast ultrafast -ssim -psnr`*

# About the model files:
As you may have noticed, there are two types of model files; original and 4K versions. There is also the phone model that can be enabled by using the `-pm` argument.

This program uses the original model by default, which is "based on the assumption that the viewers sit in front of a 1080p display in a living room-like environment with the viewing distance of 3x the screen height (3H)".

The phone model was created because the original model "did not accurately reflect how a viewer perceives quality on a phone. In particular, due to smaller screen size and longer viewing distance relative to the screen height (>3H), viewers perceive high-quality videos with smaller noticeable differences. For example, on a mobile phone, there is less distinction between 720p and 1080p videos compared to other devices. With this in mind, we trained and released a VMAF phone model."

The 4K model "predicts the subjective quality of video displayed on a 4K TV and viewed from a distance of 1.5H. A viewing distance of 1.5H is the maximum distance for the average viewer to appreciate the sharpness of 4K content. The 4K model is similar to the default model in the sense that both models capture quality at the critical angular frequency of 1/60 degree/pixel. However, the 4K model assumes a wider viewing angle, which affects the foveal vs peripheral vision that the subject uses."

The source of the quoted text, plus more information about VMAF (such as the correct way to calculate VMAF), can be found [here](https://netflixtechblog.com/vmaf-the-journey-continues-44b51ee9ed12).

- If you are transcoding for content that will be viewed on a mobile phone, you should add the `-pm` argument when using this command line program.
- If you are transcoding for content that will be viewed on a 4K display, replace `"model_path": "vmaf_v0.6.1.pkl",` in the `run_libvmaf` function in main.py with `"model_path": "vmaf_4k_v0.6.1.pkl"`.
