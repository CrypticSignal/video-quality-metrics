import argparse, cv2, time, os, subprocess, json
from argparse import RawTextHelpFormatter
from prettytable import PrettyTable
import numpy as np
import matplotlib.pyplot as plt


def separator():
	print('-----------------------------------------------------------------------------------------------------------')

separator()
print('If the path contains a space, the path argument must be surrounded in double quotes.')
print('Example: python video-metrics.py -ovp "C:/Users/H/Desktop/test file.mp4" -p fast veryfast')
print("For more information, enter 'python video-metrics.py -h'")
separator()


def compute_metrics(transcoded_video, output_folder, json_file_path, graph_title, preset=''):

	# The comparison table will be in the following path:
	#comparison_table = os.path.join(output_folder, 'Table.txt')
	# The first line of Table.txt:
	with open(comparison_table, 'w') as f:
		f.write(f'PSNR/SSIM/VMAF values are in the format: Min | Standard Deviation | Mean\n')

	size_of_file = os.path.getsize(transcoded_video) / 1_000_000
	size_compared_to_original = round(((size_of_file / original_video_size) * 100), 3)
	size_rounded = round(size_of_file, decimal_places)

	# Base template for the values in each row in the table.
	row = [f'{size_rounded} MB', f'{size_compared_to_original}%']

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

	separator()
	print(f'Computing the quality metrics...')
	subprocess.run(subprocess_args)
	print('Done!')

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

		row.append(vmaf)

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

			row.append(ssim)

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

			row.append(psnr)

		if not args.no_transcoding_mode:
			row.insert(0, preset)
			row.insert(1, f'{time_rounded}')

		table.add_row(row)

		graph_title = f'{preset}.png' if not args.no_transcoding_mode else 'VariationOfQuality.png'

		plt.suptitle(graph_title)
		plt.xlabel('Frame Number')
		plt.ylabel('Value of Quality Metric')
		plt.legend(loc='lower right')
		plt.savefig(os.path.join(output_folder, graph_title))
		plt.clf()

	# -dqs (disable quality stats)
	else:
		if args.no_transcoding_mode:
			table.add_row([f'{size_rounded} MB', f'{size_compared_to_original}%'])
		else:
			table.add_row([preset, f'{time_rounded}', f'{size_rounded} MB', f'{size_compared_to_original}%'])

	# End of compute_metrics function

parser = argparse.ArgumentParser(description='Compare the encoding time, resulting filesize and (optionally) the VMAF '
	'value obtained with the different encoder presets: '
	"'veryslow', 'slower', 'slow', 'medium', 'fast', 'faster', 'veryfast', 'superfast' and 'ultrafast'. "
	'You can edit the presets that are tested by editing the presets list on line 2 of compare-presets.py',
	formatter_class=RawTextHelpFormatter)

parser.add_argument('-ovp', '--original-video-path', type=str, required=True, help='Enter the path of the video. '
	'A relative or absolute path can be specified.'
	'If the path contains a space, it must be surrounded in double quotes.\n'
	'Example: -ovp "C:/Users/H/Desktop/file 1.mp4"')

parser.add_argument('-e', '--video-encoder', type=str, default='x264', choices=['x264', 'x265'],
	help='Specify the encoder to use. Must enter x264 or x265. Default: x264\nExample: -e x265')

parser.add_argument('-crf', '--crf-value', type=str, default='23', help='Enter the CRF value to be used (default: 23)')

parser.add_argument('-t', '--encoding-time', type=str, help='Encode this many seconds of the video. '
	'If not specified, the whole video will get encoded.')

parser.add_argument('-p', '--presets', nargs='+',
	choices=['placebo', 'veryslow', 'slower', 'slow', 'medium', 'fast', 'faster', 'veryfast', 'superfast', 'ultrafast'],
	help="List the presets you want to be tested (separated by a space).\n"
	"Choose from: 'veryslow', 'slower', 'slow', 'medium', 'fast', 'faster', 'veryfast', 'superfast', 'ultrafast'\n"
	"Example: -p fast veryfast ultrafast", metavar='presets')

parser.add_argument('-pm', '--phone-model', action='store_true',
	help='Enable VMAF phone model (default: False)')

parser.add_argument('-dp', '--decimal-places', default=3, help='The number of decimal places to use for the data '
				    'in the table (default: 3)')

parser.add_argument('-ssim', '--calculate-ssim', action='store_true', help='Calculate SSIM in addition to VMAF.')
parser.add_argument('-psnr', '--calculate-psnr', action='store_true', help='Calculate PSNR in addition to VMAF.')

parser.add_argument('-dqs', '--disable-quality-stats', action='store_true',
	help='Disable calculation of PSNR, SSIM and VMAF; only show encoding time and filesize (improves completion time).')

parser.add_argument('-ntm', '--no-transcoding-mode', action='store_true',
	help='Simply calculate the quality metrics of a transcoded video to the original.')

parser.add_argument('-tvp', '--transcoded-video-path',
	help='The path of the transcoded video (only applicable when using the -ntm mode)')

args = parser.parse_args()
decimal_places = args.decimal_places

# Original video path.
original_video = args.original_video_path
# This will be used when comparing the size of the encoded file to the original (or cut version).
original_video_size = os.path.getsize(original_video) / 1_000_000
# Just the filename
filename = original_video.split('/')[-1]
output_ext = os.path.splitext(original_video)[-1][1:]

print(f'File: {filename}')
cap = cv2.VideoCapture(original_video)
fps = str(cap.get(cv2.CAP_PROP_FPS))
print(f'Framerate: {fps} FPS')

# Create a PrettyTable object.
table = PrettyTable()

# Base template for the column names.
table_column_names = ['Preset', 'Encoding Time (s)', 'Size', 'Size Compared to Original']

if not args.disable_quality_stats:
	table_column_names.append('VMAF')
if args.calculate_ssim:
	table_column_names.append('SSIM')
if args.calculate_psnr:
	table_column_names.append('PSNR')
if args.no_transcoding_mode:
	del table_column_names[:2]

# Set the names of the columns
table.field_names = table_column_names

if args.no_transcoding_mode:

	# Where the data will be saved.
	output_folder = f'({filename})'
	os.makedirs(output_folder, exist_ok=True)

	# The comparison table will be in the following path:
	comparison_table = os.path.join(output_folder, 'Table.txt')

	json_file_path = f'{output_folder}/QualityMetrics.json'
	# (os.path.join doesn't work with libvmaf's log_path option)

	graph_title = 'The variation of the quality of the transcoded video throughout the video'

	transcoded_video = args.transcoded_video_path

	compute_metrics(transcoded_video, output_folder, json_file_path, graph_title)

# Transcode the video with each preset and compute the metrics.
else:

	video_encoder = args.video_encoder
	crf_value = args.crf_value
	chosen_presets = args.presets

	# Where the data will be saved.
	output_folder = f'({filename})/CRF {crf_value}'
	os.makedirs(output_folder, exist_ok=True)

	# The comparison table will be in the following path:
	comparison_table = os.path.join(output_folder, 'Table.txt')

	# Set the names of the columns for the presets comparison table.
	table.field_names = table_column_names

	time_message = ''

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
		f.write(f'You chose to encode {filename}{time_message} using {args.video_encoder} with a CRF of {args.crf_value}.\n'
			    f'PSNR/SSIM/VMAF values are in the format: Min | Standard Deviation | Mean\n')

	# Transcode the video with each preset.
	for preset in chosen_presets:

		transcode_output_path = os.path.join(output_folder, f'{preset}.{output_ext}')
		graph_title = f"Preset '{preset}'"

		subprocess_args = [
			"ffmpeg", "-loglevel", "warning", "-stats", "-y",
			"-i", original_video, "-map", "0",
			"-c:v", video_encoder, "-crf", args.crf_value, "-preset", preset,
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

			json_file_path = f'{output_folder}/{preset}.json'
			# (os.path.join doesn't work with libvmaf's log_path option)

			compute_metrics(transcode_output_path, output_folder, json_file_path, preset, graph_title)

		# -dqs argument specified
		else:
			table.add_row([preset, f'{time_rounded}', f'{size_rounded} MB', f'{size_compared_to_original}%'])

# Write the table to the Table.txt file.
with open(comparison_table, 'a') as f:
	f.write(table.get_string())

separator()
print(f'All done! Check out the ({filename}) folder.')
