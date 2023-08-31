import operator
from collections import defaultdict
from dash import dcc, html
from app import cache
import pandas as pd
import dash_bootstrap_components as dbc


class ProductionMethod:
    scopes = pd.DataFrame({
        'ID': [0, 1, 2],
        'Name': ['building_modifiers', 'state_modifiers', 'country_modifiers']
    })
    scopes_to_id = scopes.set_index('Name')['ID'].to_dict()
    id_to_scopes = scopes.set_index('ID')['Name'].to_dict()

    scales = pd.DataFrame({
        'ID': [0, 1, 2, 3],
        'Name': ['level_scaled', 'workforce_scaled', 'unscaled', 'throughput_scaled'],
    })
    scales_to_id = scales.set_index('Name')['ID'].to_dict()
    id_to_scales = scales.set_index('ID')['Name'].to_dict()

    classifications = pd.DataFrame({
        'ID': [0, 1, 2],
        'Name': ['other', 'economic', 'military']
    })
    classification_military_keywords = ["unit", "army", "offense", "defense"]
    classification_to_id = classifications.set_index('Name')['ID'].to_dict()

    value_type = pd.DataFrame({
        'ID': [0, 1, 2, 3, 4],
        'Name': ['input', 'output', 'workforce', 'other', 'shares']
    })
    value_type_to_id = value_type.set_index('Name')['ID'].to_dict()
    id_to_value_type = value_type.set_index('ID')['Name'].to_dict()

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
            operation = "add" if "add" in split_name else "mul" if "mult" in split_name else None

            # Map the variable name to the corresponding dictionary
            value_type = 3
            element_name = modifier_name
            if "input" in split_name:
                value_type = 0
                element_name = "_".join(split_name[2:-1])
            elif "output" in split_name:
                value_type = 1
                element_name = "_".join(split_name[2:-1])
            elif "employment" in split_name:
                value_type = 2
                element_name = "_".join(split_name[2:-1])
            elif "shares" in split_name:
                value_type = 4
                element_name = "_".join(split_name[1:-2])

            classification = 0
            if any(keyword in split_name for keyword in ProductionMethod.classification_military_keywords):
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
        self.data = tmp_data

    def is_military(self):
        for datapoint in self.data:
            if datapoint["ClassificationID"] == ProductionMethod.classification_to_id["military"]:
                return True
        return False

    def get_data(self):
        return self.data

    def generate_info_box(self, building_name, group_name):
        tabs = []
        for scope_name, scope_object in self._raw_data.items():
            if ProductionMethod.scopes_to_id.get(scope_name) is not None:
                scales = []
                for scale_name, scale_object in scope_object.items():
                    modifiers = []
                    for modifier_name, modifier_value in scale_object.items():
                        modifiers.append(
                            html.Div([
                                html.Span(f'{modifier_name}: '),
                                dcc.Input(value=modifier_value, type='text', debounce=True, id={
                                    "index": f'{building_name}-{group_name}-{self.name}-{scope_name}-{scale_name}-{modifier_name}',
                                    'type': 'info-input'})
                            ])
                        )
                    scales.append(
                        html.Div([
                            html.Button(f'{scale_name}',
                                        id={'type': 'scale-button', 'index': f'{group_name}-{scope_name}-{scale_name}'},
                                        className='expand-button'),
                            dbc.Collapse(
                                children=modifiers,
                                id={'type': 'scale-collapse', 'index': f'{group_name}-{scope_name}-{scale_name}'},
                                is_open=True
                            )
                        ])
                    )
                tabs.append(dcc.Tab(
                    label=scope_name,
                    children=scales
                ))
        return dcc.Tabs(tabs)
