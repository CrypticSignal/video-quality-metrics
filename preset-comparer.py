import time, os

presets = ['veryslow', 'slower', 'slow', 'medium', 'fast', 'faster', 'veryfast', 'superfast', 'ultrafast']
video_extensions = ['mp4', 'mkv', 'mov', 'flv', 'wmv', 'avi', 'webm', 'MTS']

compatible_file_list = [filename for filename in os.listdir() if filename.split(".")[-1] in video_extensions]
num_compatible_files = len(compatible_file_list)

if num_compatible_files >= 1:

    for i in range(len(compatible_file_list)):
        print("{}. {} ".format(i+1, compatible_file_list[i]))

    chosen_file = input('Please select your desired video file by entering its associated integer: ')

    chosen_file_index = int(chosen_file)
    video = compatible_file_list[chosen_file_index - 1]

ext = video.split('.')[-1]
characters_to_remove = len(ext) + 1
name_without_ext = video[:- characters_to_remove]

crf_value = input('Enter a CRF value to use (0-51): ')
encoding_time = input('Desired encoding time in seconds (enter 0 if you want to encode the whole file): ').strip()

if encoding_time.strip() == '0':
	log_file_message = ''
else:
	log_file_message = f'for {encoding_time} seconds ' if int(encoding_time) > 1 else 'for 1 second '

with open(f'[CRF {crf_value}] {name_without_ext} [Presets Log].txt', 'a') as f:
	f.write(f'You chose to encode {video} {log_file_message}with a CRF of {crf_value}.\n' \
		'The last column shows the product of filesize and time, where a lower value is better.\n')

for preset in presets:

	encoding_time_flag = f'-t {encoding_time}' if encoding_time != '0' else ''
	output_filename = f'"{name_without_ext} [{preset}].mkv"'

	start_time = time.time()

	os.system(f'ffmpeg -y -i "{video}" {encoding_time_flag} -c:v libx264 -crf {crf_value} -preset {preset} -c:a copy \
	-movflags +faststart {output_filename}')
		
	end_time = time.time()
	time_to_convert = end_time - start_time
	time_rounded = round(time_to_convert, 3)
	size_of_file = os.path.getsize(f'{name_without_ext} [{preset}].mkv') / 1_000_000
	size_rounded = round(size_of_file, 3)
	product = round(time_to_convert * size_of_file, 3)

	with open(f'[CRF {crf_value}] {name_without_ext} [Presets Log].txt', 'a') as f:
		f.write(f'{preset} | {time_rounded} seconds | {size_rounded} MB | {product} \n')

input(f'Done! Log file saved as [CRF {crf_value}] {name_without_ext} [Presets Log].txt')