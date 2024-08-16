from data_utils.transformation import Transform


class Percentage(Transform):
    order = 0

    def __init__(self, query: str, is_forward: bool = True):
        super().__init__(is_forward)
        self.query = query

    def forward(self, data):
        target_data = data.filter(like=self.query, axis=1)
        sums = target_data.sum(axis=1)
        percentages = target_data.div(sums, axis=0)
        data[percentages.columns] = percentages
        data.insert(0, self.query[:-1] + "-total", sums)

        if 'is_percentage' not in data._metadata:
            data._metadata += ['is_percentage']
        data.is_percentage = True

    def inverse(self, data):
        sums = data[self.query[:-1] + '-total']
        data.drop(self.query[:-1] + '-total', axis=1, inplace=True)
        target_data = data.filter(like=self.query, axis=1)
        numbers = target_data.multiply(sums, axis=0)
        data[numbers.columns] = numbers

        if 'is_percentage' not in data._metadata:
            data._metadata += ['is_percentage']
        data.is_percentage = False

    def __hash__(self):
        return hash(self.query)

    def __eq__(self, other):
        if isinstance(other, Percentage):
            return self.query == other.query
        return False
