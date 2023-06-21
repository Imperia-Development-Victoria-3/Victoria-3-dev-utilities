from .production_method import ProductionMethod


class ProductionMethodGroup:

    def __init__(self, name, raw_data):
        self._raw_data = raw_data
        self.production_methods = {}
        self.selected = ""
        self.name = name
        self.interpret()

    def select(self, name):
        self.selected = name

    def is_commercial(self):
        return self._raw_data.get("ai_selection", "most_profitable") == "most_profitable"

    def apply_era(self, era_number):
        eras = []
        production_method_names = []
        for name, production_method in self._raw_data["production_methods"].items():
            min_era = 0
            technologies = production_method.get("unlocking_technologies", {})
            for technology in technologies.values():
                era = int(technology["era"].split('_')[-1])
                if min_era <= era:
                    min_era = era
            eras.append(min_era)
            production_method_names.append(name)

        values_below_threshold = [(i, val) for i, val in enumerate(eras) if val <= era_number]
        if not values_below_threshold:
            print(
                f"WARNING: you require technologies for a production group {self.name} which is above the building requirements (which is silly), pretending the requirement doesn't exit")
            values_below_threshold = [(i, val) for i, val in enumerate(eras)]

        max_tuple = max(values_below_threshold, key=lambda x: x[1])
        self.selected = production_method_names[max_tuple[0]]

    def interpret(self):
        for name, production_method_dict in list(self._raw_data["production_methods"].items()):
            if isinstance(production_method_dict, bool):
                print(f"WARNING: you failed to define {name} (which is silly), ignoring it for now")
                del self._raw_data["production_methods"][name]
                continue

            technologies = production_method_dict.get("unlocking_technologies", {})
            for tech_name, technology in list(technologies.items()):
                if isinstance(technology, bool):
                    print(f"WARNING: you failed to define {tech_name} (which is silly), ignoring it for now")
                    del self._raw_data["production_methods"][name]["unlocking_technologies"][tech_name]

            self.production_methods[name] = ProductionMethod(name, production_method_dict)
        self.selected = list(self._raw_data["production_methods"])[0]

    def calc_profit(self):
        return self.production_methods[self.selected].calc_profit()

    def calc_total_employees(self):
        return self.production_methods[self.selected].calc_total_employees()
