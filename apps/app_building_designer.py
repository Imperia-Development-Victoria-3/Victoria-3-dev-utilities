from dash import dcc, html, Input, Output, Patch, dash_table, State, callback_context
from dash.dependencies import Input, Output, MATCH, ALL
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from data_formats import TechnologiesFolder, ProductionMethodGroupsFolder, ProductionMethodsFolder, BuildingGroups, BuildingsFolder, GoodsFolder, PopNeedsFolder, ProductionMethod
import json

from app import app, cache


def get_layout():
    building_list = list(cache.get(BuildingsFolder.__name__).flattened_refs.keys()) if cache.get(
        BuildingsFolder.__name__) else []
    return html.Div([
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
    ])


requirements = [ProductionMethodGroupsFolder, ProductionMethodsFolder, BuildingGroups,
                BuildingsFolder, GoodsFolder, TechnologiesFolder]


@app.callback(
    Output('method-dropdowns', 'children'),
    Input('building-dropdown', 'value'))
def update_method_dropdowns(selected_building):
    if not selected_building:
        return []

    cache.set("currently_selected_building", cache.get(BuildingsFolder.__name__)[selected_building])
    prod_methods = cache.get("currently_selected_building")["production_method_groups"]
    dropdowns = []
    for name, group in prod_methods.items():
        production_methods = [method for method in group["production_methods"].keys()]
        production_method = ProductionMethod(production_methods[0], list(group["production_methods"].values())[0],
                                             cache.get(GoodsFolder.__name__))
        dropdown = html.Div([
            dcc.Dropdown(
                id={'type': 'dropdown', 'index': name},
                options=[{'label': method, 'value': method} for method in production_methods],
                value=production_methods[0] if production_methods else None,
                style={"width": "100%"}
            ),
            html.Div(id={'type': 'info', 'index': name},
                     children=production_method.generate_info_box())],
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

    production_method = cache.get("currently_selected_building")["production_method_groups"][production_method_group][
        "production_methods"][selected_value]
    production_method = ProductionMethod(selected_value, production_method)
    return production_method.generate_info_box()


@app.callback(
    Output('summary', 'children'),
    [Input({'type': 'input-value-add', 'index': ALL}, 'value'),
     Input({'type': 'input-value-mul', 'index': ALL}, 'value'),
     Input({'type': 'output-value-add', 'index': ALL}, 'value'),
     Input({'type': 'output-value-mul', 'index': ALL}, 'value'),
     Input({'type': 'employee-value-add', 'index': ALL}, 'value'),
     Input({'type': 'employee-value-mul', 'index': ALL}, 'value'),
     State({'type': 'input-value-add', 'index': ALL}, 'id'),
     State({'type': 'input-value-mul', 'index': ALL}, 'id'),
     State({'type': 'output-value-add', 'index': ALL}, 'id'),
     State({'type': 'output-value-mul', 'index': ALL}, 'id'),
     State({'type': 'employee-value-add', 'index': ALL}, 'id'),
     State({'type': 'employee-value-mul', 'index': ALL}, 'id')],
    prevent_initial_call=True)
def update_summary(input_values_add, input_values_mul, output_values_add, output_values_mul, employee_values_add,
                   employee_values_mul,
                   input_ids_add, input_ids_mul, output_ids_add, output_ids_mul, employee_ids_add, employee_ids_mul):
    def accumulate(values_add, values_mul, ids_add, ids_mul, is_goods=False):
        # Initialize dictionary to hold sum of values for each unique key
        sums = {}
        # Iterate over values and ids together
        for values, ids in [(values_add, ids_add), (values_mul, ids_mul)]:
            for value, id in zip(values, ids):
                # Get key from the id dictionary and remove '-add' or '-mul'
                key = id['index'].rsplit('-', 1)[0]
                # Convert value to float and add to the sum for this key
                try:
                    subtotal = float(cache.get(GoodsFolder.__name__)[key]["cost"]) * float(
                        value) if is_goods else float(value)
                    sums[key] = sums.get(key, 0) + subtotal
                except ValueError:
                    pass
        return sums

    input_sums = accumulate(input_values_add, input_values_mul, input_ids_add, input_ids_mul, True)
    output_sums = accumulate(output_values_add, output_values_mul, output_ids_add, output_ids_mul, True)
    employee_sums = accumulate(employee_values_add, employee_values_mul, employee_ids_add, employee_ids_mul)

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
