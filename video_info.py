import json
import re
import subprocess
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from time import perf_counter

from utils import fail, format_si, log


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
        fail(f"FFprobe was unable to read {video_path}:\n{error.stderr.strip()}")
    return json.loads(result.stdout)


def get_duration(info: dict) -> float:
    """Return the container's duration in seconds, or 0 if it is unknown."""
    return float(info["format"].get("duration", 0))


def get_video_duration(info: dict) -> float:
    """Return the duration of the first video stream in seconds, or the container's duration
    if the stream's is unknown.

    The container's duration is the longest of its streams, so it is too long for the video if
    e.g. the audio carries on after the video ends, which makes the video bitrate too low.
    """
    video_stream = get_video_stream(info) or {}
    try:
        # MP4 and MOV store each stream's duration.
        if video_stream.get("duration"):
            return float(video_stream["duration"])
        # MKV stores it as a tag, e.g. "DURATION": "00:00:10.010000000". The tag can have a
        # language suffix, e.g. "DURATION-eng".
        for key, value in video_stream.get("tags", {}).items():
            if key.upper().startswith("DURATION"):
                hours, minutes, seconds = value.split(":")
                return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    except ValueError:
        pass
    return get_duration(info)


def get_video_stream(info: dict) -> dict | None:
    """Return the first video stream, or None if there isn't one."""
    return next((stream for stream in info["streams"] if stream["codec_type"] == "video"), None)


# The transfer characteristics that HDR video uses, as FFprobe names them.
HDR_FORMATS = {"smpte2084": "PQ", "arib-std-b67": "HLG"}


def get_hdr_format(info: dict) -> str | None:
    """Return "PQ" or "HLG" if the first video stream is HDR, or None if it isn't."""
    video_stream = get_video_stream(info) or {}
    return HDR_FORMATS.get(video_stream.get("color_transfer"))


def get_resolution(
    video_path: str | Path, video_filters: str | None = None
) -> tuple[int, int] | None:
    """Return the resolution of the video's frames as FFmpeg decodes them, after the filters
    (if any) are applied to them, e.g. a crop.

    This is the resolution that libvmaf sees. It can differ from the resolution that FFprobe
    reports, e.g. FFmpeg rotates a phone video that is stored as 1920x1080 with a rotation of
    90 degrees, so its frames are 1080x1920. Returns None if it can't be found, e.g. because a
    filter is invalid.
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
            f"{video_filters},showinfo" if video_filters else "showinfo",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
    )
    match = re.search(r" s:(\d+)x(\d+) ", result.stderr)
    return (int(match[1]), int(match[2])) if match else None


def get_frame_rate(info: dict) -> str:
    """Return the frame rate of the first video stream, e.g. "24000/1001 (23.976)"."""
    video_stream = get_video_stream(info)
    if video_stream is None:
        return "N/A"
    fraction = video_stream["r_frame_rate"]
    return f"{fraction} ({float(Fraction(fraction)):.3f})"


def get_video_bitrate(
    info: dict, video_packets_size: int, decimal_places: int
) -> tuple[float | None, str | None]:
    """Return the video bitrate in bits per second and how it was found, e.g. (1526000,
    "confidence = high, method = video packet sizes"). video_packets_size is the total size of
    the video packets in bytes, from read_video_packets. decimal_places is used for logging.

    The most accurate method is tried first, falling back to less reliable methods. Both are
    None if the bitrate couldn't be determined.
    """
    duration = get_video_duration(info)
    streams = info["streams"]

    def describe(bitrate: float, confidence: str, method: str) -> tuple[float, str]:
        formatted_bitrate = format_si(bitrate, "bps", decimal_places)
        log.info(
            f"Video Bitrate: {formatted_bitrate} | Confidence: {confidence} | Method: {method}"
        )
        return bitrate, f"confidence = {confidence}, method = {method}"

    # Method 1: Total size of the video packets divided by the video's duration.
    if duration > 0 and video_packets_size > 0:
        return describe(video_packets_size * 8 / duration, "high", "video packet sizes")

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
    return None, None


@dataclass
class VideoPackets:
    total_size: int  # In bytes.
    count: int  # Each packet of a video stream holds one frame, so this is the frame count.


def read_video_packets(video_path: str | Path, info: dict) -> VideoPackets:
    """Return the total size and the number of the first video stream's packets.

    Both are found in one pass over the file, because reading every packet of a long video
    takes a while. Both are 0 if FFprobe can't read the packets.
    """
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

    log.info(f"Reading the video packets of {video_path}...")
    duration = get_video_duration(info)
    total_size = 0
    count = 0
    last_progress_update = perf_counter()

    # Each line of output is "<pts_time>,<size>". This can take a while for long videos,
    # so progress is logged every second.
    with subprocess.Popen(command, stdout=subprocess.PIPE, text=True) as process:
        for output_line in process.stdout:
            pts_time, _, size = output_line.strip().partition(",")
            if size.isdigit():
                total_size += int(size)
                count += 1

            if duration > 0 and perf_counter() - last_progress_update >= 1:
                try:
                    log.info(f"Progress: {min(float(pts_time) / duration, 1):.1%}")
                except ValueError:
                    pass
                last_progress_update = perf_counter()

    return VideoPackets(total_size, count)
