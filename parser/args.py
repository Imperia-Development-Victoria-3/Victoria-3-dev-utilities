import argparse
import os


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
            raise ValueError("Tried to set non-existent key")
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


def get_mutexes():
    mutex_1 = Mutex(["default_no_double_line", "default_yes_double_line"], True, bool)
    mutex_3 = Mutex(["object_yes_double_line"], True, bool)
    mutex_4 = Mutex(["default_yes_double_line", "force_multi_line_from_item_count"], True, bool)
    mutex_5 = Mutex(["force_single_line_until_item_count", "force_multi_line_from_item_count"], True, int)
    mutex_6 = Mutex(["format_folder", "format_files"], False, str)
    mutexes = [mutex_1, mutex_3, mutex_4, mutex_5, mutex_6]

    mutex_lookup = {}
    for mutex in mutexes:
        for argument in mutex.keys:
            mutex_lookup[argument] = mutex

    return mutexes, mutex_lookup


MUTEXES, MUTEX_LOOKUP = get_mutexes()


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

    return parser.parse_args()
