from dataclasses import dataclass
import logging
import os
from pathlib import Path
import subprocess
import sys
from time import time, perf_counter
from typing import Literal, Optional

from ffmpeg import probe
import matplotlib.pyplot as plt
import numpy as np


class Logger:
    def __init__(self, name, filename="logs.log", print_to_terminal=True):
        self._logger = logging.getLogger(name)
        self._logger.setLevel(logging.DEBUG)

        # Add handlers only if this logger has no handlers (ignore ancestors)
        if not self._logger.handlers:
            file_handler = logging.FileHandler(filename)
            file_formatter = logging.Formatter("[%(name)s] %(levelname)s: %(message)s")
            file_handler.setFormatter(file_formatter)
            self._logger.addHandler(file_handler)
            self._file_handler = file_handler

            if print_to_terminal:
                stream_handler = logging.StreamHandler()
                stream_formatter = logging.Formatter("%(message)s")
                stream_handler.setFormatter(stream_formatter)
                self._logger.addHandler(stream_handler)

        # Avoid propagating logs to ancestor loggers
        self._logger.propagate = False

    def info(self, msg):
        self._logger.info(msg)

    def warning(self, msg):
        self._logger.warning(msg)

    def debug(self, msg):
        self._logger.debug(msg)

    def close(self):
        handlers = self._logger.handlers[:]
        for handler in handlers:
            handler.close()
            self._logger.removeHandler(handler)


log = Logger("utils")


class Timer:
    def start(self):
        self._start_time = time()

    def stop(self, decimal_places):
        time_to_convert = time() - self._start_time
        time_rounded = force_decimal_places(round(time_to_convert, decimal_places), decimal_places)
        return time_rounded


@dataclass
class BitrateResult:
    bitrate: int
    confidence: str
    method: str


class VideoInfoProvider:
    def __init__(self, video_path):
        self._video_path = video_path

    def get_video_bitrate_str(self, decimal_places: int) -> str:
        result = self.get_video_bitrate()

        if result is None:
            return "N/A"

        formatted = format_value(
            result.bitrate,
            decimal_places,
            input_unit_type="bits",
            output_unit_type="bits",
        )

        return f"{formatted}ps | {result.confidence} | {result.method}"

    def get_video_bitrate(self) -> Optional[BitrateResult]:
        probe_data = self._probe_file()

        if probe_data is None:
            return None

        format_info = probe_data.get("format", {})
        streams = probe_data.get("streams", [])

        duration = self._parse_duration(format_info.get("duration"))

        line()

        # ---------------------------
        # Method 1
        # ---------------------------
        log.info(
            "Determining video bitrate by summing video packet sizes and dividing by file duration..."
        )
        result = self._get_bitrate_from_packets(duration)
        if result:
            log.info(f"Done! Bitrate: {format_value(result.bitrate, input_unit_type='bits', output_unit_type='bits')}ps | Confidence: {result.confidence} | Method: {result.method}")
            return result

        # ---------------------------
        # Method 2 (Video Stream Metadata)
        # ---------------------------
        log.info("Determining video bitrate from video stream metadata...")
        result = self._get_bitrate_from_video_stream_metadata(streams)
        if result:
            log.info(f"Done! Bitrate: {format_value(result.bitrate, input_unit_type='bits', output_unit_type='bits')}ps | Confidence: {result.confidence} | Method: {result.method}")
            return result

        # ---------------------------
        # Method 3 (overall bitrate reported by container minus reported audio bitrate(s))
        # ---------------------------
        log.info(
            "Determining video bitrate from overall bitrate reported by container (minus reported audio bitrate(s))..."
        )
        result = self._get_bitrate_from_container_minus_audio(format_info, streams)
        if result:
            log.info(f"Done! Bitrate: {format_value(result.bitrate, input_unit_type='bits', output_unit_type='bits')}ps | Confidence: {result.confidence} | Method: {result.method}")
            return result

        log.info("Unable to determine video bitrate.")
        return None

    def _probe_file(self):
        try:
            return probe(self._video_path)
        except Exception as e:
            log.info(
                f"Unable to probe file with FFprobe. Cannot determine video bitrate. Error:\n{e}"
            )
            return None

    def _parse_duration(self, value) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def _get_bitrate_from_packets(self, duration: float) -> Optional[BitrateResult]:
        if duration <= 0:
            return None

        start_time = perf_counter()

        try:
            cmd = [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "V:0",
                "-show_entries",
                "packet=pts_time,size",
                "-of",
                "csv=p=0",
                self._video_path,
            ]

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1,
            )

            total_bytes = 0
            packet_count = 0

            last_log_time = start_time
            LOG_FREQUENCY_SECONDS = 1
            last_pts_time = 0.0

            for line in process.stdout:
                try:
                    pts_time_str, size_str = line.strip().split(",")
                    size = int(size_str)
                    pts_time = float(pts_time_str) if pts_time_str else 0.0

                    total_bytes += size
                    packet_count += 1
                    last_pts_time = pts_time

                    now = perf_counter()

                    if now - last_log_time >= LOG_FREQUENCY_SECONDS:
                        if last_pts_time > 0:
                            progress = min(last_pts_time / duration, 1.0) * 100
                            log.info(
                                f"Processed {packet_count} packets | Progress: {progress:.1f}%"
                            )

                        last_log_time = now

                except ValueError:
                    continue

            process.wait()

            elapsed = perf_counter() - start_time

            if packet_count == 0:
                return None

            bitrate = int((total_bytes * 8) / duration)

            return BitrateResult(bitrate, "High", "Video Packet Sizes")

        except Exception as e:
            log.info(f"Unable to determine video bitrate. Error:\n{e}")
            return None

    def _get_bitrate_from_video_stream_metadata(self, streams) -> Optional[BitrateResult]:
        for stream in streams:
            if stream.get("codec_type") == "video":
                bitrate = stream.get("bit_rate")
                if bitrate:
                    return BitrateResult(int(bitrate), "Medium", "Video Stream Metadata")

        log.info("Unable to determine video bitrate.")
        return None

    def _get_bitrate_from_container_minus_audio(
        self,
        format_info,
        streams,
    ) -> Optional[BitrateResult]:
        container_bitrate = format_info.get("bit_rate")

        if not container_bitrate:
            log.info("Unable to determine video bitrate.")
            return None

        try:
            total_audio_bitrate = sum(
                int(s["bit_rate"])
                for s in streams
                if s.get("codec_type") == "audio" and s.get("bit_rate")
            )

            video_bitrate = int(container_bitrate) - total_audio_bitrate

            if video_bitrate > 0:
                return BitrateResult(video_bitrate, "Low", "Container Derived (Minus Audio)")

        except (ValueError, KeyError) as e:
            log.info(f"Unable to determine video bitrate. Error:\n{e}")
            return None

        return None

    def get_framerate_fraction(self):
        r_frame_rate = [
            stream
            for stream in probe(self._video_path)["streams"]
            if stream["codec_type"] == "video"
        ][0]["r_frame_rate"]
        return r_frame_rate

    def get_framerate_float(self):
        numerator, denominator = self.get_framerate_fraction().split("/")
        return int(numerator) / int(denominator)

    def get_duration_str(self, decimal_places=3):
        duration = self.get_duration()
        return f"{duration:.{decimal_places}f} s" if duration >= 0 else "N/A"

    def get_duration(self):
        try:
            return float(probe(self._video_path)["format"]["duration"])
        except:
            return -1

    def get_all_info(self):
        return probe(self._video_path)


def cut_video(filename, args, output_ext, output_folder, comparison_table):
    cut_version_filename = f"{Path(filename).stem} [{args.transcode_length}s]{output_ext}"
    # Output path for the cut video.
    output_file_path = os.path.join(output_folder, cut_version_filename)
    # The reference file will be the cut version of the video.
    # Create the cut version.
    log.info(f"Cutting the video to a length of {args.transcode_length} seconds...")
    os.system(
        f"ffmpeg -loglevel debug -y -i {args.original_video_path} -t {args.transcode_length} "
        f'-map 0 -c copy "{output_file_path}"'
    )
    log.info("Done!")

    time_message = (
        f" for {args.transcode_length} seconds"
        if int(args.transcode_length) > 1
        else "for 1 second"
    )

    with open(comparison_table, "w") as f:
        f.write(f"You chose to encode {filename}{time_message} using {args.encoder}.")

    return output_file_path


def exit_program(message):
    line()
    log.info(f"{message}\nThis program will now exit.")
    line()
    sys.exit()


def force_decimal_places(value, decimal_places):
    return f"{value:.{decimal_places}f}"


def line():
    width, _ = os.get_terminal_size()
    log.info("-" * width)


def plot_graph(
    title,
    x_label,
    y_label,
    x_values,
    y_values,
    mean_y_value,
    save_path,
    bar_graph=False,
):
    def generate_colors(n):
        """Generate n distinct colors by evenly spacing hues."""
        return [plt.cm.hsv(i / n) for i in range(n)]

    plt.figure(figsize=(10, 6))
    plt.suptitle(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)

    if bar_graph:
        x_positions = np.arange(len(x_values))
        plt.bar(x_positions, y_values, color=generate_colors(len(x_values)))
        plt.xticks(x_positions, x_values, rotation=45, ha="right")

        # Go 1 point lower than the lowest value, but not below 0
        y_min = max(0, min(y_values) - 1)
        # Go 1 point higher than the highest value, but not above 100
        y_max = min(100, max(y_values) + 1)
        plt.ylim(y_min, y_max)

        # Show the value in the middle of each bar
        for i, v in enumerate(y_values):
            y_position = (y_min + v) / 2  # Calculate middle position
            plt.text(i, y_position, str(v), ha="center", va="center")

    else:
        plt.plot(x_values, y_values, label=f"{y_label} ({mean_y_value})")
        plt.legend(loc="lower right")

    plt.tight_layout()
    plt.savefig(save_path, bbox_inches="tight")
    plt.clf()


def write_table_info(table_path, video_filename, args):
    with open(table_path, "a") as f:
        buff = (
            f"\nOriginal File: {video_filename}\n"
            f"VQM transcoded the file with the {args.encoder} encoder\n"
            f"FFmpeg output options: {args.output_options}\n"
            + (
                f"Filter(s) applied to original video before quality metrics calculation: {args.video_filters}\n"
                if args.video_filters
                else ""
            )
            + f"libvmaf n_subsample: {args.n_subsample}"
        )
        f.write(buff)
        return buff


def get_metrics_list(args):
    metrics_list = [
        "VMAF",
        "PSNR" if not args.disable_psnr else None,
        "SSIM" if not args.disable_ssim else None,
    ]

    return list(filter(None, metrics_list))


def format_value(
    value,
    decimal_places: int = 3,
    system: Literal["si", "iec"] = "si",
    input_unit_type: Literal["bytes", "bits"] = "bytes",
    output_unit_type: Literal["bytes", "bits"] = "bytes",
    default: str = "N/A",
    separator: str = " ",
):
    """
    system:
        "si"  -> base 1000 (KB, MB, GB)
        "iec" -> base 1024 (KiB, MiB, GiB)

    """
    try:
        int(value)
    except ValueError:
        return value

    if system not in ("si", "iec"):
        raise ValueError("system must be 'si' or 'iec'")

    if input_unit_type not in ("bytes", "bits") or output_unit_type not in ("bytes", "bits"):
        raise ValueError("units must be 'bytes' or 'bits'")

    try:
        value = float(value)
    except (TypeError, ValueError):
        return default

    if value < 0:
        return default

    if input_unit_type == "bits" and output_unit_type == "bytes":
        value = value / 8

    if input_unit_type == "bytes" and output_unit_type == "bits":
        value = value * 8

    if output_unit_type == "bits":
        suffix = "b"
    else:
        suffix = "B"

    if system == "iec":
        base, prefixes = 1024, ["", "Ki", "Mi", "Gi", "Ti", "Pi"]
    else:
        base, prefixes = 1000, ["", "K", "M", "G", "T", "P"]

    units = [p + suffix for p in prefixes]

    index = 0
    while value >= base and index < len(units) - 1:
        value = value / base
        index += 1

    # No decimal places if it's bytes or bits
    if index == 0:
        decimal_places = 0

    return f"{value:.{decimal_places}f}{separator}{units[index]}"
