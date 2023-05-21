from constants import GlobalState

GlobalState.reset()

from dash import dcc, html, Input, Output, dash
from apps import app_buy_packages, app_building_designer, app_index_page

from app import app

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])


@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/apps/app_buy_packages.py':
        return app_buy_packages.layout
    elif pathname == '/apps/app_building_designer.py':
        return app_building_designer.layout
    else:
        return app_index_page.layout


if __name__ == '__main__':
    GlobalState.reset()
    app.run_server(debug=True)
