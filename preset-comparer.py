# Remove the presets that you don't want to be tested.
presets = ['veryslow', 'slower', 'slow', 'medium', 'fast', 'faster', 'veryfast', 'superfast', 'ultrafast']

import argparse, time, os, subprocess, json
from prettytable import PrettyTable

def separator():
	print('-----------------------------------------------------------------------------------------------------------') 

separator()
print('If the path contains a space, the path argument must be surrounded in double quotes.')
print('Example: python compare-presets.py -path "C:/Users/H/Desktop/test file.mp4" -encoder libx264 -crf 23 -t 60')
print("For more information, enter 'compare-presets.py -h'")
separator()

parser = argparse.ArgumentParser(description='Compare the encoding time, resulting filesize and (optionally) the VMAF '
	'value obtained with the different encoder presets: '
	"'veryslow', 'slower', 'slow', 'medium', 'fast', 'faster', 'veryfast', 'superfast' and 'ultrafast'. "
	'You can edit the presets that are tested by editing the presets list on line 2 of compare-presets.py')

parser.add_argument('-path', '--video-path', type=str, required=True, help='Enter the path of the video. '
	'A relative or absolute path can be specified. '
	'If the path contains a space, it must be surrounded in double quotes.')

parser.add_argument('-encoder', '--video-encoder', type=str, required=True, choices=['libx264', 'libx265'],
	help='Specify the encoder to use. Must enter libx264 or libx265')

parser.add_argument('-crf', '--crf-value', type=str, required=True, help='Enter the CRF value to be used.')

parser.add_argument('-t', '--encoding-time', type=str, help='Encode this many seconds of the video. '
	'If not specified, the whole video will get encoded.')

parser.add_argument('-vmaf', '--calculate-vmaf', action='store_true', 
	help='Specify this argument if you want the VMAF value to be calculated for each preset. '
	'(drastically increases completion time)')

args = parser.parse_args()

# Initialise the comparison table that will be created.
table = PrettyTable()

filename = args.video_path.split('/')[-1]
print(f'File: {filename}')
output_folder = f'({filename})'
os.makedirs(output_folder, exist_ok=True)

comparison_file_dir = os.path.join(output_folder, f'Presets Comparison (CRF {args.crf_value}).txt')

if not args.encoding_time:
	txt_file_message = ''
else:
	txt_file_message = f' for {args.encoding_time} seconds' if int(args.encoding_time) > 1 else 'for 1 second'

with open(comparison_file_dir, 'w') as f:
	f.write(f'You chose to encode {args.video_path}{txt_file_message} using {args.video_encoder} '
		f'with a CRF of {args.crf_value}.\n')

# This will be used when comparing the size of the encoded file to the original.
original_video_size = os.path.getsize(args.video_path) / 1_000_000

for preset in presets:

	encoding_time_flag = f'-t {args.encoding_time}' if args.encoding_time else ''
	print(encoding_time_flag)
	output_file_path = os.path.join(output_folder, f'{preset}.mkv')

	separator()
	print(f'Encoding with preset {preset}...')

	start_time = time.time()

	os.system(f'ffmpeg -loglevel warning -stats -y -i "{args.video_path}" {encoding_time_flag} '
		f'-c:v {args.video_encoder} -crf {args.crf_value} -preset {preset} -c:a copy -c:s copy '
		f'-movflags +faststart "{output_file_path}"')

	end_time = time.time()
	time_to_convert = end_time - start_time
	time_rounded = round(time_to_convert, 2)
	print('Done!')

	size_of_file = os.path.getsize(output_file_path) / 1_000_000
	size_compared_to_original = round(((size_of_file / original_video_size) * 100), 2) 
	size_rounded = round(size_of_file, 2)
	product = round(time_to_convert * size_of_file, 2)

	if args.calculate_vmaf: # -vmaf argument specified

		# os.path.join doesn't work with log_path= when using libvmaf
		json_file_path = f'{output_folder}/VMAF with preset {preset}.json'

		separator()
		print(f'Calculating the VMAF achieved with preset {preset}...')

		vmaf_start_time = time.time()

		# vmaf_options = {
		# 	"model_path": "vmaf_v0.6.1.pkl",
		# 	"log_path": f'"{json_file_path}"',
		# 	"log_fmt": "json"
		# }

		# vmaf_options = ":".join(f'{key}={value}' for key, value in vmaf_options.items())
		# print('vmaf options is:')
		# print(vmaf_options)

		# subprocess.run(
		# 	[
		# 	"ffmpeg", "-loglevel", "error", "-stats",
		# 	"-i", output_file_path, "-i", args.video_path,
		# 	"-lavfi", f'libvmaf={vmaf_options}',
		# 	"-f", "null", "-"
		# 	]
		# )

		os.system(f'ffmpeg -loglevel error -stats -i "{output_file_path}" -i "{args.video_path}" '
			f'-lavfi libvmaf=model_path=vmaf_v0.6.1.pkl:log_path="{json_file_path}":log_fmt=json -f null -')

		vmaf_end_time = time.time()
		calculation_time = round(vmaf_end_time - vmaf_start_time, 1)
		print(f'Time taken to calculate VMAF: {calculation_time} seconds.')

		with open(json_file_path, 'r') as f:
			json_dict = json.load(f)

		vmaf = round(json_dict['VMAF score'], 2)

		table.field_names = ['Preset', 'Encoding Time (s)', 'Size', 'Size Compared to Original',
			'Product of Time and Size', 'VMAF']

		table.add_row([preset, f'{time_rounded}', f'{size_rounded} MB', f'{size_compared_to_original}%', product, vmaf])

	else: # -vmaf argument not specified.

		table.field_names = ['Preset', 'Encoding Time (s)', 'Size', 'Size Compared to Original',
			'Product of Time and Size']

		table.add_row([preset, f'{time_rounded}', f'{size_rounded} MB', f'{size_compared_to_original}%', product])
		
with open(comparison_file_dir, 'a') as f:
	f.write(table.get_string())

print(f'Done! Comparison data saved in {comparison_file_dir}')
input('You may now close this window.')
