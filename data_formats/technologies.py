from data_formats import DataFormat
from parse_encoder import parse_text_file
import os


class Technologies(DataFormat):
    def __init__(self, dictionary: dict):
        super().__init__(dictionary)
        self.interpret()


class TechnologiesFolder(DataFormat):

    def __init__(self, folder: str, folder_of: type = Technologies):
        super().__init__()
        self.folder = folder
        self.folder_of = folder_of
        self.interpret()

    def interpret(self):
        for dirpath, dirnames, filenames in os.walk(self.folder):
            for filename in filenames:
                if filename.endswith('.txt'):
                    file_path = os.path.join(dirpath, filename)
                    dictionary = parse_text_file(file_path)
                    building_file = Technologies(dictionary)
                    self.data[filename] = building_file

    def get_iterable(self, key1="root", key2="root", return_path=False, special_data=None, type_filter=None):
        if not special_data:
            special_data = self.folder_of
        yield from super().get_iterable(key1, key2, return_path, special_data, type_filter)


if __name__ == '__main__':
    import os
    from constants import Constants

    technologies_folder = TechnologiesFolder(
        Constants.DEFAULT_GAME_PATH + os.path.normpath("/common/technology/technologies"))

    print(list(technologies_folder.get_iterable("era", return_path=True)))
