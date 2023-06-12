from pathlib import Path
import os


class Constants:
    # PARSER TYPES
    WORD_TYPE = 0
    EQUAL_TYPE = 1
    BEGIN_DICT_TYPE = 2
    END_DICT_TYPE = 3
    PART_LINE_COMMENT_TYPE = 4
    FULL_LINE_COMMENT_TYPE = 5
    ALL_COMMENT_TYPE = 6

    # PATHS


class Test:
    game_directory = os.path.normpath("C:/Program Files (x86)/Steam/steamapps/common/Victoria 3/game")
    mod_directory = os.path.join(Path.home(), os.path.normpath("Documents/Paradox Interactive/Victoria 3/mod/Victoria-3-Dev"))
