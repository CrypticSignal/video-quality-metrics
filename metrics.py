import json
from argparse import Namespace
from pathlib import Path
from statistics import fmean, pstdev

# The name that libvmaf uses for each metric in its JSON log.
LIBVMAF_NAMES = {"VMAF": "vmaf", "PSNR": "psnr_y", "SSIM": "float_ssim"}


def enabled_metrics(args: Namespace) -> list[str]:
    metrics = ["VMAF"]
    if not args.disable_psnr:
        metrics.append("PSNR")
    if not args.disable_ssim:
        metrics.append("SSIM")
    return metrics


def read_per_frame_scores(
    json_path: Path, metrics: list[str]
) -> tuple[list[int], dict[str, list[float]]]:
    """Read libvmaf's JSON log.

    Returns the frame numbers and the per-frame scores of each metric, e.g.
    ([0, 1, ...], {"VMAF": [95.1, 94.8, ...], "PSNR": [...]})
    """
    with open(json_path, encoding="utf-8") as f:
        frames = json.load(f)["frames"]

    frame_numbers = [frame["frameNum"] for frame in frames]
    scores = {
        metric: [frame["metrics"][LIBVMAF_NAMES[metric]] for frame in frames] for metric in metrics
    }
    return frame_numbers, scores


def summarise(scores: list[float], decimal_places: int) -> str:
    """Return the scores in the format "Min | Standard Deviation | Mean"."""
    return " | ".join(
        f"{value:.{decimal_places}f}" for value in (min(scores), pstdev(scores), fmean(scores))
    )
