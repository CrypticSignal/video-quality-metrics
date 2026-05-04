import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from prettytable import PrettyTable

from utils import Logger, force_decimal_places, get_metrics_list, plot_graph

log = Logger("save_metrics")


@dataclass
class MetricScores:
    min: str
    std: str
    mean: str


def load_frame_data(json_file_path: str | Path) -> Tuple[List[Dict[str, Any]], List[int]]:
    file_path = Path(json_file_path)
    if not file_path.is_file():
        log.error(f"The following file path does not exist:\n{file_path}")
        return [], []

    with open(file_path, "r", encoding="utf-8") as f:
        try:
            file_contents = json.load(f)
        except json.JSONDecodeError:
            log.error(f"Failed to decode JSON from {file_path}")
            return [], []
        else:
            frames = file_contents.get("frames", [])
            frame_numbers = [frame.get("frameNum", i) for i, frame in enumerate(frames)]

            return frames, frame_numbers


def calculate_metric_scores(metric_scores: List[float], decimal_places: int) -> MetricScores:
    """Calculate statistical scores for a given metric."""
    scores_array = np.array(metric_scores)
    return MetricScores(
        min=force_decimal_places(np.min(scores_array), decimal_places),
        std=force_decimal_places(np.std(scores_array), decimal_places),
        mean=force_decimal_places(np.mean(scores_array), decimal_places),
    )


def process_metric(
    metric_type: str,
    frames: List[Dict[str, Any]],
    frame_numbers: List[int],
    args: Any,
    output_folder: str | Path,
    decimal_places: int,
) -> Optional[MetricScores]:
    metric_lookup = {"VMAF": "vmaf", "PSNR": "psnr_y", "SSIM": "float_ssim"}
    metric_key = metric_lookup.get(metric_type)

    if not metric_key:
        return None

    if frames:
        if metric_key not in frames[0].get("metrics", {}):
            return None

        metric_scores = [
            frame["metrics"][metric_key]
            for frame in frames
            if metric_key in frame.get("metrics", {})
        ]

        if not metric_scores:
            return None

        scores = calculate_metric_scores(metric_scores, decimal_places)

        plot_graph(
            f"{metric_type}\nlibvmaf n_subsample: {args.n_subsample}",
            "Frame Number",
            metric_type,
            frame_numbers[: len(metric_scores)],
            metric_scores,
            scores.mean,
            str(Path(output_folder) / metric_type),
        )

        return scores
    return None


def write_table_to_file(
    table_path: str | Path, table: PrettyTable, metric_types: List[str]
) -> None:
    collected_metric_types = "/".join(metric_types)
    table_title = (
        f"{collected_metric_types} values are in the format: Min | Standard Deviation | Mean"
    )

    with open(table_path, "w", encoding="utf-8") as f:
        f.write(f"{table_title}\n")
        f.write(table.get_string())


def process_metrics(
    comparison_table: str | Path,
    json_file_path: str | Path,
    args: Any,
    decimal_places: int,
    data_for_current_row: List[Any],
    table: PrettyTable,
    output_folder: str | Path,
    time_taken: Optional[float],
    first_column_data: str,
) -> None:
    frames, frame_numbers = load_frame_data(json_file_path)

    metrics_list = get_metrics_list(args)

    for metric_type in metrics_list:
        scores = process_metric(
            metric_type, frames, frame_numbers, args, output_folder, decimal_places
        )

        if scores:
            data_for_current_row.append(f"{scores.min} | {scores.std} | {scores.mean}")

    data_for_current_row.insert(0, first_column_data)
    data_for_current_row.insert(1, args.encoder)
    data_for_current_row.insert(2, time_taken if time_taken is not None else "N/A")

    # Pad the row if it has fewer elements than the number of columns
    while len(data_for_current_row) < len(table.field_names):
        data_for_current_row.append("")

    table.add_row(data_for_current_row)
    write_table_to_file(comparison_table, table, metrics_list)


def extract_mean_vmaf(json_file_path: str | Path) -> str:
    frames, _ = load_frame_data(json_file_path)
    if not frames:
        return "N/A"

    metric_key = "vmaf"
    if metric_key not in frames[0].get("metrics", {}):
        return "N/A"

    metric_scores = [
        frame["metrics"][metric_key] for frame in frames if metric_key in frame.get("metrics", {})
    ]

    if not metric_scores:
        return "N/A"

    return str(np.mean(metric_scores))
