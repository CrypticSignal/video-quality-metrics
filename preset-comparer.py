import argparse, cv2, time, os, subprocess, json
from argparse import RawTextHelpFormatter
from prettytable import PrettyTable

def separator():
	print('-----------------------------------------------------------------------------------------------------------') 

separator()
print('If the path contains a space, the path argument must be surrounded in double quotes.')
print('Example: python compare-presets.py -f "C:/Users/H/Desktop/test file.mp4" -p fast veryfast')
print("For more information, enter 'compare-presets.py -h'")
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

parser.add_argument('-crf', '--crf-value', type=str, default='23', help='Enter the CRF value to be used. Default: 23')

parser.add_argument('-t', '--encoding-time', type=str, help='Encode this many seconds of the video. '
	'If not specified, the whole video will get encoded.')

parser.add_argument('-p', '--presets', nargs='+', required=True,
	choices=['placebo', 'veryslow', 'slower', 'slow', 'medium', 'fast', 'faster', 'veryfast', 'superfast', 'ultrafast'],
	help="List the presets you want to be tested (separated by a space).\n"
	"Choose from: 'veryslow', 'slower', 'slow', 'medium', 'fast', 'faster', 'veryfast', 'superfast', 'ultrafast'\n"
	"Example: -p fast veryfast ultrafast", metavar='presets')

parser.add_argument('-vmaf', '--calculate-vmaf', action='store_true', 
	help='Specify this argument if you want the VMAF value to be calculated for each preset. '
	'(drastically increases completion time)')

args = parser.parse_args()

filename = args.video_path.split('/')[-1]
print(f'File: {filename}')

video = args.video_path
cap = cv2.VideoCapture(video)
fps = str(cap.get(cv2.CAP_PROP_FPS))
print(f'Framerate: {fps}')

chosen_presets = args.presets

# Initialise the comparison table that will be created.
table = PrettyTable()

output_folder = f'({filename})'
os.makedirs(output_folder, exist_ok=True)

comparison_file_dir = os.path.join(output_folder, f'Presets Comparison (CRF {args.crf_value}).txt')

if args.encoding_time:
	time_message = f' for {args.encoding_time} seconds' if int(args.encoding_time) > 1 else 'for 1 second'
else:
	time_message = ''

with open(comparison_file_dir, 'w') as f:
	f.write(f'You chose to encode {args.video_path}{time_message} using {args.video_encoder} '
		f'with a CRF of {args.crf_value}.\n')

# This will be used when comparing the size of the encoded file to the original.
original_video_size = os.path.getsize(args.video_path) / 1_000_000

for preset in chosen_presets:

	crf_value = '23' # Default CRF value.
	if args.crf_value:
		crf_value = args.crf_value

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
	time_rounded = round(time_to_convert, 2)
	print('Done!')

	size_of_file = os.path.getsize(output_file_path) / 1_000_000
	size_compared_to_original = round(((size_of_file / original_video_size) * 100), 2) 
	size_rounded = round(size_of_file, 2)
	product = round(time_to_convert * size_of_file, 2)

	if args.calculate_vmaf: # -vmaf argument specified

		json_file_path = f'{output_folder}/VMAF with preset {preset}.json'
		# (os.path.join doesn't work with libvmaf's log_path option)

		separator()
		print(f'Calculating the VMAF achieved with preset {preset}...')

		vmaf_start_time = time.time()

		vmaf_options = {
			"model_path": "vmaf_v0.6.1.pkl",
			#"psnr": "1",
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

		subprocess.run(subprocess_args)

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
