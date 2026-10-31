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
            "Transcode Time (s)",
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


def longest_word(text: str) -> int:
    return max((len(word) for word in text.split()), default=len(text))


def print_results(
    first_column: str,
    metrics: list[str],
    rows: list[ResultRow],
    notes: list[str],
    decimal_places: int,
) -> None:
    """Print the results and the notes underneath them in the terminal.

    The table is fitted to the terminal, or printed as a list if the terminal is too narrow, so
    that no values are split or cut off.
    """
    columns = get_columns(first_column, metrics, decimal_places)
    caption = (
        f"{'/'.join(metrics)} values are the mean of the per-frame scores. "
        "The best values are in green."
    )

    def cell(column: Column, row: ResultRow) -> Text:
        # Text objects are used so that e.g. "[" in a label isn't read as Rich's markup.
        best = is_best(column, row, rows)
        return Text(column.text(row), style="bold green" if best else "")

    texts = [[column.text(row) for column in columns] for row in rows]
    # The width that each column needs to fit its heading and values on one line.
    widths = [
        max(len(column.name), *(len(text[index]) for text in texts))
        for index, column in enumerate(columns)
    ]
    # Each column has a border and a space on either side, and the table has a border at the end.
    borders_width = 3 * len(columns) + 1
    full_width = max(sum(widths) + borders_width, len(caption), *(len(note) for note in notes))

    # To fit a narrow terminal, the headings and the labels in the first column can wrap at
    # spaces, but the other values are never split. So each column's minimum width is its
    # longest word or value.
    min_widths = [
        max(
            longest_word(column.name),
            *(longest_word(text[0]) if index == 0 else len(text[index]) for text in texts),
        )
        for index, column in enumerate(columns)
    ]
    console = Console()
    available_width = console.width - borders_width
    if console.is_terminal and sum(min_widths) > available_width:
        print_list(console, columns, rows, cell, caption)
    else:
        if console.is_terminal:
            # Narrow the column that can lose the most width, one character at a time, until
            # the table fits. Rich's own way of fitting a table can cut values off.
            while sum(widths) > available_width:
                index = max(range(len(columns)), key=lambda i: widths[i] - min_widths[i])
                widths[index] -= 1
        else:
            # Rich assumes a width of 80 characters if the output isn't a terminal (e.g. it is
            # redirected to a file), so the table is printed at its full width instead.
            console.width = max(console.width, full_width)
        console.print(build_table(columns, rows, widths, cell, caption))

    console.print("\n".join(notes), markup=False, highlight=False)


def build_table(
    columns: list[Column],
    rows: list[ResultRow],
    widths: list[int],
    cell: Callable[[Column, ResultRow], Text],
    caption: str,
) -> Table:
    table = Table(caption=caption, caption_justify="left")
    for index, (column, width) in enumerate(zip(columns, widths)):
        # The first column is the labels, and the rest are numbers.
        table.add_column(column.name, justify="left" if index == 0 else "right", width=width)
    fixed_rows = [row for row in rows if not row.is_transcode]
    for row in rows:
        # A line separates the original and reference videos from the transcodes.
        table.add_row(
            *(cell(column, row) for column in columns),
            style=None if row.is_transcode else "dim",
            end_section=bool(fixed_rows) and row is fixed_rows[-1],
        )
    return table


def print_list(
    console: Console,
    columns: list[Column],
    rows: list[ResultRow],
    cell: Callable[[Column, ResultRow], Text],
    caption: str,
) -> None:
    """Print each row as a heading followed by its values, one per line."""
    for row in rows:
        console.print(Text(row.label, style="bold" if row.is_transcode else "bold dim"))
        for column in columns[1:]:
            value = cell(column, row)
            # The original and reference videos have no quality metrics, so they are skipped.
            if value.plain != "-":
                console.print(Text(f"  {column.name}: ") + value)
        console.print()
    console.print(caption, markup=False, highlight=False)
