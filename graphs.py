"""Plots the graphs as PNG data URIs, so that they can be embedded in the HTML report."""

from base64 import b64encode
from io import BytesIO

import matplotlib

# The graphs are only saved, never shown in a window, so no GUI backend is needed.
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402


def plot_per_frame_graph(
    metric: str,
    frame_numbers: list[int],
    scores: list[float],
    mean_score: str,
    n_subsample: int,
) -> str:
    plt.figure(figsize=(10, 6))
    plt.suptitle(f"{metric}\nlibvmaf n_subsample: {n_subsample}")
    plt.xlabel("Frame Number")
    plt.ylabel(metric)
    plt.plot(frame_numbers, scores, label=f"{metric} ({mean_score})")
    plt.legend(loc="lower right")
    return to_data_uri()


def plot_mean_vmaf_graph(
    x_label: str, labels: list[str], mean_vmafs: list[float], decimal_places: int
) -> str:
    """Plot a bar graph of the mean VMAF achieved with each parameter value/combination."""
    plt.figure(figsize=(10, 6))
    plt.suptitle(f"{x_label} vs VMAF")
    plt.xlabel(x_label)
    plt.ylabel("VMAF")

    positions = range(len(labels))
    colours = [plt.cm.hsv(i / len(labels)) for i in positions]
    plt.bar(positions, mean_vmafs, color=colours)
    plt.xticks(positions, labels, rotation=45, ha="right")

    # Zoom in on the scores so that small differences are visible.
    y_min = max(0, min(mean_vmafs) - 1)
    y_max = min(100, max(mean_vmafs) + 1)
    plt.ylim(y_min, y_max)

    for position, vmaf in zip(positions, mean_vmafs):
        plt.text(position, (y_min + vmaf) / 2, f"{vmaf:.{decimal_places}f}", ha="center")

    return to_data_uri()


def to_data_uri() -> str:
    """Return the current figure as a PNG data URI, and close it."""
    buffer = BytesIO()
    plt.tight_layout()
    plt.savefig(buffer, format="png", bbox_inches="tight")
    plt.close()
    return "data:image/png;base64," + b64encode(buffer.getvalue()).decode("ascii")
