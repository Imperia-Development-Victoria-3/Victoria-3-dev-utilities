from dash import dcc, html, Input, Output
from app import app, cache
from apps import app_buy_packages, app_building_designer, app_index_page
from inspect import signature
import inspect
import os
from typing import Union
from data_formats import *
import sys

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])


def load_requirements(requirements: list):
    for requirement in requirements:
        get_or_create_data_format(requirement)


def get_or_create_data_format(cls):
    data_format = cache.get(cls.__name__)
    if data_format is None:
        constructor_params = signature(cls.__init__).parameters
        args = {}
        for name, param in constructor_params.items():
            if name == 'self':
                continue
            if param.annotation != inspect._empty:
                if isinstance(param.annotation, str) and issubclass(getattr(sys.modules[__name__], param.annotation), DataFormat):
                    tmp_class = getattr(sys.modules[__name__], param.annotation)
                    args[name] = get_or_create_data_format(tmp_class)
                else:
                    continue

        working_directory = cache.get('game_directory')
        folder_path = os.path.join(working_directory, cls.relative_file_location)
        args['data'] = folder_path
        data_format = cls(**args)  # Create a new instance of the class
        cache.set(cls.__name__, data_format)
    return data_format


@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/apps/app_buy_packages.py':
        try:
            load_requirements(app_buy_packages.requirements)
        except:
            return dcc.Location(id='url', pathname="")
        return app_buy_packages.get_layout()
    elif pathname == '/apps/app_building_designer.py':
        try:
            load_requirements(app_building_designer.requirements)
        except:
            return dcc.Location(id='url', pathname="")
        return app_building_designer.get_layout()
    else:
        return app_index_page.get_layout()


if __name__ == '__main__':
    app.run_server(debug=True)
