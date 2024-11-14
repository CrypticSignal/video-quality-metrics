import json
import os

import numpy as np

from utils import force_decimal_places, line, Logger, plot_graph, get_metrics_list

log = Logger("save_metrics")


def get_metrics_save_table(
    comparison_table,
    json_file_path,
    args,
    decimal_places,
    data_for_current_row,
    table,
    output_folder,
    time_taken,
    first_column_data,
):
    with open(json_file_path, "r") as f:
        file_contents = json.load(f)

    frames = file_contents["frames"]
    frame_numbers = [frame["frameNum"] for frame in frames]

    # Maps the metric type to the corresponding JSON metric key.
    metric_lookup = {
        "VMAF": "vmaf",
        "PSNR": "psnr_y",
        "SSIM": "float_ssim",
        "MS-SSIM": "float_ms_ssim",
    }

    # Only used for accessing the VMAF mean score to return at the end of this method.
    collected_scores = {}
    # Process metrics captured for each requested metric type.
    metrics_list = get_metrics_list(args)
    for metric_type in metrics_list:
        metric_key = metric_lookup[metric_type]
        if frames[0]["metrics"][metric_key]:
            # Get the <metric_type> score of each frame from the JSON file created by libvmaf.
            metric_scores = [frame["metrics"][metric_key] for frame in frames]

            # Calculate the mean, minimum and standard deviation scores across all frames.
            mean_score = force_decimal_places(np.mean(metric_scores), decimal_places)
            min_score = force_decimal_places(min(metric_scores), decimal_places)
            std_score = force_decimal_places(np.std(metric_scores), decimal_places)

            collected_scores[metric_type] = {
                "min": min_score,
                "std": std_score,
                "mean": mean_score,
            }

            plot_graph(
                f"{metric_type}\nlibvmaf n_subsample: {args.n_subsample}",
                "Frame Number",
                metric_type,
                frame_numbers,
                metric_scores,
                mean_score,
                os.path.join(output_folder, metric_type),
            )

            # Add the <metric_type> values to the table.
            data_for_current_row.append(f"{min_score} | {std_score} | {mean_score}")

    if not args.no_transcoding_mode:
        data_for_current_row.insert(0, first_column_data)
        data_for_current_row.insert(1, time_taken)

    table.add_row(data_for_current_row)

    collected_metric_types = "/".join(metrics_list)
    table_title = f"{collected_metric_types} values are in the format: Min | Standard Deviation | Mean"

    # Write the table to metrics_table.txt
    with open(comparison_table, "w") as f:
        f.write(f"{table_title}\n")
        f.write(table.get_string())

    if args.no_transcoding_mode:
        line()
        log.info(f"All done! Check out the '{output_folder}' folder.")

    return float(collected_scores["VMAF"]["mean"])
