"""Optional ways of creating a shorter reference video, so that the program runs faster."""

import shutil
import subprocess
from pathlib import Path

from utils import exit_program, line, log
from video_info import get_duration, probe


def run_ffmpeg(command: list[str]) -> None:
    """Run an FFmpeg command, which prints its own errors, and exit if it fails."""
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError:
        exit_program("FFmpeg failed. Its error message is above.")


def cut_video(video_path: str, output_folder: Path, length: float) -> Path:
    """Losslessly create a copy of the video that is just the first `length` seconds."""
    # :g shows e.g. 10.0 as "10" and 2.5 as "2.5".
    output_path = output_folder / f"{Path(video_path).stem} [{length:g}s].mkv"

    log.info(f"Cutting the video to a length of {length:g} seconds...")
    run_ffmpeg(
        [
            "ffmpeg",
            "-loglevel",
            "error",
            "-y",
            "-i",
            video_path,
            "-t",
            str(length),
            "-map",
            "0",
            "-c",
            "copy",
            str(output_path),
        ]
    )
    log.info("Done!")
    return output_path


def create_overview_video(
    video_path: str, output_folder: Path, interval: int, clip_length: int
) -> Path:
    """Create a lossless overview video.

    This is done by taking a clip_length seconds long clip every interval seconds
    and concatenating the clips.
    """
    duration = get_duration(probe(video_path))
    if interval > duration:
        exit_program(f"The interval ({interval}s) may not be longer than the video ({duration}s).")
    if clip_length > duration:
        exit_program(
            f"The clip length ({clip_length}s) may not be longer than the video ({duration}s)."
        )

    clips_folder = output_folder / "clips"
    clips_folder.mkdir(exist_ok=True)
    clip_names = []

    log.info(f"Creating a {clip_length} second clip every {interval} seconds from {video_path}...")
    line()

    # Clips start at 0s, interval s, 2 * interval s, etc., as long as the whole clip fits.
    clip_count = int((duration - clip_length) // interval) + 1
    for clip_number in range(1, clip_count + 1):
        clip_name = f"clip{clip_number}.mkv"
        clip_names.append(clip_name)
        log.info(f"Creating clip {clip_number} of {clip_count}...")
        run_ffmpeg(
            [
                "ffmpeg",
                "-loglevel",
                "error",
                "-stats",
                "-y",
                "-ss",
                str((clip_number - 1) * interval),
                "-i",
                video_path,
                "-map",
                "0:V",
                "-t",
                str(clip_length),
                "-c:V",
                "libx264",
                "-crf",
                "0",
                str(clips_folder / clip_name),
            ]
        )

    # FFmpeg's concat demuxer reads the list of clips from a text file.
    clips_list = clips_folder / "clips.txt"
    clips_list.write_text("".join(f"file '{name}'\n" for name in clip_names))
    # The clips are H.264, which some containers (e.g. WebM) do not support, so use MKV.
    overview_video = output_folder / "Overview_Video.mkv"

    line()
    log.info("Concatenating the clips to create the overview video...")
    run_ffmpeg(
        [
            "ffmpeg",
            "-loglevel",
            "error",
            "-stats",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(clips_list),
            "-c",
            "copy",
            str(overview_video),
        ]
    )
    shutil.rmtree(clips_folder)
    log.info("Done! The clips have been deleted as they are no longer needed.")
    log.info(f"Overview Video: {overview_video}")
    line()

    return overview_video
