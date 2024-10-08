from collections import defaultdict

from dash import dcc, html, Input, Output, Patch, dash_table, State, callback_context
from data_utils import TransformNoInverse, Percentage, update_table_fill, linear_fill, \
    exponential_fill
from dash.exceptions import PreventUpdate
from data_formats import DashBuyPackages, Goods
import numpy as np
from app import app, cache


def get_layout():
    is_percentage = cache.get(DashBuyPackages.__name__).data_frame.is_percentage if hasattr(
        cache.get(DashBuyPackages.__name__).data_frame, "is_percentage") else False
    return html.Div([
        # Hidden Div
        html.Div(id="hidden-output", style={"display": "none"}),

        # Data Store
        dcc.Store(id='table-selected-prev'),

        # Action Buttons
        html.Div([
            html.Button('Save to mod folder', id='save-button', n_clicks=0),
            html.Button('Normalize', id='normalize-button', hidden=True, n_clicks=0),
        ], style={'margin-bottom': '10px'}),

        # Tabs
        dcc.Tabs(id='tabs', value='tab-1', children=[
            dcc.Tab(label='View Options', value='tab-1', children=[
                html.Div([
                    html.Div([
                        html.Label('Number Type:', style={'color': 'blue', 'font-weight': 'bold'}),
                        dcc.RadioItems(
                            options=[{'label': 'Percentage', 'value': 'Percentage'},
                                     {'label': 'Absolute', 'value': 'Absolute'}],
                            value='Percentage' if is_percentage else 'Absolute',
                            id='table-number-type'
                        ),
                    ], style={'display': 'inline-block', 'vertical-align': 'top'}),

                    html.Div([
                        html.Label('Table Height (in pixels)', style={'color': 'purple', 'font-weight': 'bold'}),
                        dcc.Slider(
                            id='table-height-slider',
                            min=0,
                            max=1200,
                            value=300,
                            # marks={i: str(i) for i in range(0, 801, 100)},
                        ),
                    ], style={'margin-top': '20px'}),

                    html.Div([
                        html.Label('Plot Height (in pixels)', style={'color': 'purple', 'font-weight': 'bold'}),
                        dcc.Slider(
                            id='plot-height-slider',
                            min=0,
                            max=1200,
                            value=700,
                            # marks={i: str(i) for i in range(0, 801, 100)},
                        ),
                    ], style={'margin-top': '20px'}),
                ]),
            ]),
            dcc.Tab(label='Edit Tools', value='tab-2', children=[
                html.Div([
                    html.Div([
                        html.Label('Mass Operations to all selected cells',
                                   style={'color': 'green', 'font-weight': 'bold'}),
                        html.Div([
                            dcc.Input(id='input-box', type='number', value=0),
                            html.Button('Add', id='button-add'),
                            html.Button('Multiply', id='button-mult'),
                            dcc.Checklist(
                                options=[{'label': 'Apply to 0 values in table', 'value': 'handle_zeros'}],
                                value=[],
                                id="user-options"
                            ),
                        ])
                    ], style={'display': 'inline-block', 'margin-right': '50px', 'vertical-align': 'top'}),

                    html.Div([
                        html.Label('Interpolation between top and bottom selected cells',
                                   style={'color': 'green', 'font-weight': 'bold'}),
                        html.Div([
                            html.Button('Linear', id='linear-button', n_clicks=0),
                            html.Button('Exponential', id='exponential-button', n_clicks=0),
                        ])
                    ], style={'display': 'inline-block', 'vertical-align': 'top'}),
                ])
            ])
        ]),
        dash_table.DataTable(
            id='editable-table',
            columns=cache.get(DashBuyPackages.__name__).get_table_formatting() if cache.get(
                DashBuyPackages.__name__) is not None else [],
            data=cache.get(DashBuyPackages.__name__).data_frame.to_dict("records") if cache.get(
                DashBuyPackages.__name__) is not None else [],
            editable=True,
            style_table={'height': '300px', 'resize': 'both', 'overflowY': 'auto'},
            column_selectable="multi",  # allows selecting multiple columns
            cell_selectable=True,  # allows selecting individual cells
        ),
        html.Br(),
        dcc.Graph(
            figure=cache.get(DashBuyPackages.__name__).get_plotly_plot("goods.",
                                                                       "area") if cache.get(
                DashBuyPackages.__name__) is not None else [],
            id='buy-packages-plot',
            style={'height': '700px'})
    ])


requirements = [DashBuyPackages, Goods]


@app.callback(
    Output('table-selected-prev', 'data'),
    Input('editable-table', 'active_cells'),
    prevent_initial_call=True)
def store_previous_data(previous_data):
    return previous_data

@app.callback(
    Output('hidden-output', 'children'),
    Input('save-button', 'n_clicks'),
    prevent_initial_call=True)
def update_output(n_clicks):
    if n_clicks > 0:
        cache.get(DashBuyPackages.__name__).export_paradox()
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
    Input('linear-button', 'n_clicks'),
    State('editable-table', 'selected_cells'),
    State('editable-table', 'data'),
    prevent_initial_call=True)
def update_linear_fill(n_clicks, active_cells, data):
    patch = Patch()
    return update_table_fill(n_clicks, active_cells, data, patch, linear_fill)


@app.callback(
    Output('editable-table', 'data', allow_duplicate=True),
    Input('exponential-button', 'n_clicks'),
    State('editable-table', 'selected_cells'),
    State('editable-table', 'data'),
    prevent_initial_call=True)
def update_exponential_fill(n_clicks, active_cells, data):
    patch = Patch()
    return update_table_fill(n_clicks, active_cells, data, patch, exponential_fill)


@app.callback(
    Output('editable-table', 'style_table'),
    Input('table-height-slider', 'value')
)
def update_table_height(value):
    patch = Patch()
    patch['height'] = f'{value}px'
    return patch

@app.callback(
    Output('buy-packages-plot', 'style'),
    Input('plot-height-slider', 'value')
)
def update_plot_height(value):
    patch = Patch()
    patch['height'] = f'{value}px'
    return patch


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
    figure = cache.get(DashBuyPackages.__name__).get_plotly_plot("goods.", "area")

    return cache.get(DashBuyPackages.__name__).data_frame.to_dict("records"), columns, figure, normalize_button_hidden


@app.callback(
    Output('buy-packages-plot', 'figure', allow_duplicate=True),
    Input('editable-table', 'data'),
    State('editable-table', 'selected_cells'),
    State('table-selected-prev', 'data'),
    State('editable-table', 'selected_columns'),
    prevent_initial_call=True
)
def update_buy_packages_plot(data, active_cells, prev_active_cells, selected_columns):
    if not active_cells:
        active_cells = []
    if not prev_active_cells:
        prev_active_cells = []
    cells = active_cells + prev_active_cells
    patched_figure = Patch()
    for cell in cells:
        if cell:
            value = data[cell["row"]].get(cell["column_id"], None)
            cache.get(DashBuyPackages.__name__).update_value(cell["column_id"], cell["row"], value)
            cache.get(DashBuyPackages.__name__).patch_plotly_plot_value(cell, patched_figure)
    if selected_columns:
        for column_id in selected_columns:
            new_column = []
            for row_id in range(len(data)):
                new_value = data[row_id].get(column_id) if data[row_id].get(column_id) and data[row_id].get(
                    column_id) == data[row_id].get(column_id) else np.nan
                new_column.append(new_value)
            cache.get(DashBuyPackages.__name__).update_column(column_id, new_column)
            cache.get(DashBuyPackages.__name__).patch_plotly_plot_column(column_id, patched_figure)
    return patched_figure


@app.callback(
    Output('editable-table', 'data'),
    [Input('button-add', 'n_clicks'),
     Input('button-mult', 'n_clicks')],
    State('input-box', 'value'),
    State('editable-table', 'selected_columns'),
    State('editable-table', 'selected_cells'),
    State('editable-table', 'data'),
    State('user-options', 'value')
)
def update_table(n_clicks, n_clicks_2, input_value, selected_columns, selected_cells, rows, overwrite_zero):
    if not callback_context.triggered:
        button_id = 'No clicks yet'
    else:
        button_id = callback_context.triggered[0]['prop_id'].split('.')[0]

    patched_table = Patch()

    if button_id in ['button-add', 'button-mult']:
        if selected_columns:  # if any column is selected
            for col_id in selected_columns:
                for i, row in enumerate(rows):
                    if row[col_id] and row[col_id] == row[col_id]:
                        if button_id == 'button-add':
                            patched_table[i][col_id] = row[col_id] + input_value
                        elif button_id == 'button-mult':
                            patched_table[i][col_id] = row[col_id] * input_value
                    elif overwrite_zero:
                        if button_id == 'button-add':
                            patched_table[i][col_id] = input_value
        elif selected_cells:  # if no column is selected
            for cell in selected_cells:
                if rows[cell['row']][cell['column_id']] and rows[cell['row']][cell['column_id']] == rows[cell['row']][
                    cell['column_id']]:
                    if button_id == 'button-add':
                        patched_table[cell['row']][cell['column_id']] = rows[cell['row']][
                                                                            cell['column_id']] + input_value
                    elif button_id == 'button-mult':
                        patched_table[cell['row']][cell['column_id']] = rows[cell['row']][
                                                                            cell['column_id']] * input_value
                elif overwrite_zero:
                    if button_id == 'button-add':
                        patched_table[cell['row']][cell['column_id']] = input_value
                    elif button_id == 'button-mult':
                        patched_table[cell['row']][cell['column_id']] = input_value
    return patched_table
