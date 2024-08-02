from data_formats import DataFormat
import os


class Eras(DataFormat):
    prefixes = ["era"]
    relative_file_location = os.path.normpath("common/technology/eras")

    def __init__(self, game_folder: str, mod_folder: str, prefixes: list = None):
        if not prefixes:
            prefixes = Eras.prefixes
        else:
            prefixes += Eras.prefixes

        game_version = os.path.join(game_folder, Eras.relative_file_location)
        if mod_folder:
            mod_version = os.path.join(mod_folder, Eras.relative_file_location)
        else:
            mod_version = None
        super().__init__(game_version, mod_version, prefixes=prefixes)
        self.interpret()


if __name__ == '__main__':
    import os
    from constants import Test

    eras = Eras(Test.game_directory, Test.mod_directory)
    print("\n GAME FILES \n")
    for name, element in eras.items():
        if Test.game_directory in eras.data_refs[name]["_source"]:
            print(name, element)

    print("\n MOD FILES \n")
    for name, element in eras.items():
        if Test.mod_directory in eras.data_refs[name]["_source"]:
            print(name, element)
