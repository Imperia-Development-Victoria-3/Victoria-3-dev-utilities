import copy
from data_formats import DataFormat
import os
from typing import Union


class BuildingGroups(DataFormat):
    relative_file_location = os.path.normpath("common/building_groups")

    default_values = {
        "parent_group": "None",
        "always_possible": "no",
        "economy_of_scale": "no",
        "is_subsistence": "no",
        "default_building": "None",
        "lens": "None",
        "auto_place_buildings": "no",
        "capped_by_resources": "no",
        "discoverable_resource": "no",
        "depletable_resource": "no",
        "can_use_slaves": "no",
        "land_usage": None,
        "cash_reserves_max": "0",
        "inheritable_construction": "no",
        "stateregion_max_level": "no",
        "urbanization": "0",
        "should_auto_expand": {"should_auto_expand": {
            "default_auto_expand_rule": "yes"
        }},
        "hiring_rate": 0,
        "proportionality_limit": 0,
        "hires_unemployed_only": "no",
        "infrastructure_usage_per_level": 0,
        "fired_pops_become_radical": "yes",
        "is_government_funded": "no",
        "subsidized": "no",
        "pays_taxes": "yes",
    }

    def __init__(self, game_folder: str, mod_folder: str, prefixes: list = None):
        if not prefixes:
            prefixes = BuildingGroups.prefixes
        else:
            prefixes += BuildingGroups.prefixes

        game_version = os.path.join(game_folder, BuildingGroups.relative_file_location)
        mod_version = os.path.join(mod_folder, BuildingGroups.relative_file_location)
        super().__init__(game_version, mod_version, prefixes=prefixes)
        self.interpret()

    def interpret(self):
        super().interpret()
        for name, building_group in self.data.items():
            self.overwrite_values(name, building_group, self.data)

    def overwrite_values(self, name, building_group, dictionary):
        if building_group.get("parent_group"):
            parent = building_group["parent_group"]
            if not dictionary[parent].get("_finished"):
                self.overwrite_values(parent, dictionary[parent], dictionary)

            new_building_group = copy.deepcopy(dictionary[parent])
            for key, value in building_group.items():
                new_building_group[key] = value
        else:
            new_building_group = copy.deepcopy(BuildingGroups.default_values)
            for key, value in building_group.items():
                new_building_group[key] = value

        new_building_group["_finished"] = True
        dictionary[name] = new_building_group


if __name__ == '__main__':
    import os
    from constants import Test

    building_groups = BuildingGroups(Test.game_directory, Test.mod_directory)

    print("\n GAME FILES \n")
    for name, element in building_groups.items():
        if Test.game_directory in building_groups.data_refs[name]["_source"]:
            print(name, element)

    print("\n MOD FILES \n")
    for name, element in building_groups.items():
        if Test.mod_directory in building_groups.data_refs[name]["_source"]:
            print(name, element)
