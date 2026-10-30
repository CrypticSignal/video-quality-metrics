"""Optional ways of creating a shorter reference video, so that the program runs faster."""

import shutil
import subprocess
from pathlib import Path

from utils import exit_program, line, log
from video_info import get_duration, probe


def cut_video(video_path: str, output_folder: Path, length: str) -> Path:
    """Losslessly create a copy of the video that is just the first `length` seconds."""
    output_path = output_folder / f"{Path(video_path).stem} [{length}s].mkv"

    log.info(f"Cutting the video to a length of {length} seconds...")
    subprocess.run(
        [
            "ffmpeg",
            "-loglevel",
            "error",
            "-y",
            "-i",
            video_path,
            "-t",
            length,
            "-map",
            "0",
            "-c",
            "copy",
            str(output_path),
        ],
        check=True,
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
        subprocess.run(
            [
                "ffmpeg",
                "-loglevel",
                "quiet",
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
            ],
            check=True,
        )

    # FFmpeg's concat demuxer reads the list of clips from a text file.
    clips_list = clips_folder / "clips.txt"
    clips_list.write_text("".join(f"file '{name}'\n" for name in clip_names))
    overview_video = output_folder / f"Overview_Video{Path(video_path).suffix}"

    line()
    log.info("Concatenating the clips to create the overview video...")
    subprocess.run(
        [
            "ffmpeg",
            "-loglevel",
            "quiet",
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
        ],
        check=True,
    )
    shutil.rmtree(clips_folder)
    log.info("Done! The clips have been deleted as they are no longer needed.")
    log.info(f"Overview Video: {overview_video}")
    line()

    return overview_video
