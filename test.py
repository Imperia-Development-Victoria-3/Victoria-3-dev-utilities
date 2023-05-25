import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

app = dash.Dash(__name__)

# Assuming that 'building_categories' is a dictionary with category names as keys and lists of buildings as values
building_categories = {
    "Category 1": ["Building 1", "Building 2"],
    "Category 2": ["Building 3", "Building 4"],
    "Category 3": ["Building 5", "Building 6"],
}

app.layout = html.Div([
    dcc.Dropdown(
        id='building-dropdown',
        options=[
            {'label': category, 'value': buildings[0], 'disabled': True} for category, buildings in building_categories.items()
        ] + [
            {'label': building, 'value': building} for buildings in building_categories.values() for building in buildings
        ],
        value='Building 1'
    ),
    html.Div(id='selected-building'),
])

@app.callback(
    Output('selected-building', 'children'),
    Input('building-dropdown', 'value'))
def update_building_info(selected_building):
    return f"Selected Building: {selected_building}"

if __name__ == '__main__':
    app.run_server(debug=True)
