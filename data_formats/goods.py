import copy


class Goods:

    def __init__(self, dictionary):
        self._dictionary = dictionary
        self._interpret_goods(dictionary)
        self._transforms = {}

    def _interpret_goods(self, dictionary):
        self.goods = copy.deepcopy(self._dictionary)

        self.keys = {"root"}
        for name, goods_group in self.goods.items():
            if isinstance(name, str):
                self.keys |= {name}
                self.keys |= {key for key in goods_group.keys() if type(key) == str}

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

        yield from search_dict({"root": self.goods}, [])

    def __getitem__(self, key):
        return self.goods[key]

if __name__ == '__main__':
    from parse_decoder import decode_dictionary
    from parse_encoder import parse_text_file

    # Test the parsing function
    dictionary = parse_text_file("../00_goods.txt")
    goods = Goods(dictionary)
    print(list(goods.get_iterable("category", return_path=True)))
    # print(dictionary)
    # print(decode_dictionary(dictionary))
