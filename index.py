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
        args = {}
        if hasattr(cls, "data_links"):
            args["link_data"] = []
            for class_name, _ in cls.data_links.items():
                tmp_class = getattr(sys.modules[__name__], class_name)
                args["link_data"].append(get_or_create_data_format(tmp_class))

        args["game_folder"] = cache.get('game_directory')
        args["mod_folder"] = cache.get('mod_directory')
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
