from dash import dcc, html, Input, Output, Patch, dash_table, State, callback_context
from dash.dependencies import Input, Output, MATCH, ALL
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from data_formats import Technologies, ProductionMethodGroups, ProductionMethods, BuildingGroups, Buildings, Goods
from data_processors import ProductionMethod, DashBuildings
import json
from plotly import graph_objects as go

from app import app, cache


def get_layout():
    building_list = list(cache.get(DashBuildings.__name__).keys()) if cache.get(
        DashBuildings.__name__) else []
    return html.Div([
        html.Button('Save Changes', id="save"),
        html.Div(id="hidden-output-building", style={"display": "none"}),
        dcc.Dropdown(
            id='building-dropdown',
            options=[{'label': i, 'value': i} for i in building_list],
            value=''
        ),
        html.Div(id='method-dropdowns', className='dropdown-container'),
        html.Div(id="summary"), dcc.Dropdown(
            id='attribute-dropdown',
            options=[
                {'label': 'Profitability', 'value': 'profitability'},
            ],
            value='profitability',
            placeholder='Select an attribute...'
        ),
        html.Div([
            dcc.Dropdown(
                id='plot-type-dropdown',
                options=[
                    {'label': 'Violin', 'value': 'Violin'},
                    {'label': 'Bar', 'value': 'Bar'},
                ],
                value='Violin',
                placeholder='Select a plot type...'
            ),
            dcc.Dropdown(
                id='era-dropdown',
                options=[{'label': i, 'value': i} for i in ["0", "1", "2", "3", "4", "5"]],
                value=["0", "1", "2", "3", "4", "5"],
                multi=True,
                placeholder='Select eras...'
            ),
            dcc.Checklist(
                id='building-filter-options',
                options=[
                    {'label': 'Commercial Buildings Only', 'value': 'commercial_only'},
                    {'label': 'Exclude Unique Buildings', 'value': 'no_unique_buildings'},
                ],
                value=['commercial_only', 'no_unique_buildings'],
            )], className='horizontal-container'
        ),
        dcc.Graph(id='building-plot',
                  figure=cache.get(DashBuildings.__name__).get_plotly_plot("profitability",
                                                                           selected_building="building_steel_mills") if cache.get(
                      DashBuildings.__name__) else [])
    ])


requirements = [ProductionMethodGroups, ProductionMethods, BuildingGroups,
                DashBuildings, Goods, Technologies]


@app.callback(
    Output('hidden-output-building', 'children'),
    Input('save', 'n_clicks'),
    prevent_initial_call=True)
def save_changes(n_clicks):
    if n_clicks > 0:
        cache.get(DashBuildings.__name__).export_paradox()
    return ""


@app.callback(
    Output('method-dropdowns', 'children'),
    Input('building-dropdown', 'value'))
def update_method_dropdowns(selected_building):
    if not selected_building:
        return []

    cache.set("currently_selected_building", cache.get(DashBuildings.__name__)[selected_building])
    prod_methods = cache.get("currently_selected_building")["production_method_groups"]
    dropdowns = []
    for name, group in prod_methods.items():
        production_methods = [method for method in group["production_methods"].keys()]
        production_method = ProductionMethod(production_methods[0], list(group["production_methods"].values())[0])
        dropdown = html.Div([
            dcc.Dropdown(
                id={'type': 'dropdown', 'index': selected_building + '-' + name},
                options=[{'label': method, 'value': method} for method in production_methods],
                value=production_methods[0] if production_methods else None,
                style={"width": "100%"}
            ),
            html.Div(id={'type': 'info', 'index': selected_building + '-' + name},
                     children=production_method.generate_info_box(selected_building, name))],
            className='dropdown'
        )
        dropdowns.append(dropdown)

    return dropdowns


@app.callback(
    Output({'type': 'info', 'index': MATCH}, 'children'),
    Input({'type': 'dropdown', 'index': MATCH}, 'value'),
    prevent_initial_call=True)
def update_info_div(selected_value):
    triggered = list(callback_context.triggered_prop_ids.values())[0]
    building, production_method_group = triggered['index'].split('-')
    production_method = cache.get("currently_selected_building")["production_method_groups"][production_method_group][
        "production_methods"][selected_value]
    production_method = ProductionMethod(selected_value, production_method)
    return production_method.generate_info_box(building, production_method_group)


@app.callback(
    Output('building-plot', 'figure', allow_duplicate=True),
    Input({'type': ALL, 'index': ALL, 'hook': 'info'}, 'value'),
    State({'type': ALL, 'index': ALL, 'hook': 'info'}, 'id'),
    State('building-dropdown', 'value'),
    State('attribute-dropdown', 'value'),
    State('plot-type-dropdown', 'value'),
    State('era-dropdown', 'value'),
    State('building-filter-options', 'value'),
    prevent_initial_call=True)
def update_database(info_value, info_ids, selected_building, attribute, plot_type, eras, building_filter_options):
    for i, triggered in enumerate(info_ids):
        building_name, group_name, production_method, operation = triggered['index'].split('-')
        production_methods = cache.get(DashBuildings.__name__)[building_name]["production_method_groups"]
        if (triggered["type"].split('-')[0] == "input" or triggered["type"].split('-')[0] == "output") and \
                production_methods[group_name]["production_methods"][production_method]["building_modifiers"].get(
                    "workforce_scaled"):
            production_methods[group_name]["production_methods"][production_method]["building_modifiers"][
                "workforce_scaled"]["building_" + triggered["type"].replace('-', '_')] = str(info_value[i])

        if triggered["type"].split('-')[0] == "employee" and \
                production_methods[group_name]["production_methods"][production_method]["building_modifiers"].get(
                    "level_scaled"):
            production_methods[group_name]["production_methods"][production_method]["building_modifiers"][
                "level_scaled"]["building_" + triggered["type"].replace('-', '_')] = str(info_value[i])

    cache.get(DashBuildings.__name__).reset_building(building_name)
    commercial_only = 'commercial_only' in building_filter_options
    no_unique_buildings = 'no_unique_buildings' in building_filter_options

    if cache.get(DashBuildings.__name__):
        return cache.get(DashBuildings.__name__).get_plotly_plot(
            attribute, plot_type, selected_building, eras, commercial_only, no_unique_buildings
        )
    return go.Figure()


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
                key = id['index'].split('-')[-2]
                # Convert value to float and add to the sum for this key
                try:
                    subtotal = float(cache.get(Goods.__name__)[key]["cost"]) * float(
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


@app.callback(
    Output('building-plot', 'figure', allow_duplicate=True),
    Input('building-dropdown', 'value'),
    Input('attribute-dropdown', 'value'),
    Input('plot-type-dropdown', 'value'),
    Input('era-dropdown', 'value'),
    Input('building-filter-options', 'value'),
    prevent_initial_call=True
)
def update_figure(selected_building, attribute, plot_type, eras, building_filter_options):
    commercial_only = 'commercial_only' in building_filter_options
    no_unique_buildings = 'no_unique_buildings' in building_filter_options

    if cache.get(DashBuildings.__name__):
        return cache.get(DashBuildings.__name__).get_plotly_plot(
            attribute, plot_type, selected_building, eras, commercial_only, no_unique_buildings
        )
    return go.Figure()
