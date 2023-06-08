import dash
from flask_caching import Cache
import os
from pathlib import Path

app = dash.Dash(__name__, suppress_callback_exceptions=True)
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

home = os.path.normpath(str(Path.home()))
DEFAULT_MOD_PATH = home + os.path.normpath("/Documents/Paradox Interactive/Victoria 3/mod/Victoria-3-Dev")
cache.set("mod_directory", os.path.normpath(DEFAULT_MOD_PATH))
