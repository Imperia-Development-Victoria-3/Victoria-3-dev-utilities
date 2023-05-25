from dash import dcc, html, Input, Output, Patch, dash_table, State
from dash.dependencies import Input, Output, MATCH, ALL
from dash import callback_context
from data_utils import TransformNoInverse
from data_utils.transformation_types import Percentage, PriceCompensation
from dash.exceptions import PreventUpdate
from constants import GlobalState
import json

from app import app

building_list = list(GlobalState.buildings_folder.flattened_refs.keys())

layout = html.Div([
    dcc.Dropdown(
        id='building-dropdown',
        options=[{'label': i, 'value': i} for i in building_list],
        value=''
    ),
    html.Div(id='method-dropdowns', className='dropdown-container')
    # html.Img(id='building-image', src=''),
    # html.Div(id='profit-score'),
    # html.Div(id='other-scores'),
    # html.Div(id='production-methods'),
])


@app.callback(
    Output('method-dropdowns', 'children'),
    Input('building-dropdown', 'value'))
def update_method_dropdowns(selected_building):
    print(selected_building)
    if not selected_building:
        return []

    GlobalState.currently_selected_building = GlobalState.buildings_folder[selected_building]
    prod_methods = GlobalState.currently_selected_building["production_method_groups"]
    dropdowns = []
    for name, group in prod_methods.items():
        production_methods = [method for method in group["production_methods"].keys()]
        dropdown = html.Div([
            dcc.Dropdown(
                id={'type': 'dropdown', 'index': name},
                options=[{'label': method, 'value': method} for method in production_methods],
                value=production_methods[0] if production_methods else None,
                style={"width": "100%"}
            ),
            html.Div(id={'type': 'info', 'index': name})],
            className='dropdown'
        )
        dropdowns.append(dropdown)

    return dropdowns


@app.callback(
    Output({'type': 'info', 'index': MATCH}, 'children'),
    Input({'type': 'dropdown', 'index': MATCH}, 'value'),
    prevent_initial_call=True)
def update_info_div(selected_value):
    production_method_group = callback_context.triggered[0]['prop_id'].split('.')[0]
    production_method_group = json.loads(production_method_group)['index']

    production_method = GlobalState.currently_selected_building["production_method_groups"][production_method_group][
        "production_methods"][selected_value]
    inputs = {}
    outputs = {}
    employees = {}
    if production_method.get("building_modifiers"):
        for modifier, values in production_method["building_modifiers"].items():
            if modifier == "workforce_scaled":
                inputs = {key.split("_add")[0]: value for key, value in values.items() if
                          key.startswith("building_input")}
                outputs = {key.split("_add")[0]: value for key, value in values.items() if
                           key.startswith("building_output")}
            elif modifier == "level_scaled":
                employees = {key.split("_add")[0]: value for key, value in values.items() if
                             key.startswith("building_employment")}

    return html.Div([
        html.P('Inputs:'),
        html.Ul([html.Li(f'{i} {n}') for i, n in inputs.items()]),
        html.P('Outputs:'),
        html.Ul([html.Li(f'{o} {n}') for o, n in outputs.items()]),
        html.P('Employees:'),
        html.Ul([html.Li(f'{o} {n}') for o, n in employees.items()])
    ])
