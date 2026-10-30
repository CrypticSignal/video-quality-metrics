from pathlib import Path

import matplotlib.pyplot as plt


def plot_per_frame_graph(
    metric: str,
    frame_numbers: list[int],
    scores: list[float],
    mean_score: str,
    n_subsample: int,
    save_path: Path,
) -> None:
    plt.figure(figsize=(10, 6))
    plt.suptitle(f"{metric}\nlibvmaf n_subsample: {n_subsample}")
    plt.xlabel("Frame Number")
    plt.ylabel(metric)
    plt.plot(frame_numbers, scores, label=f"{metric} ({mean_score})")
    plt.legend(loc="lower right")
    save(save_path)


def plot_mean_vmaf_graph(
    x_label: str, labels: list[str], mean_vmafs: list[float], decimal_places: int, save_path: Path
) -> None:
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

    save(save_path)


def save(save_path: Path) -> None:
    plt.tight_layout()
    plt.savefig(save_path, bbox_inches="tight")
    plt.close()
