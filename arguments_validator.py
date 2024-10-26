import os
import requests


class ArgumentsValidator:
    def validate(self, args):
        validation_results = []
        validation_errors = []
        result = True

        validation_results.append(
            self.__validate_original_video_exists(args.input_video)
        )

        for validation_tuple in validation_results:
            if not validation_tuple[0]:
                result = False
                validation_errors.append(validation_tuple[1])

        return result, validation_errors

    def __validate_original_video_exists(self, input_video):
        return (
            os.path.exists(input_video) or requests.get(input_video).ok,
            f"Unable to find {input_video}",
        )
