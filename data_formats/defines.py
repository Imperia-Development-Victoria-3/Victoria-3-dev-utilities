class Defines:

    def __init__(self, dictionary : dict):
        self._defines = dictionary

    def __getitem__(self, key):
        return self._defines[key]

