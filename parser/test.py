import argparse
import warnings
from dataclasses import dataclass
from pathlib import Path
import yaml

context_size = 100


def test_text_reconstruction(original_text, reconstructed_text):
    # Remove all whitespaces for comparison
    original_text_no_whitespace = ''.join(original_text.split())
    reconstructed_text_no_whitespace = ''.join(reconstructed_text.split())

    # Check if the texts are the same
    if original_text_no_whitespace != reconstructed_text_no_whitespace:
        # Find the position of the first difference
        for i, (orig_char, recon_char) in enumerate(
                zip(original_text_no_whitespace, reconstructed_text_no_whitespace)):
            if orig_char != recon_char:
                # Calculate the starting position for the 50 character context
                start = max(0, i - int(context_size / 2))
                # Extract the context from the original text
                context = original_text_no_whitespace[start:start + context_size]
                context_vs = reconstructed_text_no_whitespace[start:start + context_size]

                warnings.warn(f'\n{context}\nVS\n{context_vs}', UserWarning)
                # raise
                return False
        # In case the reconstructed text is shorter than the original
        context = original_text[-context_size:]
        warnings.warn(context, UserWarning)
        return False
    return True


def test_parsing_consistency(original_parsed_data, reconstructed_parsed_data):
    return original_parsed_data == reconstructed_parsed_data


def test_file(file_path, parser_func, reconstruct_func):
    # Read the content
    with open(file_path, 'r', encoding='utf-8-sig') as file:
        content = file.read()

    parsed_data = parser_func.parse(content)
    reconstructed_text = reconstruct_func(parsed_data, {})
    reconstructed_parsed_data = parser_func.parse(reconstructed_text)

    return test_text_reconstruction(content, reconstructed_text), test_parsing_consistency(parsed_data,
                                                                                           reconstructed_parsed_data)


exclusion_list = {
    "common\\cultures\\00_additional_cultures.txt",
    "common\\cultures\\00_cultures.txt",
    'common\\genes\\02_genes_accessories_hairstyles.txt',
    'common\\genes\\03_genes_accessories_beards.txt',
    'common\\genes\\97_genes_accessories_clothes.txt',
    'common\\genes\\99_genes_special.txt',
    'common\\laws\\00_slavery.txt',
    'common\\mobilization_options\\00_mobilization_option.txt',
    'common\\named_colors\\00_formation_colors.txt',
    'common\\state_traits\\06_eastern_europe_traits.txt',
    'gfx'
}


@dataclass
class Config:
    items_same_line: bool
    comments_same_level: bool


class Mutex:

    def __init__(self, keys, can_be_empty, type):
        self.keys = keys
        self.can_be_empty = can_be_empty
        self.type = type

    def check(self, config: dict) -> bool:
        if self.type == bool:
            return self.check_bool(config)
        elif self.type == int:
            return self.check_int(config)

    def check_bool(self, config) -> bool:
        count = 0
        for key in self.keys:
            if config[key]:
                count += 1
        if count == 1 or (count == 0 and self.can_be_empty):
            return True
        return False

    # assumes > ordered series of numbers creating a mutually exclusive integer ranges
    def check_int(self, config: dict) -> bool:
        new_key_list = [key for key in self.keys if config[key] is not None]
        for i, key in enumerate(new_key_list[1:], 1):
            if config[key] is None or config[new_key_list[i - 1]] > config[key]:
                return False
        return True

    def set(self, config: dict, key: str, value: int = None) -> None:
        if key not in self.keys:
            raise ValueError("Tried to set non existant key")
        if self.type == int and value is None:
            raise ValueError("Tried to set int mutex without giving a value")

        if self.type == bool:
            self.set_bool(config, key)
        elif self.type == int:
            self.set_int(config, key, value)

    def set_bool(self, config: dict, set_key: str) -> None:
        for key in self.keys:
            if key is not set_key:
                config[key] = False
            else:
                config[key] = True

    def set_int(self, config: dict, set_key: str, set_value: int) -> None:
        index = self.keys.index(set_key)
        for key in self.keys[:set_key]:
            value = config[key]
            if value > set_value:
                config[set_key] = set_value


def load_yaml_config(file_path):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config


def parse_args():
    parser = argparse.ArgumentParser(description="A script with YAML config and command-line args")
    parser.add_argument('--config', type=str, help='Path to the YAML configuration file', default=os.path.normpath('parser/config/general.yml'))
    parser.add_argument('--default_no_double_line', type=bool, help='Default no double line')
    parser.add_argument('--allow_single_list_no_double_line', type=bool, help='Allow single list no double line')
    parser.add_argument('--default_yes_double_line', type=bool, help='Default yes double line')
    parser.add_argument('--object_yes_double_line', type=bool, help='Object yes double line')
    parser.add_argument('--force_single_line_until_item_count', type=int, help='Force single line until item count')
    parser.add_argument('--force_multi_line_from_item_count', type=int, help='Force multi line from item count')

    mutex_1 = Mutex(["default_no_double_line", "default_yes_double_line"], True, bool)
    mutex_2 = Mutex(["force_single_line_until_item_count", "force_multi_line_from_item_count"], True, bool)
    mutex_3 = Mutex(["object_yes_double_line"], True, bool)
    mutex_4 = Mutex(["allow_single_list_no_double_line", "default_yes_double_line", "force_multi_line_from_item_count"], True, bool)
    mutex_5 = Mutex(["force_single_line_until_item_count", "force_multi_line_from_item_count"], False, int)
    mutexes = [mutex_1, mutex_2, mutex_3, mutex_4, mutex_5]

    return parser.parse_args(), mutexes


def test_all_txt_files(folder_path, parser_func, reconstruct_func):
    total_files = 0
    passed_reconstruction = 0
    passed_consistency = 0
    failed_files = []

    for root, dirs, files in os.walk(folder_path):
        for file_name in files:
            if file_name.endswith('.txt'):
                print(file_name)
                file_path = os.path.join(root, file_name)
                if os.path.getsize(file_path) <= 3:
                    continue

                total_files += 1

                print("Testing", file_path)
                try:
                    reconstruction_bool, consistency_bool = test_file(file_path, parser_func, reconstruct_func)
                except TypeError:
                    reconstruction_bool = False
                    consistency_bool = False
                # Track passed tests
                if reconstruction_bool:
                    passed_reconstruction += 1
                if consistency_bool:
                    passed_consistency += 1

                # Track failed files
                if not reconstruction_bool:
                    failed_files.append(file_path)

    # Calculate percentages
    reconstruction_percentage = (passed_reconstruction / total_files) * 100 if total_files > 0 else 0
    consistency_percentage = (passed_consistency / total_files) * 100 if total_files > 0 else 0

    # Produce report
    report = {
        'Reconstruction Test Pass Rate': reconstruction_percentage,
        'Parsing Consistency Test Pass Rate': consistency_percentage,
        'Failed Files': failed_files
    }

    return report


def process_file(file_path, parser_func, reconstruct_func, reconstruct_config):
    # Read the content
    with open(file_path, 'r', encoding='utf-8-sig') as file:
        content = file.read()

    original_parsed_data = parser_func.parse(content)
    reconstructed_text = reconstruct_func(original_parsed_data, reconstruct_config)
    #
    with open(file_path, 'w', encoding='utf-8-sig') as file:
        file.write(reconstructed_text)


def is_excluded(file_path, exclusion_list):
    path = Path(file_path)
    for pattern in exclusion_list:
        if path.match(pattern):
            return True
    return False


def process_all_txt_files(folder_path, parser_func, reconstruct_func, exclusion_list, reconstruct_config):
    for root, dirs, files in os.walk(folder_path):
        dirs[:] = [d for d in dirs if not is_excluded(os.path.join(root, d), exclusion_list)]
        for file_name in files:
            if file_name.endswith('.txt'):
                file_path = os.path.join(root, file_name)
                if not is_excluded(file_path, exclusion_list):
                    print(f"Processing {file_path}:")
                    process_file(file_path, parser_func, reconstruct_func, reconstruct_config)
                else:
                    print(f"Excluded {file_path}")


if __name__ == '__main__':
    from constants import Test
    import os
    import re
    import pprint
    from victoria_script_parses import parser
    from victoria_script_reconstructor import reconstruct

    from constants import Test
    import os

    args, mutexes = parse_args()
    config = load_yaml_config(args.config)["config"]

    args_dict = vars(args)
    config_path = args_dict.pop('config')

    # Override config values with command-line arguments if provided
    for key, value in args_dict.items():
        if value is not None:
            config[key] = value


    for mutex in mutexes:
        if not mutex.check(config):
            raise Exception(f"The provided general config is not valid conflicting mutexes are: {mutex.keys} with values {[config[key] for key in mutex.keys]}\n(only one should be true, or ints should be in ascending order)")

    # path = os.path.join(Test.game_directory, "common\\")
    # path = os.path.normpath(
    #     'C:\\Program Files (x86)\\Steam\\steamapps\\common\\Victoria 3\\game\\common\\coat_of_arms\\coat_of_arms\\02_countries.txt')

    # path = os.path.normpath("C:\\Users\\hidde\\Documents\\Paradox Interactive\\Victoria 3\\mod\\External-mods")
    path = os.path.normpath(
        "C:\\Users\\hidde\\Documents\\Paradox Interactive\\Victoria 3\\mod\\Victoria-3-dev")

    # process_all_txt_files(path, parser, reconstruct, exclusion_list, config)
    # print(test_all_txt_files(path, parser, reconstruct))

    # with open(path, encoding='utf-8-sig') as file:
    #     file_string = file.read()
    # # print(path)

    # parsed_data = parser.parse(test_input)
    # reconstructed_text = reconstruct(parsed_data)
    # reconstructed_parsed_data = parser.parse(reconstructed_text)
    #
    # print(test_text_reconstruction(test_input, reconstructed_text))
    # print(test_parsing_consistency(parsed_data, reconstructed_parsed_data))
    # #
    # # print(file_string)
    # # Parse an expression
    # # pprint.pprint(reconstructed_parsed_data)
    # if parsed_data:
    #     thing = reconstruct(reconstructed_parsed_data)
    #     print(thing)
