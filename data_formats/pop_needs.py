from data_formats import DataFormat
import os


class PopNeeds(DataFormat):
    prefixes = ["popneed_"]
    relative_file_location = os.path.normpath("common/pop_needs")
    data_links = {"Goods": ["entry", "goods"]}

    def __init__(self, game_folder: str, mod_folder: str, prefixes: list = None, link_data: list = None):
        if not prefixes:
            prefixes = PopNeeds.prefixes
        else:
            prefixes += PopNeeds.prefixes

        game_version = os.path.join(game_folder, PopNeeds.relative_file_location)
        if mod_folder:
            mod_version = os.path.join(mod_folder, PopNeeds.relative_file_location)
        else:
            mod_version = None
        super().__init__(game_version, mod_version, prefixes=prefixes)
        self.interpret()

        if link_data:
            for external_data in link_data:
                self.replace_at_path(PopNeeds.data_links[type(external_data).__name__], external_data)


if __name__ == '__main__':
    import os
    from constants import Test
    from data_formats import Goods

    goods = Goods(Test.game_directory, Test.mod_directory)
    pop_needs = PopNeeds(Test.game_directory, Test.mod_directory, link_data=[goods])
    print("\n GAME FILES \n")
    for name, element in pop_needs.items():
        if Test.game_directory in pop_needs.data_refs[name]["_source"]:
            print(name, element)

    print("\n MOD FILES \n")
    for name, element in pop_needs.items():
        if Test.mod_directory in pop_needs.data_refs[name]["_source"]:
            print(name, element)
