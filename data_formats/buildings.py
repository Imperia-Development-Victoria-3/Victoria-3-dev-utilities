import os
from constants import Constants
from parse_encoder import parse_text_file
from data_formats import DataFormat


class Buildings(DataFormat):
    def __init__(self, dictionary: dict, building_groups: "BuildingGroups" = None,
                 production_method_groups: "ProductionMethodGroupsFolder" = None):
        super().__init__(dictionary)
        self._building_groups = building_groups
        self._production_method_groups = production_method_groups
        self.interpret()

    def interpret(self):
        self.data = DataFormat.copy_dict_with_string_keys(self._dictionary)
        for name, building in self.data.items():
            if self._building_groups:
                building["building_group"] = {name: self._building_groups[building["building_group"]]}
            if self._production_method_groups:
                for production_method_group in building["production_method_groups"]:
                    building[production_method_group] = \
                    list(self._production_method_groups.get_iterable(production_method_group, type_filter=dict))[0]


class BuildingsFolder(DataFormat):

    def __init__(self, folder: str, building_groups: "BuildingGroups" = None,
                 production_method_groups: "ProductionMethodGroupsFolder" = None, folder_of: type = Buildings):
        super().__init__()
        self.folder = folder
        self.folder_of = folder_of
        self._building_groups = building_groups
        self._production_method_groups = production_method_groups
        self.interpret()

    def interpret(self):
        for dirpath, dirnames, filenames in os.walk(self.folder):
            for filename in filenames:
                if filename.endswith('.txt'):
                    file_path = os.path.join(dirpath, filename)
                    dictionary = parse_text_file(file_path)
                    building_file = Buildings(dictionary, self._building_groups, self._production_method_groups)
                    self.data[filename] = building_file

    def get_iterable(self, key1="root", key2="root", return_path=False, special_data=None, type_filter=None):
        if not special_data:
            special_data = self.folder_of
        yield from super().get_iterable(key1, key2, return_path, special_data, type_filter)


if __name__ == '__main__':
    from data_formats import BuildingGroups, ProductionMethodGroupsFolder

    dictionary = parse_text_file("../00_building_groups.txt")
    buildings_groups = BuildingGroups(dictionary)
    buildings_folder = BuildingsFolder(Constants.DEFAULT_GAME_PATH + os.path.normpath("/common/buildings"),
                                       buildings_groups)

    print(list(buildings_folder.get_iterable("unlocking_technologies", '01_industry.txt', return_path=True)))
