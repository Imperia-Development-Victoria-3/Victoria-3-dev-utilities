import operator
from collections import defaultdict
from dash import dcc, html
from app import cache
import pandas as pd


class ProductionMethod:
    scopes = pd.DataFrame({
        'ID': [1, 2, 3, 4],
        'Name': ['building_modifiers', 'state_modifiers', 'country_modifiers', 'timed_modifiers']
    })
    scopes_to_id = scopes.set_index('Name')['ID'].to_dict()

    scales = pd.DataFrame({
        'ID': [1, 2, 3],
        'Name': ['level_scaled', 'workforce_scaled', 'unscaled'],
    })
    scales_to_id = scales.set_index('Name')['ID'].to_dict()

    classifications = pd.DataFrame({
        'ID': [1, 2, 3],
        'Name': ['economic', 'military', 'other']
    })
    classification_to_id = classifications.set_index('Name')['ID'].to_dict()

    def __init__(self, name: str, raw_data: dict):
        self._raw_data = raw_data
        self.name = name
        self.data = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
        self.attributes = []
        self.interpret()

    def interpret(self):
        def handle_modifier(modifier_value, scope_name, scale_name, modifier_name):
            # Skip over keys that are integers (representing comment lines)
            if isinstance(modifier_name, int):
                continue

            split_name = modifier_name.split("_")

            # Ensure that the item is a modifier
            if "add" not in split_name:
                continue

            # Get the operation, scope, and element name
            operation = operator.add if "add" in split_name else operator.mul if "mult" in split_name else None
            scope = split_name[0]
            element_name = "_".join(split_name[2:-1])

            # Map the variable name to the corresponding dictionary
            if "input" in split_name:
                data = self.data["input"]
            elif "output" in split_name:
                data = self.data["output"]
            elif "employment" in split_name:
                data = self.data["workforce"]
            elif "shares" in split_name:
                data = self.data["shares"]
            else:
                data = self.data["other"]

            # Update the dictionary with the new data
            data[element_name][operation.__name__] += float(modifier_value)

        if not self._raw_data.get("building_modifiers"):
            return

        for scope_name, scope_object in self._raw_data.items():
            for scale_name, scale_object in scope_object.items():
                for modifier_name, modifier_value in scale_object.items():
                    handle_modifier(modifier_value, scope_name, scale_name, modifier_name)

    def calc_profit(self, level):
        profit = 0
        for name, operations in self.data["input"].items():
            price = float(cache.get("Goods")[name]["cost"]) if cache.get("Goods") else 1
            profit -= price * (operations[operator.add.__name__] + level * operations.get(operator.mul.__name__, 0))
        for name, operations in self.data["output"].items():
            price = float(cache.get("Goods")[name]["cost"]) if cache.get("Goods") else 1
            profit += price * (operations[operator.add.__name__] + level * operations.get(operator.mul.__name__, 0))
        return profit

    def calc_total_employees(self, level):
        employees = 0
        for name, operations in self.data["workforce"].items():
            employees += (operations[operator.add.__name__] + level * operations.get(operator.mul.__name__, 0))
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
            html.P('employments:'),
            html.Ul([html.Li(create_inputs(key, value, 'employment')) for key, value in self.workforce.items()]),
        ])
