"""The rows of the results table, and how each column is shown."""

from collections.abc import Callable
from dataclasses import dataclass, field

from rich.console import Console
from rich.table import Table
from rich.text import Text

from utils import format_si


@dataclass
class ResultRow:
    """One row of the table: the original video, the reference video or a transcode."""

    label: str
    codec: str  # The video codec, which is listed under the table for the original and reference.
    size: int  # In bytes.
    bitrate: float | None  # The video bitrate in bits per second, if it could be found.
    bitrate_source: str | None  # The bitrate's confidence and method.
    frame_count: int | None = None  # The number of video frames, if they could be counted.
    transcode_time: float | None = None  # None if the video wasn't transcoded this time.
    mean_scores: dict[str, float] = field(default_factory=dict)  # Only set for transcodes.
    per_frame_graphs: dict[str, str] = field(default_factory=dict)  # Metric -> PNG data URI.

    @property
    def is_transcode(self) -> bool:
        return bool(self.mean_scores)


@dataclass
class Column:
    name: str
    # The raw value is used to sort the rows and to find the highest value. None means "no value".
    value: Callable[[ResultRow], float | str | None]
    text: Callable[[ResultRow], str]
    # Whether the highest value is highlighted, as the best one. Only the quality metrics are,
    # because e.g. the smallest size or the lowest bitrate usually just means lower quality.
    highlight_highest: bool = False


def get_columns(first_column: str, metrics: list[str], decimal_places: int) -> list[Column]:
    def number(value: float | None) -> str:
        return "-" if value is None else f"{value:.{decimal_places}f}"

    def metric_column(metric: str) -> Column:
        return Column(
            metric,
            lambda row: row.mean_scores.get(metric),
            lambda row: number(row.mean_scores.get(metric)),
            highlight_highest=True,
        )

    return [
        Column(first_column, lambda row: row.label, lambda row: row.label),
        Column(
            "Time Taken (s)",
            lambda row: row.transcode_time,
            lambda row: number(row.transcode_time),
        ),
        Column(
            "Size",
            lambda row: row.size,
            lambda row: format_si(row.size, "B", decimal_places),
        ),
        Column(
            "Video Bitrate",
            lambda row: row.bitrate,
            lambda row: (
                "N/A" if row.bitrate is None else format_si(row.bitrate, "bps", decimal_places)
            ),
        ),
    ] + [metric_column(metric) for metric in metrics]


def is_best(column: Column, row: ResultRow, rows: list[ResultRow]) -> bool:
    """Return whether the row has the highest value in a highlighted column, out of the
    transcodes.

    Nothing is the best if there is only one transcode to compare.
    """
    values = [column.value(r) for r in rows if r.is_transcode and column.value(r) is not None]
    if not column.highlight_highest or not row.is_transcode or len(values) < 2:
        return False
    return column.value(row) == max(values)


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


def print_results(
    first_column: str,
    metrics: list[str],
    rows: list[ResultRow],
    notes: list[str],
    decimal_places: int,
) -> None:
    """Print the results and the notes underneath them in the terminal."""
    columns = get_columns(first_column, metrics, decimal_places)
    table = Table(
        caption=f"{'/'.join(metrics)} values are the mean of the per-frame scores. "
        "The best values are in green.",
        caption_justify="left",
    )
    for index, column in enumerate(columns):
        # The first column is the labels, and the rest are numbers. If the terminal is too
        # narrow, "fold" wraps the values onto more lines rather than cutting them off.
        justify = "left" if index == 0 else "right"
        table.add_column(column.name, justify=justify, overflow="fold")

    fixed_rows = [row for row in rows if not row.is_transcode]
    for row in rows:
        # Text objects are used so that e.g. "[" in a label isn't read as Rich's markup.
        cells = [
            Text(column.text(row), style="bold green" if is_best(column, row, rows) else "")
            for column in columns
        ]
        # The original and reference videos are dimmed, and a line separates them from the
        # transcodes.
        table.add_row(
            *cells,
            style=None if row.is_transcode else "dim",
            end_section=bool(fixed_rows) and row is fixed_rows[-1],
        )

    console = Console()
    if not console.is_terminal:
        # Rich assumes a width of 80 characters if the output isn't a terminal (e.g. it is
        # redirected to a file), so don't limit the width.
        console.width = 1000
    console.print(table)
    console.print("\n".join(notes), markup=False, highlight=False)
