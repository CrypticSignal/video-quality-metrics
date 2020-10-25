# What can this program do?
There are two main things that this program can do.

**Option 1:**

You already have a transcoded video (and the original) and you want the quality of the transcoded version to be calculated using the VMAF and (optionally) the SSIM and PSNR metrics.

**Option 2:**

Transcode a video using the x264 or x265 encoder (you can specify multiple CRF values OR presets and this program will automatically transcode the video with each preset/CRF value), and the quality of each transcode is calculated using the VMAF and (optionally) the SSIM and PSNR metrics. Other factors such as the time taken to transcode the video and the resulting filesize (with each preset/CRF value) are also calculated and saved in a table (Table.txt).

**With both options, the data is shown in a table (see the example at the bottom of this README) and graph(s) which show the frame-by-frame VMAF/SSIM/PSNR (this shows you the variation of the quality throughout the video). [Here's](CRF%2023.png) an example graph.**

*Click [here](https://trac.ffmpeg.org/wiki/Encode/H.264) to learn more about CRF values and presets.*

# You already have a transcoded video:

You already have a transcoded and original video, and you want to calculate the quality of the transcoded video using the VMAF and (optionally) the SSIM and PSNR metrics. The data is saved in a file named **Table.txt**, and a graph is also created which shows the variation of the VMAF/SSIM/PSNR throughout the video. The graph is saved as a PNG file.

Example: `python video-metrics.py -ntm -ovp original.mp4 -tvp transcoded.mp4 -ssim -psnr`

*(VMAF is calculated by default unless the `-dqs` argument is specified).*

# You want to transcode a video and calculate the quality achieved with different CRF values OR presets:
There are two options:

1. **Calculate the quality achieved with different *CRF values*:**

You want to calculate the quality achieved with certain CRF value. The program will automatically transcode the original video with every CRF value that you specify (using the `-crf` argument) without having to manually start a new transcode with a different CRF value. You must specify the CRF values that you want to compare and (optionally) **one** preset (if you don't want the default preset (medium) to be used). See the example below:

`python video-metrics.py -ovp original.mp4 -e x264 -crf 18 19 20 -p veryfast -ssim -psnr`

*(VMAF is calculated by default unless the `-dqs` argument is specified).*

**2. Calculate the quality achieved with different *presets*:**

You want to calculate the quality achieved with certain presets. The program will automatically transcode the original video with every preset that you specify (using the `-p` argument) without having to manually start a new encode with each preset. You must specify the presets that you want to compare and (optionally) **one** CRF value (if you don't want the default CRF value of 23 to be used). See the example below:

`python video-metrics.py -ovp original.mp4 -e x264 -p medium fast faster -crf 18 -ssim -psnr`

*(VMAF is calculated by default unless the `-dqs` argument is specified).*

Also, for each CRF value/preset that the video was encoded with, the following data is presented in a table and saved in a file named **Table.txt**:
1. Time taken to encode the video (in seconds)
2. Resulting filesize (MB)
3. Filesize compared to the original (as a percentage)
4. [Optional] Structural Similarity Index (SSIM) 
5. [Optional] Peak Signal-to-Noise-Ratio (PSNR)
6. [Video Multimethod Assessment Fusion (VMAF)](https://github.com/Netflix/vmaf) - a perceptual video quality assessment algorithm developed by Netflix.

**In addition to the above, a graph is created for each CRF value/preset that the video was encoded with, showing the variation of the SSIM, PSNR and VMAF throughout the encoded video. [Here's](CRF%2023.png) an example of the graph that is created.**

# Option 2 features:
- You can choose whether you want the whole video to be encoded or just a certain amount of seconds (using the `-t` argument).
- Choose whether you want the x264 (H.264/AVC) or x265 (H.265/HEVC) encoder to be used.
- You can specify whether you want the SSIM and/or PSNR to be calculated in addition to the VMAF. Or you can disable the computation of quality metrics entirely, if the only information you're interested in is the time taken to transcode and the resulting filesize.

# Usage:
```
usage: video-metrics.py [-h] -ovp ORIGINAL_VIDEO_PATH [-e {x264,x265}] [-crf CRF_VALUEs) [CRF_VALUE(s) ...]] [-p PRESET(s) [PRESET(s ...]] [-t ENCODING_TIME] [-pm]
                        [-dp <number of decimal places>] [-ssim] [-psnr] [-dqs] [-ntm] [-tvp TRANSCODED_VIDEO_PATH]
                          
If there is a space in the path, it must be surrounded with double quotes. Example:
python video-metrics.py -ovp "C:/Users/H/Desktop/my file.mp4" -p veryfast superfast

Available arguments:
  -h, --help            show this help message and exit
  -ovp ORIGINAL_VIDEO_PATH, --original-video-path ORIGINAL_VIDEO_PATH
                        Enter the path of the video. A relative or absolute path can be specified. If the path contains a space, it must be surrounded in double quotes. Example: -ovp
                        "C:/Users/H/Desktop/file 1.mp4"
  -e {x264,x265}, --video-encoder {x264,x265}
                        Specify the encoder to use. Must enter x264 or x265. Default: x264 Example: -e x265
  -crf CRF_VALUE(s) [CRF_VALUE(s) ...], --crf-value CRF_VALUE(s) [CRF_VALUE(s) ...]
                        Specify the CRF value(s) to use.
  -p PRESET(s) [PRESET(s) ...], --preset PRESET(s) [PRESET(s) ...]
                        Specify the preset(s) to use.
  -t ENCODING_TIME, --encoding-time ENCODING_TIME
                        Encode this many seconds of the video. If not specified, the whole video will get encoded.
  -pm, --phone-model    Enable VMAF phone model (default: False)
  -dp <number of decimal places>, --decimal-places <number of decimal places>
                        The number of decimal places to use for the data in the table (default: 3).
  -ssim, --calculate-ssim
                        Calculate SSIM in addition to VMAF.
  -psnr, --calculate-psnr
                        Calculate PSNR in addition to VMAF.
  -dqs, --disable-quality-stats
                        Disable calculation of PSNR, SSIM and VMAF; only show encoding time and filesize (improves completion time).
  -ntm, --no-transcoding-mode
                        Simply calculate the quality metrics of a transcoded video to the original.
  -tvp TRANSCODED_VIDEO_PATH, --transcoded-video-path TRANSCODED_VIDEO_PATH
                        The path of the transcoded video (only applicable when using the -ntm mode).
```
# Requirements:
- Python **3.6+**
- FFmpeg installed and in your PATH. Your build of FFmpeg must have `--enable-libvmaf` in the configuration (unless you don't care about the quality metrics and you specify `-dqs` when running this command line program). If you're on Windows, you can download an FFmpeg binary which has `--enable-libvmaf` in the configuration by clicking on [this](http://learnffmpeg.s3.amazonaws.com/ffmpeg-vmaf-static-bin.zip) link.
- The files **vmaf_v0.6.1.pkl** and **vmaf_v0.6.1.pkl.model** need to be in the same directory as video-metrics.py. These files are not needed if you only want the encoding time and filesize to be shown (you must specify `-dqs` in this case).
- `pip install -r requirements.txt`

# An example of the table that is saved:
The table is saved in a file named **Table.txt**. Here's an example of the table that is created when opting to compare presets:
```
You chose to encode a30.mkv using x264 with a CRF of 23.
+-----------+-------------------+----------+---------------------------+-------+------+-------+
|   Preset  | Encoding Time (s) |   Size   | Size Compared to Original |  PSNR | SSIM |  VMAF |
+-----------+-------------------+----------+---------------------------+-------+------+-------+
|    slow   |       31.65       | 11.58 MB |           71.87%          | 43.81 | 1.0  | 95.55 |
|   medium  |       22.57       | 12.07 MB |           74.93%          | 43.84 | 1.0  | 95.56 |
|    fast   |       18.83       | 12.49 MB |           77.5%           | 43.77 | 1.0  | 95.22 |
|   faster  |       14.58       | 11.79 MB |           73.17%          | 43.59 | 1.0  | 94.86 |
|  veryfast |        9.06       | 9.95 MB  |           61.77%          | 42.28 | 0.99 | 91.99 |
| superfast |        6.51       | 15.64 MB |           97.07%          | 43.46 | 1.0  | 94.43 |
| ultrafast |        4.24       | 31.89 MB |          197.95%          | 42.63 | 0.99 | 96.55 |
+-----------+-------------------+----------+---------------------------+-------+------+-------+
```
*Note: A video file with a length of 30 seconds was encoded.*

*Command: `python video-metrics.py -ovp a30.mkv -p slow medium fast faster veryfast superfast ultrafast -ssim -psnr`*
