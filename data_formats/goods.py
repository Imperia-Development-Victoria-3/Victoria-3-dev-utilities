from data_formats import DataFormat


class Goods(DataFormat):

    def __init__(self, dictionary):
        super().__init__(dictionary)
        self.interpret()
        self._transforms = {}


if __name__ == '__main__':
    from parse_decoder import decode_dictionary
    from parse_encoder import parse_text_file
    from constants import Constants
    import os

    # Test the parsing function
    dictionary = parse_text_file(Constants.DEFAULT_GAME_PATH + os.path.normpath("\\common\\goods\\00_goods.txt"))
    goods = Goods(dictionary)
    print(list(goods.get_iterable("category", return_path=True)))
    print(decode_dictionary(dictionary))
