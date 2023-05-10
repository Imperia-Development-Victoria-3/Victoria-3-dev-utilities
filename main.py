from dash import Dash, dcc, html, Input, Output, Patch, dash_table, State
from dash.dash_table import FormatTemplate
from dash.dash_table.Format import Format, Scheme, Trim

from parse_encoder import parse_text_file, parse_text
from data_formats.buy_packages import DashBuyPackages
from data_utils.transformation import Transform, Percentage, PriceCompensation
from dash.exceptions import PreventUpdate

app = Dash(__name__)
dictionary = parse_text_file("00_buy_packages.txt")
buy_packages = DashBuyPackages(dictionary)
buy_packages.apply_transformation(Percentage("goods."))

app.layout = html.Div([
    html.Div(id="hidden-output", style={"display": "none"}),
    dcc.Store(id='table-selected-prev'),
    html.Button('Save copy', id='save-button', n_clicks=0),
    html.Button('Normalize', id='normalize-button', n_clicks=0),
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
        Transform.normalize(buy_packages.df, "goods.")
    return buy_packages.df.to_dict("records")


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
    Output('buy-packages-plot', 'figure'),
    Input('editable-table', 'data'),
    State('editable-table', 'active_cell'),
    State('table-selected-prev', 'data')
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
