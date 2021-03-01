import json
import os

import matplotlib.pyplot as plt
import numpy as np

from utils import force_decimal_places, line, Logger, plot_graph

log = Logger('save_metrics')


def get_metrics_save_table(comparison_table, json_file_path, args, decimal_places, data_for_current_row, 
						   table, output_folder, time_taken, crf_or_preset=None):
	with open(json_file_path, 'r') as f:
		file_contents = json.load(f)

	# Get the VMAF score of each frame from the JSON file created by libvmaf.
	vmaf_scores = [frame['metrics']['vmaf'] for frame in file_contents['frames']]

	# Calculate the mean, minimum and standard deviation.
	mean_vmaf = force_decimal_places(np.mean(vmaf_scores), decimal_places)
	min_vmaf = force_decimal_places(min(vmaf_scores), decimal_places)
	vmaf_std = force_decimal_places(np.std(vmaf_scores), decimal_places)

	frame_numbers = [frame['frameNum'] for frame in file_contents['frames']]

	plot_graph(f'VMAF\nn_subsample: {args.subsample}', 'Frame Number', 'VMAF', frame_numbers,
			   vmaf_scores, os.path.join(output_folder, 'VMAF'))

	# Add the VMAF values to the table.
	data_for_current_row.append(f'{min_vmaf} | {vmaf_std} | {mean_vmaf}')

	ssim_string = ''
	psnr_string = ''
	
	if args.calculate_ssim:
		ssim_string = '/SSIM'
		# Get the SSIM score of each frame from the JSON file created by libvmaf.
		ssim_scores = [ssim['metrics']['ssim'] for ssim in file_contents['frames']]

		mean_ssim = force_decimal_places(np.mean(ssim_scores), decimal_places)
		min_ssim = force_decimal_places(min(ssim_scores), decimal_places)
		ssim_std = force_decimal_places(np.std(ssim_scores), decimal_places) # Standard deviation.
	
		log.info(f'Creating SSIM graph...')
		plot_graph(f'SSIM\nn_subsample: {args.subsample}', 'Frame Number', 'SSIM', frame_numbers,
			       ssim_scores, mean_ssim, os.path.join(output_folder, 'SSIM'))

		# Add the SSIM values to the table.
		data_for_current_row.append(f'{min_ssim} | {ssim_std} | {mean_ssim}')

	if args.calculate_psnr:
		psnr_string = '/PSNR'
		# Get the PSNR score of each frame from the JSON file created by libvmaf.
		psnr_scores = [psnr['metrics']['psnr'] for psnr in file_contents['frames']]

		mean_psnr = force_decimal_places(np.mean(psnr_scores), decimal_places)
		min_psnr = force_decimal_places(min(psnr_scores), decimal_places)
		psnr_std = force_decimal_places(np.std(psnr_scores), decimal_places) # Standard deviation.

		log.info(f'Creating PSNR graph...')
		plot_graph(f'PSNR\nn_subsample: {args.subsample}', 'Frame Number', 'PSNR', frame_numbers,
				   psnr_scores, mean_psnr, os.path.join(output_folder, 'PSNR'))

		# Add the PSNR values to the table.
		data_for_current_row.append(f'{min_psnr} | {psnr_std} | {mean_psnr}')

	if not args.no_transcoding_mode:
		data_for_current_row.insert(0, crf_or_preset)
		data_for_current_row.insert(1, time_taken)
	
	table.add_row(data_for_current_row)
	table_title = f'VMAF{ssim_string}{psnr_string} values are in the format: Min | Standard Deviation | Mean'

	# Write the table to the Table.txt file.
	with open(comparison_table, 'w') as f:
		f.write(table.get_string(title=table_title))

	log.info(f'{comparison_table} has been updated.')
	line()
	return float(mean_vmaf)