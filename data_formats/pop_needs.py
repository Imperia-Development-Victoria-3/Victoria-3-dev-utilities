from data_formats import DataFormat


class PopNeeds(DataFormat):

    def __init__(self, dictionary):
        super().__init__(dictionary)
        self.interpret()
        self._transforms = {}

    def interpret(self):
        super().interpret()
        for name, need_group in list(self.data.items()):
            # just getting rid of the popneed qualifier as it is uninformative
            self.data["_".join(name.split("_")[1:])] = need_group
            del self.data[name]


if __name__ == '__main__':
    from parse_encoder import parse_text_file
    from constants import Constants
    import os

    # Test the parsing function
    dictionary = parse_text_file(
        Constants.DEFAULT_GAME_PATH + os.path.normpath("\\common\\pop_needs\\00_pop_needs.txt"))
    pop_needs = PopNeeds(dictionary)
    print(list(pop_needs.get_iterable("default", return_path=True)))
