import copy
import json
from data_formats import DataFormat


class BuildingGroups(DataFormat):
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
        "hires_unemployed_only": "no"
    }

    def __init__(self, dictionary):
        super().__init__(dictionary)
        self.interpret()
        self.keys = list(BuildingGroups.default_values.keys())

    def overwrite_values(self, name, building_group, dictionary):
        if building_group.get("parent_group"):
            parent = building_group["parent_group"]
            if not dictionary[parent].get("finished"):
                self.overwrite_values(parent, dictionary[parent], dictionary)

            new_building_group = copy.deepcopy(dictionary[parent])
            for key, value in building_group.items():
                new_building_group[key] = value
        else:
            new_building_group = copy.deepcopy(BuildingGroups.default_values)
            for key, value in building_group.items():
                new_building_group[key] = value

        new_building_group["finished"] = True
        dictionary[name] = new_building_group

    def interpret(self):
        self.data = DataFormat.copy_dict_with_string_keys(self._dictionary)

        for name, building_group in self.data.items():
            self.overwrite_values(name, building_group, self.data)


if __name__ == '__main__':
    from parse_encoder import parse_text_file

    dictionary = parse_text_file("../00_building_groups.txt")
    goods = BuildingGroups(dictionary)
    print(list(goods.get_iterable()))
