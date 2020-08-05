import argparse, cv2, time, os, subprocess, json
from argparse import RawTextHelpFormatter
import numpy as np
from prettytable import PrettyTable
import matplotlib.pyplot as plt

def separator():
	print('-----------------------------------------------------------------------------------------------------------') 

separator()
print('If the path contains a space, the path argument must be surrounded in double quotes.')
print('Example: python compare-presets.py -f "C:/Users/H/Desktop/test file.mp4" -p fast veryfast')
print("For more information, enter 'python compare-presets.py -h'")
separator()

parser = argparse.ArgumentParser(description='Compare the encoding time, resulting filesize and (optionally) the VMAF '
	'value obtained with the different encoder presets: '
	"'veryslow', 'slower', 'slow', 'medium', 'fast', 'faster', 'veryfast', 'superfast' and 'ultrafast'. "
	'You can edit the presets that are tested by editing the presets list on line 2 of compare-presets.py',
	formatter_class=RawTextHelpFormatter)

parser.add_argument('-f', '--video-path', type=str, required=True, help='Enter the path of the video. '
	'A relative or absolute path can be specified.'
	'If the path contains a space, it must be surrounded in double quotes.\n'
	'Example: -path "C:/Users/H/Desktop/file 1.mp4"')

parser.add_argument('-e', '--video-encoder', type=str, default='libx264', choices=['libx264', 'libx265'],
	help='Specify the encoder to use. Must enter libx264 or libx265. Default: libx264\nExample: -e libx265')

parser.add_argument('-crf', '--crf-value', type=str, default='23', help='Enter the CRF value to be used (default: 23)')

parser.add_argument('-t', '--encoding-time', type=str, help='Encode this many seconds of the video. '
	'If not specified, the whole video will get encoded.')

parser.add_argument('-p', '--presets', nargs='+', required=True,
	choices=['placebo', 'veryslow', 'slower', 'slow', 'medium', 'fast', 'faster', 'veryfast', 'superfast', 'ultrafast'],
	help="List the presets you want to be tested (separated by a space).\n"
	"Choose from: 'veryslow', 'slower', 'slow', 'medium', 'fast', 'faster', 'veryfast', 'superfast', 'ultrafast'\n"
	"Example: -p fast veryfast ultrafast", metavar='presets')

parser.add_argument('-pm', '--phone-model', action='store_true', 
	help='Enable VMAF phone model (default: False)')

parser.add_argument('-dp', '--decimal-places', default=3, help='The number of decimal places to use for the data '
				    'in the table (default: 3)')

parser.add_argument('-dqs', '--disable-quality-stats', action='store_true', 
	help='Disable calculation of PSNR, SSIM and VMAF; only show encoding time and filesize (improves completion time).')

args = parser.parse_args()

filename = args.video_path.split('/')[-1]
print(f'File: {filename}')

video = args.video_path
cap = cv2.VideoCapture(video)
fps = str(cap.get(cv2.CAP_PROP_FPS))
print(f'Framerate: {fps} FPS')

chosen_presets = args.presets
# Default CRF value is 23 if -crf argument is not specified.
crf_value = '23' if not args.crf_value else args.crf_value
# Default number of decimal places is 3 if -dp argument is not specified.
decimal_places = 3 if not args.decimal_places else int(args.decimal_places)

output_folder = f'({filename})/CRF {crf_value}'
os.makedirs(output_folder, exist_ok=True)
# The comparison table will be in the following path:
comparison_table = os.path.join(output_folder, 'Table.txt')

time_message = ''
if args.encoding_time:
	time_message = f' for {args.encoding_time} seconds' if int(args.encoding_time) > 1 else 'for 1 second'

with open(comparison_table, 'w') as f:
	f.write(f'You chose to encode {args.video_path}{time_message} using {args.video_encoder} '
		f'with a CRF of {args.crf_value}.\nPSNR/SSIM/VMAF values are in the format: Min | Standard Deviation | Mean\n')

# This will be used when comparing the size of the encoded file to the original.
original_video_size = os.path.getsize(args.video_path) / 1_000_000

# Initialise the comparison table that will be created.
table = PrettyTable()

for preset in chosen_presets:

	output_file_path = os.path.join(output_folder, f'{preset}.mkv')

	subprocess_args = [
		"ffmpeg", "-loglevel", "warning", "-stats", "-y",
		"-i", args.video_path,
		"-c:v", args.video_encoder, "-crf", args.crf_value, "-preset", preset,
		"-c:a", "copy", "-c:s", "copy", "-movflags", "+faststart", output_file_path
	]

	if args.encoding_time:
		subprocess_args.insert(7, "-t")
		subprocess_args.insert(8, args.encoding_time)

	separator()
	print(f'Encoding with preset {preset}...')

	start_time = time.time()

	subprocess.run(subprocess_args)

	end_time = time.time()
	time_to_convert = end_time - start_time
	time_rounded = round(time_to_convert, decimal_places)
	print('Done!')

	size_of_file = os.path.getsize(output_file_path) / 1_000_000
	size_compared_to_original = round(((size_of_file / original_video_size) * 100), 3) 
	size_rounded = round(size_of_file, decimal_places)

	if not args.disable_quality_stats:
		
		json_file_path = f'{output_folder}/{preset}.json'
		# (os.path.join doesn't work with libvmaf's log_path option)

		vmaf_options = {
			"model_path": "vmaf_v0.6.1.pkl",
			"phone_model": "1" if args.phone_model else "0",
			"psnr": "1",
			"ssim": "1",
			"log_path": json_file_path, 
			"log_fmt": "json"
		}

		vmaf_options = ":".join(f'{key}={value}' for key, value in vmaf_options.items())

		subprocess_args = [
			"ffmpeg", "-loglevel", "error", "-stats", "-r", fps, "-i", output_file_path,
			"-r", fps, "-i", args.video_path,
			"-lavfi", "[0:v]setpts=PTS-STARTPTS[dist];[1:v]setpts=PTS-STARTPTS[ref];[dist][ref]"
			f'libvmaf={vmaf_options}', "-f", "null", "-"
		]

		separator()
		print(f'Calculating the quality achieved with preset {preset}...')
		subprocess.run(subprocess_args)
		print('Done!')

		with open(json_file_path, 'r') as f:
			file_contents = json.load(f)

		frame_numbers = [frame['frameNum'] for frame in file_contents['frames']]

		# SSIM
		ssim_scores = [ssim['metrics']['ssim'] for ssim in file_contents['frames']]
		mean_ssim = round(np.mean(ssim_scores), decimal_places)
		min_ssim = round(min(ssim_scores), decimal_places)
		ssim_std = round(np.std(ssim_scores), decimal_places) # Standard deviation.
		ssim = f'{min_ssim} | {ssim_std} | {mean_ssim}'
		# Plot a line showing the variation of the SSIM throughout the video.
		print(f'Plotting SSIM graph for preset {preset}...')
		plt.plot(frame_numbers, ssim_scores, label='SSIM')

		# PSNR
		psnr_scores = [psnr['metrics']['psnr'] for psnr in file_contents['frames']]
		mean_psnr = round(np.mean(psnr_scores), decimal_places)
		min_psnr = round(min(psnr_scores), decimal_places)
		psnr_std = round(np.std(psnr_scores), decimal_places) # Standard deviation.
		psnr = f'{min_psnr} | {psnr_std} | {mean_psnr}'
		# Plot a line showing the variation of the PSNR throughout the video.
		print(f'Plotting PSNR graph for preset {preset}...')
		plt.plot(frame_numbers, psnr_scores, label='PSNR')

		# VMAF
		vmaf_scores = [frame['metrics']['vmaf'] for frame in file_contents['frames']]
		mean_vmaf = round(np.mean(vmaf_scores), decimal_places)
		min_vmaf = round(min(vmaf_scores), decimal_places)
		vmaf_std = round(np.std(vmaf_scores), decimal_places) # Standard deviation.
		vmaf = f'{min_vmaf} | {vmaf_std} | {mean_vmaf}'
		# Plot a line showing the variation of the VMAF score throughout the video.
		print(f'Plotting VMAF graph for preset {preset}...')
		plt.plot(frame_numbers, vmaf_scores, label='VMAF')

		# Set the names of the columns for the presets comparison table.
		table.field_names = ['Preset', 'Encoding Time (s)', 'Size', 'Size Compared to Original', 'SSIM', 'PSNR', 'VMAF']
		# The values for the row for the current preset.
		row = [preset, f'{time_rounded}', f'{size_rounded} MB', f'{size_compared_to_original}%', ssim, psnr, vmaf]
		table.add_row(row)

		plt.suptitle(f'Preset "{preset}"')
		plt.xlabel('Frame Number')
		plt.ylabel('Value of Quality Metric')
		plt.legend(loc='lower right')
		plt.savefig(os.path.join(output_folder, f'{preset}.png'))
		plt.clf()

	# -dqs argument specified
	else: 
		table.add_row([preset, f'{time_rounded}', f'{size_rounded} MB', f'{size_compared_to_original}%'])

# Write the table to the .txt file.
with open(comparison_table, 'a') as f:
	f.write(table.get_string())

separator()
print(f'All done! Check out the ({filename}) folder.')
