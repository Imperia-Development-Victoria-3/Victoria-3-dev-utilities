import os
from data_formats import DataFormat
from parse_decoder import decode_dictionary


class ProductionMethods(DataFormat):
    prefixes = ["building_"]
    relative_file_location = os.path.normpath("common/production_methods")
    data_links = {"Technologies": ["unlocking_technologies"]}

    def __init__(self, game_folder: str, mod_folder: str, prefixes: list = None, link_data: list = None):
        if not prefixes:
            prefixes = ProductionMethods.prefixes
        else:
            prefixes += ProductionMethods.prefixes

        game_version = os.path.join(game_folder, ProductionMethods.relative_file_location)
        if mod_folder:
            mod_version = os.path.join(mod_folder, ProductionMethods.relative_file_location)
        else:
            mod_version = None
        super().__init__(game_version, mod_version, prefixes=prefixes)
        self.interpret()

        if link_data:
            for external_data in link_data:
                self.replace_at_path(ProductionMethods.data_links[type(external_data).__name__], external_data)

    def export_paradox(self):
        self.update_if_needed()

        for path, dictionary in self._mod_dictionary.items():
            folder_path = os.path.dirname(path)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            with open(path, 'w', encoding='utf-8-sig') as file:
                file.write(decode_dictionary(dictionary))


if __name__ == '__main__':
    import os
    from constants import Test
    from data_formats import Technologies

    technologies = Technologies(Test.game_directory, Test.mod_directory)
    production_methods = ProductionMethods(Test.game_directory, Test.mod_directory, link_data=[technologies])

    print("\nGAME FILES\n")
    for name, element in production_methods.items():
        if Test.game_directory in production_methods.data_refs[name]["_source"]:
            print(name, element)

    print("\nMOD FILES\n")
    for name, element in production_methods.items():
        if Test.mod_directory in production_methods.data_refs[name]["_source"]:
            print(name, element)
