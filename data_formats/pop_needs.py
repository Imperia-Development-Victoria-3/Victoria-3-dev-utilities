from data_formats import DataFormat


class PopNeeds(DataFormat):
    prefixes = ["popneed_"]

    def __init__(self, dictionary):
        super().__init__(dictionary, PopNeeds.prefixes)
        self.interpret()
        self._transforms = {}


if __name__ == '__main__':
    from parse_encoder import parse_text_file
    from constants import Constants
    import os

    # Test the parsing function
    dictionary = parse_text_file(
        Constants.DEFAULT_GAME_PATH + os.path.normpath("\\common\\pop_needs\\00_pop_needs.txt"))
    pop_needs = PopNeeds(dictionary)
    print(list(pop_needs.get_iterable("default", return_path=True)))
