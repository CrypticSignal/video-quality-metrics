import math
import os
from pathlib import Path
import shutil
import subprocess
import time

from utils import VideoInfoProvider, line, exit_program, Logger

log = Logger("overview")


class ClipError(Exception):
    pass


class ConcatenateError(Exception):
    pass


def clip_number_to_movie_timestamp(clip_number_seconds):
    time_from_clip_number = time.gmtime(clip_number_seconds)
    timestamp = time.strftime("%H:%M:%S", time_from_clip_number)
    return timestamp


def create_clips(input_video, output_folder, interval_seconds, clip_length):
    # The output folder for the clips.
    output_folder = os.path.join(output_folder, "clips")
    os.makedirs(output_folder, exist_ok=True)

    provider = VideoInfoProvider(input_video)
    duration = int(float(provider.get_duration()))

    if interval_seconds > duration:
        raise ClipError(
            f"The interval ({interval_seconds}s) may not be longer than the video ({duration}s)."
        )

    num_clips = math.trunc(duration / interval_seconds)

    txt_file_path = os.path.join(output_folder, "clips.txt")
    # Create the file.
    open(txt_file_path, "w").close()

    log.info("Overview mode activated.")
    log.info(
        f"Creating a {clip_length} second clip every {interval_seconds} seconds from {input_video}..."
    )
    line()

    try:
        for clip_number in range(1, num_clips):
            clip_name = f"clip{clip_number}.mkv"

            with open(txt_file_path, "a") as f:
                f.write(f"file '{clip_name}'\n")

            clip_output_path = os.path.join(output_folder, clip_name)
            clip_offset = clip_number_to_movie_timestamp(clip_number * interval_seconds)

            log.info(
                f"Creating clip {clip_number} which starts at {clip_offset} and ends {interval_seconds} seconds later ..."
            )

            subprocess_cut_args = [
                "ffmpeg",
                "-loglevel",
                "warning",
                "-stats",
                "-y",
                "-ss",
                clip_offset,
                "-i",
                input_video,
                "-map",
                "0:V",
                "-t",
                clip_length,
                "-c:v",
                "libx264",
                "-crf",
                "0",
                "-preset",
                "ultrafast",
                clip_output_path,
            ]

            subprocess.run(subprocess_cut_args)

    except Exception as error:
        log.info("An error occurred while trying to create the clips.")
        exit_program(error)

    else:
        return txt_file_path


def concatenate_clips(txt_file_path, output_folder, extension):
    if not os.path.exists(txt_file_path):
        raise ConcatenateError(f"{txt_file_path} does not exist.")

    overview_filename = f"Overview_Video{extension}"
    concatenated_filepath = os.path.join(output_folder, overview_filename)

    subprocess_concatenate_args = [
        "ffmpeg",
        "-loglevel",
        "warning",
        "-stats",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        txt_file_path,
        "-c",
        "copy",
        concatenated_filepath,
    ]

    line()
    log.info("Concatenating the clips to create the overview video...")
    result = subprocess.run(subprocess_concatenate_args)
    log.info("Done!")
    shutil.rmtree(os.path.join(output_folder, "clips"))
    log.info("The clips have been deleted as they are no longer needed.")

    if result.returncode == 0:
        return concatenated_filepath


def create_overview_video(input_video, output_folder, interval_seconds, clip_length):
    os.makedirs(output_folder, exist_ok=True)
    extension = Path(input_video).suffix
    try:
        txt_file_path = create_clips(
            input_video, output_folder, interval_seconds, clip_length
        )
        output_file = concatenate_clips(txt_file_path, output_folder, extension)
        result = True
    except ClipError as err:
        result = False
        exit_program(err.args[0])
    except ConcatenateError as err:
        result = False
        exit_program(err.args[0])

    if result:
        log.info(f"Overview Video: {output_file}")
        line()
        return result, output_file
