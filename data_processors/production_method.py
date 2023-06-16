import operator
from collections import defaultdict
from dash import dcc, html
from app import cache


class ProductionMethod:
    def __init__(self, name: str, raw_data: dict):
        self._raw_data = raw_data
        self.name = name
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
            price = float(cache.get("Goods")[name]["cost"]) if cache.get("Goods") else 1
            profit -= price * operations[operator.add.__name__] * (1 + operations[operator.mul.__name__])
        for name, operations in self.output_goods.items():
            price = float(cache.get("Goods")[name]["cost"]) if cache.get("Goods") else 1
            profit += price * operations[operator.add.__name__] * (1 + operations[operator.mul.__name__])
        return profit

    def calc_total_employees(self):
        employees = 0
        for name, operations in self.workforce.items():
            employees += operations[operator.add.__name__] * (1 + operations[operator.mul.__name__])
        return employees

    def generate_info_box(self, building_name, group_name):
        def create_inputs(key, value, category):
            inputs = [html.Span(f'{key}: '),
                      dcc.Input(id={'type': f'{category}-{key}-add', 'hook': 'info',
                                    'index': building_name + '-' + group_name + '-' + self.name + '-add'},
                                value=value.get('add', 0),
                                type='text')]
            if 'mul' in value:
                inputs.append(
                    dcc.Input(id={'type': f'{category}-{key}-mul', 'hook': 'info',
                                  'index': building_name + '-' + group_name + '-' + self.name + '-mul'},
                              value=value.get('mul', 0),
                              type='text'))
            return inputs

        return html.Div([
            html.P('Inputs:'),
            html.Ul([html.Li(create_inputs(key, value, 'input')) for key, value in self.input_goods.items()]),
            html.P('Outputs:'),
            html.Ul([html.Li(create_inputs(key, value, 'output')) for key, value in self.output_goods.items()]),
            html.P('Employees:'),
            html.Ul([html.Li(create_inputs(key, value, 'employee')) for key, value in self.workforce.items()]),
        ])
