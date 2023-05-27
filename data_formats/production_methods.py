import os
import operator
from collections import defaultdict

from data_formats import DataFormat, DataFormatFolder
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

        print(len(self.input_goods), len(self.output_goods), len(self.workforce))
        # for _, item in self.input_goods.items():
        #     for key, value in item.items():
        #         for key2, value2 in value.items():
        #             print(key2, value2)

    def interpret(self):
        def handle_modifier(modifier_object, split_name_index):
            for name, number in modifier_object.items():
                split_name = name.split("_")
                is_additive = split_name[-1] == "add"
                is_multiplicative = split_name[-1] == "mult"
                operation = operator.add if is_additive else operator.mul if is_multiplicative else None
                element_name = "_".join(split_name[1:-1])

                if split_name[split_name_index] == "input":
                    self.input_goods[element_name][operation.__name__] += float(number)
                elif split_name[split_name_index] == "output":
                    self.output_goods[element_name][operation.__name__] += float(number)
                elif split_name[split_name_index] == "employment":
                    self.workforce[element_name][operation.__name__] += float(number)

        if not self._raw_data.get("modifiers"):
            return

        for modifier_name, modifier_object in self._raw_data["modifiers"].items():
            if modifier_name in ("workforce_scaled", "level_scaled", "unscaled"):
                handle_modifier(modifier_object, 0)

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

    def __init__(self, dictionary: dict, technologies_folder: "TechnologiesFolder" = None):
        super().__init__(dictionary, ProductionMethods.prefixes)
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
