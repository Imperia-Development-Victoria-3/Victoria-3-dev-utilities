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
    DEFAULT_GAME_PATH = os.path.normpath("C:/Program Files (x86)/Steam/steamapps/common/Victoria 3/game")
    DEFAULT_MOD_PATH = home + os.path.normpath("/Documents/Paradox Interactive/Victoria 3/mod/Victoria-3-Dev")


class GlobalState:
    buy_packages = None
    goods = None
    pop_needs = None
    buildings_folder = None
    currently_selected_building = None
    currently_selected_game_folder = None

    @staticmethod
    def reset(cache: "Cache", force=False):
        from data_formats import Goods, PopNeeds, DashBuyPackages, BuildingGroups, BuildingsFolder, TechnologiesFolder, \
            ProductionMethodsFolder, ProductionMethodGroupsFolder
        from parse_encoder import parse_text_file
        from data_utils import Percentage

        # execute when folder has changed.
        if GlobalState.currently_selected_game_folder != Constants.DEFAULT_GAME_PATH or force:
            GlobalState.currently_selected_game_folder = Constants.DEFAULT_GAME_PATH
        else:
            return

        if not os.path.exists(GlobalState.currently_selected_game_folder):
            print(
                "please set a valid folder for your game files it is now: " + GlobalState.currently_selected_game_folder)
            return

        dictionary = parse_text_file(
            Constants.DEFAULT_GAME_PATH + os.path.normpath("/common/buy_packages/00_buy_packages.txt"))
        GlobalState.buy_packages = DashBuyPackages(dictionary)
        GlobalState.buy_packages.apply_transformation(Percentage("goods."))

        dictionary = parse_text_file(Constants.DEFAULT_GAME_PATH + os.path.normpath("/common/goods/00_goods.txt"))
        GlobalState.goods = Goods(dictionary)

        dictionary = parse_text_file(
            Constants.DEFAULT_GAME_PATH + os.path.normpath("/common/pop_needs/00_pop_needs.txt"))
        GlobalState.pop_needs = PopNeeds(dictionary)

        technologies_folder = TechnologiesFolder(
            Constants.DEFAULT_GAME_PATH + os.path.normpath("/common/technology/technologies"))
        production_method_folder = ProductionMethodsFolder(
            Constants.DEFAULT_GAME_PATH + os.path.normpath("/common/production_methods"), technologies_folder)

        production_method_groups_folder = ProductionMethodGroupsFolder(
            Constants.DEFAULT_GAME_PATH + os.path.normpath("/common/production_method_groups"),
            production_method_folder)

        dictionary = parse_text_file(
            Constants.DEFAULT_GAME_PATH + os.path.normpath("/common/building_groups/00_building_groups.txt"))
        buildings_groups = BuildingGroups(dictionary)
        GlobalState.buildings_folder = BuildingsFolder(
            Constants.DEFAULT_GAME_PATH + os.path.normpath("/common/buildings"),
            buildings_groups, production_method_groups_folder)
