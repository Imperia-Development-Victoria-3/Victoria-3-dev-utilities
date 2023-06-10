from data_formats import DataFormat
import os


class Technologies(DataFormat):
    relative_file_location = os.path.normpath("common/technology/technologies")

    def __init__(self, game_folder: str, mod_folder: str, prefixes: list = None):
        if not prefixes:
            prefixes = Technologies.prefixes
        else:
            prefixes += Technologies.prefixes

        game_version = os.path.join(game_folder, Technologies.relative_file_location)
        mod_version = os.path.join(mod_folder, Technologies.relative_file_location)
        super().__init__(game_version, mod_version, prefixes=prefixes)
        self.interpret()


if __name__ == '__main__':
    import os
    from constants import Test

    technologies = Technologies(Test.game_directory, Test.mod_directory)
    print("\n GAME FILES \n")
    for name, element in technologies.items():
        if Test.game_directory in technologies.data_refs[name]["_source"]:
            print(name, element)

    print("\n MOD FILES \n")
    for name, element in technologies.items():
        if Test.mod_directory in technologies.data_refs[name]["_source"]:
            print(name, element)

    print(technologies.game_folder)
