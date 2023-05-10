import copy


class PopNeeds:

    def __init__(self, dictionary):
        self._dictionary = dictionary
        self._interpret_pop_needs(dictionary)
        self._transforms = {}

    def _interpret_pop_needs(self, dictionary):
        self.pop_needs = {}
        for name, need_group in list(dictionary.items()):
            if type(name) == str:
                # just getting rid of the popneed qualifier as it is uninformative
                self.pop_needs["_".join(name.split("_")[1:])] = copy.deepcopy(need_group)

        self.keys = {"root"}
        for name, need_group in self.pop_needs.items():
            if isinstance(name, str):
                self.keys |= {name}
                self.keys |= {key for key in need_group.keys() if isinstance(key, str)}
                if type(need_group["entry"]) == list:
                    for entry in need_group["entry"]:
                        self.keys |= {key for key in entry.keys() if isinstance(key, str)}
                else:
                    self.keys |= {key for key in need_group["entry"].keys() if isinstance(key, str)}

    def get_iterable(self, key1="root", key2="root", return_path=False):
        def search_dict(d, path):
            for key, value in d.items():
                new_path = path + [key]
                if key == key1 and key2 in new_path:
                    if return_path:
                        yield value, path[1:]
                    else:
                        yield value
                if isinstance(value, dict):
                    yield from search_dict(value, new_path)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            yield from search_dict(item, new_path)

        yield from search_dict({"root": self.pop_needs}, [])


if __name__ == '__main__':
    from parse_decoder import decode_dictionary
    from parse_encoder import parse_text_file

    # Test the parsing function
    dictionary = parse_text_file("../00_pop_needs.txt")
    pop_needs = PopNeeds(dictionary)
    print(list(pop_needs.get_iterable("default", return_path=True)))
    # print(dictionary)
    # print(decode_dictionary(dictionary))
