from dash import dcc, html, Input, Output

from app import app
from apps import app_buy_packages

# Define the home page layout
home_page = html.Div([
    html.H1('Welcome to the multi-page app'),
    html.H2('Please choose an app:'),
    html.Div([
        dcc.Link('Go to Buy Package app', href='/apps/app_buy_packages.py'),
        html.Br(),
        dcc.Link('Go to App 2', href='/apps/app2'),
    ]),
])

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
        return app2.layout
    else:
        return home_page


if __name__ == '__main__':
    app.run_server(debug=True)
