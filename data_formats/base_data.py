import copy
import os
from parse_encoder import parse_text_file
from typing import Union


class DataFormat:
    relative_file_location = ""
    prefixes = []

    def __init__(self, game_folder: str, mod_folder: str, prefixes: list = None):
        self.data = {}
        self._prefix_manager = PrefixManager(prefixes)

        self.game_folder = game_folder
        self.mod_folder = mod_folder

        self._game_dictionary = {}
        self._mod_dictionary = {}
        self.data_refs = {}

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

    @staticmethod
    def add_file_location(dictionary, file_path):
        for key, value in dictionary.items():
            value["_source"] = file_path

    def interpret(self):
        mod_folder_walk = list(os.walk(self.mod_folder))
        overwritten_files = {os.path.basename(dirpath): filenames for (dirpath, _, filenames) in mod_folder_walk}
        for dirpath, _, filenames in os.walk(self.game_folder):
            for filename in filenames:
                if filename.endswith('.txt'):
                    file_path = os.path.join(dirpath, filename)
                    dictionary = parse_text_file(file_path)
                    self._game_dictionary[file_path] = dictionary
                    # If not being overwritten by file name then add entries to general data
                    if filename not in overwritten_files.get(os.path.basename(dirpath), []):
                        dictionary = DataFormat.copy_dict_with_string_keys(dictionary)
                        self.add_file_location(dictionary, file_path)
                        self.data_refs.update(dictionary)

        for dirpath, _, filenames in mod_folder_walk:
            for filename in filenames:
                if filename.endswith('.txt'):
                    file_path = os.path.join(dirpath, filename)
                    dictionary = parse_text_file(file_path)
                    self._mod_dictionary[file_path] = dictionary

                    dictionary = DataFormat.copy_dict_with_string_keys(dictionary)
                    self.add_file_location(dictionary, file_path)
                    self.data_refs.update(dictionary)

        self.data = copy.deepcopy(self.data_refs)

    def update_nested_dict(self, dict1, dict2, prefix_manager: "PrefixManager" = None):
        for key, value in dict1.items():
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

    def get_iterable(self, key1="root", key2="root", return_path=False, type_filter=None):
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
                        if type(value) == type and issubclass(value, DataFormat):
                            yield from search_dict(value.data, new_path, seen)
                elif type(value) == type and issubclass(value, DataFormat):
                    yield from search_dict(value.data, new_path, seen)

        yield from search_dict({"root": self.data}, [], set())

    def link(self, key, external_data):
        for _, entry in self.items():
            if entry.get(key):
                linked_data = entry[key]
                if isinstance(linked_data, dict):
                    for name in linked_data.keys():
                        linked_data[name] = external_data[name]
                elif isinstance(linked_data, str):
                    entry[key] = {linked_data: external_data[linked_data]}

    def __getitem__(self, key):
        return self.data[self._prefix_manager.add_prefix(key)]

    def __setitem__(self, key, value):
        self.data[self._prefix_manager.add_prefix(key)] = value

    def __delitem__(self, key):
        del self.data[self._prefix_manager.add_prefix(key)]

    def __contains__(self, key):
        return self._prefix_manager.add_prefix(key) in self.data

    def keys(self):
        yield from self.data.keys()

    def values(self):
        yield from self.data.values()

    def items(self):
        yield from self.data.items()


class PrefixManager:
    def __init__(self, prefixes: list = None):
        self._prefixes = {prefix: "" for prefix in prefixes} if prefixes else {}
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
