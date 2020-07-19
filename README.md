# Compare x264 or x265 presets
A command line program that automates the testing of x264 or x265 presets with FFmpeg. A for-loop is used to encode the chosen video with the specified preset(s) (you can choose from: 'veryslow', 'slower', 'slow', 'medium', 'fast', 'faster', 'veryfast', 'superfast' and 'ultrafast'). This saves you from manually having to start a new encode with each preset. The time taken for each preset, the resulting filesize, the filesize compared to the original (as a percentage) and (optionally) the VMAF value of each encode is presented in a table. 
# Features
- Automatically encodes a video file with the specified preset(s).
- Choose whether you want the libx264 or libx265 encoder to be used.
- Choose the CRF value to be used.
- You can choose whether you want the whole video to be encoded or just a certain amount of seconds.
- The time taken for each preset, the resulting filesize, the filesize compared to the original (as a percentage) and (optionally) the VMAF value of each encode is presented in a table.
# How to use
```
Arguments in square brackets are optional:
python compare-presets.py [-h] -f VIDEO_PATH [-e {libx264,libx265}] [-crf CRF_VALUE] [-t ENCODING_TIME] -p presets [presets ...] [-vmaf]

If there is a space in the path, it must be surrounded with double quotes. Example:
python compare-presets.py -f "C:/Users/H/Desktop/file 1.mp4" -p veryfast superfast

optional arguments:
  -h, --help            show this help message and exit
  -f VIDEO_PATH, --video-path VIDEO_PATH
                        Enter the path of the video. A relative or absolute path can be specified.If the path contains a space, it must be surrounded in double quotes.
                        Example: -f "C:/Users/H/Desktop/file 1.mp4"
  -e {libx264,libx265}, --video-encoder {libx264,libx265}
                        Specify the encoder to use. Must enter libx264 or libx265. Default: libx264
                        Example: -e libx265
  -crf CRF_VALUE, --crf-value CRF_VALUE
                        Enter the CRF value to be used. Default: 23
  -t ENCODING_TIME, --encoding-time ENCODING_TIME
                        Encode this many seconds of the video. If not specified, the whole video will get encoded.
  -p presets [presets ...], --presets presets [presets ...]
                        List the presets you want to be tested (separated by a space).
                        Choose from: 'veryslow', 'slower', 'slow', 'medium', 'fast', 'faster', 'veryfast', 'superfast', 'ultrafast'
                        Example: -p fast veryfast ultrafast
  -vmaf, --calculate-vmaf
                        Specify this argument if you want the VMAF value to be calculated for each preset. (drastically increases completion time)
```
# Requirements
- Python 3.6+
- FFmpeg installed and in your PATH. The build of FFmpeg must have `--enable-libvmaf` in the configuration. If you're on Windows, you can download a compatible FFmpeg binary by clicking on [this](http://learnffmpeg.s3.amazonaws.com/ffmpeg-vmaf-static-bin.zip) link.
- The files **vmaf_v0.6.1.pkl** and **vmaf_v0.6.1.pkl.model** need to be in the same directory as compare-presets.py
# Example
The table is saved in a .txt file. Here's an example of the table that is produced:
```
You chose to encode aqp60.mkv using libx264 with a CRF of 23.
+-----------+-------------------+----------+---------------------------+--------------------------+-------+
|   Preset  | Encoding Time (s) |   Size   | Size Compared to Original | Product of Time and Size |  VMAF |
+-----------+-------------------+----------+---------------------------+--------------------------+-------+
|    slow   |       71.36       | 24.95 MB |           26.86%          |         1780.55          | 97.55 |
|   medium  |       49.72       | 25.64 MB |           27.6%           |         1274.53          | 97.55 |
|    fast   |       42.29       | 27.27 MB |           29.36%          |         1153.51          | 97.34 |
|   faster  |       33.48       | 25.66 MB |           27.62%          |          858.81          | 97.12 |
|  veryfast |       21.51       | 22.1 MB  |           23.79%          |          475.38          | 95.08 |
| superfast |        15.8       | 39.41 MB |           42.43%          |          622.9           | 96.75 |
| ultrafast |       10.03       | 53.61 MB |           57.71%          |          537.63          | 98.26 |
+-----------+-------------------+----------+---------------------------+--------------------------+-------+
```
*Note: A 1 minute long file was encoded.*

*Command: `python compare-presets.py -f aqp60.mkv -p slow medium fast faster veryfast superfast ultrafast -vmaf`*
