from dash import dcc, html, Input, Output, Patch, dash_table, State

from data_utils import TransformNoInverse, Percentage, PriceCompensation
from dash.exceptions import PreventUpdate
from data_formats import DashBuyPackages, GoodsFolder, PopNeedsFolder

from app import app, cache


def get_layout():
    return html.Div([
        html.Div(id="hidden-output", style={"display": "none"}),
        dcc.Store(id='table-selected-prev'),
        html.Button('Save copy', id='save-button', n_clicks=0),
        html.Button('Normalize', id='normalize-button', n_clicks=0),
        dcc.Checklist(
            options={
                'price': 'Apply Price Adjustment',
            },
            value=[],
            id="transform options"
        ),
        dcc.RadioItems(['Percentage', 'Absolute'], 'Absolute', id='table-number-type'),
        html.Br(),
        dash_table.DataTable(
            id='editable-table',
            columns=cache.get(DashBuyPackages.__name__).get_table_formatting() if cache.get(
                DashBuyPackages.__name__) is not None else [],
            data=cache.get(DashBuyPackages.__name__).data_frame.to_dict("records") if cache.get(
                DashBuyPackages.__name__) is not None else [],
            editable=True,
            style_table={'height': '200px', 'overflowY': 'auto'}
        ),
        html.Br(),
        dcc.Graph(
            figure=cache.get(DashBuyPackages.__name__).get_ploty_plot("goods.",
                                                                      "area") if cache.get(
                DashBuyPackages.__name__) is not None else [],
            id='buy-packages-plot',
            style={'height': '700px'})
    ])


requirements = [DashBuyPackages, GoodsFolder, PopNeedsFolder]


@app.callback(
    Output('table-selected-prev', 'data'),
    Input('editable-table', 'active_cell'),
    prevent_initial_call=True)
def store_previous_data(previous_data):
    return previous_data


@app.callback(
    Output('editable-table', 'data', allow_duplicate=True),
    Output('buy-packages-plot', 'figure', allow_duplicate=True),
    Input('transform options', "value"),
    prevent_initial_call=True
)
def update_transformations(transforms):
    transformation = PriceCompensation(cache.get(GoodsFolder.__name__), cache.get(PopNeedsFolder.__name__))
    if 'price' in transforms:
        cache.get(DashBuyPackages.__name__).apply_transformation(transformation)
    else:
        cache.get(DashBuyPackages.__name__).apply_transformation(transformation, forward=False)
    return cache.get(DashBuyPackages.__name__).data_frame.to_dict("records"), cache.get(
        DashBuyPackages.__name__).get_ploty_plot("goods.",
                                                 "area")


@app.callback(
    Output('hidden-output', 'children'),
    Input('save-button', 'n_clicks'),
    prevent_initial_call=True)
def update_output(n_clicks):
    if n_clicks > 0:
        cache.get(DashBuyPackages.__name__).export_paradox("00_buy_packages_copy.txt")
    raise PreventUpdate


@app.callback(
    Output('editable-table', 'data', allow_duplicate=True),
    Input('normalize-button', 'n_clicks'),
    prevent_initial_call=True,
)
def update_output(n_clicks):
    if n_clicks > 0:
        TransformNoInverse.normalize(cache.get(DashBuyPackages.__name__).data_frame, "goods.")
    return cache.get(DashBuyPackages.__name__).data_frame.to_dict("records")


@app.callback(
    Output('editable-table', 'data', allow_duplicate=True),
    Output('editable-table', 'columns'),
    Output('buy-packages-plot', 'figure', allow_duplicate=True),
    Output('normalize-button', 'hidden'),
    Input('table-number-type', 'value'),
    prevent_initial_call=True,
)
def update_table_type(value):
    if value == "Percentage":
        cache.get(DashBuyPackages.__name__).apply_transformation(Percentage('goods.'))
        normalize_button_hidden = False
    elif value == "Absolute":
        cache.get(DashBuyPackages.__name__).apply_transformation(Percentage('goods.'), forward=False)
        normalize_button_hidden = True
    else:
        raise NotImplementedError(value + " not implemented")

    columns = cache.get(DashBuyPackages.__name__).get_table_formatting()
    figure = cache.get(DashBuyPackages.__name__).get_ploty_plot("goods.", "area")

    return cache.get(DashBuyPackages.__name__).data_frame.to_dict("records"), columns, figure, normalize_button_hidden


@app.callback(
    Output('buy-packages-plot', 'figure', allow_duplicate=True),
    Input('editable-table', 'data'),
    State('editable-table', 'active_cell'),
    State('table-selected-prev', 'data'),
    prevent_initial_call=True
)
def update_buy_packages_plot(data, active_cell, prev_active_cell):
    cells = [active_cell, prev_active_cell]
    patched_figure = Patch()
    for cell in cells:
        if cell:
            value = data[cell["row"]].get(cell["column_id"], None)
            cache.get(DashBuyPackages.__name__).update_value(cell["column_id"], cell["row"], value)
            cache.get(DashBuyPackages.__name__).patch_ploty_plot(cell, patched_figure)
    return patched_figure
