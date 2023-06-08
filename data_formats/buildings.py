import os
from data_formats import DataFormat


class Buildings(DataFormat):
    prefixes = ["building_"]
    relative_file_location = os.path.normpath("common/buildings")
    data_links = {"BuildingGroups": "building_group",
                  "ProductionMethodGroups": "production_method_groups"}

    def __init__(self, game_folder: str, mod_folder: str, prefixes: list = None, link_data: list = None):
        if not prefixes:
            prefixes = Buildings.prefixes
        else:
            prefixes += Buildings.prefixes

        game_version = os.path.join(game_folder, Buildings.relative_file_location)
        mod_version = os.path.join(mod_folder, Buildings.relative_file_location)
        super().__init__(game_version, mod_version, prefixes=prefixes)
        self.interpret()

        if link_data:
            for external_data in link_data:
                self.link(Buildings.data_links[type(external_data).__name__], external_data)

    # def interpret(self):
    #     super().interpret()
    #     for name, building in self.data.items():
    #         if self._building_groups:
    #             building["group"] = {name: self._building_groups[building["group"]]}
    #         if self._production_method_groups:
    #             for production_method_group in building["production_method_groups"]:
    #                 building["production_method_groups"][production_method_group] = self._production_method_groups[
    #                     production_method_group]


if __name__ == '__main__':
    import os
    from constants import Test
    from data_formats import BuildingGroups, ProductionMethodGroups

    building_groups = BuildingGroups(Test.game_directory, Test.mod_directory)
    production_method_groups = ProductionMethodGroups(Test.game_directory, Test.mod_directory, )
    buildings = Buildings(Test.game_directory, Test.mod_directory,
                          link_data=[building_groups, production_method_groups])

    print("\n GAME FILES \n")
    for name, element in buildings.items():
        if Test.game_directory in element["_source"]:
            print(name, element)

    print("\n MOD FILES \n")
    for name, element in buildings.items():
        if Test.mod_directory in element["_source"]:
            print(name, element)
