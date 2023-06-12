from .production_method import ProductionMethod


class ProductionMethodGroup:

    def __init__(self, raw_data):
        self.raw_data = raw_data
        self.production_methods = {}
        self.selected = ""

        self.interpret()

    def select(self, name):
        self.selected = name

    def apply_era(self, era_number):
        eras = []
        building_names = []
        for name, production_method in self.raw_data["production_methods"].items():
            min_era = 0
            technologies = production_method.get("unlocking_technologies", {})
            for technology in technologies.values():
                era = int(technology["era"].split('_')[-1])
                if min_era < era:
                    min_era = era
            eras.append(min_era)
            building_names.append(name)

        values_below_threshold = [(i, val) for i, val in enumerate(eras) if val <= era_number]
        max_tuple = max(values_below_threshold, key=lambda x: x[1])
        self.selected = building_names[max_tuple[0]]
        print(self.selected)

    def interpret(self):
        for name, production_method_dict in self.raw_data["production_methods"].items():
            self.production_methods[name] = ProductionMethod(name, production_method_dict)
        self.selected = list(self.raw_data["production_methods"])[0]

    def calc_profit(self):
        return self.production_methods[self.selected].calc_profit()

    def calc_total_employees(self):
        return self.production_methods[self.selected].calc_total_employees()
