from multiprocessing import Queue, Process
from dash import dcc, html, Input, Output
from dash.exceptions import PreventUpdate
from tkinter import filedialog, Tk
from constants import Constants, GlobalState
import os

from app import app

layout = html.Div([
    html.H1('Welcome to the babylon dev tools'),
    html.H2('Please choose the application you want to go to:'),
    html.Div([
        dcc.Link('Go to Buy Package app', href='/apps/app_buy_packages.py'),
        html.Br(),
        dcc.Link('Go to Building Designer app', href='/apps/app_building_designer.py'),
    ]),
    html.Button('Select Game Folder', id='select-folder', n_clicks=0),
    html.Div(id='output-container-button', children=Constants.DEFAULT_GAME_PATH),
])


def select_folder(q):
    root = Tk()
    root.withdraw()
    directory = filedialog.askdirectory()
    q.put(directory)


@app.callback(Output('output-container-button', 'children'),
              Input('select-folder', 'n_clicks'))
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
        Constants.DEFAULT_GAME_PATH = path
        GlobalState.reset()
        return f'Selected folder: {path}'
    else:
        return f'Selected folder: {Constants.DEFAULT_GAME_PATH}'