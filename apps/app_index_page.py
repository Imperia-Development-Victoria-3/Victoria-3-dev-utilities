from multiprocessing import Queue, Process
from dash import dcc, html, Input, Output
from dash.exceptions import PreventUpdate
from tkinter import filedialog, Tk
import os

from app import app, cache


def get_layout():
    return html.Div([
        html.H1('Welcome to the babylon dev tools'),
        html.H2('Please choose the application you want to go to:'),
        html.Div([
            dcc.Link('Go to Buy Package app', href='/apps/app_buy_packages.py'),
            html.Br(),
            dcc.Link('Go to Building Designer app', href='/apps/app_building_designer.py'),
        ]),
        html.H2('Check if the folders are correct:'),
        html.Button('Select Game Folder', id='select-folder-game', n_clicks=0),
        html.Div(id='output-select-folder-game', children=f'Selected folder: {cache.get("game_directory")}'),
        html.Button('Select Mod Folder', id='select-folder-mod', n_clicks=0),
        html.Div(id='output-select-folder-mod', children=f'Selected folder: {cache.get("mod_directory")}'),
    ])


def select_folder(q):
    root = Tk()
    root.withdraw()
    directory = filedialog.askdirectory()
    q.put(directory)


@app.callback(Output('output-select-folder-game', 'children'),
              Input('select-folder-game', 'n_clicks'),
              prevent_initial_call=True)
def select_folder_path(n_clicks):
    if n_clicks < 1:
        raise PreventUpdate
    q = Queue()
    p = Process(target=select_folder, args=(q,))
    p.start()
    p.join()
    path = q.get()
    if path:
        path = os.path.normpath(path)
        if path != cache.get("game_directory"):
            tmp_mod_directory = cache.get("game_mod_directory", path)
            cache.clear()
            cache.set("game_directory", path)
            cache.set("mod_directory", tmp_mod_directory)
        return f'Selected folder: {path}'
    else:
        return f'Selected folder: {cache.get("game_directory")}'


@app.callback(Output('output-select-folder-mod', 'children'),
              Input('select-folder-mod', 'n_clicks'),
              prevent_initial_call=True)
def select_folder_path(n_clicks):
    if n_clicks < 1:
        raise PreventUpdate
    q = Queue()
    p = Process(target=select_folder, args=(q,))
    p.start()
    p.join()
    path = q.get()
    if path:
        path = os.path.normpath(path)
        if path != cache.get("mod_directory"):
            tmp_game_directory = cache.get("game_directory", path)
            cache.clear()
            cache.set("mod_directory", path)
            cache.set("game_directory", tmp_game_directory)
            return f'Selected folder: {path}'
        else:
            return f'Selected folder: {cache.get("mod_directory")}'
