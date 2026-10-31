"""Writes the results to a single HTML file, with the graphs embedded in it."""

from html import escape
from pathlib import Path

from results import Column, ResultRow, get_columns, is_best

STYLE = """
body { font-family: system-ui, sans-serif; margin: 2rem; color: #1a1a1a; background: #fff; }
h1 { font-size: 1.5rem; }
h2 { font-size: 1.2rem; margin-top: 2rem; }
table { border-collapse: collapse; font-variant-numeric: tabular-nums; }
th, td { border: 1px solid #ccc; padding: 0.4rem 0.7rem; text-align: right; white-space: nowrap; }
th:first-child, td:first-child { text-align: left; }
th { background: #f0f0f0; cursor: pointer; user-select: none; }
th[data-order="ascending"]::after { content: " \\25B2"; }
th[data-order="descending"]::after { content: " \\25BC"; }
tbody.fixed td { color: #555; background: #fafafa; }
td.best { font-weight: bold; color: #0a6b2d; background: #e3f5e8; }
pre { white-space: pre-wrap; }
img { max-width: 100%; }
img.mean-vmaf { width: 800px; }
.per-frame { display: grid; grid-template-columns: repeat(auto-fit, minmax(380px, 1fr)); gap: 1rem; }
details { margin: 0.5rem 0; }
summary { cursor: pointer; font-weight: bold; }
@media (prefers-color-scheme: dark) {
  body { color: #e6e6e6; background: #181818; }
  th, td { border-color: #444; }
  th { background: #2a2a2a; }
  tbody.fixed td { color: #aaa; background: #202020; }
  td.best { color: #7ee2a0; background: #183a24; }
  img { background: #fff; }
}
"""

# Sorts the transcodes when a column's heading is clicked. The original and reference videos are
# in a separate tbody, so they stay at the top. Rows without a value go last.
SCRIPT = """
document.querySelectorAll("th").forEach((heading, index) => {
  heading.addEventListener("click", () => {
    const order = heading.dataset.order === "ascending" ? "descending" : "ascending";
    document.querySelectorAll("th").forEach((th) => delete th.dataset.order);
    heading.dataset.order = order;
    const tbody = document.querySelector("tbody.transcodes");
    const value = (row) => row.children[index].dataset.value;
    const rows = [...tbody.rows].sort((a, b) => {
      const [x, y] = [value(a), value(b)];
      if (x === "") return 1;
      if (y === "") return -1;
      const comparison = isNaN(x) || isNaN(y) ? x.localeCompare(y) : x - y;
      return order === "ascending" ? comparison : -comparison;
    });
    tbody.append(...rows);
  });
});
"""


def table_row(row: ResultRow, columns: list[Column], rows: list[ResultRow]) -> str:
    cells = []
    for column in columns:
        value = column.value(row)
        best = ' class="best"' if is_best(column, row, rows) else ""
        data_value = "" if value is None else escape(str(value))
        cells.append(f'<td data-value="{data_value}"{best}>{escape(column.text(row))}</td>')
    return f"<tr>{''.join(cells)}</tr>"


def write_report(
    report_path: Path,
    title: str,
    first_column: str,
    metrics: list[str],
    rows: list[ResultRow],
    notes: list[str],
    mean_vmaf_graph: str | None,
    decimal_places: int,
) -> None:
    """Write the HTML report. Graphs are PNG data URIs, so the report is a single file."""
    columns = get_columns(first_column, metrics, decimal_places)
    headings = "".join(f"<th>{escape(column.name)}</th>" for column in columns)
    fixed_rows = "".join(table_row(row, columns, rows) for row in rows if not row.is_transcode)
    transcode_rows = "".join(table_row(row, columns, rows) for row in rows if row.is_transcode)

    sections = []
    if mean_vmaf_graph:
        sections.append(
            f'<h2>Mean VMAF</h2>\n<img class="mean-vmaf" src="{mean_vmaf_graph}" alt="Mean VMAF">'
        )
    transcodes = [row for row in rows if row.is_transcode]
    if transcodes:
        sections.append("<h2>Per-frame Scores</h2>")
    for row in transcodes:
        images = "".join(
            f'<img src="{graph}" alt="Per-frame {escape(metric)}">'
            for metric, graph in row.per_frame_graphs.items()
        )
        sections.append(
            f"<details>\n<summary>{escape(row.label)}</summary>\n"
            f'<div class="per-frame">{images}</div>\n</details>'
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)}</title>
<style>{STYLE}</style>
</head>
<body>
<h1>{escape(title)}</h1>
<p>{escape("/".join(metrics))} values are the mean of the per-frame scores. The per-frame graphs
below show any dips in quality. The best values are in green. Click a column's heading to sort
the transcodes by it.</p>
<table>
<thead><tr>{headings}</tr></thead>
<tbody class="fixed">{fixed_rows}</tbody>
<tbody class="transcodes">{transcode_rows}</tbody>
</table>
<pre>{escape(chr(10).join(notes))}</pre>
{chr(10).join(sections)}
<script>{SCRIPT}</script>
</body>
</html>
"""
    report_path.write_text(html, encoding="utf-8")
