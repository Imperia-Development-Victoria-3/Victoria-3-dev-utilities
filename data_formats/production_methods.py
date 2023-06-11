import os
import operator
from collections import defaultdict

from data_formats import DataFormat
from parse_encoder import parse_text_file
from dash import dcc, html, Input, Output, Patch, dash_table, State


class ProductionMethod:
    def __init__(self, name: str, dictionary: dict, goods: "Goods" = None):
        self._raw_data = dictionary
        self.name = name
        self.goods = goods
        self.input_goods = defaultdict(lambda: defaultdict(float))
        self.output_goods = defaultdict(lambda: defaultdict(float))
        self.workforce = defaultdict(lambda: defaultdict(float))
        self.shares = defaultdict(lambda: defaultdict(float))
        self.interpret()

    def interpret(self):
        def handle_modifier(modifier_object, split_name_index):
            for name, number in modifier_object.items():
                split_name = name.split("_")
                is_additive = split_name[-1] == "add"
                is_multiplicative = split_name[-1] == "mult"
                operation = operator.add if is_additive else operator.mul if is_multiplicative else None
                element_name = "_".join(split_name[2:-1])

                if split_name[split_name_index] == "input":
                    self.input_goods[element_name][operation.__name__] += float(number)
                elif split_name[split_name_index] == "output":
                    self.output_goods[element_name][operation.__name__] += float(number)
                elif split_name[split_name_index] == "employment":
                    self.workforce[element_name][operation.__name__] += float(number)
        if not self._raw_data.get("building_modifiers"):
            return

        for modifier_name, modifier_object in self._raw_data["building_modifiers"].items():
            if modifier_name in ("workforce_scaled", "level_scaled", "unscaled"):
                handle_modifier(modifier_object, 1)

    def calc_profit(self):
        profit = 0
        for name, operations in self.input_goods.items():
            price = self.goods[name]["cost"]
            profit -= price * operations[operator.add.__name__] * operations[operator.mul.__name__]
        for name, operations in self.output_goods.items():
            price = self.goods[name]["cost"]
            profit += price * operations[operator.add.__name__] * operations[operator.mul.__name__]
        return profit

    def get_total_employees(self):
        employees = 0
        for name, operations in self.workforce.items():
            employees += operations[operator.add.__name__] * operations[operator.mul.__name__]
        return employees

    def generate_info_box(self):
        def create_inputs(key, value, category):
            inputs = [html.Span(f'{key}: '),
                      dcc.Input(id={'type': f'{category}-value-add', 'index': f'{key}-add'}, value=value.get('add', 0),
                                type='text')]
            if 'mul' in value:
                inputs.append(
                    dcc.Input(id={'type': f'{category}-value-mul', 'index': f'{key}-mul'}, value=value.get('mul', 0),
                              type='text'))
            return inputs

        return html.Div([
            html.P('Inputs:'),
            html.Ul([html.Li(create_inputs(key, value, 'input')) for key, value in self.input_goods.items()]),
            html.P('Outputs:'),
            html.Ul([html.Li(create_inputs(key, value, 'output')) for key, value in self.output_goods.items()]),
            html.P('Employees:'),
            html.Ul([html.Li(create_inputs(key, value, 'employee')) for key, value in self.workforce.items()]),
            html.Button('Save Changes', id={'type': 'save', 'index': self.name}),
        ])


class ProductionMethods(DataFormat):
    prefixes = ["building_"]
    relative_file_location = os.path.normpath("common/production_methods")
    data_links = {"Technologies": ["unlocking_technologies"]}

    def __init__(self, game_folder: str, mod_folder: str, prefixes: list = None, link_data: list = None):
        if not prefixes:
            prefixes = ProductionMethods.prefixes
        else:
            prefixes += ProductionMethods.prefixes

        game_version = os.path.join(game_folder, ProductionMethods.relative_file_location)
        mod_version = os.path.join(mod_folder, ProductionMethods.relative_file_location)
        super().__init__(game_version, mod_version, prefixes=prefixes)
        self.interpret()

        if link_data:
            for external_data in link_data:
                self.replace_at_path(ProductionMethods.data_links[type(external_data).__name__], external_data)


if __name__ == '__main__':
    import os
    from constants import Test
    from data_formats import Technologies

    technologies = Technologies(Test.game_directory, Test.mod_directory)
    production_methods = ProductionMethods(Test.game_directory, Test.mod_directory, link_data=[technologies])

    print("\nGAME FILES\n")
    for name, element in production_methods.items():
        if Test.game_directory in  production_methods.data_refs[name]["_source"]:
            print(name, element)

    print("\nMOD FILES\n")
    for name, element in production_methods.items():
        if Test.mod_directory in production_methods.data_refs[name]["_source"]:
            print(name, element)

