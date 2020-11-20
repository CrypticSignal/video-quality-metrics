import os
import math
import subprocess
import shutil
import time

from pathlib import Path

from utils import VideoInfoProvider, line, exit_program


class ClipError(Exception):
    pass


class ConcatenateError(Exception):
    pass


def step_to_movie_timestamp(step_seconds):
    time_from_step = time.gmtime(step_seconds)
    timestamp = time.strftime('%H:%M:%S', time_from_step)
    return timestamp


def create_clips(video_path, output_folder, interval_seconds, clip_length):
    # The output folder for the clips.
    output_folder = os.path.join(output_folder, 'clips')

    if not os.path.exists(video_path):
        raise ClipError('The specified video file does not exist.')

    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    provider = VideoInfoProvider(video_path)
    duration = int(float(provider.get_duration()))

    if interval_seconds > duration:
        raise ClipError(f'The interval ({interval_seconds}s) may not be longer than the video ({duration}s).')

    number_steps = math.trunc(duration / interval_seconds)
    txt_file_path = f'{output_folder}/clips.txt'
    # Create the file.
    open(txt_file_path, 'w').close()

    line()
    print(f'Creating a {clip_length} second clip every {interval_seconds} seconds from {video_path}...')
    line()

    try:
        for step in range(1, number_steps):
            clip_name = f'clip{step}.mkv'
            with open(txt_file_path, 'a') as f:
                f.write(f"file '{clip_name}'\n")
            clip_output_path = os.path.join(output_folder, clip_name)
            clip_offset = step_to_movie_timestamp(step * interval_seconds)
            print(f'Creating clip {step} which starts at {clip_offset}...')
            subprocess_cut_args = [
                "ffmpeg", "-loglevel", "warning", "-stats", "-y",
                "-ss", clip_offset, "-i", video_path,
                "-map", "0:V", "-t", clip_length,
                "-c:v", "libx264", "-crf", "0", "-preset", "ultrafast",
                clip_output_path
            ]
            subprocess.run(subprocess_cut_args)
    except Exception as error:
        print('An error occurred while trying to create the clips.')
        exit_program(error)
    else:
        return txt_file_path


def concatenate_clips(txt_file_path, output_folder, extension, interval_seconds, clip_length):
    if not os.path.exists(txt_file_path):
        raise ConcatenateError(f'{txt_file_path} does not exist.')

    overview_filename = f'{clip_length}-{interval_seconds} (ClipLength-IntervalSeconds){extension}'
    concatenated_filepath = os.path.join(output_folder, overview_filename)

    subprocess_concatenate_args = [
        "ffmpeg", "-loglevel", "warning", "-stats", "-y",
        "-f", "concat", "-safe", "0", "-i", txt_file_path, "-c", "copy", concatenated_filepath
    ]

    line()
    print('Concatenating the clips to create the overview video...')
    result = subprocess.run(subprocess_concatenate_args)
    print('Done!')
    shutil.rmtree(os.path.join(output_folder, 'clips'))
    print('The clips have been deleted as they are no longer needed.')

    if result.returncode == 0:
        return concatenated_filepath


def create_movie_overview(video_path, output_folder, interval_seconds, clip_length):
    extension = Path(video_path).suffix
    try:
        txt_file_path = create_clips(video_path, output_folder, interval_seconds, clip_length)
        output_file = concatenate_clips(txt_file_path, output_folder, extension, interval_seconds, clip_length)
        result = True
    except ClipError as err:
        result = False
        exit_program(err.args[0])
    except ConcatenateError as err:
        result = False
        exit_program(err.args[0])

    if result:
        print(f'Overview Video: {clip_length}-{interval_seconds} (ClipLength-IntervalSeconds){extension}')
        line()
        return result, output_file
