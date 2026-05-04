import logging
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any, Dict, List, Literal, Optional, Union

import matplotlib.pyplot as plt
import numpy as np
from ffmpeg import probe


class Logger:
    def __init__(
        self, name: str, filename: str = "logs.log", print_to_terminal: bool = True
    ) -> None:
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

    def info(self, msg: str) -> None:
        self._logger.info(msg)

    def warning(self, msg: str) -> None:
        self._logger.warning(msg)

    def debug(self, msg: str) -> None:
        self._logger.debug(msg)

    def error(self, msg: str) -> None:
        self._logger.error(msg)

    def close(self) -> None:
        handlers = self._logger.handlers[:]
        for handler in handlers:
            handler.close()
            self._logger.removeHandler(handler)


log = Logger("utils")


class Timer:
    def __init__(self) -> None:
        self._start_time = perf_counter()

    def start(self) -> None:
        self._start_time = perf_counter()

    def stop(self, decimal_places: int) -> float:
        time_to_convert = perf_counter() - self._start_time
        return round(time_to_convert, decimal_places)


@dataclass
class BitrateResult:
    bitrate: int
    confidence: str
    method: str


class VideoInfoProvider:
    def __init__(self, video_path: Union[str, Path]) -> None:
        self._video_path = str(video_path)
        self._probe_data: Optional[Dict[str, Any]] = None

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

        if not probe_data:
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
            log.info(
                f"Done! Bitrate: {format_value(result.bitrate, input_unit_type='bits', output_unit_type='bits')}ps | Confidence: {result.confidence} | Method: {result.method}"
            )
            return result

        # ---------------------------
        # Method 2 (Video Stream Metadata)
        # ---------------------------
        log.info("Determining video bitrate from video stream metadata...")
        result = self._get_bitrate_from_video_stream_metadata(streams)
        if result:
            log.info(
                f"Done! Bitrate: {format_value(result.bitrate, input_unit_type='bits', output_unit_type='bits')}ps | Confidence: {result.confidence} | Method: {result.method}"
            )
            return result

        # ---------------------------
        # Method 3 (overall bitrate reported by container minus reported audio bitrate(s))
        # ---------------------------
        log.info(
            "Determining video bitrate from overall bitrate reported by container (minus reported audio bitrate(s))..."
        )
        result = self._get_bitrate_from_container_minus_audio(format_info, streams)
        if result:
            log.info(
                f"Done! Bitrate: {format_value(result.bitrate, input_unit_type='bits', output_unit_type='bits')}ps | Confidence: {result.confidence} | Method: {result.method}"
            )
            return result

        log.info("Unable to determine video bitrate.")
        return None

    def _probe_file(self) -> Optional[Dict[str, Any]]:
        if self._probe_data is not None:
            return self._probe_data

        try:
            self._probe_data = probe(self._video_path)
            return self._probe_data
        except Exception as e:
            log.info(
                f"Unable to probe file with FFprobe. Cannot determine video bitrate. Error:\n{e}"
            )
            return None

    def _parse_duration(self, value: Any) -> float:
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

            total_bytes = 0
            packet_count = 0

            last_log_time = start_time
            LOG_FREQUENCY_SECONDS = 1
            last_pts_time = 0.0

            with subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1,
            ) as process:
                if process.stdout is None:
                    return None

                for cmd_line in process.stdout:
                    try:
                        pts_time_str, size_str = cmd_line.strip().split(",")
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

            if packet_count == 0:
                return None

            bitrate = int((total_bytes * 8) / duration)

            return BitrateResult(bitrate, "High", "Video Packet Sizes")

        except Exception as e:
            log.info(f"Unable to determine video bitrate. Error:\n{e}")
            return None

    def _get_bitrate_from_video_stream_metadata(
        self, streams: List[Dict[str, Any]]
    ) -> Optional[BitrateResult]:
        for stream in streams:
            if stream.get("codec_type") == "video":
                bitrate = stream.get("bit_rate")
                if bitrate:
                    return BitrateResult(int(bitrate), "Medium", "Video Stream Metadata")

        log.info("Unable to determine video bitrate.")
        return None

    def _get_bitrate_from_container_minus_audio(
        self,
        format_info: Dict[str, Any],
        streams: List[Dict[str, Any]],
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

    def get_framerate_fraction(self) -> str:
        probe_data = self._probe_file()
        if not probe_data:
            return "N/A"
        for stream in probe_data.get("streams", []):
            if stream.get("codec_type") == "video":
                return stream.get("r_frame_rate", "N/A")
        return "N/A"

    def get_framerate_float(self) -> float:
        fraction = self.get_framerate_fraction()
        if fraction == "N/A":
            return 0.0
        try:
            numerator, denominator = map(int, fraction.split("/"))
            if denominator == 0:
                return 0.0
            return numerator / denominator
        except (ValueError, AttributeError):
            return 0.0

    def get_duration_str(self, decimal_places: int = 3) -> str:
        duration = self.get_duration()
        return f"{duration:.{decimal_places}f} s" if duration >= 0 else "N/A"

    def get_duration(self) -> float:
        try:
            probe_data = self._probe_file()
            if probe_data and "format" in probe_data and "duration" in probe_data["format"]:
                return float(probe_data["format"]["duration"])
            return -1.0
        except Exception:
            return -1.0

    def get_all_info(self) -> Dict[str, Any]:
        probe_data = self._probe_file()
        return probe_data if probe_data else {}


def cut_video(
    video_path: str,
    filename: str,
    args: Any,
    output_ext: str,
    output_folder: str,
    comparison_table: str,
) -> str:
    cut_version_filename = f"{Path(filename).stem} [{args.transcode_length}s]{output_ext}"
    output_file_path = Path(output_folder) / cut_version_filename

    log.info(f"Cutting the video to a length of {args.transcode_length} seconds...")
    subprocess.run(
        [
            "ffmpeg",
            "-loglevel",
            "debug",
            "-y",
            "-i",
            str(video_path),
            "-t",
            str(args.transcode_length),
            "-map",
            "0",
            "-c",
            "copy",
            str(output_file_path),
        ],
        check=True,
    )
    log.info("Done!")

    time_message = (
        f" for {args.transcode_length} seconds"
        if int(args.transcode_length) > 1
        else "for 1 second"
    )

    with open(comparison_table, "w") as f:
        f.write(f"You chose to encode {filename}{time_message} using {args.encoder}.")

    return str(output_file_path)


def exit_program(message: str) -> None:
    line()
    log.info(f"{message}\nThis program will now exit.")
    line()
    sys.exit()


def force_decimal_places(value: Union[float, int], decimal_places: int) -> str:
    return f"{value:.{decimal_places}f}"


def line() -> None:
    try:
        width, _ = os.get_terminal_size()
    except OSError:
        width = 80
    log.info("-" * width)


def plot_graph(
    title: str,
    x_label: str,
    y_label: str,
    x_values: List[Any],
    y_values: List[Union[int, float]],
    mean_y_value: Union[int, float, str],
    save_path: str,
    bar_graph: bool = False,
) -> None:
    def generate_colors(n: int) -> List[Any]:
        return [plt.cm.hsv(i / max(n, 1)) for i in range(n)]

    plt.figure(figsize=(10, 6))
    plt.suptitle(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)

    if bar_graph:
        x_positions = np.arange(len(x_values))
        plt.bar(x_positions, y_values, color=generate_colors(len(x_values)))
        plt.xticks(x_positions, x_values, rotation=45, ha="right")

        y_min = max(0, min(y_values) - 1) if y_values else 0
        y_max = min(100, max(y_values) + 1) if y_values else 100
        plt.ylim(y_min, y_max)

        for i, v in enumerate(y_values):
            y_position = (y_min + v) / 2
            plt.text(i, y_position, str(v), ha="center", va="center")

    else:
        plt.plot(x_values, y_values, label=f"{y_label} ({mean_y_value})")
        plt.legend(loc="lower right")

    plt.tight_layout()
    plt.savefig(save_path, bbox_inches="tight")
    plt.close()


def write_supplementary_info(table_path: str, video_filename: str, args: Any) -> str:
    with open(table_path, "a") as f:
        supplementary_info = (
            f"\nOriginal File: {video_filename}\n"
            f"FFmpeg output options: {args.output_options}\n"
            + (
                f"Filter(s) applied to original video before quality metrics calculation: {args.video_filters}\n"
                if args.video_filters
                else ""
            )
            + f"libvmaf n_subsample: {args.n_subsample}"
        )
        f.write(supplementary_info)
        return supplementary_info


def get_metrics_list(args: Any) -> List[str]:
    metrics_list = [
        "VMAF",
        "PSNR" if not args.disable_psnr else None,
        "SSIM" if not args.disable_ssim else None,
    ]

    return [m for m in metrics_list if m is not None]


def format_value(
    value: Any,
    decimal_places: int = 3,
    system: Literal["si", "iec"] = "si",
    input_unit_type: Literal["bytes", "bits"] = "bytes",
    output_unit_type: Literal["bytes", "bits"] = "bytes",
    default: str = "N/A",
    separator: str = " ",
) -> str:
    try:
        int(value)
    except (ValueError, TypeError):
        return str(value)

    if system not in ("si", "iec"):
        raise ValueError("system must be 'si' or 'iec'")

    if input_unit_type not in ("bytes", "bits") or output_unit_type not in ("bytes", "bits"):
        raise ValueError("units must be 'bytes' or 'bits'")

    try:
        value_float = float(value)
    except (TypeError, ValueError):
        return default

    if value_float < 0:
        return default

    if input_unit_type == "bits" and output_unit_type == "bytes":
        value_float = value_float / 8.0

    if input_unit_type == "bytes" and output_unit_type == "bits":
        value_float = value_float * 8.0

    suffix = "b" if output_unit_type == "bits" else "B"

    if system == "iec":
        base, prefixes = 1024, ["", "Ki", "Mi", "Gi", "Ti", "Pi"]
    else:
        base, prefixes = 1000, ["", "K", "M", "G", "T", "P"]

    units = [p + suffix for p in prefixes]

    index = 0
    while value_float >= base and index < len(units) - 1:
        value_float = value_float / base
        index += 1

    if index == 0:
        decimal_places = 0

    return f"{value_float:.{decimal_places}f}{separator}{units[index]}"
