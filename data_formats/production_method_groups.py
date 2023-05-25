from data_formats import DataFormat
from parse_encoder import parse_text_file
import os


class ProductionMethodGroups(DataFormat):
    def __init__(self, dictionary: dict, production_methods_folder: "ProductionMethodsFolder" = None):
        super().__init__(dictionary)
        self.production_methods_folder = production_methods_folder
        self.interpret()

    def interpret(self):
        self.data = DataFormat.copy_dict_with_string_keys(self._dictionary)
        # Link production methods directly
        if self.production_methods_folder:
            for key, value in self.data.items():
                if value.get("production_methods"):
                    production_methods = value["production_methods"]
                    for production_method in production_methods:
                        production_method_object = list(
                            self.production_methods_folder.get_iterable(production_method, type_filter=dict))
                        production_methods[production_method] = production_method_object[0]

class ProductionMethodGroupsFolder(DataFormat):

    def __init__(self, folder: str, production_methods_folder: "ProductionMethodsFolder" = None,
                 folder_of: type = ProductionMethodGroups):
        super().__init__()
        self.folder = folder
        self.folder_of = folder_of
        self.production_methods_folder = production_methods_folder
        self.interpret()

    def interpret(self):
        for dirpath, dirnames, filenames in os.walk(self.folder):
            for filename in filenames:
                if filename.endswith('.txt'):
                    file_path = os.path.join(dirpath, filename)
                    dictionary = parse_text_file(file_path)
                    building_file = ProductionMethodGroups(dictionary, self.production_methods_folder)
                    self.data[filename] = building_file

    def get_iterable(self, key1="root", key2="root", return_path=False, special_data=None, type_filter=None):
        if not special_data:
            special_data = self.folder_of
        yield from super().get_iterable(key1, key2, return_path, special_data, type_filter)


if __name__ == '__main__':
    from constants import Constants
    from data_formats import ProductionMethodsFolder

    production_methods_folder = ProductionMethodsFolder(
        Constants.DEFAULT_GAME_PATH + os.path.normpath("/common/production_methods"))
    production_method_groups_folder = ProductionMethodGroupsFolder(
        Constants.DEFAULT_GAME_PATH + os.path.normpath("/common/production_method_groups"), production_methods_folder)

    print(list(production_method_groups_folder.get_iterable("production_methods", '01_industry.txt', return_path=True)))
