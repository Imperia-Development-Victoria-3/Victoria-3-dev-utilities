import os
from constants import Constants
from parse_encoder import parse_text_file
from data_formats import DataFormat, DataFormatFolder, production_methods


class Buildings(DataFormat):
    prefixes = ["building_"]

    def __init__(self, dictionary: dict, building_groups: "BuildingGroups" = None,
                 production_method_groups: "ProductionMethodGroupsFolder" = None):
        super().__init__(dictionary, Buildings.prefixes)
        self._building_groups = building_groups
        self._production_method_groups = production_method_groups
        self.interpret()

    def interpret(self):
        super().interpret()
        for name, building in self.data.items():
            if self._building_groups:
                building["group"] = {name: self._building_groups[building["group"]]}
            if self._production_method_groups:
                for production_method_group in building["production_method_groups"]:
                    building["production_method_groups"][production_method_group] = self._production_method_groups[
                        production_method_group]


class BuildingsFolder(DataFormatFolder):

    def __init__(self, folder: str, building_groups: "BuildingGroups" = None,
                 production_method_groups: "ProductionMethodGroupsFolder" = None, folder_of: type = Buildings):
        super().__init__(folder, folder_of)
        self._building_groups = building_groups
        self._production_method_groups = production_method_groups
        self.interpret()
        self.construct_refs()

    def interpret(self):
        for dirpath, dirnames, filenames in os.walk(self.folder):
            for filename in filenames:
                if filename.endswith('.txt'):
                    file_path = os.path.join(dirpath, filename)
                    dictionary = parse_text_file(file_path)
                    building_file = Buildings(dictionary, self._building_groups, self._production_method_groups)
                    self.data[filename] = building_file


if __name__ == '__main__':
    from data_formats import BuildingGroups, ProductionMethodGroupsFolder

    dictionary = parse_text_file(
        Constants.DEFAULT_GAME_PATH + os.path.normpath("/common/building_groups/00_building_groups.txt"))
    buildings_groups = BuildingGroups(dictionary)
    buildings_folder = BuildingsFolder(Constants.DEFAULT_GAME_PATH + os.path.normpath("/common/buildings"),
                                       buildings_groups)

    print(list(buildings_folder.get_iterable("unlocking_technologies", '01_industry.txt', return_path=True)))
