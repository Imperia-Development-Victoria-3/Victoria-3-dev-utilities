import dash
# from flask_caching import Cache
from config import *
import os
from pathlib import Path
import dash_bootstrap_components as dbc

app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server


class MyDict(dict):
    def set(self, key, value):
        self[key] = value


config = load_configurations()
if not config:
    def first_valid_path(paths):
        for path in paths:
            path = os.path.normpath(path)
            if os.path.exists(path):
                return path
        return None


    # Example usage:
    game_folder_paths = [
        "C:/Program Files (x86)/Steam/steamapps/common/Victoria 3/game/",
        "D:/Steam Library/steamapps/common/Victoria 3/game/",
        "E:/Steam Library/steamapps/common/Victoria 3/game/",
        "F:/Steam Library/steamapps/common/Victoria 3/game/",
        "G:/Steam Library/steamapps/common/Victoria 3/game/",
        "H:/Steam Library/steamapps/common/Victoria 3/game/",
        "I:/Steam Library/steamapps/common/Victoria 3/game/",
        "J:/Steam Library/steamapps/common/Victoria 3/game/",
        "K:/Steam Library/steamapps/common/Victoria 3/game/",
        os.path.join(Path.home(), os.path.normpath(".steam/steam/SteamApps/common/Victoria 3/game/")),
        os.path.join(Path.home(), os.path.normpath(".local/share/Steam/common/Victoria 3/game/")),
        os.path.join(Path.home(), os.path.normpath(".steam/debian-installation/steamapps/common/Victoria 3/game/"))]

    mod_folders_paths = [
        os.path.join(Path.home(), os.path.normpath("Documents/Paradox Interactive/Victoria 3/mod/Victoria-3-Dev")),
        os.path.join(Path.home(), os.path.normpath(".local/share/Paradox Interactive/Victoria 3/mod/Victoria-3-Dev"))
    ]

    config = {
        "game_directory": first_valid_path(game_folder_paths),
        "mod_directory": first_valid_path(mod_folders_paths)
    }

cache = MyDict()

cache.set("game_directory", config["game_directory"])
cache.set("mod_directory", config["mod_directory"])

# cache = Cache(app.server, config={
#     'CACHE_TYPE': 'simple'
#     # 'CACHE_TYPE': 'filesystem',
#     # 'CACHE_DIR': '.cache'
# })
