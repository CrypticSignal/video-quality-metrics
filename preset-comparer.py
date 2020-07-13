import time, os
from prettytable import PrettyTable

def separator():
	print('-----------------------------------------------------------------------------------------------------------') 

separator()
print('This program must be in the same directory as the video file that you want to encode. '
		'If it\'s not, close this window and make sure that this is the case before re-opening this program.')
separator()

encoders = ['libx264', 'libx265']
# Remove presets that you don't want to be tested.
presets = ['veryslow', 'slower', 'slow', 'medium', 'fast', 'faster', 'veryfast', 'superfast', 'ultrafast']
# Add extensions if necessary.
video_extensions = ['mp4', 'mkv', 'mov', 'flv', 'wmv', 'avi', 'webm', 'MTS']

# Initialise the comparison table that will be created.
table = PrettyTable()
table.field_names = ['Preset', 'Encoding Time (s)', 'Size', 'Size Compared to Original', 'Product of Time and Size']

print('The following video files found in the current directory:')
separator()

video_files = [filename for filename in os.listdir() if filename.split(".")[-1] in video_extensions]
num_video_files = len(video_files)

if num_video_files >= 1:

	for position, file in enumerate(video_files):
		print(position, file)

	separator()
	chosen_file = input('Select the video you wish to encode by entering the number that appears before it: ')
	video = video_files[int(chosen_file)]
	print(f'You chose {video}')
	separator()

else:
	print('No video files found in the current directory.')

original_video_size = os.path.getsize(video) / 1_000_000

print('The file can be encoded using one of the following encoders:')

for position, encoder in enumerate(encoders):
    print(position, encoder)

encoder = input('Enter 0 or 1, depending on which encoder you want to be used: ').strip()
encoder = 'libx264' if encoder == '0' else 'libx265'
print(f'You chose {encoder}')
separator()

crf_value = input('Enter a CRF value to use (0-51): ')
print(f'A CRF value of {crf_value} will be used.')
separator()

encoding_time = input('Desired encoding time in seconds (enter 0 if you want to encode the whole file): ').strip()

ext = video.split('.')[-1]
characters_to_remove = len(ext) + 1
name_without_ext = video[:- characters_to_remove]

if encoding_time.strip() == '0':
	log_file_message = ''
else:
	log_file_message = f' for {encoding_time} seconds' if int(encoding_time) > 1 else 'for 1 second'

with open(f'[CRF {crf_value}] {name_without_ext} [Presets Log].txt', 'a') as f:
	f.write(f'You chose to encode {video}{log_file_message} using {encoder} with a CRF of {crf_value}.\n')

time_encodings_began = time.time()

for preset in presets:

	encoding_time_flag = f'-t {encoding_time}' if encoding_time != '0' else ''
	output_filename = f'"{name_without_ext} [{preset}].mkv"'

	start_time = time.time()
	print(f'Encoding with preset {preset}...')
	os.system(f'ffmpeg -hide_banner -y -i "{video}" {encoding_time_flag} -c:v {encoder} -crf {crf_value} \
		-preset {preset} -c:a copy -movflags +faststart {output_filename}')
		
	end_time = time.time()
	time_to_convert = end_time - start_time
	time_rounded = round(time_to_convert, 2)

	size_of_file = os.path.getsize(f'{name_without_ext} [{preset}].mkv') / 1_000_000
	size_compared_to_original = round(((size_of_file / original_video_size) * 100), 2) 
	size_rounded = round(size_of_file, 2)
	
	product = round(time_to_convert * size_of_file, 2)

	table.add_row([preset, f'{time_rounded}', f'{size_rounded} MB', f'{size_compared_to_original}%', product])

time_encodings_finished = time.time()
total_time = round((time_encodings_finished - time_encodings_began), 1)

with open(f'[CRF {crf_value}] {name_without_ext} [Presets Log].txt', 'a') as f:
	f.write(table.get_string())


with open(f'[CRF {crf_value}] {name_without_ext} [Presets Log].txt', 'a') as f:
	f.write(f'\nTime taken to encode with all presets: {total_time} seconds.')

print(f'Done! Time taken to encode with all presets: {total_time} seconds.')
print(f'Log file saved as [CRF {crf_value}] {name_without_ext} [Presets Log].txt')
input('You may now close this window.')
