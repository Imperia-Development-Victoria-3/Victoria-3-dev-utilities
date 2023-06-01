import os
from parse_encoder import parse_text_file
from typing import Union


class DataFormat:
    relative_file_location = ""

    def __init__(self, data: Union[dict, str] = None, prefixes: list = None):
        if isinstance(data, dict):
            self._dictionary = data
        elif isinstance(data, str):
            self._dictionary = parse_text_file(data)  # replace with your function to load data from a file
        elif isinstance(data, type(None)):
            self._dictionary = {}
        else:
            raise TypeError('data must be a dictionary or a string')

        self.data = {}
        self._prefix_manager = None
        if prefixes:
            self._prefix_manager = PrefixManager(prefixes)

    @staticmethod
    def copy_dict_with_string_keys(item, prefix_manager: "PrefixManager" = None):
        if isinstance(item, dict):
            return {
                (prefix_manager.remove_prefix(k) if prefix_manager else k):
                    DataFormat.copy_dict_with_string_keys(v, prefix_manager)
                for k, v in item.items() if isinstance(k, str)
            }
        elif isinstance(item, list):
            return [DataFormat.copy_dict_with_string_keys(i, prefix_manager) for i in item]
        else:
            return item

    def update_nested_dict(self, dict1, dict2, prefix_manager: "PrefixManager" = None):
        for key, value in dict1.items():
            # print(key)
            key_2 = prefix_manager.add_prefix(key)
            if key_2 in dict2:
                if isinstance(value, dict) and isinstance(dict2[key_2], dict):
                    dict2[key_2] = self.update_nested_dict(value, dict2[key_2], prefix_manager)
                elif isinstance(value, list) and isinstance(dict2[key_2], list):
                    dict2[key_2] = [self.update_nested_dict(d1, d2, prefix_manager) for d1, d2 in
                                    zip(value, dict2[key_2])]
                    # If dict1's list is longer, append the remaining items.
                    if len(value) > len(dict2[key_2]):
                        dict2[key_2].extend(value[len(dict2[key_2]):])
                else:
                    dict2[key_2] = value
            else:
                dict2[key_2] = value
        return dict2

    def get_iterable(self, key1="root", key2="root", return_path=False, special_data=None, type_filter=None):
        def search_dict(d, path, seen):
            if id(d) in seen:
                return
            seen.add(id(d))
            for key, value in d.items():
                new_path = path + [key]
                if key == key1 and key2 in new_path:
                    if return_path:
                        if type_filter is None or isinstance(value, type_filter):
                            yield value, path[1:]
                    else:
                        if type_filter is None or isinstance(value, type_filter):
                            yield value
                if isinstance(value, dict):
                    yield from search_dict(value, new_path, seen)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            yield from search_dict(item, new_path, seen)
                        if special_data and isinstance(value, special_data):
                            yield from search_dict(value.data, new_path, seen)
                elif special_data and isinstance(value, special_data):
                    yield from search_dict(value.data, new_path, seen)

        yield from search_dict({"root": self.data}, [], set())

    def interpret(self):
        self.data = DataFormat.copy_dict_with_string_keys(self._dictionary, self._prefix_manager)

    def __getitem__(self, key):
        return self.data[key]


class DataFormatFolder(DataFormat):

    def __init__(self, folder: str, folder_of: type = DataFormat):
        super().__init__()
        self.folder = folder
        self.folder_of = folder_of
        self.flattened_refs = {}

    def interpret(self):
        for dirpath, dirnames, filenames in os.walk(self.folder):
            for filename in filenames:
                if filename.endswith('.txt'):
                    file_path = os.path.join(dirpath, filename)
                    dictionary = parse_text_file(file_path)
                    technology_file = self.folder_of(dictionary)
                    self.data[filename] = technology_file

    def construct_refs(self):
        for file in self.data.values():
            for real_key, value in file.data.items():
                self.flattened_refs[real_key] = value

    def get_iterable(self, key1="root", key2="root", return_path=False, special_data=None, type_filter=None):
        if not special_data:
            special_data = self.folder_of
        yield from super().get_iterable(key1, key2, return_path, special_data, type_filter)

    def __getitem__(self, key):
        return self.flattened_refs[key]


class PrefixManager:
    def __init__(self, prefixes):
        self._prefixes = {prefix: "" for prefix in prefixes}
        self._memory = {}

    def remove_prefix(self, key):
        new_key = key
        for prefix in self._prefixes:
            if key.startswith(prefix):
                new_key = key[len(prefix):]
                self._memory[new_key] = key
        return new_key

    def remove_prefixes(self, data):
        for prefix in self._prefixes:
            keys_to_modify = [k for k in data if k.startswith(prefix)]
            for key in keys_to_modify:
                new_key = key[len(prefix):]
                self._memory[new_key] = key
                data[new_key] = data.pop(key)

    def add_prefixes(self, data):
        keys_to_modify = [k for k in data if k in self._memory]
        for key in keys_to_modify:
            original_key = self._memory[key]
            data[original_key] = data.pop(key)

    def add_prefix(self, key):
        if self._memory.get(key):
            return self._memory[key]
        else:
            return key
