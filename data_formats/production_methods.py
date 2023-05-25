from data_formats import DataFormat
from parse_encoder import parse_text_file
import os


class ProductionMethods(DataFormat):
    def __init__(self, dictionary: dict, technologies_folder: "TechnologiesFolder" = None):
        super().__init__(dictionary)
        self.technologies_folder = technologies_folder
        self.interpret()

    def interpret(self):
        self.data = DataFormat.copy_dict_with_string_keys(self._dictionary)
        if self.technologies_folder:
            for key, value in self.data.items():
                if value.get("unlocking_technologies"):
                    unlocking_technologies = value["unlocking_technologies"]
                    new_dictionary = {}
                    for technology in unlocking_technologies:
                        technology_object = list(
                            self.technologies_folder.get_iterable(technology, type_filter=dict))
                        new_dictionary[technology] = technology_object[0]
                    value["unlocking_technologies"] = new_dictionary


class ProductionMethodsFolder(DataFormat):

    def __init__(self, folder: str, technologies_folder: "TechnologiesFolder" = None,
                 folder_of: type = ProductionMethods):
        super().__init__()
        self.folder = folder
        self.folder_of = folder_of
        self.technologies_folder = technologies_folder
        self.interpret()

    def interpret(self):
        for dirpath, dirnames, filenames in os.walk(self.folder):
            for filename in filenames:
                if filename.endswith('.txt'):
                    file_path = os.path.join(dirpath, filename)
                    dictionary = parse_text_file(file_path)
                    building_file = ProductionMethods(dictionary, self.technologies_folder)
                    self.data[filename] = building_file

    def get_iterable(self, key1="root", key2="root", return_path=False, special_data=None, type_filter=None):
        if not special_data:
            special_data = self.folder_of
        yield from super().get_iterable(key1, key2, return_path, special_data, type_filter)


if __name__ == '__main__':
    from constants import Constants
    from data_formats import TechnologiesFolder

    technologies_folder = TechnologiesFolder(
        Constants.DEFAULT_GAME_PATH + os.path.normpath("/common/technology/technologies"))
    production_method_folder = ProductionMethodsFolder(
        Constants.DEFAULT_GAME_PATH + os.path.normpath("/common/production_methods"), technologies_folder)

    print(list(production_method_folder.get_iterable("era", return_path=True)))
