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


def test_file(file_path, parser_func, reconstruct_func, config):
    # Read the content
    with open(file_path, 'r', encoding='utf-8-sig') as file:
        content = file.read()

    parsed_data = parser_func.parse(content)
    reconstructed_text = reconstruct_func(parsed_data, config)
    reconstructed_parsed_data = parser_func.parse(reconstructed_text)

    return test_text_reconstruction(content, reconstructed_text), test_parsing_consistency(parsed_data,
                                                                                           reconstructed_parsed_data)


class Mutex:

    def __init__(self, keys, can_be_empty, type):
        self.keys = keys
        self.can_be_empty = can_be_empty
        self.type = type

    def check(self, config: dict) -> bool:
        if self.type == bool or self.type == str:
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
            print(config[new_key_list[i - 1]], config[key])
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
        elif self.type == str:
            self.set_string(key, value)

    def set_bool(self, config: dict, set_key: str) -> None:
        for key in self.keys:
            if key is not set_key:
                config[key] = False
            else:
                config[key] = True

    def set_int(self, config: dict, set_key: str, set_value: int) -> None:
        tmp_keys = list(self.keys)
        index = self.keys.index(tmp_keys)
        for key in tmp_keys[:index]:
            value = config[key]
            if value > set_value:
                config[key] = set_value

        for key in tmp_keys[index:]:
            value = config[key]
            if value < set_value:
                config[key] = set_value

    def set_string(self, config: dict, set_key: str, set_value: int) -> None:
        for key in self.keys:
            if key is not set_key:
                config[key] = set_value
            else:
                config[key] = set_value


def load_yaml_config(file_path):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config


def parse_args():
    parser = argparse.ArgumentParser(description="A script with YAML config and command-line args")
    parser.add_argument('--config', type=str, help='Path to the YAML configuration file',
                        default=os.path.normpath('parser/config/general.yml'))
    parser.add_argument('--default_no_double_line', type=bool, help='Default no double line')
    parser.add_argument('--default_yes_double_line', type=bool, help='Default yes double line')
    parser.add_argument('--object_yes_double_line', type=bool, help='Object yes double line')
    parser.add_argument('--force_single_line_until_item_count', type=int, help='Force single line until item count')
    parser.add_argument('--force_multi_line_from_item_count', type=int, help='Force multi line from item count')
    parser.add_argument('--format_folder', type=str, help='Format folder')
    parser.add_argument("--format_files", nargs='*', type=str, help="Format files")

    mutex_1 = Mutex(["default_no_double_line", "default_yes_double_line"], True, bool)
    mutex_3 = Mutex(["object_yes_double_line"], True, bool)
    mutex_4 = Mutex(["default_yes_double_line", "force_multi_line_from_item_count"], True, bool)
    mutex_5 = Mutex(["force_single_line_until_item_count", "force_multi_line_from_item_count"], True, int)
    mutex_6 = Mutex(["format_folder", "format_files"], False, str)
    mutexes = [mutex_1, mutex_3, mutex_4, mutex_5, mutex_6]

    return parser.parse_args(), mutexes


def test_all_txt_files(folder_path, parser_func, reconstruct_func, config={}):
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
                    reconstruction_bool, consistency_bool = test_file(file_path, parser_func, reconstruct_func, config)
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

    if test_text_reconstruction(content, reconstructed_text):
        with open(file_path, 'w', encoding='utf-8-sig') as file:
            file.write(reconstructed_text)
    else:
        print(f"ERROR {file_path} couldn't be reconstructed")


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
    import os
    from victoria_script_parses import parser
    from victoria_script_reconstructor import reconstruct

    args, mutexes = parse_args()
    configs_yaml = load_yaml_config(args.config)
    config, exclusion_list = configs_yaml["config"], configs_yaml["exclusion_list"]
    args_dict = vars(args)

    # Override config values with command-line arguments if provided
    for key, value in args_dict.items():
        if value is not None or config.get(key) is None:
            config[key] = value
    for mutex in mutexes:
        if not mutex.check(config):
            raise Exception(
                f"The provided general config is not valid conflicting mutexes are: {mutex.keys} with values {[config[key] for key in mutex.keys]}\n(only one should be true, or ints should be in ascending order)")

    if args.format_folder:
        target = os.path.expanduser(os.path.normpath(args.format_folder))
    elif args.format_files:
        target = [os.path.expanduser(os.path.normpath(path)) for path in args.format_files]
    else:
        raise ValueError("no target defined")

    process_all_txt_files(target, parser, reconstruct, exclusion_list, config)

