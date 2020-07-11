# x264 preset comparer
A command line program that automates the testing of x264 presets with FFmpeg. A for-loop is used to encode the chosen video with every preset from "veryslow" to "ultrafast. This saves you from manually having to start a new encode with each preset. Also, the time taken for each preset, the resulting file size and the product of the two is logged to a .txt file.
# Features
- Automatically encodea your chosen video file with each preset from "veryslow" to "ultrafast". 
- Choose the CRF value to be used.
- You can choose to only encode x seconds of the video, if you want to save time.
- The time taken for each preset, the resulting file size and the product of the two is logged to a .txt file.

*If you want to change which presets are tested, simply edit the `presets` list in preset-comparer.py*
# How it works
- You are asked to choose a video file (you are presented with a list of video files in the directory that preset-comparer.py is in). Therefore, you should move the .py file to the directory that the video file that you want to encode is in.
- You are asked to choose a CRF value that you want to be used.
- You can specify whether you want the whole file to be encoded or only a certain amount of seconds.
# Log file example
Below is an example of the type of log file that is produced. In this example, I chose to encode 5 seconds of the video:
```
You chose to encode trim2.mp4 for 5 seconds with a CRF of 18.
The last column shows the product of filesize and time, where a lower value is better.
veryslow | 52.767 seconds | 2.132 MB | 112.514 
slower | 58.584 seconds | 2.289 MB | 134.121 
slow | 20.951 seconds | 2.434 MB | 51.0 
medium | 17.487 seconds | 2.498 MB | 43.676 
fast | 13.971 seconds | 2.639 MB | 36.873 
faster | 11.478 seconds | 2.688 MB | 30.856 
veryfast | 5.553 seconds | 2.592 MB | 14.395 
superfast | 3.657 seconds | 4.448 MB | 16.265 
ultrafast | 1.826 seconds | 5.921 MB | 10.812
```
# Requirements
- Python 3.6+
- FFmpeg installed and in your PATH.
