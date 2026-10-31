"""The rows of the results table, and how each column is shown."""

from collections.abc import Callable
from dataclasses import dataclass, field

from utils import format_si


@dataclass
class ResultRow:
    """One row of the table: the original video, the reference video or a transcode."""

    label: str
    encoder: str  # For the original and reference videos, this is their codec.
    size: int  # In bytes.
    bitrate: float | None  # The video bitrate in bits per second, if it could be found.
    bitrate_source: str | None  # The bitrate's confidence and method.
    duration: float  # In seconds.
    transcode_time: float | None = None  # None if the video wasn't transcoded this time.
    mean_scores: dict[str, float] = field(default_factory=dict)  # Only set for transcodes.
    per_frame_graphs: dict[str, str] = field(default_factory=dict)  # Metric -> PNG data URI.

    @property
    def is_transcode(self) -> bool:
        return bool(self.mean_scores)


@dataclass
class Column:
    name: str
    # The raw value is used to sort the rows and to find the best value. None means "no value".
    value: Callable[[ResultRow], float | str | None]
    text: Callable[[ResultRow], str]
    # Whether a "higher" or "lower" value is better, or None if neither is.
    better: str | None = None


def get_columns(first_column: str, metrics: list[str], decimal_places: int) -> list[Column]:
    def number(value: float | None) -> str:
        return "-" if value is None else f"{value:.{decimal_places}f}"

    def metric_column(metric: str) -> Column:
        return Column(
            metric,
            lambda row: row.mean_scores.get(metric),
            lambda row: number(row.mean_scores.get(metric)),
            "higher",
        )

    return [
        Column(first_column, lambda row: row.label, lambda row: row.label),
        Column("Encoder", lambda row: row.encoder, lambda row: row.encoder),
        Column(
            "Transcode Time (s)",
            lambda row: row.transcode_time,
            lambda row: number(row.transcode_time),
            "lower",
        ),
        Column(
            "Size",
            lambda row: row.size,
            lambda row: format_si(row.size, "B", decimal_places),
            "lower",
        ),
        Column(
            "Video Bitrate",
            lambda row: row.bitrate,
            lambda row: (
                "N/A" if row.bitrate is None else format_si(row.bitrate, "bps", decimal_places)
            ),
            "lower",
        ),
        Column("Duration (s)", lambda row: row.duration, lambda row: number(row.duration)),
    ] + [metric_column(metric) for metric in metrics]


def is_best(column: Column, row: ResultRow, rows: list[ResultRow]) -> bool:
    """Return whether the row has the best value in the column, out of the transcodes.

    Nothing is the best if there is only one transcode to compare.
    """
    values = [column.value(r) for r in rows if r.is_transcode and column.value(r) is not None]
    if column.better is None or not row.is_transcode or len(values) < 2:
        return False
    best = max(values) if column.better == "higher" else min(values)
    return column.value(row) == best


def describe_bitrate_sources(rows: list[ResultRow]) -> list[str]:
    """Describe how each row's video bitrate was found, e.g.
    ["Video bitrate confidence = high, method = video packet sizes"].

    If the rows differ, each row is listed so that a less reliable bitrate stands out.
    """
    known_sources = {row.label: row.bitrate_source for row in rows if row.bitrate_source}
    if not known_sources:
        return []
    if len(set(known_sources.values())) == 1:
        return [f"Video bitrate {next(iter(known_sources.values()))}"]
    return ["Video bitrate:"] + [f"  {label}: {source}" for label, source in known_sources.items()]
