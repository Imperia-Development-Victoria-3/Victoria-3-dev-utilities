from data_formats import DataFormat, DataFormatFolder
import os
from typing import Union


class PopNeeds(DataFormat):
    prefixes = ["popneed_"]

    def __init__(self, data: Union[dict, str]):
        super().__init__(data, PopNeeds.prefixes)
        self.interpret()
        self._transforms = {}


class PopNeedsFolder(DataFormatFolder):
    relative_file_location = os.path.normpath("common/pop_needs")

    def __init__(self, data: str, folder_of: type = PopNeeds):
        super().__init__(data, folder_of)
        self.interpret()
        self.construct_refs()


if __name__ == '__main__':
    from parse_encoder import parse_text_file
    from constants import Constants

    # Test the parsing function
    dictionary = parse_text_file(
        Constants.DEFAULT_GAME_PATH + os.path.normpath("\\common\\pop_needs\\00_pop_needs.txt"))
    pop_needs = PopNeeds(dictionary)
    print(list(pop_needs.get_iterable("default", return_path=True)))
