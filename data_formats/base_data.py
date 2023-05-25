class DataFormat:

    def __init__(self, dictionary: dict = {}):
        self._dictionary = dictionary
        self.data = {}

    @staticmethod
    def copy_dict_with_string_keys(item):
        if isinstance(item, dict):
            return {k: DataFormat.copy_dict_with_string_keys(v) for k, v in item.items() if isinstance(k, str)}
        elif isinstance(item, list):
            return [DataFormat.copy_dict_with_string_keys(v) for v in item]
        else:
            return item

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
                        if isinstance(value, special_data):
                            yield from search_dict(value.data, new_path, seen)
                elif special_data and isinstance(value, special_data):
                    yield from search_dict(value.data, new_path, seen)

        yield from search_dict({"root": self.data}, [], set())

    def interpret(self):
        self.data = DataFormat.copy_dict_with_string_keys(self._dictionary)

    def __getitem__(self, key):
        return self.data[key]
