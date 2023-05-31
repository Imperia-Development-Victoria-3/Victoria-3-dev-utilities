from data_formats import DataFormat, DataFormatFolder
from parse_encoder import parse_text_file
import os
from typing import Union


class Technologies(DataFormat):
    def __init__(self, data: Union[dict, str]):
        super().__init__(data)
        self.interpret()


class TechnologiesFolder(DataFormatFolder):
    relative_file_location = os.path.normpath("common/technology/technologies")

    def __init__(self, data: str, folder_of: type = Technologies):
        super().__init__(data, folder_of)
        self.interpret()
        self.construct_refs()


if __name__ == '__main__':
    import os
    from constants import Constants

    technologies_folder = TechnologiesFolder(
        Constants.DEFAULT_GAME_PATH + os.path.normpath("/common/technology/technologies"))

    print(list(technologies_folder.get_iterable("era", return_path=True)))
