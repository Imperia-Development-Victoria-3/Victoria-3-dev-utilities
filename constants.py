from pathlib import Path
import os
from copy import deepcopy


class Constants:
    # PARSER TYPES
    WORD_TYPE = 0
    EQUAL_TYPE = 1
    BEGIN_DICT_TYPE = 2
    END_DICT_TYPE = 3
    PART_LINE_COMMENT_TYPE = 4
    FULL_LINE_COMMENT_TYPE = 5
    ALL_COMMENT_TYPE = 6
    EQUAL_OR_GREATER_TYPE = 7
    EQUAL_OR_LESSER_TYPE = 8
    LESSER_TYPE = 9
    GREATER_TYPE = 10
    EQUAL_AND_EXISTS_TYPE = 11


class Test:
    game_directory = os.path.normpath("C:/Program Files (x86)/Steam/steamapps/common/Victoria 3/game")
    mod_directory = os.path.join(Path.home(),
                                 os.path.normpath("Documents/Paradox Interactive/Victoria 3/mod/Victoria-3-Dev"))


def update_and_return(d, update_dict):
    new_dict = deepcopy(d)
    new_dict.update(update_dict)
    return new_dict


class BuildingDesignerConstants:
    FILTER_TYPES = {
        "commercial"
        "military"
        "unique"
        "expandable"
    }

    BASE_CONFIG = {
        "unique": False,
        "expandable": True
    }

    ECONOMICS_CONFIG = update_and_return(BASE_CONFIG, {
        "commercial": True,
        "military": False
    })

    MILITARY_CONFIG = update_and_return(BASE_CONFIG, {
        "military": True
    })
