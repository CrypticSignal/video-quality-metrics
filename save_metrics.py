import json
import os
import numpy as np
import matplotlib.pyplot as plt

from utils import line, force_decimal_places


def create_table_plot_metrics(comparison_table, json_file_path, args, decimal_places, data_for_current_row, 
							  table, output_folder, time_taken, crf_or_preset=None):

	with open(json_file_path, 'r') as f:
		file_contents = json.load(f)

	# Grab the VMAF data from the JSON file.
	vmaf_scores = [frame['metrics']['vmaf'] for frame in file_contents['frames']]
	mean_vmaf = force_decimal_places(np.mean(vmaf_scores), decimal_places)
	min_vmaf = force_decimal_places(min(vmaf_scores), decimal_places)
	vmaf_std = force_decimal_places(np.std(vmaf_scores), decimal_places) # Standard deviation.
	print(f'VMAF score: {mean_vmaf}, Standard Deviation: {vmaf_std}')

	frame_numbers = [frame['frameNum'] for frame in file_contents['frames']]

	print(f'Creating VMAF graph...')
	plt.plot(frame_numbers, vmaf_scores, label=f'VMAF ({mean_vmaf})')
	plt.suptitle(f'VMAF\nn_subsample: {args.subsample}')
	plt.xlabel('Frame Number')
	plt.ylabel('Value of Quality Metric')
	plt.legend(loc='lower right')
	plt.savefig(os.path.join(output_folder, 'VMAF'))
	print(f'Done! Graph saved at {output_folder}/VMAF.png')
	plt.clf()

	# VMAF data.
	vmaf = f'{min_vmaf} | {vmaf_std} | {mean_vmaf}'
	# Add the VMAF values to the table.
	data_for_current_row.append(vmaf)

	ssim_string = ''
	psnr_string = ''
	
	if args.calculate_ssim:
		ssim_string = '/SSIM'
		ssim_scores = [ssim['metrics']['ssim'] for ssim in file_contents['frames']]
		mean_ssim = force_decimal_places(np.mean(ssim_scores), decimal_places)
		min_ssim = force_decimal_places(min(ssim_scores), decimal_places)
		ssim_std = force_decimal_places(np.std(ssim_scores), decimal_places) # Standard deviation.
		ssim = f'{min_ssim} | {ssim_std} | {mean_ssim}'
	
		print(f'Creating SSIM graph...')
		plt.plot(frame_numbers, ssim_scores, label=f'SSIM ({mean_ssim})')
		plt.suptitle(f'SSIM\nn_subsample: {args.subsample}')
		plt.xlabel('Frame Number')
		plt.ylabel('Value of Quality Metric')
		plt.legend(loc='lower right')
		plt.savefig(os.path.join(output_folder, 'SSIM'))
		print(f'Done! Graph saved at {output_folder}/SSIM.png')
		plt.clf()
		# Add the SSIM values to the table.
		data_for_current_row.append(ssim)

	if args.calculate_psnr:
		psnr_string = '/PSNR'
		psnr_scores = [psnr['metrics']['psnr'] for psnr in file_contents['frames']]
		mean_psnr = force_decimal_places(np.mean(psnr_scores), decimal_places)
		min_psnr = force_decimal_places(min(psnr_scores), decimal_places)
		psnr_std = force_decimal_places(np.std(psnr_scores), decimal_places) # Standard deviation.
		psnr = f'{min_psnr} | {psnr_std} | {mean_psnr}'

		print(f'Creating PSNR graph...')
		plt.plot(frame_numbers, psnr_scores, label=f'PSNR ({mean_psnr})')
		plt.suptitle(f'PSNR\nn_subsample: {args.subsample}')
		plt.xlabel('Frame Number')
		plt.ylabel('Value of Quality Metric')
		plt.legend(loc='lower right')
		plt.savefig(os.path.join(output_folder, 'PSNR'))
		print(f'Done! Graph saved at {output_folder}/PSNR.png')
		plt.clf()
		# Add the PSNR values to the table.
		data_for_current_row.append(psnr)

	if not args.no_transcoding_mode:
		data_for_current_row.insert(0, crf_or_preset)
		data_for_current_row.insert(1, time_taken)
	
	table.add_row(data_for_current_row)
	table_title = f'VMAF{ssim_string}{psnr_string} values are in the format: Min | Standard Deviation | Mean'

	# Write the table to the Table.txt file.
	with open(comparison_table, 'w') as f:
		f.write(table.get_string(title=table_title))

	print(f'{comparison_table} has been updated.')
	line()