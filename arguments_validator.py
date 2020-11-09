import os

from utils import is_list


class ArgumentsValidator:
    def validate(self, arguments):
        validation_results = []
        validation_errors = []
        result = True

        validation_results.append(self._validate_original_video_exists(
                arguments.original_video_path))
        validation_results.append(
            self._validate_crf_and_preset_count(
                arguments.crf_value, arguments.preset))

        for validation_tuple in validation_results:
            if not validation_tuple[0]:
                result = False
                validation_errors.append(validation_tuple[1])

        return result, validation_errors

    def _validate_original_video_exists(self, video_path):
        return (os.path.exists(video_path),
                f'Original video {video_path} does not exist')

    def _validate_crf_and_preset_count(self, crf_values, presets):
        result = True
        if is_list(crf_values) and len(crf_values) > 1 and is_list(presets) \
                and len(presets) > 1:
            result = False

        return (result, 'More than one CRF value AND more than one preset '
                        'specified. No suitable mode found.')
