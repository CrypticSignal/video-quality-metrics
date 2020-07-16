# Compare x264 or x265 presets
A command line program that automates the testing of x264 or x265 presets with FFmpeg. A for-loop is used to encode the chosen video with every preset from "veryslow" to "ultrafast. This saves you from manually having to start a new encode with each preset. Also, the time taken for each preset, the resulting file size and the product of the two is logged to a .txt file.
# Features
- Automatically encodes a video file with each preset ('veryslow', 'slower', 'slow', 'medium', 'fast', 'faster', 'veryfast', 'superfast' and 'ultrafast').

*If you want to change which presets are tested, simply edit the `presets` list in preset-comparer.py*
- Choose whether you want the libx264 or libx265 encoder to be used.
- Choose the CRF value to be used.
- You can choose whether you want the whole video to be encoded or just a certain amount of seconds.
- The time taken for each preset, the resulting file size and other data is saved to a .txt file.
- NEW: Compare VMAF.
# How to use
```
Arguments in square brackets are optional:
python compare-presets.py [-h] -path VIDEO_PATH -encoder {libx264,libx265} -crf CRF_VALUE [-t ENCODING_TIME] [-vmaf]

If there is a space in the path of filename, the path must be surrounded in double quotes. Example:
python compare-presets.py -path "C:/Users/H/Desktop/file 1.mp4" -encoder libx264 -crf 23 -t 60

optional arguments:
  -h, --help            show this help message and exit
  -path VIDEO_PATH, --video-path VIDEO_PATH
                        Enter the path of the video.
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
# Example
Below is an example of the type of .txt file that is produced. I chose to encode 5 seconds of the video:
```
You chose to encode trim2.mp4 for 5 seconds using libx264 with a CRF of 23.
+-----------+-------------------+---------+---------------------------+--------------------------+
|   Preset  | Encoding Time (s) |   Size  | Size Compared to Original | Product of Time and Size |
+-----------+-------------------+---------+---------------------------+--------------------------+
|  veryslow |       57.11       | 1.55 MB |           77.41%          |          88.67           |
|   slower  |       19.33       | 1.64 MB |           81.64%          |          31.65           |
|    slow   |       11.25       | 1.68 MB |           83.93%          |          18.93           |
|   medium  |        8.95       | 1.72 MB |           85.95%          |          15.43           |
|    fast   |        7.98       | 1.81 MB |           90.25%          |          14.44           |
|   faster  |        6.56       | 1.82 MB |           90.61%          |          11.92           |
|  veryfast |        4.33       | 1.64 MB |           82.01%          |           7.13           |
| superfast |        2.87       | 2.57 MB |          127.93%          |           7.35           |
| ultrafast |        1.86       | 3.52 MB |          175.59%          |           6.53           |
+-----------+-------------------+---------+---------------------------+--------------------------+
Time taken to encode with all presets: 120.2 seconds.
```
