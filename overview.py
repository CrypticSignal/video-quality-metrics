import os

from utils import get_duration, separator
import math
import shutil
import subprocess
import time


class ClipError(Exception):
    pass


class ConcatenateError(Exception):
    pass


def step_to_movie_timestamp(step_seconds):
    time_from_step = time.gmtime(step_seconds)
    timestamp = time.strftime('%H:%M:%S', time_from_step)
    return timestamp


def create_clips(video_path, output_folder, interval_seconds, clip_length_seconds):
    if not os.path.exists(video_path):
        raise ClipError(f'Video file does not exist')

    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    duration = int(round(float(get_duration(video_path)), 2))

    if interval_seconds > duration:
        raise ClipError(f'Interval may not be longer than the video. {interval_seconds} > {duration}')

    number_steps = math.trunc(duration / interval_seconds)
    output_clip_names = 'clips.txt'
    output_file_path = f'{output_folder}/{output_clip_names}'
    clip_file = open(output_file_path, 'w')
    separator()
    print(f'Now creating a {clip_length_seconds} second clip every {interval_seconds} seconds from {video_path}.\n'
          f'Duration: {duration} seconds, Interval: {interval_seconds} seconds -> {number_steps} clips')
    separator()

    try:
        for step in range(1, number_steps):
            clip_name = f'clip{step}.mkv'
            output_filename = f'{output_folder}/{clip_name}'
            clip_offset = step_to_movie_timestamp(step * interval_seconds)
            print(f'Clip: {step} offset: {clip_offset}')
            clip_file.write(f'file \'{clip_name}\'\n')
            subprocess_cut_args = [
                "ffmpeg", "-loglevel", "warning", "-stats", "-y",
                "-ss", str(clip_offset), "-i", "original.mkv",
                "-map", "0", "-t", str(clip_length_seconds),
                "-c:v", "libx264", "-crf", "0", "-preset", "ultrafast",
                "-an", "-sn", output_filename
            ]

            subprocess.run(subprocess_cut_args)
    finally:
        clip_file.close()

    return output_file_path


def concatenate_clips(clips_file_path, output_folder, output_extension, interval_seconds, clip_length_seconds):
    if not os.path.exists(clips_file_path):
        raise ConcatenateError(f'Clips file does not exist')

    overview_filename = f'overview_{clip_length_seconds}secs_every_{interval_seconds}secs.{output_extension}'
    concatenated_filepath = f'{output_folder}/../{overview_filename}'
    # concatenated_filepath = os.path.join(output_folder, f'concatenated.{output_extension}')
    subprocess_concatenate_args = [
        "ffmpeg", "-loglevel", "warning", "-stats", "-y",
        "-f", "concat", "-safe", "0", "-i", clips_file_path, "-c", "copy", concatenated_filepath
    ]

    separator()
    print('Now concatenating clips to a single video file.')
    result = subprocess.run(subprocess_concatenate_args)
    shutil.rmtree(f'{output_folder}')
    print('Done.')
    separator()

    if result.returncode == 0:
        return concatenated_filepath


def create_movie_overview(video_path, output_folder, interval_seconds, clip_length):
    extension = os.path.splitext(video_path)[-1][1:]
    output_file = str()

    try:
        clips_file = create_clips(video_path, output_folder, interval_seconds, clip_length)
        output_file = concatenate_clips(clips_file, output_folder, extension, interval_seconds, clip_length)
        result = True
    except ClipError as err:
        result = False
        print(err.args[0])
    except ConcatenateError as err:
        result = False
        print(err.args[0])

    if result:
        print('Done.')

    return result, output_file
