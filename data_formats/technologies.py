from data_formats import DataFormat
import os


class Technologies(DataFormat):
    relative_file_location = os.path.normpath("common/technology/technologies")
    data_links = {"Eras": ["era"]}

    def __init__(self, game_folder: str, mod_folder: str, prefixes: list = None, link_data: list = None):
        if not prefixes:
            prefixes = Technologies.prefixes
        else:
            prefixes += Technologies.prefixes

        game_version = os.path.join(game_folder, Technologies.relative_file_location)
        mod_version = os.path.join(mod_folder, Technologies.relative_file_location)
        super().__init__(game_version, mod_version, prefixes=prefixes)
        self.interpret()

        if link_data:
            for external_data in link_data:
                self.replace_at_path(Technologies.data_links[type(external_data).__name__], external_data)

    def interpret(self):
        super().interpret()

        # Replace name-only to object references
        for name, technology in self.data.items():
            if technology.get("unlocking_technologies"):
                new_unlocking_technologies = {}
                for requirement in technology["unlocking_technologies"].keys():
                    new_unlocking_technologies[requirement] = self.data[requirement]
                technology["unlocking_technologies"] = new_unlocking_technologies

    def calc_category_cost(self):
        # Extracting all unique categories
        unique_categories = set([d["category"] for d in self.data.values()])
        # Calculating total tech cost for each category
        category_costs = {}
        for category in unique_categories:
            category_entries = [d for d in self.data.values() if d.get("category") == category]
            total_cost = sum([float(entry["era"]["technology_cost"]) for entry in category_entries if "era" in entry])
            category_costs[category] = total_cost

        return category_costs


def calculate_multipliers(category_costs, specified_value=None):
    # Calculate the lowest, average, and highest costs
    lowest_cost = min(category_costs.values())
    average_cost = sum(category_costs.values()) / len(category_costs)
    highest_cost = max(category_costs.values())

    # Calculate the multipliers
    multipliers = {
        "to_lowest": {},
        "to_average": {},
        "to_highest": {},
        "to_specified": {}
    }

    for category, cost in category_costs.items():
        multipliers["to_lowest"][category] = lowest_cost / cost if cost != 0 else 0
        multipliers["to_average"][category] = average_cost / cost if cost != 0 else 0
        multipliers["to_highest"][category] = highest_cost / cost if cost != 0 else 0
        if specified_value is not None:
            multipliers["to_specified"][category] = specified_value / cost if cost != 0 else 0

    # Remove 'to_specified' key if no specified value is provided
    if specified_value is None:
        del multipliers["to_specified"]

    return multipliers


if __name__ == '__main__':
    import os
    from constants import Test
    from data_formats import Eras
    import pprint

    pp = pprint.PrettyPrinter(indent=4)

    eras = Eras(Test.game_directory, Test.mod_directory)
    technologies = Technologies(Test.game_directory, Test.mod_directory, link_data=[eras])
    costs = technologies.calc_category_cost()

    print(costs)
    pp.pprint(calculate_multipliers(costs, 730000))

    print("\n GAME FILES \n")
    for name, element in technologies.items():
        if Test.game_directory in technologies.data_refs[name]["_source"]:
            print(name, element)

    print("\n MOD FILES \n")
    for name, element in technologies.items():
        if Test.mod_directory in technologies.data_refs[name]["_source"]:
            print(name, element)
