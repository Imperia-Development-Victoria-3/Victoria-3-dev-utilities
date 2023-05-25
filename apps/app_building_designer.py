from dash import dcc, html, Input, Output, Patch, dash_table, State

from data_utils import TransformNoInverse
from data_utils.transformation_types import Percentage, PriceCompensation
from dash.exceptions import PreventUpdate
from constants import GlobalState

from app import app

building_list = [path[-1] for category, path in
                 GlobalState.buildings_folder.get_iterable("production_method_groups", return_path=True)]

layout = html.Div([
    dcc.Dropdown(
        id='building-dropdown',
        options=[{'label': i, 'value': i} for i in building_list],
        value='Building 1'
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
    building = list(GlobalState.buildings_folder.get_iterable(selected_building))
    building = building[0]  # the first item found

    prod_methods = building["production_method_groups"]

    dropdowns = []

    for name, group in prod_methods.items():
        production_methods = [method for method in group["production_methods"].keys()]
        dropdown = dcc.Dropdown(
            id=f'{name}',
            options=[{'label': method, 'value': method} for method in production_methods],
            value=production_methods[0] if production_methods else None,
            # setting the default value to the first method in the group
            style={"width": "100%"}
        )
        dropdowns.append(dropdown)

    return dropdowns
