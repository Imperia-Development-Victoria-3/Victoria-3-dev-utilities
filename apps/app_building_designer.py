from dash import dcc, html, Input, Output, Patch, dash_table, State
from dash.dependencies import Input, Output, MATCH, ALL
from dash import callback_context
from data_utils import TransformNoInverse
from data_utils.transformation_types import Percentage, PriceCompensation
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
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
    html.Div(id='method-dropdowns', className='dropdown-container'),
    html.Div(id="summary")

    # html.Img(id='building-image', src=''),
    # html.Div(id='profit-score'),
    # html.Div(id='other-scores'),
    # html.Div(id='production-methods'),
])


@app.callback(
    Output('method-dropdowns', 'children'),
    Input('building-dropdown', 'value'))
def update_method_dropdowns(selected_building):
    if not selected_building:
        return []

    GlobalState.currently_selected_building = GlobalState.buildings_folder[selected_building]
    prod_methods = GlobalState.currently_selected_building["production_method_groups"]
    dropdowns = []
    for name, group in prod_methods.items():
        production_methods = [method for method in group["production_methods"].keys()]
        inputs, outputs, employees = get_attributes(list(group["production_methods"].values())[0])
        dropdown = html.Div([
            dcc.Dropdown(
                id={'type': 'dropdown', 'index': name},
                options=[{'label': method, 'value': method} for method in production_methods],
                value=production_methods[0] if production_methods else None,
                style={"width": "100%"}
            ),
            html.Div(id={'type': 'info', 'index': name},
                     children=generate_info_box(production_methods[0], inputs, outputs, employees))],
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
    inputs, outputs, employees = get_attributes(production_method)

    return generate_info_box(selected_value, inputs, outputs, employees)


def get_attributes(production_method):
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
    return inputs, outputs, employees


def generate_info_box(name, inputs, outputs, employees):
    return html.Div([
        html.P('Inputs:'),
        html.Ul([html.Li([
            html.Span(f'{key}: '),  # Show the name of the input
            dcc.Input(id={'type': 'input-value', 'index': key}, value=value, type='text')
        ]) for key, value in inputs.items()]),
        html.P('Outputs:'),
        html.Ul([html.Li([
            html.Span(f'{key}: '),  # Show the name of the output
            dcc.Input(id={'type': 'output-value', 'index': key}, value=value, type='text')
        ]) for key, value in outputs.items()]),
        html.P('Employees:'),
        html.Ul([html.Li([
            html.Span(f'{key}: '),  # Show the name of the employee
            dcc.Input(id={'type': 'employee-value', 'index': key}, value=value, type='text')
        ]) for key, value in employees.items()]),
        html.Button('Save Changes', id={'type': 'save', 'index': name}),
        html.Div(id='output-div')
    ])


@app.callback(
    Output('summary', 'children'),
    [Input({'type': 'input-value', 'index': ALL}, 'value'),
     Input({'type': 'output-value', 'index': ALL}, 'value'),
     Input({'type': 'employee-value', 'index': ALL}, 'value'),
     State({'type': 'input-value', 'index': ALL}, 'id'),
     State({'type': 'output-value', 'index': ALL}, 'id'),
     State({'type': 'employee-value', 'index': ALL}, 'id')],
    prevent_initial_call=True)
def update_summary(input_values, output_values, employee_values, input_ids, output_ids, employee_ids):
    def accumulate(values, ids):
        # Initialize dictionary to hold sum of values for each unique key
        sums = {}
        # Iterate over values and ids together
        for value, id in zip(values, ids):
            # Get key from the id dictionary
            key = id['index']
            # Convert value to float and add to the sum for this key
            try:
                sums[key] = sums.get(key, 0) + float(value)
            except ValueError:
                "do Nothing"
        return sums

    input_sums, output_sums, employee_sums = map(accumulate, [input_values, output_values, employee_values],
                                                 [input_ids, output_ids, employee_ids])

    # Create rows for inputs, outputs, and employees
    input_rows = [html.Div(f'{key}: {val}', className='three columns') for key, val in input_sums.items()]
    output_rows = [html.Div(f'{key}: {val}', className='three columns') for key, val in output_sums.items()]
    employee_rows = [html.Div(f'{key}: {val}', className='three columns') for key, val in employee_sums.items()]

    # Determine the maximum length of rows among all categories
    max_len = max(len(input_rows), len(output_rows), len(employee_rows))

    # Fill shorter categories with empty strings to make them equal in length to the longest category
    input_rows += [''] * (max_len - len(input_rows))
    output_rows += [''] * (max_len - len(output_rows))
    employee_rows += [''] * (max_len - len(employee_rows))

    # Combine each corresponding row from each category into one row
    rows = [html.Div([input_rows[i], output_rows[i], employee_rows[i]], className='row') for i in range(max_len)]

    # Add a row for total values
    total_row = html.Div([
        html.Div(f'Total Input: {sum(input_sums.values())}', className='three columns'),
        html.Div(f'Total Output: {sum(output_sums.values())}', className='three columns'),
        html.Div(f'Total Employee: {sum(employee_sums.values())}', className='three columns'),
    ], className='row')
    rows.append(total_row)

    return rows
