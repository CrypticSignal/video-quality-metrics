import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
from prettytable import PrettyTable

from utils import force_decimal_places, line, Logger, plot_graph, get_metrics_list

log = Logger("save_metrics")


@dataclass
class MetricScores:
    min: float
    std: float
    mean: float


def load_frame_data(json_file_path: str) -> Tuple[List[Dict], List[int]]:
    if not os.path.isfile(json_file_path):
        print(f"The following file path does not exist:\n{json_file_path}")
        return [], []

    with open(json_file_path, "r") as f:
        try:
            file_contents = json.load(f)
        except json.JSONDecodeError:
            return [], []
        else:
            frames = file_contents["frames"]
            frame_numbers = [frame["frameNum"] for frame in frames]

            return frames, frame_numbers


def calculate_metric_scores(
    metric_scores: List[float], decimal_places: int
) -> MetricScores:
    """Calculate statistical scores for a given metric."""
    return MetricScores(
        min=force_decimal_places(min(metric_scores), decimal_places),
        std=force_decimal_places(np.std(metric_scores), decimal_places),
        mean=force_decimal_places(np.mean(metric_scores), decimal_places),
    )


def process_metric(
    metric_type: str,
    frames: List[Dict],
    frame_numbers: List[int],
    args,
    output_folder: str,
    decimal_places: int,
) -> Optional[MetricScores]:
    metric_lookup = {"VMAF": "vmaf", "PSNR": "psnr_y"}
    metric_key = metric_lookup[metric_type]

    if len(frames):
        if not frames[0]["metrics"][metric_key]:
            return None

        metric_scores = [frame["metrics"][metric_key] for frame in frames]
        scores = calculate_metric_scores(metric_scores, decimal_places)

        plot_graph(
            f"{metric_type}\nlibvmaf n_subsample: {args.n_subsample}",
            "Frame Number",
            metric_type,
            frame_numbers,
            metric_scores,
            scores.mean,
            os.path.join(output_folder, metric_type),
        )

        return scores


def write_table_to_file(
    table_path: str, table: PrettyTable, metric_types: List[str]
) -> None:
    collected_metric_types = "/".join(metric_types)
    table_title = f"{collected_metric_types} values are in the format: Min | Standard Deviation | Mean"

    with open(table_path, "w") as f:
        f.write(f"{table_title}\n")
        f.write(table.get_string())


def process_metrics(
    comparison_table: str,
    json_file_path: str,
    args,
    decimal_places: int,
    data_for_current_row: List[str],
    table: PrettyTable,
    output_folder: str,
    time_taken: Optional[float],
    first_column_data: str,
) -> float:
    frames, frame_numbers = load_frame_data(json_file_path)

    metrics_list = get_metrics_list(args)
    vmaf_mean = None

    for metric_type in metrics_list:
        scores = process_metric(
            metric_type, frames, frame_numbers, args, output_folder, decimal_places
        )

        if scores:
            data_for_current_row.append(f"{scores.min} | {scores.std} | {scores.mean}")
            if metric_type == "VMAF":
                vmaf_mean = scores.mean

    if not args.no_transcoding_mode:
        data_for_current_row.insert(0, first_column_data)
        data_for_current_row.insert(1, time_taken)

    # Pad the row if it has fewer elements than the number of columns
    while len(data_for_current_row) < len(table._field_names):
        data_for_current_row.append("")

    table.add_row(data_for_current_row)
    write_table_to_file(comparison_table, table, metrics_list)

    if args.no_transcoding_mode:
        line()
        log.info(f"All done! Check out the '{output_folder}' folder.")

    return float(vmaf_mean) if vmaf_mean is not None else 0
