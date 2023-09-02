from pprint import pprint

from dash import dcc, html, Input, Output, Patch, dash_table, State, callback_context, no_update
from dash.dependencies import Input, Output, MATCH, ALL
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from data_formats import Technologies, ProductionMethodGroups, ProductionMethods, BuildingGroups, Goods, Eras
from data_processors import ProductionMethod, DashBuildings, Building
import json
import copy
from plotly import graph_objects as go

from app import app, cache


def get_layout():
    building_list = list(cache.get(DashBuildings.__name__).keys()) if cache.get(
        DashBuildings.__name__) else []
    era_list = list(cache.get(Eras.__name__).keys()) if cache.get(
        Eras.__name__) else []
    filter_options = [{'label': name.capitalize(), 'value': name} for name in Building.FILTER_FUNCTIONS.keys()]
    attribute_options = [{'label': name.capitalize(), 'value': name} for name in Building.ATTRIBUTE_FUNCTIONS.keys()]
    attribute_start_value = attribute_options[0]["value"] if attribute_options else []
    attribute_config = Building.ATTRIBUTE_FUNCTIONS[attribute_start_value]

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
            options=attribute_options,
            value=attribute_start_value,
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
                options=[{'label': i, 'value': i} for i in era_list],
                value=era_list,
                multi=True,
                placeholder='Select eras...'
            ),
            dcc.Checklist(
                id='building-filter-options',
                options=filter_options,
                value=[name for name, is_enabled in attribute_config["config"].items() if is_enabled],
            )], className='horizontal-container'
        ),
        dcc.Graph(id='building-plot',
                  figure=cache.get(DashBuildings.__name__).get_plotly_plot(attribute_start_value, attribute_config,
                                                                           selected_building="",
                                                                           eras=era_list) if cache.get(
                      DashBuildings.__name__) else [])
    ])


requirements = [Goods, ProductionMethodGroups, ProductionMethods, BuildingGroups,
                DashBuildings, Technologies, Eras]


@app.callback(
    Output('hidden-output-building', 'children'),
    Input('save', 'n_clicks'),
    prevent_initial_call=True)
def save_changes(n_clicks):
    if n_clicks > 0:
        for tracked_info in requirements:
            instance = cache.get(tracked_info.__name__)
            if hasattr(instance, "export_paradox"):
                cache.get(tracked_info.__name__).export_paradox()
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
    Input({'index': ALL, 'type': 'info-input'}, 'value'),
    State('building-dropdown', 'value'),
    State('attribute-dropdown', 'value'),
    State('plot-type-dropdown', 'value'),
    State('era-dropdown', 'value'),
    State('building-filter-options', 'value'),
    prevent_initial_call=True)
def update_database(info_value, selected_building, attribute, plot_type, eras, building_filter_options):
    args = callback_context.args_grouping[0]  # info_value but then complete
    building_name = None
    for input_args in args:
        if not input_args["triggered"]:
            continue
        building_name, group_name, production_method_name, scope_name, scale_name, modifier_name = input_args['id'][
            'index'].split('-')
        value = input_args['value']
        production_methods = cache.get(DashBuildings.__name__)[building_name]['production_method_groups']
        production_methods[group_name]['production_methods'][production_method_name][scope_name][scale_name][
            modifier_name] = value

    if building_name and cache.get(DashBuildings.__name__):
        cache.get(DashBuildings.__name__).reset_building(building_name)
        attribute_config = Building.ATTRIBUTE_FUNCTIONS[attribute]
        attribute_config["config"].update({name: True for name in building_filter_options})
        return cache.get(DashBuildings.__name__).get_plotly_plot(
            attribute, attribute_config, plot_type, selected_building, eras
        )
    return go.Figure()


# @app.callback(
#     Output('summary', 'children'),
#     Input({'index': ALL, 'type': 'info-input'}, 'value'),
#     Input({'type': 'dropdown', 'index': ALL}, 'value'),
#     prevent_initial_call=True)
# def update_summary(info_value, production_methods):
#     settings = {}
#     production_method_infos = callback_context.args_grouping[1]  # production_method_info
#     building_name = None
#     for production_method_info in production_method_infos:
#         building_name, production_method_group_name = production_method_info['id']['index'].split('-')
#         settings[production_method_group_name] = production_method_info['value']
#     if building_name:
#         building = cache.get(DashBuildings.__name__)._buildings[building_name]
#         return building.get_summary(settings)


@app.callback(
    Output('building-plot', 'figure'),
    Output('building-filter-options', 'value'),
    Input('building-dropdown', 'value'),
    Input('attribute-dropdown', 'value'),
    Input('plot-type-dropdown', 'value'),
    Input('era-dropdown', 'value'),
    Input('building-filter-options', 'value'),
    prevent_initial_call=True
)
def update_figure(selected_building, attribute, plot_type, eras, building_filter_options):
    triggered_id = callback_context.triggered[0]['prop_id'].split('.')[0] if callback_context.triggered else None

    filter_value = no_update
    if triggered_id == 'attribute-dropdown':
        attribute_config = Building.ATTRIBUTE_FUNCTIONS[attribute]
        filter_value = [name for name, is_enabled in attribute_config["config"].items() if is_enabled]
        building_filter_options = filter_value

    if cache.get(DashBuildings.__name__):
        attribute_config = copy.deepcopy(Building.ATTRIBUTE_FUNCTIONS[attribute])
        attribute_config["config"].update({name: True for name in building_filter_options})
        return cache.get(DashBuildings.__name__).get_plotly_plot(
            attribute, attribute_config, plot_type, selected_building, eras
        ), filter_value
    return go.Figure(), filter_value


@app.callback(
    Output({'type': 'scale-collapse', 'index': MATCH}, 'is_open'),
    Input({'type': 'scale-button', 'index': MATCH}, 'n_clicks'),
    State({'type': 'scale-collapse', 'index': MATCH}, 'is_open')
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open
