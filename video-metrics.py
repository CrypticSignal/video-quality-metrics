import time, os, subprocess, json, sys
from argparse import ArgumentParser, RawTextHelpFormatter
from moviepy.editor import VideoFileClip
from prettytable import PrettyTable
import numpy as np
import matplotlib.pyplot as plt

if '-h' not in sys.argv or '--help' not in sys.argv:
	print("To see a list of the options available along with descriptions, enter 'python video-metrics.py -h'")

parser = ArgumentParser(formatter_class=RawTextHelpFormatter)
# Original video path.
parser.add_argument('-ovp', '--original-video-path', type=str, required=True, help='Enter the path of the original '
				    'video. A relative or absolute path can be specified. '
					'If the path contains a space, it must be surrounded in double quotes.\n'
					'Example: -ovp "C:/Users/H/Desktop/file 1.mp4"')
# Encoder.
parser.add_argument('-e', '--video-encoder', type=str, default='x264', choices=['x264', 'x265'],
					help='Specify the encoder to use (default: x264).\nExample: -e x265')
# CRF value(s).
parser.add_argument('-crf', '--crf-value', nargs='+', type=int, choices=range(0, 51),
				    default=23, help='Specify the CRF value(s) to use.', metavar='CRF_VALUE(s)')
# Preset(s).
parser.add_argument('-p', '--preset', nargs='+', choices=
	                ['veryslow', 'slower', 'slow', 'medium', 'fast', 'faster', 'veryfast', 'superfast', 'ultrafast'],
				    default='medium', help='Specify the preset(s) to use.', metavar='PRESET(s)')
# How many seconds to transcode.
parser.add_argument('-t', '--encoding-time', type=str, help='Encode this many seconds of the video. '
	'If not specified, the whole video will get encoded.\nExample: -t 60')
# Enable phone model?
parser.add_argument('-pm', '--phone-model', action='store_true', help='Enable VMAF phone model.')
# Number of decimal places to use for the data.
parser.add_argument('-dp', '--decimal-places', default=2, help='The number of decimal places to use for the data '
				    'in the table (default: 2).\nExample: -dp 3')
# Calculate SSIM?
parser.add_argument('-ssim', '--calculate-ssim', action='store_true', help='Calculate SSIM in addition to VMAF.')
# Calculate psnr?
parser.add_argument('-psnr', '--calculate-psnr', action='store_true', help='Calculate PSNR in addition to VMAF.')
# Disable quality calculation?
parser.add_argument('-dqs', '--disable-quality-stats', action='store_true', help='Disable calculation of '
					'PSNR, SSIM and VMAF; only show encoding time and filesize (improves completion time).')
# No transcoding mode.
parser.add_argument('-ntm', '--no-transcoding-mode', action='store_true', 
					help='Use this mode if you\'ve already transcoded a video and would like its VMAF and (optionally) '
						  'the SSIM and PSNR to be calculated.\n'
					      'Example: -ntm -tvp transcoded.mp4 -ovp original.mp4 -ssim -psnr')
# Transcoded video path (only applicable when using the -ntm mode).
parser.add_argument('-tvp', '--transcoded-video-path', 
					help='The path of the transcoded video (only applicable when using the -ntm mode).')

args = parser.parse_args()

def separator():
	print('-----------------------------------------------------------------------------------------------------------')

# If no CRF or preset is specified, the default data types are as str and int, respectively.
if isinstance(args.crf_value, int) and isinstance(args.preset, str):
	separator()
	print('No CRF value(s) or preset(s) specified. Exiting.')
	separator()
	sys.exit()
elif len(args.crf_value) > 1 and isinstance(args.preset, list) and len(args.preset) > 1:
	separator()
	print(f'More than one CRF value AND more than one preset specified. No suitable mode found. Exiting.')
	separator()
	sys.exit()

separator()


def force_decimal_places(value):
	return '{:0.{dp}f}'.format(value, dp=decimal_places)

def compute_metrics(transcoded_video, output_folder, json_file_path, graph_filename, crf_or_preset=None):
	preset_string = ','.join(args.preset)
	# The first line of Table.txt:
	with open(comparison_table, 'w') as f:
		f.write(f'PSNR/SSIM/VMAF values are in the format: Min | Standard Deviation | Mean\n')
		f.write(f'Chosen preset(s): {preset_string}\n')

	transcode_size = os.path.getsize(transcoded_video) / 1_000_000
	size_compared_to_original = round(((transcode_size / original_video_size) * 100), 3) 
	size_rounded = round(transcode_size, decimal_places)

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
		f'libvmaf={vmaf_options}', "-f"
		, "null", "-"
	]

	if args.calculate_psnr and args.calculate_ssim:
		end_of_computing_message = ', PSNR and SSIM'
	elif args.calculate_psnr:
		end_of_computing_message = ' and PSNR'
	elif args.calculate_ssim:
		end_of_computing_message = ' and SSIM'
	else:
		end_of_computing_message = ''

	print(f'Computing the VMAF{end_of_computing_message}...')
	subprocess.run(subprocess_args)
	print('Done!')

	# Make a list containing the frame numbers from the JSON file.
	with open(json_file_path, 'r') as f:
		file_contents = json.load(f)
	frame_numbers = [frame['frameNum'] for frame in file_contents['frames']]

	if not args.disable_quality_stats:
		# VMAF
		vmaf_scores = [frame['metrics']['vmaf'] for frame in file_contents['frames']]
		mean_vmaf = force_decimal_places(round(np.mean(vmaf_scores), decimal_places))
		min_vmaf = force_decimal_places(round(min(vmaf_scores), decimal_places))
		vmaf_std = force_decimal_places(round(np.std(vmaf_scores), decimal_places)) # Standard deviation.
		vmaf = f'{min_vmaf} | {vmaf_std} | {mean_vmaf}'
		# Plot a line showing the variation of the VMAF score throughout the video.
		print(f'Plotting VMAF graph...')
		plt.plot(frame_numbers, vmaf_scores, label=f'VMAF ({mean_vmaf})')
		print('Done!')
		# Add the VMAF values to the table.
		data_for_current_row.append(vmaf)

		if args.calculate_ssim:
			ssim_scores = [ssim['metrics']['ssim'] for ssim in file_contents['frames']]
			mean_ssim = force_decimal_places(round(np.mean(ssim_scores), decimal_places))
			min_ssim = force_decimal_places(round(min(ssim_scores), decimal_places))
			ssim_std = force_decimal_places(round(np.std(ssim_scores), decimal_places)) # Standard deviation.
			ssim = f'{min_ssim} | {ssim_std} | {mean_ssim}'
			# Plot a line showing the variation of the SSIM throughout the video.
			print(f'Plotting SSIM graph...')
			plt.plot(frame_numbers, ssim_scores, label=f'SSIM ({mean_ssim})')
			print('Done!')
			# Add the SSIM values to the table.
			data_for_current_row.append(ssim)

		if args.calculate_psnr:
			psnr_scores = [psnr['metrics']['psnr'] for psnr in file_contents['frames']]
			mean_psnr = force_decimal_places(round(np.mean(psnr_scores), decimal_places))
			min_psnr = force_decimal_places(round(min(psnr_scores), decimal_places))
			psnr_std = force_decimal_places(round(np.std(psnr_scores), decimal_places)) # Standard deviation.
			psnr = f'{min_psnr} | {psnr_std} | {mean_psnr}'
			# Plot a line showing the variation of the PSNR throughout the video.
			print(f'Plotting PSNR graph...')
			plt.plot(frame_numbers, psnr_scores, label=f'PSNR ({mean_psnr})')
			print('Done!')
			# Add the PSNR values to the table.
			data_for_current_row.append(psnr)

		if not args.no_transcoding_mode:
			if isinstance(args.crf_value, list) and len(args.crf_value) > 1:
				data_for_current_row.insert(0, crf)
				data_for_current_row.insert(1, time_rounded)
			# Presets comparison mode.
			else:
				data_for_current_row.insert(0, preset)
				data_for_current_row.insert(1, time_rounded)
			
		table.add_row(data_for_current_row)

		if args.no_transcoding_mode:
			graph_filename = 'VariationOfQuality.png'

		plt.suptitle(graph_filename)
		plt.xlabel('Frame Number')
		plt.ylabel('Value of Quality Metric')
		plt.legend(loc='lower right')
		plt.savefig(os.path.join(output_folder, graph_filename))
		plt.clf()

	# -dqs (disable quality stats)
	else:
		transcode_size = os.path.getsize(transcoded_video) / 1_000_000
		size_compared_to_original = round(((transcode_size / original_video_size) * 100), 3) 
		size_rounded = round(transcode_size, decimal_places)
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

with VideoFileClip(original_video) as clip:
    fps = str(clip.fps)

print(f'File: {filename}')
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
	seperator()
	output_folder = f'({filename})'
	os.makedirs(output_folder, exist_ok=True)
	comparison_table = os.path.join(output_folder, 'Table.txt')
	table.field_names = table_column_names
	# os.path.join doesn't work with libvmaf's log_path option so we're manually defining the path with slashes.
	json_file_path = f'{output_folder}/QualityMetrics.json'
	graph_filename = 'The variation of the quality of the transcoded video throughout the video'
	transcoded_video = args.transcoded_video_path
	compute_metrics(transcoded_video, output_folder, json_file_path, graph_filename)

# args.crf_value is a list when more than one CRF value is specified.
elif isinstance(args.crf_value, list) and len(args.crf_value) > 1:
	separator()
	print('CRF comparison mode activated.')
	crf_values = args.crf_value
	crf_values_string = ', '.join(str(crf) for crf in crf_values)
	preset = args.preset[0] if isinstance(args.preset, list) else args.preset
	print(f'CRF values {crf_values_string} will be compared and the {preset} preset will be used.')
	video_encoder = args.video_encoder
	# Cannot use os.path.join for output_folder as this gives an error like the following:
	# No such file or directory: '(2.mkv)\\Presets comparison at CRF 23/Raw JSON Data/superfast.json'
	output_folder = f'({filename})/CRF comparison at preset {preset}'
	os.makedirs(output_folder, exist_ok=True)
	# The comparison table will be in the following path:
	comparison_table = os.path.join(output_folder, 'Table.txt')
	# Add a CRF column.
	table_column_names.insert(0, 'CRF')
	# Set the names of the columns
	table.field_names = table_column_names

	# The user only wants to transcode the first x seconds of the video.
	if args.encoding_time:
		cut_version_filename = f'{os.path.splitext(filename)[0]} [{args.encoding_time}s].{output_ext}'
		# Output path for the cut video.
		output_file_path = os.path.join(output_folder, cut_version_filename)
		# The reference file will be the cut version of the video.
		original_video = output_file_path
		# Create the cut version.
		print(f'Cutting the video to a length of {args.encoding_time} seconds...')
		os.system(f'ffmpeg -loglevel warning -y -i {args.original_video_path} -t {args.encoding_time} '
			      f'-map 0 -c copy "{output_file_path}"')
		print('Done!')

		original_video_size = os.path.getsize(original_video) / 1_000_000
		time_message = f' for {args.encoding_time} seconds' if int(args.encoding_time) > 1 else 'for 1 second'

		with open(comparison_table, 'w') as f:
			f.write(f'You chose to encode {filename}{time_message} using {args.video_encoder}.\n'
					f'PSNR/SSIM/VMAF values are in the format: Min | Standard Deviation | Mean\n')

	# Transcode the video with each preset.
	for crf in crf_values:
		transcode_output_path = os.path.join(output_folder, f'CRF {crf} at preset {preset}.{output_ext}')
		graph_filename = f'CRF {crf} at preset {preset}'

		subprocess_args = [
			"ffmpeg", "-loglevel", "warning", "-stats", "-y",
			"-i", original_video, "-map", "0",
			"-c:v", f'lib{video_encoder}', "-crf", str(crf), "-preset", preset,
			"-c:a", "copy", "-c:s", "copy", "-movflags", "+faststart", transcode_output_path
		]

		separator()
		print(f'Transcoding the video with CRF {crf}...')
		start_time = time.time()
		subprocess.run(subprocess_args)
		end_time = time.time()
		print('Done!')
		time_to_convert = end_time - start_time
		time_rounded = round(time_to_convert, decimal_places)
		transcode_size = os.path.getsize(transcode_output_path) / 1_000_000
		size_compared_to_original = round(((transcode_size / original_video_size) * 100), 3) 
		size_rounded = round(transcode_size, decimal_places)

		if not args.disable_quality_stats:
			os.makedirs(os.path.join(output_folder, 'Raw JSON Data'), exist_ok=True)
			# os.path.join doesn't work with libvmaf's log_path option so we're manually defining the path with slashes.
			json_file_path = f'{output_folder}/Raw JSON Data/CRF {crf}.json'
			# Run the compute_metrics function.
			compute_metrics(transcode_output_path, output_folder, json_file_path, graph_filename, crf)

		# -dqs argument specified
		else: 
			table.add_row([preset, f'{time_rounded}', f'{size_rounded} MB', f'{size_compared_to_original}%'])

# args.preset is a list when more than one preset is specified.
elif isinstance(args.preset, list):
	separator()
	print('Presets comparison mode activated.')
	chosen_presets = args.preset
	presets_string = ', '.join(chosen_presets)
	video_encoder = args.video_encoder
	print(f'Presets {presets_string} will be compared at a CRF of {args.crf_value[0]}.')
	# Cannot use os.path.join for output_folder as this gives an error like the following:
	# No such file or directory: '(2.mkv)\\Presets comparison at CRF 23/Raw JSON Data/superfast.json'
	output_folder = f'({filename})/Presets comparison at CRF {args.crf_value[0]}'
	os.makedirs(output_folder, exist_ok=True)
	comparison_table = os.path.join(output_folder, 'Table.txt')
	table_column_names.insert(0, 'Preset')
	# Set the names of the columns
	table.field_names = table_column_names

	# The user only wants to transcode the first x seconds of the video.
	if args.encoding_time:
		cut_version_filename = f'{os.path.splitext(filename)[0]} [{args.encoding_time}s].{output_ext}'
		# Output path for the cut video.
		output_file_path = os.path.join(output_folder, cut_version_filename)
		# The reference file will be the cut version of the video.
		original_video = output_file_path
		# Create the cut version.
		print(f'Cutting the video to {args.encoding_time} seconds...')
		os.system(f'ffmpeg -loglevel warning -y -i {args.video_path} -t {args.encoding_time} '
			      f'-map 0 -c copy "{output_file_path}"')
		print('Done!')

		original_video_size = os.path.getsize(original_video) / 1_000_000
		time_message = f' for {args.encoding_time} seconds' if int(args.encoding_time) > 1 else 'for 1 second'

		with open(comparison_table, 'w') as f:
			f.write(f'You chose to encode {filename}{time_message} using {args.video_encoder} with a CRF of {args.crf_value[0]}.\n'
					f'PSNR/SSIM/VMAF values are in the format: Min | Standard Deviation | Mean\n')

	# Transcode the video with each preset.
	for preset in chosen_presets:
		transcode_output_path = os.path.join(output_folder, f'{preset}.{output_ext}')
		graph_filename = f"Preset '{preset}'"
		subprocess_args = [
			"ffmpeg", "-loglevel", "warning", "-stats", "-y",
			"-i", original_video, "-map", "0",
			"-c:v", f'lib{video_encoder}', "-crf", str(args.crf_value[0]), "-preset", preset,
			"-c:a", "copy", "-c:s", "copy", "-movflags", "+faststart", transcode_output_path
		]
		separator()
		print(f'Transcoding the video with preset {preset}...')
		start_time = time.time()
		subprocess.run(subprocess_args)
		end_time = time.time()
		print('Done!')
		time_to_convert = end_time - start_time
		time_rounded = round(time_to_convert, decimal_places)
		transcode_size = os.path.getsize(transcode_output_path) / 1_000_000
		size_compared_to_original = round(((transcode_size / original_video_size) * 100), 3) 
		size_rounded = round(transcode_size, decimal_places)

		if not args.disable_quality_stats:
			os.makedirs(os.path.join(output_folder, 'Raw JSON Data'), exist_ok=True)
			# os.path.join doesn't work with libvmaf's log_path option so we're manually defining the path with slashes.
			json_file_path = f'{output_folder}/Raw JSON Data/{preset}.json'
			# Run the compute_metrics function.
			compute_metrics(transcode_output_path, output_folder, json_file_path, graph_filename, preset)
			
		# -dqs argument specified
		else:
			table.add_row([preset, f'{time_rounded}', f'{size_rounded} MB', f'{size_compared_to_original}%'])

# Write the table to the Table.txt file.
with open(comparison_table, 'a') as f:
	f.write(table.get_string())

separator()
print(f'All done! Check out the ({filename}) folder.')
