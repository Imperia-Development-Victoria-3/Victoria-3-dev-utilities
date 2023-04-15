from dash import Dash, dcc, html, Input, Output, Patch, dash_table, State
from random import seed
from parse_encoder import parse_text_file, parse_text
import numpy as np
from data_formats.buy_packages import DashBuyPackages

# For the documentation to always render the same values
seed(0)

app = Dash(__name__)
dictionary = parse_text_file("00_buy_packages.txt")
buy_packages = DashBuyPackages(dictionary)

app.layout = html.Div([
    html.Div(id="hidden-output", style={"display": "none"}),
    dcc.Store(id='table-selected-prev'),
    html.Button('Save copy', id='save-button', n_clicks=0),
    html.Br(),
    dash_table.DataTable(
        id='editable-table',
        columns=buy_packages.get_formatted_keys(),
        data=buy_packages.get_formatted_goods_data(),
        editable=True,
        style_table={'height': '200px', 'overflowY': 'auto'}
    ),
    html.Br(),
    dcc.Graph(
        figure=buy_packages.get_ploty_plot(True),
        id='buy-packages-plot',
        style={'height': '700px'})
])


@app.callback(
    Output('table-selected-prev', 'data'),
    Input('editable-table', 'active_cell'))
def store_previous_data(previous_data):
    return previous_data


@app.callback(
    Output('hidden-output', 'children'),
    Input('save-button', 'n_clicks')
)
def update_output(n_clicks):
    if n_clicks > 0:
        buy_packages.export_paradox("00_buy_packages_copy.txt")


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
            value = data[cell["row"]].get(cell["column_id"], 0)
            buy_packages.update_value(cell["column_id"], cell["row"], value)
            buy_packages.patch_ploty_plot(cell, patched_figure, True)
    return patched_figure


if __name__ == '__main__':
    app.run_server(debug=True)
