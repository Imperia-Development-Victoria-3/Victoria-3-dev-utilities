from data_formats import DataFormat, DataFormatFolder
from parse_encoder import parse_text_file
import os


class ProductionMethods(DataFormat):
    def __init__(self, dictionary: dict, technologies_folder: "TechnologiesFolder" = None):
        super().__init__(dictionary)
        self._technologies_folder = technologies_folder
        self.interpret()

    def interpret(self):
        super().interpret()
        if self._technologies_folder:
            for key, value in self.data.items():
                if value.get("unlocking_technologies"):
                    unlocking_technologies = value["unlocking_technologies"]
                    for technology in unlocking_technologies:
                        unlocking_technologies[technology] = self._technologies_folder[technology]


class ProductionMethodsFolder(DataFormatFolder):

    def __init__(self, folder: str, technologies_folder: "TechnologiesFolder" = None,
                 folder_of: type = ProductionMethods):
        super().__init__(folder, folder_of)
        self.technologies_folder = technologies_folder
        self.interpret()
        self.construct_refs()

    def interpret(self):
        for dirpath, dirnames, filenames in os.walk(self.folder):
            for filename in filenames:
                if filename.endswith('.txt'):
                    file_path = os.path.join(dirpath, filename)
                    dictionary = parse_text_file(file_path)
                    building_file = ProductionMethods(dictionary, self.technologies_folder)
                    self.data[filename] = building_file


if __name__ == '__main__':
    from constants import Constants
    from data_formats import TechnologiesFolder

    technologies_folder = TechnologiesFolder(
        Constants.DEFAULT_GAME_PATH + os.path.normpath("/common/technology/technologies"))
    production_method_folder = ProductionMethodsFolder(
        Constants.DEFAULT_GAME_PATH + os.path.normpath("/common/production_methods"), technologies_folder)

    print(list(production_method_folder.get_iterable("era", return_path=True)))
