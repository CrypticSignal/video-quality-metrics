# What does this program do?
This command line program encodes a video file (using the x264 or x265 encoder) with every specified preset without having to manually start a new encode with each preset. Also, for every preset that the video was encoded with, the following data is presented in a table and saved as a file named "Table.txt":
1. Time taken to encode the video (in seconds)
2. Resulting filesize (MB)
3. Filesize compared to the original (as a percentage)
4. Structural Similarity Index (SSIM) 
5. Peak Signal-to-Noise-Ratio (PSNR)
6. [Video Multimethod Assessment Fusion (VMAF)](https://github.com/Netflix/vmaf) - a perceptual video quality assessment algorithm developed by Netflix.

- In addition to the above, a graph is created for each preset that the video was encoded with, showing the variation of the SSIM, PSNR and VMAF throughout the encoded video. [Here's](example-graph.png) an example of the graph that is created.

# Options:
- Choose whether you want the x264 (H.264/AVC) or x265 (H.265/HEVC) encoder to be used.
- Choose the CRF value to be used.
- You can choose whether you want the whole video to be encoded or just a certain amount of seconds.

# Usage:
```
Arguments in square brackets are optional:
usage: python compare-presets.py [-h] -f VIDEO_PATH [-e {libx264,libx265}] [-crf CRF_VALUE] [-t ENCODING_TIME] -p presets
                          [presets ...] [-pm] [-dp DECIMAL_PLACES] [-dqs]
                          
If there is a space in the path, it must be surrounded with double quotes. Example:
python compare-presets.py -f "C:/Users/H/Desktop/my file.mp4" -p veryfast superfast

optional arguments:
  -h, --help            show this help message and exit
  -f VIDEO_PATH, --video-path VIDEO_PATH
                        Enter the path of the video. A relative or absolute path can be specified.If the path contains a space, it must be surrounded in double quotes.
                        Example: -f "C:/Users/H/Desktop/my file.mp4"
  -e {libx264,libx265}, --video-encoder {libx264,libx265}
                        Specify the encoder to use. Must enter libx264 or libx265. Default: libx264
                        Example: -e libx265
  -crf CRF_VALUE, --crf-value CRF_VALUE
                        Enter the CRF value to be used (default: 23)
  -t ENCODING_TIME, --encoding-time ENCODING_TIME
                        Encode this many seconds of the video. If not specified, the whole video will get encoded.
  -p presets [presets ...], --presets presets [presets ...]
                        List the presets you want to be tested (separated by a space).
                        Choose from: 'veryslow', 'slower', 'slow', 'medium', 'fast', 'faster', 'veryfast', 'superfast', 'ultrafast'
                        Example: -p fast veryfast ultrafast
  -pm, --phone-model    Enable VMAF phone model (default: False)
  -dp DECIMAL_PLACES, --decimal-places DECIMAL_PLACES
                        The number of decimal places to use for the data in the table (default: 3)
  -dqs, --disable-quality-stats
                        Disable calculation of PSNR, SSIM and VMAF; only show encoding time and filesize (improves completion time).
```

# Requirements:
- Python **3.6+**
- FFmpeg installed and in your PATH. The build of FFmpeg must have `--enable-libvmaf` in the configuration (unless you don't care about the quality metrics and you specify `-dqs` when running this command line program). If you're on Windows, you can download an FFmpeg binary which has `--enable-libvmaf` in the configuration by clicking on [this](http://learnffmpeg.s3.amazonaws.com/ffmpeg-vmaf-static-bin.zip) link.
- The files **vmaf_v0.6.1.pkl** and **vmaf_v0.6.1.pkl.model** need to be in the same directory as compare-presets.py. These files are not needed if you only want the encoding time and filesize to be shown (you must specify `-dqs` in this case).
- `pip install -r requirements.txt`

# An example of the table that is saved:
The table is saved in a .txt file. Here's an example of the table that is produced:
```
You chose to encode a30.mkv using libx264 with a CRF of 23.
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

*Command: `python compare-presets.py -f a30.mkv -p slow medium fast faster veryfast superfast ultrafast`*
