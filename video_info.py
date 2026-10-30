import json
import subprocess
from fractions import Fraction
from pathlib import Path
from time import perf_counter

from utils import format_si, log


def probe(video_path: str | Path) -> dict:
    """Return FFprobe's information about the container ("format") and its "streams"."""
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
    return json.loads(result.stdout)


def get_duration(info: dict) -> float:
    return float(info["format"].get("duration", 0))


def get_video_stream(info: dict) -> dict | None:
    """Return the first video stream, or None if there isn't one."""
    return next((stream for stream in info["streams"] if stream["codec_type"] == "video"), None)


def get_frame_rate(info: dict) -> str:
    """Return the frame rate of the first video stream, e.g. "24000/1001 (23.976)"."""
    video_stream = get_video_stream(info)
    if video_stream is None:
        return "N/A"
    fraction = video_stream["r_frame_rate"]
    return f"{fraction} ({float(Fraction(fraction)):.3f})"


def describe_video_bitrate(video_path: str | Path, info: dict, decimal_places: int) -> str:
    """
    Return the video bitrate, how confident we are in it and the method used to find it,
    e.g. "1.526 Mbps | high | video packet sizes".

    The most accurate method is tried first, falling back to less reliable methods.
    """
    duration = get_duration(info)
    streams = info["streams"]

    def describe(bitrate: float, confidence: str, method: str) -> str:
        formatted_bitrate = format_si(bitrate, "bps", decimal_places)
        log.info(
            f"Video Bitrate: {formatted_bitrate} | Confidence: {confidence} | Method: {method}"
        )
        # The table's column header already names each part.
        return f"{formatted_bitrate} | {confidence} | {method}"

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
    return "N/A"


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
