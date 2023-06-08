from data_formats import DataFormat
import os


class PopNeeds(DataFormat):
    prefixes = ["popneed_"]
    relative_file_location = os.path.normpath("common/pop_needs")

    def __init__(self, game_folder: str, mod_folder: str, prefixes: list = None):
        if not prefixes:
            prefixes = PopNeeds.prefixes
        else:
            prefixes += PopNeeds.prefixes

        game_version = os.path.join(game_folder, PopNeeds.relative_file_location)
        mod_version = os.path.join(mod_folder, PopNeeds.relative_file_location)
        super().__init__(game_version, mod_version, prefixes=prefixes)
        self.interpret()


if __name__ == '__main__':
    import os
    from constants import Test

    pop_needs = PopNeeds(Test.game_directory, Test.mod_directory)
    print("\n GAME FILES \n")
    for name, element in pop_needs.items():
        if Test.game_directory in element["_source"]:
            print(name, element)

    print("\n MOD FILES \n")
    for name, element in pop_needs.items():
        if Test.mod_directory in element["_source"]:
            print(name, element)
