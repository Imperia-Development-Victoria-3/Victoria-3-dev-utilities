from dash import Dash, dcc, html, Input, Output, Patch, dash_table, State
from dash.dash_table import FormatTemplate
from dash.dash_table.Format import Format, Scheme, Trim

from parse_encoder import parse_text_file, parse_text
from data_utils.transformation import TransformNoInverse, Percentage, PriceCompensation
from dash.exceptions import PreventUpdate
from data_formats import Goods, PopNeeds, DashBuyPackages

standard_victoria_3_path = "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Victoria 3\\game"

app = Dash(__name__)
dictionary = parse_text_file(standard_victoria_3_path + "\\common\\buy_packages\\00_buy_packages.txt")
buy_packages = DashBuyPackages(dictionary)
buy_packages.apply_transformation(Percentage("goods."))

dictionary = parse_text_file(standard_victoria_3_path + "\\common\\goods\\00_goods.txt")
goods = Goods(dictionary)

dictionary = parse_text_file(standard_victoria_3_path + "\\common\\pop_needs\\00_pop_needs.txt")
pop_needs = PopNeeds(dictionary)

app.layout = html.Div([
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
    dcc.RadioItems(['Percentage', 'Absolute'], 'Percentage', id='table-number-type'),
    html.Br(),
    dash_table.DataTable(
        id='editable-table',
        columns=buy_packages.get_table_formatting(),
        data=buy_packages.df.to_dict("records"),
        editable=True,
        style_table={'height': '200px', 'overflowY': 'auto'}
    ),
    html.Br(),
    dcc.Graph(
        figure=buy_packages.get_ploty_plot("goods.", "area"),
        id='buy-packages-plot',
        style={'height': '700px'})
])


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
    # Output('buy-packages-plot', 'figure', allow_duplicate=True),
)
def update_transformations(transforms):
    transformation = PriceCompensation(goods, pop_needs)

    if 'price' in transforms:
        buy_packages.apply_transformation(transformation)
    else:
        buy_packages.apply_transformation(transformation, forward=False)

    return buy_packages.df.to_dict("records"), buy_packages.get_ploty_plot("goods.", "area")


@app.callback(
    Output('hidden-output', 'children'),
    Input('save-button', 'n_clicks'),
    prevent_initial_call=True)
def update_output(n_clicks):
    if n_clicks > 0:
        buy_packages.export_paradox("00_buy_packages_copy.txt")
    raise PreventUpdate


@app.callback(
    Output('editable-table', 'data', allow_duplicate=True),
    Input('normalize-button', 'n_clicks'),
    prevent_initial_call=True,
)
def update_output(n_clicks):
    if n_clicks > 0:
        TransformNoInverse.normalize(buy_packages.df, "goods.")
    return buy_packages.df.to_dict("records"),


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
        buy_packages.apply_transformation(Percentage('goods.'))
        normalize_button_hidden = False
    elif value == "Absolute":
        buy_packages.apply_transformation(Percentage('goods.'), forward=False)
        normalize_button_hidden = True
    else:
        raise NotImplementedError(value + " not implemented")

    columns = buy_packages.get_table_formatting()
    figure = buy_packages.get_ploty_plot("goods.", "area")

    return buy_packages.df.to_dict("records"), columns, figure, normalize_button_hidden


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
            buy_packages.update_value(cell["column_id"], cell["row"], value)
            buy_packages.patch_ploty_plot(cell, patched_figure, False)
    return patched_figure


if __name__ == '__main__':
    app.run_server(debug=True)
