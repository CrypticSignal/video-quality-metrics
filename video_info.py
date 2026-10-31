import json
import re
import subprocess
from fractions import Fraction
from pathlib import Path
from time import perf_counter

from utils import exit_program, format_si, log


def probe(video_path: str | Path) -> dict:
    """Return FFprobe's information about the container ("format") and its "streams"."""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_format",
                "-show_streams",
                "-of",
                "json",
                str(video_path),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as error:
        exit_program(f"FFprobe was unable to read {video_path}:\n{error.stderr.strip()}")
    return json.loads(result.stdout)


def get_duration(info: dict) -> float:
    return float(info["format"].get("duration", 0))


def get_video_stream(info: dict) -> dict | None:
    """Return the first video stream, or None if there isn't one."""
    return next((stream for stream in info["streams"] if stream["codec_type"] == "video"), None)


def get_resolution(info: dict) -> tuple[int, int] | None:
    """Return the width and height of the first video stream, or None if there isn't one."""
    video_stream = get_video_stream(info)
    if video_stream is None or "width" not in video_stream:
        return None
    return video_stream["width"], video_stream["height"]


def get_filtered_resolution(video_path: str | Path, video_filters: str) -> tuple[int, int] | None:
    """Return the resolution of the video after the filters are applied to it, e.g. a crop.

    Returns None if it can't be found, e.g. because a filter is invalid.
    """
    # The showinfo filter logs each frame's size, e.g. " s:1920x800 ".
    result = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-nostats",
            "-loglevel",
            "info",
            "-i",
            str(video_path),
            "-map",
            "0:V:0",
            "-frames:v",
            "1",
            "-vf",
            f"{video_filters},showinfo",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
    )
    match = re.search(r" s:(\d+)x(\d+) ", result.stderr)
    return (int(match[1]), int(match[2])) if match else None


def count_video_frames(video_path: str | Path) -> int | None:
    """Return the number of frames in the first video stream, or None if it can't be counted."""
    # Each packet of a video stream holds one frame. Counting them is much faster than decoding.
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "V:0",
            "-count_packets",
            "-show_entries",
            "stream=nb_read_packets",
            "-of",
            "csv=p=0",
            str(video_path),
        ],
        capture_output=True,
        text=True,
    )
    output = result.stdout.strip()
    return int(output) if output.isdigit() else None


def get_frame_rate(info: dict) -> str:
    """Return the frame rate of the first video stream, e.g. "24000/1001 (23.976)"."""
    video_stream = get_video_stream(info)
    if video_stream is None:
        return "N/A", None
    fraction = video_stream["r_frame_rate"]
    return f"{fraction} ({float(Fraction(fraction)):.3f})"


def describe_video_bitrate(
    video_path: str | Path, info: dict, decimal_places: int
) -> tuple[str, str | None]:
    """Return the video bitrate and how it was found, e.g. ("1.526 Mbps", "high | video packet
    sizes"), where the second part is the confidence and the method.

    The most accurate method is tried first, falling back to less reliable methods. The second
    part is None if the bitrate couldn't be determined.
    """
    duration = get_duration(info)
    streams = info["streams"]

    def describe(bitrate: float, confidence: str, method: str) -> tuple[str, str]:
        formatted_bitrate = format_si(bitrate, "bps", decimal_places)
        log.info(
            f"Video Bitrate: {formatted_bitrate} | Confidence: {confidence} | Method: {method}"
        )
        return formatted_bitrate, f"{confidence} | {method}"

    # Method 1: Total size of the video packets divided by the duration.
    if duration > 0:
        log.info(f"Calculating the video bitrate of {video_path} from its packet sizes...")
        total_bytes = sum_video_packet_sizes(video_path, duration)
        if total_bytes > 0:
            return describe(total_bytes * 8 / duration, "high", "video packet sizes")

    # Method 2: The bitrate reported in the video stream's metadata.
    for stream in streams:
        if stream["codec_type"] == "video" and stream.get("bit_rate"):
            return describe(int(stream["bit_rate"]), "medium", "video stream metadata")

    # Method 3: The container's overall bitrate minus the bitrate of any audio streams.
    container_bitrate = info["format"].get("bit_rate")
    if container_bitrate:
        audio_bitrate = sum(
            int(stream["bit_rate"])
            for stream in streams
            if stream["codec_type"] == "audio" and stream.get("bit_rate")
        )
        video_bitrate = int(container_bitrate) - audio_bitrate
        if video_bitrate > 0:
            return describe(video_bitrate, "low", "container derived (minus audio)")

    log.info("Unable to determine the video bitrate.")
    return "N/A", None


def sum_video_packet_sizes(video_path: str | Path, duration: float) -> int:
    """Return the total size (in bytes) of the first video stream's packets."""
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "V:0",
        "-show_entries",
        "packet=pts_time,size",
        "-of",
        "csv=p=0",
        str(video_path),
    ]

    total_bytes = 0
    last_progress_update = perf_counter()

    # Each line of output is "<pts_time>,<size>". This can take a while for long videos,
    # so progress is logged every second.
    with subprocess.Popen(command, stdout=subprocess.PIPE, text=True) as process:
        for output_line in process.stdout:
            pts_time, _, size = output_line.strip().partition(",")
            if size.isdigit():
                total_bytes += int(size)

            if perf_counter() - last_progress_update >= 1:
                try:
                    log.info(f"Progress: {min(float(pts_time) / duration, 1):.1%}")
                except ValueError:
                    pass
                last_progress_update = perf_counter()

    return total_bytes
