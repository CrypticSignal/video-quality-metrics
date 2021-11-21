import subprocess

from tqdm import tqdm

from utils import line, Logger, VideoInfoProvider

log = Logger('factory')


class EncodingArguments():
    def __init__(self, infile, encoder, outfile):
        self._infile = infile
        self._encoder = encoder
        self._outfile = outfile
        self._base_ffmpeg_arguments = ["-i", self._infile]

    # libaom-av1 "cpu-used" option.
    def av1_cpu_used(self, value):
        self._av1_cpu_used = value

    def preset(self, value):
        self._preset = value

    def crf(self, value):
        self._crf = value

    def video_filters(self, filters):
        if filters is not None:
            self._video_filters = ['-vf', filters]
        else:
            self._video_filters = ''

    def outfile(self, value):
        self._outfile = value

    def get_arguments(self):
        base_encoding_arguments = [
                "-map", "0:V",
                "-c:v", "libaom-av1" if self._encoder == 'libaom-av1' else f'lib{self._encoder}',
                "-crf", self._crf
        ]

        if self._encoder == 'libaom-av1':
            encoding_arguments = base_encoding_arguments + [
                '-b:v', '0', '-cpu-used', self._av1_cpu_used, *self._video_filters, self._outfile
            ]
        else:
            encoding_arguments = base_encoding_arguments + [
                '-preset', self._preset, *self._video_filters, self._outfile
            ]
            
        return self._base_ffmpeg_arguments + encoding_arguments
    

class LibVmafArguments():
    def __init__(self, fps, distorted_video, original_video, vmaf_options):
        self._fps = fps
        self._distorted_video = distorted_video
        self._original_video = original_video
        self._vmaf_options = vmaf_options 

    def video_filters(self, filters):
        if filters is not None:
            self._video_filters = f',{filters}'
        else:
            self._video_filters = ''

    def get_arguments(self):
        return [
            "-r", self._fps, "-i", self._distorted_video,
            "-r", self._fps, "-i", self._original_video,
            "-map", "0:V", "-map", "1:V",
            "-lavfi", f'[0:v]setpts=PTS-STARTPTS[dist];'
                      f'[1:v]setpts=PTS-STARTPTS{self._video_filters}[ref];'
                      f'[dist][ref]libvmaf={self._vmaf_options}',
            "-f", "null", "-"
        ]
        

class FfmpegProcessFactory:
    def create_process(self, arguments, args):
        _process_base_arguments = ["ffmpeg", "-progress", "-", "-nostats", "-loglevel", "warning", "-y"]
        process = FfmpegProcess(_process_base_arguments + arguments.get_arguments(), args)
        return process


class FfmpegProcess:
    def __init__(self, arguments, args):
        self._arguments = arguments
        if args.show_commands:
            line()
            log.debug(f'Running the following command:\n{" ".join(self._arguments)}')
            line()
    
    def run(self, video_path, duration):
        self._video_path = video_path
        self._duration = duration
        
        video_info = VideoInfoProvider(self._video_path)
        self._total_frames = int((video_info.get_framerate_float() * self._duration) + 1)
        previous_frame_number = 0

        self._process = subprocess.Popen(self._arguments, stdout=subprocess.PIPE)

        progress_bar = tqdm(
            total=self._total_frames, 
            unit=" frames", 
            dynamic_ncols=True,
        )

        progress_bar.clear()

        try:
            while self._process.poll() is None:
                output = self._process.stdout.readline().decode("utf-8")
                if "frame=" in output:
                    frame_number = int(output[6:])
                    frame_number_increase = frame_number - previous_frame_number
                    progress_bar.update(frame_number_increase)
                    previous_frame_number = frame_number

        except KeyboardInterrupt:
            self._process.kill()              