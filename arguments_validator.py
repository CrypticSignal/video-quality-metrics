import os

from utils import is_list


class ArgumentsValidator:
    def validate(self, args):
        validation_results = []
        validation_errors = []
        result = True

        validation_results.append(self.__validate_original_video_exists(
                args.original_video_path))
        validation_results.append(
            self.__validate_crf_and_preset_count(args.no_transcoding_mode, args.crf_value, args.preset))

        for validation_tuple in validation_results:
            if not validation_tuple[0]:
                result = False
                validation_errors.append(validation_tuple[1])

        return result, validation_errors

    def __validate_original_video_exists(self, video_path):
        return (os.path.exists(video_path), f'Unable to find {video_path}')

    def __validate_crf_and_preset_count(self, no_transcoding_mode, crf_values, presets):
        result = False
        if not no_transcoding_mode and isinstance(crf_values, int) and isinstance(presets, str):
            return (result, 'No CRF value or preset has been specified. Did you mean to use the -ntm mode?')

        elif is_list(crf_values) and len(crf_values) > 1 and is_list(presets) and len(presets) > 1:
            return (result, 'More than one CRF value AND more than one preset specified. No suitable mode found.')

        else:
            return (True, '')
