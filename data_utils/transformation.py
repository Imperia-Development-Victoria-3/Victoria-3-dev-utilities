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


if __name__ == '__main__':
    ""
