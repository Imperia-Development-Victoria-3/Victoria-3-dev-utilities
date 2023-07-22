import operator
from collections import defaultdict
from dash import dcc, html
from app import cache
import pandas as pd


class ProductionMethod:
    scopes = pd.DataFrame({
        'ID': [0, 1, 2],
        'Name': ['building_modifiers', 'state_modifiers', 'country_modifiers']
    })
    scopes_to_id = scopes.set_index('Name')['ID'].to_dict()

    scales = pd.DataFrame({
        'ID': [0, 1, 2, 3],
        'Name': ['level_scaled', 'workforce_scaled', 'unscaled', 'throughput_scaled'],
    })
    scales_to_id = scales.set_index('Name')['ID'].to_dict()

    classifications = pd.DataFrame({
        'ID': [0, 1, 2],
        'Name': ['other', 'economic', 'military']
    })
    classification_military_keywords = ["unit", "army", "offense", "defense"]
    classification_to_id = classifications.set_index('Name')['ID'].to_dict()

    value_type = pd.DataFrame({
        'ID': [0, 1, 2, 3, 4],
        'Name': ['other', 'input', 'output', 'workforce', 'shares']
    })
    value_type_to_id = value_type.set_index('Name')['ID'].to_dict()

    def __init__(self, name: str, raw_data: dict):
        self._raw_data = raw_data
        self.name = name
        self.data = pd.DataFrame(
            columns=["ID", "Name", "Value", "ValueType", "Operation", "ScopeID", "ScaleID", "ClassificationID"])
        self.attributes = []
        self.interpret()

    def interpret(self):
        def handle_modifier(tmp_data, modifier_value, scope_name, scale_name, modifier_name):
            # Skip over keys that are integers (representing comment lines)
            if isinstance(modifier_name, int):
                return

            split_name = modifier_name.split("_")

            # Get the operation, scope, and element name
            operation = operator.add if "add" in split_name else operator.mul if "mult" in split_name else None

            # Map the variable name to the corresponding dictionary
            value_type = 0
            element_name = modifier_name
            if "input" in split_name:
                value_type = 1
                element_name = "_".join(split_name[2:-1])
            elif "output" in split_name:
                value_type = 2
                element_name = "_".join(split_name[2:-1])
            elif "employment" in split_name:
                value_type = 3
                element_name = "_".join(split_name[2:-1])
            elif "shares" in split_name:
                value_type = 4
                element_name = "_".join(split_name[1:-2])

            classification = 0
            if any(ProductionMethod.classification_military_keywords) in split_name:
                classification = 2
            elif cache.get("Goods") and cache.get("Goods").get(element_name):
                classification = 1

            # Update the dictionary with the new data
            tmp_data.append({"ID": modifier_name, "Name": element_name,
                             "Value": float(modifier_value), "ValueType": value_type,
                             "Operation": operation,
                             "ScopeID": ProductionMethod.scopes_to_id[scope_name],
                             "ScaleID": ProductionMethod.scales_to_id[scale_name],
                             "ClassificationID": classification})

        tmp_data = []
        for scope_name, scope_object in self._raw_data.items():
            if ProductionMethod.scopes_to_id.get(scope_name) is not None:
                for scale_name, scale_object in scope_object.items():
                    for modifier_name, modifier_value in scale_object.items():
                        handle_modifier(tmp_data, modifier_value, scope_name, scale_name, modifier_name)
        self.data = pd.DataFrame(tmp_data)

    def get_data(self):
        return self.data

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
