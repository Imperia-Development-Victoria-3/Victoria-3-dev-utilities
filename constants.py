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
    home = os.path.normpath(str(Path.home()))
    DEFAULT_GAME_PATH = os.path.normpath("C:\\Program Files (x86)\\Steam\\steamapps\\common\\Victoria 3\\game")
    DEFAULT_MOD_PATH = home + os.path.normpath("\\Documents\\Paradox Interactive\\Victoria 3\\mod\\Victoria-3-Dev")


class GlobalState:
    buy_packages = None
    goods = None
    pop_needs = None

    @staticmethod
    def reset():
        from data_formats import Goods, PopNeeds, DashBuyPackages
        from parse_encoder import parse_text_file
        from data_utils.transformation_types import Percentage

        dictionary = parse_text_file(
            Constants.DEFAULT_GAME_PATH + os.path.normpath("\\common\\buy_packages\\00_buy_packages.txt"))
        GlobalState.buy_packages = DashBuyPackages(dictionary)
        GlobalState.buy_packages.apply_transformation(Percentage("goods."))

        dictionary = parse_text_file(Constants.DEFAULT_GAME_PATH + os.path.normpath("\\common\\goods\\00_goods.txt"))
        GlobalState.goods = Goods(dictionary)

        dictionary = parse_text_file(
            Constants.DEFAULT_GAME_PATH + os.path.normpath("\\common\\pop_needs\\00_pop_needs.txt"))
        GlobalState.pop_needs = PopNeeds(dictionary)
