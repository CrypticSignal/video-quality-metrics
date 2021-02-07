# Video Quality Metrics (VQM)

**What kind of graphs does this program produce?**

Graphs are created and saved as PNG files which show the variation of the VMAF/SSIM/PSNR throughout the video. Here's a VMAF graph as an example:

![Example Graph](https://github.com/BassThatHertz/video-quality-metrics/blob/master/Example%20Graphs/VMAF.png)

*Example SSIM and PSNR graphs can be found in the [Example Graphs folder](https://github.com/BassThatHertz/video-quality-metrics/tree/master/Example%20Graphs).*

**This program has two main features, and they will be referred to as [1] and [2].**

**[1]:**

You already have a transcoded video (and the original) and you want the quality of the transcoded version to be calculated using the VMAF and (optionally) the SSIM and PSNR metrics. The values of the aforementioned quality metrics are saved in a table, in a file named *Table.txt*. A VMAF graph is created (and SSIM/PSNR graphs, if the `-ssim` and `-psnr` arguments are specified) which shows the variation of the VMAF/SSIM/PSNR throughout the video. The graph(s) are saved as PNG files.

Example: `python main.py -ntm -ovp original.mp4 -tvp transcoded.mp4 -ssim -psnr`

**[2]:**

Transcode a video using the x264 or x265 encoder and see the VMAF/SSIM/PSNR values that you get with the specified presets or CRF values. There are two modes; CRF comparison mode and presets comparison mode. You must specify multiple CRF values OR presets and this program will automatically transcode the video with each preset/CRF value, and the quality of each transcode is calculated using the VMAF and (optionally) the SSIM and PSNR metrics. These metrics are saved in a table, in a file named *Table.txt*. [Here's](https://github.com/BassThatHertz/video-quality-metrics#example-table) an example table. In addition to this, VMAF/SSIM/PSNR graphs are created for each preset/CRF value, showing the variation of the quality metric throughout the video.

**[2] CRF Comparison Mode Example:**

`python main.py -ovp original.mp4 -crf 18 19 20 -p veryfast -ssim -psnr`

*You must specify the CRF values that you want to compare and (optionally) **one** preset. If you do not specify a preset, the `medium` preset will be used.*

**[2] Presets Comparison Mode Example:**

`python main.py -ovp original.mp4 -p medium fast faster -crf 18 -ssim -psnr`

*You must specify the presets that you want to compare and (optionally) **one** CRF value. If you do specify a CRF value, a CRF of 23 will be used.*

To see example graphs (which are created whether feature [1] or [2] is used), check out the [Example Graphs](https://github.com/BassThatHertz/video-quality-metrics/tree/master/Example%20Graphs) folder.

# [2] Overview Mode:
A recent addition to this program is "overview mode", which can be used with feature [2] by specifying the `--interval` and `--clip-length` arguments. The benefit of this mode is especially apparent with long videos, such as movies. What this mode does is create a lossless "overview video" by grabbing a `<clip length>` seconds long segment every `<interval>` seconds from the original video. The transcodes and computation of the quality metrics are done using this overview video instead of the original video. As the overview video can be much shorter than the original, the process of trancoding and computing the quality metrics is much quicker, while still being a fairly accurate representation of the original video as the program goes through the whole video and grabs, say, a 2 seconds long segment every 60 seconds. 
  
Example: `python main.py -ovp original.mp4 -crf 17 18 19 --interval 60 --clip-length 2`

In the example above, we're grabbing a two-second-long clip (`--clip-length 2`) every minute (`--interval 60`) in the video. These 2-second long clips are concatenated to make the overview video. A 1-hour long video is turned into an overview video that is 1 minute and 58 seconds long. The benefit of overview mode should now be clear - transcoding and computing the quality metrics of a <2 minutes long video is **much** quicker than doing so with an hour long video.

*An alternative method of reducing the execution time of this program is by only using the first x seconds of the original video (you can do this with the `-t` argument), but **Overview Mode** provides a better representation of the whole video.*

# What data is shown in the table?
The following data is presented in a table and saved as a file named *Table.txt*:
- Time taken to transcode the video (in seconds). *Applicable to feature [2] only.*
- Filesize (MB)
- Bitrate (Mbps)
- Filesize compared to the original video (as a percentage).
- [Video Multimethod Assessment Fusion (VMAF)](https://github.com/Netflix/vmaf) values. VMAF is a perceptual video quality assessment algorithm developed by Netflix.
- [Optional] Structural Similarity Index (SSIM). *You must use the `-ssim` argument.*
- [Optional] Peak Signal-to-Noise-Ratio (PSNR). *You must use the `-psnr` argument.*

# Requirements:
1. Python **3.6+**
2. `pip install -r requirements.txt`
3. FFmpeg and FFprobe installed and in your PATH (or in the same directory as this program). Your build of FFmpeg must have v2.1.1 (or above) of the libvmaf filter, and depending on the encoders that you wish to test, libx264, libx265 and libaom. You can check whether your build of FFmpeg has libvmaf/libx264/libx265/libaom by entering `ffmpeg -buildconf` in the terminal and looking for `--enable-libvmaf`, `--enable-libx265`, `--enable-libx264` and `--enable-libaom` under "configuration:".

FFmpeg builds that support all features of VQM:

**Windows:** https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-essentials.7z

**macOS:** https://evermeet.cx/ffmpeg/. You must download the snapshot build rather than the release build.

**Linux (kernels 3.2.0+):** https://johnvansickle.com/ffmpeg/. Download the **git** build. Installation instructions, as well as how to add FFmpeg and FFprobe to your PATH, can be found [here](https://www.johnvansickle.com/ffmpeg/faq/).

# Usage:
```
usage: main.py [-h] [--av1-cpu-used {1,2,3,4,5,6,7,8}] [-cl <an integer between 1 and 60>] [-crf CRF_VALUEs) [CRF_VALUE(s) ...]] [-dp DECIMAL_PLACES] [-e {x264,x265,av1}]
               [-i <an integer between 1 and 600>] [-n x] [-ntm] [-o OUTPUT_FOLDER] -ovp ORIGINAL_VIDEO_PATH [-pm] [-p PRESET(s) [PRESET(s ...]] [-psnr] [-sc] [-ssim] [-t x]
               [--threads x] [-tvp TRANSCODED_VIDEO_PATH] [-vf VIDEO_FILTERS]

Available arguments:
  -h, --help            show this help message and exit
  --av1-cpu-used {1,2,3,4,5,6,7,8}
                        Only applicable if choosing the AV1 encoder. Set the quality/encoding speed tradeoff.
                        Lower values mean slower encoding but better quality, and vice-versa.
                        If this argument is not specified, the value will be set to 5.
  -cl <an integer between 1 and 60>, --clip-length <an integer between 1 and 60>
                        Defines the length of the clips (default: 1). Only applies when used with -i > 0.
                        Example: -cl 2
  -crf CRF_VALUE(s) [CRF_VALUE(s) ...], --crf-value CRF_VALUE(s) [CRF_VALUE(s) ...]
                        Specify the CRF value(s) to use.
  -dp DECIMAL_PLACES, --decimal-places DECIMAL_PLACES
                        The number of decimal places to use for the data in the table (default: 2).
                        Example: -dp 3
  -e {x264,x265,av1}, --video-encoder {x264,x265,av1}
                        Specify the encoder to use (default: x264).
  -i <an integer between 1 and 600>, --interval <an integer between 1 and 600>
                        Create a lossless overview video by grabbing a <cliplength> seconds long segment every <interval> seconds from the original video and use this overview video as the "original" video that the transcodes are compared with.
                        Example: -i 30
  -n x, --subsample x   Set a value for libvmaf's n_subsample option if you only want the VMAF/SSSIM to be calculated for every nth frame.
                        Without this argument, VMAF/SSIM scores will be calculated for every frame.
                        Example: -n 24
  -ntm, --no-transcoding-mode
                        Enable "no transcoding mode", which allows you to calculate the VMAF/SSIM/PSNR for a video that you have already transcoded.
                        The original and transcoded video paths must be specified using the -ovp and -tvp arguments, respectively.
                        Example: python main.py -ntm -ovp original.mp4 -tvp transcoded.mp4 -ssim
  -o OUTPUT_FOLDER, --output-folder OUTPUT_FOLDER
                        Use this argument if you want a specific name for the output folder.
                        If you want the name of the output folder to contain a space, the string must be surrounded in double quotes.
                        Example: -o "VQM Output"
  -ovp ORIGINAL_VIDEO_PATH, --original-video-path ORIGINAL_VIDEO_PATH
                        Enter the path of the original video. A relative or absolute path can be specified. If the path contains a space, it must be surrounded in double quotes.
                        Example: -ovp "C:/Users/H/Desktop/file 1.mp4"
  -pm, --phone-model    Enable VMAF phone model.
  -p PRESET(s) [PRESET(s) ...], --preset PRESET(s) [PRESET(s) ...]
                        Specify the preset(s) to use.
  -psnr, --calculate-psnr
                        Enable PSNR calculation in addition to VMAF (default: disabled).
  -sc, --show-commands  Show the FFmpeg commands that are being run.
  -ssim, --calculate-ssim
                        Enable SSIM calculation in addition to VMAF (default: disabled).
  -t x, --encode-length x
                        Create a lossless version of the original video that is just the first x seconds of the video. This cut version of the original video is what will be transcoded and used as the reference video. You cannot use this option in conjunction with the -i or -cl arguments.
                        Example: -t 60
  --threads x           Set the number of threads to be used when computing VMAF.
                        The default is set to what Python's os.cpu_count() method returns. For example, on a dual-core Intel CPU with hyperthreading, the default will be set to 4.       
                        Example: --threads 2
  -tvp TRANSCODED_VIDEO_PATH, --transcoded-video-path TRANSCODED_VIDEO_PATH
                        The path of the transcoded video (only applicable when using the -ntm mode).
  -vf VIDEO_FILTERS, --video-filters VIDEO_FILTERS
                        Add FFmpeg video filter(s). Each filter must be separated by a comma.
                        Example: -vf bwdif=mode=0,crop=1920:800:0:140
```

# Example Table:
This program creates a file named *Table.txt*. Here's an example of what that file will contain when opting to compare presets:
```
+-------------------------------------------------------------------------------+
|        VMAF values are in the format: Min | Standard Deviation | Mean         |
+-----------+-------------------+----------+-------------+----------------------+
|   Preset  | Encoding Time (s) |   Size   |   Bitrate   |         VMAF         |
+-----------+-------------------+----------+-------------+----------------------+
|    slow   |       20.64       | 25.44 MB | 3.379 Mbps  | 88.79 | 2.56 | 97.58 |
|   medium  |       12.96       | 26.04 MB | 3.458 Mbps  | 88.77 | 2.55 | 97.58 |
|    fast   |       11.50       | 27.65 MB | 3.672 Mbps  | 88.66 | 2.71 | 97.38 |
|   faster  |        9.09       | 25.93 MB | 3.444 Mbps  | 88.78 | 2.84 | 97.18 |
|  veryfast |        5.89       | 22.53 MB | 2.993 Mbps  | 84.33 | 4.00 | 95.17 |
| superfast |        3.96       | 39.77 MB | 5.282 Mbps  | 88.55 | 3.19 | 96.72 |
+-----------+-------------------+----------+-------------+----------------------+
File Transcoded: aqp60.mkv
Bitrate: 12.339 Mbps
Encoder used for the transcodes: x264
CRF 23 was used.
```
*The `-ssim` and `-psnr` arguments were not specified. Command: `python main.py -ovp aqp60.mkv -p slow medium fast faster veryfast superfast`*

# About the model files:
As you may have noticed, two model files have been provided. `vmaf_v0.6.1.json` and `vmaf_4k_v0.6.1.json`. There is also the phone model that can be enabled by using the `-pm` argument.

This program uses the `vmaf_v0.6.1.json` model by default, which is "based on the assumption that the viewers sit in front of a 1080p display in a living room-like environment. All the subjective data were collected in such a way that the distorted videos (with native resolutions of 1080p, 720p, 480p etc.) get rescaled to 1080 resolution and shown on the 1080p display with a viewing distance of three times the screen height (3H)."

The phone model was created because the original model "did not accurately reflect how a viewer perceives quality on a phone. In particular, due to smaller screen size and longer viewing distance relative to the screen height (>3H), viewers perceive high-quality videos with smaller noticeable differences. For example, on a mobile phone, there is less distinction between 720p and 1080p videos compared to other devices. With this in mind, we trained and released a VMAF phone model."

The 4K model (`vmaf_4k_v0.6.1.json`) "predicts the subjective quality of video displayed on a 4K TV and viewed from a distance of 1.5H. A viewing distance of 1.5H is the maximum distance for the average viewer to appreciate the sharpness of 4K content. The 4K model is similar to the default model in the sense that both models capture quality at the critical angular frequency of 1/60 degree/pixel. However, the 4K model assumes a wider viewing angle, which affects the foveal vs peripheral vision that the subject uses."

The source of the quoted text, plus more information about VMAF (such as the correct way to calculate VMAF), can be found [here](https://netflixtechblog.com/vmaf-the-journey-continues-44b51ee9ed12).

- If you are transcoding a video that will be viewed on a mobile phone, you can add the `-pm` argument which will enable the [phone model](https://github.com/Netflix/vmaf/blob/master/resource/doc/models.md/#predict-quality-on-a-cellular-phone-screen).
- If you are transcoding a video that will be viewed on a 4K display, the default model (`vmaf_v0.6.1.json`) is fine if you are only interested in relative VMAF scores, i.e. the score differences between different presets/CRF values, but if you are interested in absolute scores, it may be better to use the 4K model file which was predicts the subjective quality of video displayed on a 4K screen at a distance of 1.5x the height of the screen. To use the 4K model, replace the value of the `vmaf_model_file_path` variable in libvmaf.py with `'vmaf_models/vmaf_4k_v0.6.1.json'`.
