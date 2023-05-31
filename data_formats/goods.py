from data_formats import DataFormat, DataFormatFolder
import os
from typing import Union


class Goods(DataFormat):

    def __init__(self, data: Union[dict, str]):
        super().__init__(data)
        self.interpret()
        self._transforms = {}


class GoodsFolder(DataFormatFolder):
    relative_file_location = os.path.normpath("common/goods")

    def __init__(self, data: str, folder_of: type = Goods):
        super().__init__(data, folder_of)
        self.interpret()
        self.construct_refs()


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
