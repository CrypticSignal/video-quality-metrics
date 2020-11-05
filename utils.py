from ffmpeg import probe
import math

def GetBitrate(videofile):
	videofileprobe = probe(videofile)
	format = videofileprobe['format']
	bitrate = format['bit_rate']
	return f'{math.trunc(int(bitrate) / 1000)} kbits/s'
