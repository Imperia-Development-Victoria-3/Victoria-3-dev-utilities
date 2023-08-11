import dash
from flask_caching import Cache
import os
from pathlib import Path
import dash_bootstrap_components as dbc


app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server


class MyDict(dict):
    def set(self, key, value):
        self[key] = value


cache = MyDict()
# cache = Cache(app.server, config={
#     'CACHE_TYPE': 'simple'
#     # 'CACHE_TYPE': 'filesystem',
#     # 'CACHE_DIR': '.cache'
# })

cache.set("game_directory", os.path.normpath("C:/Program Files (x86)/Steam/steamapps/common/Victoria 3/game"))
cache.set("mod_directory", os.path.join(Path.home(), os.path.normpath("Documents/Paradox Interactive/Victoria 3/mod/Victoria-3-Dev")))
