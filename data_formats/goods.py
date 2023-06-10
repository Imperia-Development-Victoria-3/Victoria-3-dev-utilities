from data_formats import DataFormat
import os


class Goods(DataFormat):
    relative_file_location = os.path.normpath("common/goods")

    def __init__(self, game_folder: str, mod_folder: str, prefixes: list = None):
        if not prefixes:
            prefixes = Goods.prefixes
        else:
            prefixes += Goods.prefixes

        game_version = os.path.join(game_folder, Goods.relative_file_location)
        mod_version = os.path.join(mod_folder, Goods.relative_file_location)
        super().__init__(game_version, mod_version, prefixes=prefixes)
        self.interpret()


if __name__ == '__main__':
    import os
    from constants import Test

    goods = Goods(Test.game_directory, Test.mod_directory)
    print("\n GAME FILES \n")
    for name, element in goods.items():
        if Test.game_directory in goods.data_refs[name]["_source"]:
            print(name, element)

    print("\n MOD FILES \n")
    for name, element in goods.items():
        if Test.mod_directory in goods.data_refs[name]["_source"]:
            print(name, element)
