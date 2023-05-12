class TransformNoInverse:
    @staticmethod
    def normalize(data, query_target):
        target_data = data.filter(like=query_target, axis=1)
        sums = target_data.sum(axis=1)
        percentages = target_data.div(sums, axis=0)
        data[percentages.columns] = percentages


class Transform:
    order = None

    def __init__(self, is_forward: bool = True):
        self.is_forward = is_forward

    def apply(self, data, reverse: bool = False):
        if (self.is_forward and not reverse) or (not self.is_forward and reverse):
            self.forward(data)
        else:
            self.inverse(data)

    def forward(self, data):
        pass

    def inverse(self, data):
        pass

    def __hash__(self):
        pass

    def __eq__(self, other):
        pass


class PriceCompensation(Transform):
    order = 1
    from data_formats import Goods
    from data_formats import PopNeeds

    def __init__(self, goods: Goods, needs: PopNeeds, is_forward: bool = True):
        super().__init__(is_forward)
        self.goods = goods
        self.needs = needs

        self.need_to_good = {path[-1]: good for good, path in needs.get_iterable("default", return_path=True)}

    def forward(self, data):
        for column in data.columns:
            original_name = column.split(".")[-1]
            if self.need_to_good.get(original_name):
                good = self.need_to_good[original_name]
                price = float(self.goods[good]["cost"])
                data[column] = data[column].multiply(price)


    def inverse(self, data):
        for column in data.columns:
            original_name = column.split(".")[-1]
            if self.need_to_good.get(original_name):
                good = self.need_to_good[original_name]
                price = float(self.goods[good]["cost"])
                data[column] = data[column].div(price)

    def __hash__(self):
        return hash(tuple(sorted([(self.goods[value]["cost"], key) for key, value in self.need_to_good.items()])))

    def __eq__(self, other):
        if isinstance(other, PriceCompensation):
            return tuple(sorted([(self.goods[value]["cost"], key) for key, value in self.need_to_good.items()])) == tuple(
                sorted([(self.goods[value]["cost"], key) for key, value in self.need_to_good.items()]))
        return False


class Percentage(Transform):
    order = 0

    def __init__(self, query, is_forward: bool = True):
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


if __name__ == '__main__':
    ""
