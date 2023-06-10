import copy
import os
from parse_encoder import parse_text_file
from deepdiff import DeepDiff, path, extract
from data_utils import set_nested_obj, exclude_int_keys_callback


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

    @staticmethod
    def remove_file_location(dictionary):
        for key, value in dictionary.items():
            del value["_source"]

    def interpret(self):
        mod_folder_walk = list(os.walk(self.mod_folder))
        overwritten_files = {os.path.basename(dirpath): filenames for (dirpath, _, filenames) in mod_folder_walk}
        for dirpath, _, filenames in os.walk(self.game_folder):
            for filename in filenames:
                if filename.endswith('.txt'):
                    file_path = os.path.normpath(os.path.join(dirpath, filename))
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
                    file_path = os.path.normpath(os.path.join(dirpath, filename))
                    dictionary = parse_text_file(file_path)
                    self._mod_dictionary[file_path] = dictionary

                    dictionary = DataFormat.copy_dict_with_string_keys(dictionary)
                    self.add_file_location(dictionary, file_path)
                    self.data_refs.update(dictionary)

        DataFormat.copy_dict_with_string_keys(self.data_refs)
        self.data = copy.deepcopy(self.data_refs)
        self.remove_file_location(self.data)

    # def update_complex_structure(self, data, data_ref, _dictionary, prefix_manager: "PrefixManager" = None):
    #     for key, value in data.items():
    #         if key in data_ref:
    #             file_path = data_ref[key]["_source"]
    #             if isinstance(value, dict) and file_path in _dictionary and key in _dictionary[file_path]:
    #                 _dictionary[file_path][key] = \
    #                     self.update_complex_structure(value, data_ref[key], _dictionary[file_path], prefix_manager)
    #             elif isinstance(value, list) and file_path in _dictionary and key in _dictionary[file_path]:
    #                 _dictionary[file_path][key] = [
    #                     self.update_complex_structure(d1, d2, _dictionary[file_path], prefix_manager) for
    #                     d1, d2 in zip(value, _dictionary[file_path][key])]
    #                 # If data's list is longer, append the remaining items.
    #                 if len(value) > len(_dictionary[file_path][key]):
    #                     _dictionary[file_path][key].extend(
    #                         value[len(_dictionary[file_path][key]):])
    #             else:
    #                 if file_path in _dictionary:
    #                     # Check if value in data is a pointer (represented as True), if so, use the corresponding value from data_ref.
    #                     if value is True:
    #                         _dictionary[file_path][key] = data_ref[key]
    #                     else:
    #                         _dictionary[file_path][key] = value
    #         else:
    #             # Handle cases where there is no file reference in data_ref for this key.
    #             pass
    #     return _dictionary

    def update_if_needed(self):
        formatted_game_data = {}
        formatted_mod_data = {}
        for key, value in self.data.items():
            path_string = self.data_refs[key]["_source"]
            if self.game_folder in path_string:
                if not formatted_game_data.get(path_string):
                    formatted_game_data[path_string] = {}
                formatted_game_data[path_string][key] = value

            if self.mod_folder in path_string:
                if not formatted_mod_data.get(path_string):
                    formatted_mod_data[path_string] = {}
                formatted_mod_data[path_string][key] = value

        # mod_diff = DeepDiff(self._mod_dictionary, formatted_mod_data, exclude_obj_callback=exclude_int_keys_callback)
        game_diff = DeepDiff(self._game_dictionary, formatted_game_data, exclude_obj_callback=exclude_int_keys_callback)
        filenames = set()
        # print(game_diff)
        for type_name, differences in game_diff.items():
            if type_name == "dictionary_item_added" or type_name == "dictionary_item_removed":
                for index, dict_path in list(enumerate(differences)):
                    new_path = dict_path.replace(self.game_folder, self.mod_folder)
                    print(extract(self._game_dictionary, dict_path))
                    elements = path._path_to_elements(dict_path, root_element=None)
                    filenames.add(os.path.normpath(elements[0][0]))
                    differences.remove(dict_path)
                    differences.add(new_path)
            else:
                for dict_path, change in list(differences.items()):
                    new_path = dict_path.replace(self.game_folder, self.mod_folder)
                    print(dict_path)
                    elements = path._path_to_elements(dict_path, root_element=None)
                    print(elements[0][0])
                    filenames.add(os.path.normpath(elements[0][0]))
                    del differences[dict_path]
                    differences[new_path] = change
        # print(filenames)
        for filename in filenames:
            print(list(self._game_dictionary.keys()), filename)
            self._mod_dictionary[filename] = self._game_dictionary[filename]
            del self._game_dictionary[filename]

        values_changes = game_diff.get("values_changed")
        for path_string, change in values_changes:
            set_nested_obj(self._mod_dictionary, path_string, change["new_value"])

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

    # def link(self, external_data, max_depth=3):
    #     def replace_dict(d, depth_level):
    #         if depth_level >= max_depth:
    #             return
    #         for key, value in d.items():
    #             if isinstance(value, dict):
    #                 replace_dict(value, depth_level + 1)
    #             elif isinstance(value, list):
    #                 for item in value:
    #                     if isinstance(item, dict):
    #                         replace_dict(item, depth_level + 1)
    #             elif isinstance(value, str) and external_data.get(value):
    #                 d[key] = {value: external_data[value]}
    #
    #             if key in external_data:
    #                 d[key] = external_data[key]
    #
    #     replace_dict(self.data, 0)

    def replace_at_path(self, path, external_data, data=None, depth=-1):
        if data is None:
            data = self.data

        # If we've reached the maximum depth, replace the value
        if depth == len(path):
            if isinstance(data, str) and data in external_data:
                return {data: external_data[data]}
            elif isinstance(data, dict):
                for key, _ in data.items():
                    if key in external_data:
                        data[key] = external_data[key]
                return data
            else:
                return {}

        # If the current data is a dictionary, look for the key
        if isinstance(data, dict):
            if depth == -1:  # Explore every key on the top level
                for key in data:
                    self.replace_at_path(path, external_data, data.get(key), depth + 1)
            else:  # Follow the path key directly
                key = path[depth]
                if key in data:
                    data[key] = self.replace_at_path(path, external_data, data.get(key), depth + 1)

        # If the current data is a list, process each element
        elif isinstance(data, list):
            for i in range(len(data)):
                data[i] = self.replace_at_path(path, external_data, data[i], depth)

        return data

    def __getitem__(self, key):
        return self.data[self._prefix_manager.add_prefix(key)]

    def __setitem__(self, key, value):
        self.data[self._prefix_manager.add_prefix(key)] = value

    def __delitem__(self, key):
        del self.data[self._prefix_manager.add_prefix(key)]

    def __contains__(self, key):
        return self._prefix_manager.add_prefix(key) in self.data

    def get(self, key):
        return self.data.get(self._prefix_manager.add_prefix(key))

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
