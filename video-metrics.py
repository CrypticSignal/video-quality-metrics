import argparse, cv2, time, os, subprocess, json, sys
from argparse import RawTextHelpFormatter
from prettytable import PrettyTable
import numpy as np
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser(description='Calculate the quality of transcoded video(s). For more info, visit:\n'
								 'https://github.com/BassThatHertz/video-quality-metrics')
# Original video path.
parser.add_argument('-ovp', '--original-video-path', type=str, required=True, help='Enter the path of the video. '
				    'A relative or absolute path can be specified. '
					'If the path contains a space, it must be surrounded in double quotes.\n'
					'Example: -ovp "C:/Users/H/Desktop/file 1.mp4"')
# Encoder.
parser.add_argument('-e', '--video-encoder', type=str, default='x264', choices=['x264', 'x265'],
					help='Specify the encoder to use. Must enter x264 or x265. Default: x264\nExample: -e x265')
# CRF value(s).
parser.add_argument('-crf', '--crf-value', nargs='+', type=int, choices=range(0, 51),
				    default=23, help='Specify the CRF value(s) to use.', metavar='CRF_VALUE(s)')
# Preset(s).
parser.add_argument('-p', '--preset', nargs='+', choices=
	                ['veryslow', 'slower', 'slow', 'medium', 'fast', 'faster', 'veryfast', 'superfast', 'ultrafast'],
				    default='medium', help='Specify the preset(s) to use.', metavar='PRESET(s)')
# How many seconds to transcode.
parser.add_argument('-t', '--encoding-time', type=str, help='Encode this many seconds of the video. '
	'If not specified, the whole video will get encoded.')
# Enable phone model?
parser.add_argument('-pm', '--phone-model', action='store_true', 
				    help='Enable VMAF phone model (default: False)')
# Number of decimal places to use for the data.
parser.add_argument('-dp', '--decimal-places', default=3, help='The number of decimal places to use for the data '
				    'in the table (default: 3).', metavar='<number of decimal places>')
# Calculate SSIM?
parser.add_argument('-ssim', '--calculate-ssim', action='store_true', help='Calculate SSIM in addition to VMAF.')
# Calculate psnr?
parser.add_argument('-psnr', '--calculate-psnr', action='store_true', help='Calculate PSNR in addition to VMAF.')
# Disable quality calculation?
parser.add_argument('-dqs', '--disable-quality-stats', action='store_true', help='Disable calculation of '
					'PSNR, SSIM and VMAF; only show encoding time and filesize (improves completion time).')
# No transcoding mode.
parser.add_argument('-ntm', '--no-transcoding-mode', action='store_true', 
					help='Simply calculate the quality metrics of a transcoded video to the original.')
# Transcoded video path (only applicable when using the -ntm mode).
parser.add_argument('-tvp', '--transcoded-video-path', 
					help='The path of the transcoded video (only applicable when using the -ntm mode).')

args = parser.parse_args()

def separator():
	print('-----------------------------------------------------------------------------------------------------------') 

# If more than one CRF value and more than one preset was specified then we don't have a suitable comparison mode. Exit.
if len(args.crf_value) > 1 and len(args.preset) > 1:
	separator()
	print(f'More than one CRF value AND more than one preset specified. No suitable mode found. Exiting.')
	separator()
	sys.exit()

separator()
print('If the path contains a space, the path argument must be surrounded in double quotes. Example:')
print('python video-metrics.py -ovp "C:/Users/H/Desktop/test file.mp4" -p fast veryfast')
print("For more information, enter 'python video-metrics.py -h'")
separator()

def compute_metrics(transcoded_video, output_folder, json_file_path, graph_title, crf_or_preset=None):
	preset_string = ','.join(args.preset)
	# The first line of Table.txt:
	with open(comparison_table, 'w') as f:
		f.write(f'PSNR/SSIM/VMAF values are in the format: Min | Standard Deviation | Mean\n')
		f.write(f'Chosen preset(s): {preset_string}\n')

	size_of_file = os.path.getsize(transcoded_video) / 1_000_000
	size_compared_to_original = round(((size_of_file / original_video_size) * 100), 3) 
	size_rounded = round(size_of_file, decimal_places)

	data_for_current_row = [f'{size_rounded} MB', f'{size_compared_to_original}%']

	vmaf_options = {
		"model_path": "vmaf_v0.6.1.pkl",
		"phone_model": "1" if args.phone_model else "0",
		"psnr": "1" if args.calculate_psnr else "0",
		"ssim": "1" if args.calculate_ssim else "0",
		"log_path": json_file_path, 
		"log_fmt": "json"
	}
	vmaf_options = ":".join(f'{key}={value}' for key, value in vmaf_options.items())

	subprocess_args = [
		"ffmpeg", "-loglevel", "error", "-stats", "-r", fps, "-i", transcoded_video,
		"-r", fps, "-i", original_video,
		"-lavfi", "[0:v]setpts=PTS-STARTPTS[dist];[1:v]setpts=PTS-STARTPTS[ref];[dist][ref]"
		f'libvmaf={vmaf_options}', "-f", "null", "-"
	]

	print(f'Computing the quality metric(s)...')
	subprocess.run(subprocess_args)
	print('Done!')
	# Make a list containing the frame numbers from the JSON file.
	with open(json_file_path, 'r') as f:
		file_contents = json.load(f)
	frame_numbers = [frame['frameNum'] for frame in file_contents['frames']]

	if not args.disable_quality_stats:
		# VMAF
		vmaf_scores = [frame['metrics']['vmaf'] for frame in file_contents['frames']]
		mean_vmaf = round(np.mean(vmaf_scores), decimal_places)
		min_vmaf = round(min(vmaf_scores), decimal_places)
		vmaf_std = round(np.std(vmaf_scores), decimal_places) # Standard deviation.
		vmaf = f'{min_vmaf} | {vmaf_std} | {mean_vmaf}'
		# Plot a line showing the variation of the VMAF score throughout the video.
		print(f'Plotting VMAF graph...')
		plt.plot(frame_numbers, vmaf_scores, label=f'VMAF ({mean_vmaf})')
		print('Done!')
		# Add the VMAF values to the table.
		data_for_current_row.append(vmaf)

		if args.calculate_ssim:
			ssim_scores = [ssim['metrics']['ssim'] for ssim in file_contents['frames']]
			mean_ssim = round(np.mean(ssim_scores), decimal_places)
			min_ssim = round(min(ssim_scores), decimal_places)
			ssim_std = round(np.std(ssim_scores), decimal_places) # Standard deviation.
			ssim = f'{min_ssim} | {ssim_std} | {mean_ssim}'
			# Plot a line showing the variation of the SSIM throughout the video.
			print(f'Plotting SSIM graph...')
			plt.plot(frame_numbers, ssim_scores, label=f'SSIM ({mean_ssim})')
			print('Done!')
			# Add the SSIM values to the table.
			data_for_current_row.append(ssim)

		if args.calculate_psnr:
			psnr_scores = [psnr['metrics']['psnr'] for psnr in file_contents['frames']]
			mean_psnr = round(np.mean(psnr_scores), decimal_places)
			min_psnr = round(min(psnr_scores), decimal_places)
			psnr_std = round(np.std(psnr_scores), decimal_places) # Standard deviation.
			psnr = f'{min_psnr} | {psnr_std} | {mean_psnr}'
			# Plot a line showing the variation of the PSNR throughout the video.
			print(f'Plotting PSNR graph...')
			plt.plot(frame_numbers, psnr_scores, label=f'PSNR ({mean_psnr})')
			print('Done!')
			# Add the PSNR values to the table.
			data_for_current_row.append(psnr)

		if not args.no_transcoding_mode:
			# CRF comparison mode if a list of CRF values were provided.
			if isinstance(args.crf_value, list):
				data_for_current_row.insert(0, crf)
				data_for_current_row.insert(1, time_rounded)
			# Presets comparison mode.
			else:
				data_for_current_row.insert(0, preset)
				data_for_current_row.insert(1, time_rounded)
			
		table.add_row(data_for_current_row)

		if args.no_transcoding_mode:
			graph_title = 'VariationOfQuality.png'

		plt.suptitle(graph_title)
		plt.xlabel('Frame Number')
		plt.ylabel('Value of Quality Metric')
		plt.legend(loc='lower right')
		plt.savefig(os.path.join(output_folder, graph_title))
		plt.clf()

	# -dqs (disable quality stats)
	else:
		if args.no_transcoding_mode:
			table.add_row([time_rounded, f'{size_rounded} MB', f'{size_compared_to_original}%'])
		else:
			table.add_row([time_rounded, f'{size_rounded} MB', f'{size_compared_to_original}%'])

decimal_places = args.decimal_places
# Original video path.
original_video = args.original_video_path
# This will be used when comparing the size of the encoded file to the original (or cut version).
original_video_size = os.path.getsize(original_video) / 1_000_000
# Just the filename
filename = original_video.split('/')[-1]
output_ext = os.path.splitext(original_video)[-1][1:]

print(f'\nFile: {filename}')
cap = cv2.VideoCapture(original_video)
fps = str(cap.get(cv2.CAP_PROP_FPS))
print(f'Framerate: {fps} FPS')

# Create a PrettyTable object.
table = PrettyTable()

# Base template for the column names.
table_column_names = ['Encoding Time (s)', 'Size', 'Size Compared to Original']

if not args.disable_quality_stats:
	table_column_names.append('VMAF')
if args.calculate_ssim:
	table_column_names.append('SSIM')
if args.calculate_psnr:
	table_column_names.append('PSNR')
if args.no_transcoding_mode:
	del table_column_names[0]

# -ntm argument was specified.
if args.no_transcoding_mode:
	output_folder = f'({filename})'
	os.makedirs(output_folder, exist_ok=True)
	comparison_table = os.path.join(output_folder, 'Table.txt')
	table.field_names = table_column_names
	json_file_path = f'{output_folder}/QualityMetrics.json'
	# (os.path.join doesn't work with libvmaf's log_path option)
	graph_title = 'The variation of the quality of the transcoded video throughout the video'
	transcoded_video = args.transcoded_video_path
	compute_metrics(transcoded_video, output_folder, json_file_path, graph_title)

# If len(args.crf_value) > 1 then more than one CRF value was specified so the user wants to compare CRF values.
elif len(args.crf_value) > 1:

	print('\nMore than one CRF value specified. CRF comparison mode activated.')
	crf_values = args.crf_value
	chosen_preset = args.preset
	CRF_values_string = ','.join(map(str, crf_values))
	print(f'CRF values {CRF_values_string} will be compared and the {chosen_preset[0]} preset will be used.')
	video_encoder = args.video_encoder
	
	# Where the data will be saved.
	output_folder = f'({filename})/CRF Comparison ({chosen_preset[0]})'
	os.makedirs(output_folder, exist_ok=True)
	# The comparison table will be in the following path:
	comparison_table = os.path.join(output_folder, 'Table.txt')
	# Add a CRF column.
	table_column_names.insert(0, 'CRF')
	# Set the names of the columns
	table.field_names = table_column_names

	if args.encoding_time:
		cut_filename = f'{os.path.splitext(filename)[0]} [{args.encoding_time}s].{output_ext}'
		# Output path for the cut video.
		output_file_path = f'{output_folder}/{cut_filename}'
		# If an encoding time is specified, the reference file becomes the cut version of the video.
		reference_file = output_file_path 
		original_video_size = os.path.getsize(original_video) / 1_000_000
		# Create the cut version.
		print(f'Cutting the video to {args.encoding_time} seconds...')
		os.system(f'ffmpeg -loglevel warning -y -i {args.video_path} -t {args.encoding_time} '
			      f'-map 0 -c copy "{output_file_path}"')
		print('Done!')
		time_message = f' for {args.encoding_time} seconds' if int(args.encoding_time) > 1 else 'for 1 second'

		with open(comparison_table, 'w') as f:
			f.write(f'You chose to encode {filename}{time_message} using {args.video_encoder}.\n'
					f'PSNR/SSIM/VMAF values are in the format: Min | Standard Deviation | Mean\n')

	# Transcode the video with each preset.
	for crf in crf_values:
		transcode_output_path = os.path.join(output_folder, f'CRF {crf} preset {chosen_preset[0]}.{output_ext}')
		graph_title = f'CRF {crf} preset {chosen_preset[0]}'

		subprocess_args = [
			"ffmpeg", "-loglevel", "warning", "-stats", "-y",
			"-i", original_video, "-map", "0",
			"-c:v", f'lib{video_encoder}', "-crf", str(crf), "-preset", chosen_preset,
			"-c:a", "copy", "-c:s", "copy", "-movflags", "+faststart", transcode_output_path
		]

		separator()
		print(f'Transcoding the video with CRF {crf}...')
		start_time = time.time()
		subprocess.run(subprocess_args)
		end_time = time.time()
		time_to_convert = end_time - start_time
		time_rounded = round(time_to_convert, decimal_places)
		print('Done!')

		if not args.disable_quality_stats:

			os.makedirs(os.path.join(output_folder, 'Raw JSON Data'), exist_ok=True)
			json_file_path = f'{output_folder}/Raw JSON Data/CRF {crf}.json'
			# (os.path.join doesn't work with libvmaf's log_path option)
			compute_metrics(transcode_output_path, output_folder, json_file_path, graph_title, crf)

		# -dqs argument specified
		else: 
			table.add_row([preset, f'{time_rounded}', f'{size_rounded} MB', f'{size_compared_to_original}%'])

# The user wants to compare presets.
else:
	print('\nPresets comparison mode activated.')
	video_encoder = args.video_encoder
	crf_value = args.crf_value
	chosen_presets = args.preset
	presets_string = ','.join(chosen_presets)	
	print(f'Presets {presets_string} will be compared at a CRF of {crf_value[0]}.')
	output_folder = f'({filename})/Presets comparison at CRF {crf_value}'
	os.makedirs(output_folder, exist_ok=True)
	comparison_table = os.path.join(output_folder, 'Table.txt')
	table_column_names.insert(0, 'Preset')
	# Set the names of the columns
	table.field_names = table_column_names

	if args.encoding_time:
		cut_filename = f'{os.path.splitext(filename)[0]} [{args.encoding_time}s].{output_ext}'
		# Output path for the cut video.
		output_file_path = f'{output_folder}/{cut_filename}'
		# If an encoding time is specified, the reference file becomes the cut version of the video.
		reference_file = output_file_path 
		original_video_size = os.path.getsize(original_video) / 1_000_000
		# Create the cut version.
		print(f'Cutting the video to {args.encoding_time} seconds...')
		os.system(f'ffmpeg -loglevel warning -y -i {args.video_path} -t {args.encoding_time} '
			      f'-map 0 -c copy "{output_file_path}"')
		print('Done!')
		time_message = f' for {args.encoding_time} seconds' if int(args.encoding_time) > 1 else 'for 1 second'

		with open(comparison_table, 'w') as f:
			f.write(f'You chose to encode {filename}{time_message} using {args.video_encoder} with a CRF of {crf_value}.\n'
					f'PSNR/SSIM/VMAF values are in the format: Min | Standard Deviation | Mean\n')

	# Transcode the video with each preset.
	for preset in chosen_presets:
		transcode_output_path = os.path.join(output_folder, f'{preset}.{output_ext}')
		graph_title = f"Preset '{preset}'"
		subprocess_args = [
			"ffmpeg", "-loglevel", "warning", "-stats", "-y",
			"-i", original_video, "-map", "0",
			"-c:v", f'lib{video_encoder}', "-crf", str(crf_value[0]), "-preset", preset,
			"-c:a", "copy", "-c:s", "copy", "-movflags", "+faststart", transcode_output_path
		]
		separator()
		print(f'Transcoding the video with preset {preset}...')
		start_time = time.time()
		subprocess.run(subprocess_args)
		end_time = time.time()
		time_to_convert = end_time - start_time
		time_rounded = round(time_to_convert, decimal_places)
		print('Done!')

		if not args.disable_quality_stats:
			os.makedirs(os.path.join(output_folder, 'Raw JSON Data'), exist_ok=True)
			# os.path.join doesn't work with libvmaf's log_path option
			json_file_path = f'{output_folder}/Raw JSON Data/{preset}.json'
			compute_metrics(transcode_output_path, output_folder, json_file_path, graph_title, preset)
			#compute_metrics(transcode_output_path, output_folder, json_file_path, graph_title, crf_or_preset=preset)

		# -dqs argument specified
		else: 
			table.add_row([preset, f'{time_rounded}', f'{size_rounded} MB', f'{size_compared_to_original}%'])

# Write the table to the Table.txt file.
with open(comparison_table, 'a') as f:
	f.write(table.get_string())

separator()
print(f'All done! Check out the ({filename}) folder.')
