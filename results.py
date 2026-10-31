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
            # A lower bitrate isn't necessarily better, because it usually means lower quality.
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


def print_results(
    first_column: str,
    metrics: list[str],
    rows: list[ResultRow],
    notes: list[str],
    decimal_places: int,
) -> None:
    """Print the table and the notes underneath it in the terminal."""
    columns = get_columns(first_column, metrics, decimal_places)
    table = Table(
        caption=f"{'/'.join(metrics)} values are the mean of the per-frame scores. "
        "The best values are in bold.",
        caption_justify="left",
    )
    for index, column in enumerate(columns):
        # The first two columns are text, and the rest are numbers.
        table.add_column(column.name, justify="left" if index < 2 else "right")

    fixed_rows = [row for row in rows if not row.is_transcode]
    for row in rows:
        # Text objects are used so that e.g. "[" in a label isn't read as Rich's markup.
        cells = [
            Text(column.text(row), style="bold green" if is_best(column, row, rows) else "")
            for column in columns
        ]
        # A line separates the original and reference videos from the transcodes.
        table.add_row(
            *cells,
            style=None if row.is_transcode else "dim",
            end_section=bool(fixed_rows) and row is fixed_rows[-1],
        )

    # Rich squashes a table that is wider than the terminal, which cuts values off, and assumes
    # a width of 80 characters if the output isn't a terminal (e.g. it is redirected to a file).
    # So the table is always printed at its full width, like any other long line.
    console = Console()
    # measure() is limited to the console's width unless it is given a wider one.
    full_width = console.measure(table, options=console.options.update_width(10_000)).maximum
    console.width = max(console.width, full_width)
    console.print(table)
    console.print("\n".join(notes), markup=False, highlight=False)
