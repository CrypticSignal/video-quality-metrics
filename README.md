# Compare x264 or x265 presets
A command line program that automates the testing of x264 or x265 presets with FFmpeg. A for-loop is used to encode the chosen video with every preset apart from 'placebo' ('veryslow', 'slower', 'slow', 'medium', 'fast', 'faster', 'veryfast', 'superfast' and 'ultrafast'). This saves you from manually having to start a new encode with each preset. The time taken for each preset, the resulting filesize, the filesize compared to the original (as a percentage) and (optionally) the VMAF value of each encode is presented in a table. **You can change the presets that are tested by editing the list on line 2 of compare-presets.py**. 
# Features
- Automatically encodes a video file with each preset ('veryslow', 'slower', 'slow', 'medium', 'fast', 'faster', 'veryfast', 'superfast' and 'ultrafast').

*If you want to change which presets are tested, simply edit the `presets` list on line 2 of preset-comparer.py*
- Choose whether you want the libx264 or libx265 encoder to be used.
- Choose the CRF value to be used.
- You can choose whether you want the whole video to be encoded or just a certain amount of seconds.
- The time taken for each preset, the resulting filesize, the filesize compared to the original (as a percentage) and (optionally) the VMAF value of each encode is presented in a table.
# How to use
```
Arguments in square brackets are optional:
python compare-presets.py [-h] -path VIDEO_PATH -encoder {libx264,libx265} -crf CRF_VALUE [-t ENCODING_TIME] [-vmaf]

If there is a space in the path, it must be surrounded with double quotes. Example:
python compare-presets.py -path "C:/Users/H/Desktop/file 1.mp4" -encoder libx264 -crf 23 -t 60

optional arguments:
  -h, --help            show this help message and exit
  -path VIDEO_PATH, --video-path VIDEO_PATH
                        Enter the path of the video. A relative or absolute path can be specified. If the path contains a space, it must be surrounded with double quotes.
  -encoder {libx264,libx265}, --video-encoder {libx264,libx265}
                        Specify the encoder to use. Must enter libx264 or libx265
  -crf CRF_VALUE, --crf-value CRF_VALUE
                        Enter the CRF value to be used.
  -t ENCODING_TIME, --encoding-time ENCODING_TIME
                        Encode this many seconds of the video. If not specified, the whole video will get encoded.
  -vmaf, --calculate-vmaf
                        Specify this argument if you want the VMAF value to be calculated for each preset. (drastically increases completion time)

optional arguments:
  -h, --help            show this help message and exit
  -path VIDEO_PATH, --video-path VIDEO_PATH
                        Enter the path of the video.
  -encoder {libx264,libx265}, --video-encoder {libx264,libx265}
                        Specify the encoder to use. Must enter libx264 or libx265
  -crf CRF_VALUE, --crf-value CRF_VALUE
                        Enter the CRF value to be used.
  -t ENCODING_TIME, --encoding-time ENCODING_TIME
                        Encode this many seconds of the video.
  -vmaf, --calculate-vmaf
                        Specify this argument if you want the VMAF value to be calculated for each preset. (drastically increases completion time)
```
# Requirements
- Python 3.6+
- FFmpeg installed and in your PATH. The build of FFmpeg must have `--enable-libvmaf` in the configuration. If you're on Windows, you can download a compatible FFmpeg binary by clicking on [this](http://learnffmpeg.s3.amazonaws.com/ffmpeg-vmaf-static-bin.zip) link.
- `pip install PrettyTable`
- The files **vmaf_v0.6.1.pkl** and **vmaf_v0.6.1.pkl.model** need to be in the same directory as compare-presets.py
# Example
The table is saved in a .txt file. Here's an example of the type of .txt file that is produced. In this example, I chose to encode only with the presets from 'slow' onwards:
```
You chose to encode aqp.mkv using libx264 with a CRF of 23.
+-----------+-------------------+----------+---------------------------+--------------------------+-------+
|   Preset  | Encoding Time (s) |   Size   | Size Compared to Original | Product of Time and Size |  VMAF |
+-----------+-------------------+----------+---------------------------+--------------------------+-------+
|    slow   |       228.54      | 28.09 MB |           25.45%          |         6419.36          | 88.03 |
|   medium  |       162.43      | 28.75 MB |           26.05%          |          4670.3          | 88.01 |
|    fast   |       117.7       | 30.36 MB |           27.51%          |         3573.64          | 87.82 |
|   faster  |       97.84       | 28.47 MB |           25.79%          |         2785.08          |  87.6 |
|  veryfast |       52.06       | 24.59 MB |           22.28%          |         1279.98          | 85.75 |
| superfast |       38.99       | 45.58 MB |           41.3%           |         1777.32          | 87.24 |
| ultrafast |       25.45       | 60.17 MB |           54.52%          |         1531.35          | 88.81 |
+-----------+-------------------+----------+---------------------------+--------------------------+-------+
```
