import warnings
from pathlib import Path
import yaml
from args import parse_args, MUTEXES

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


def load_yaml_config(file_path):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config


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

    args = parse_args()
    configs_yaml = load_yaml_config(args.config)
    config, exclusion_list, word_config, path_config = configs_yaml["config"], configs_yaml["exclusion_list"], configs_yaml["special_words"], configs_yaml["special_folders"]
    args_dict = vars(args)

    config["special_words"] = word_config
    config["special_folders"] = path_config

    # Override config values with command-line arguments if provided
    for key, value in args_dict.items():
        if value is not None or config.get(key) is None:
            config[key] = value

    for mutex in MUTEXES:
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
