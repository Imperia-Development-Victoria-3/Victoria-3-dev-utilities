import pandas as pd


class Transform:
    @staticmethod
    def percentage_forward(data, query_target):
        """
        Convert the values of the specified query_target columns to percentages of the row sum.

        @param data: The input DataFrame.
        @param query_target: A string used to filter columns in the DataFrame.
        @return: None. The input DataFrame is updated in-place.
        """
        target_data = data.filter(like=query_target, axis=1)
        sums = target_data.sum(axis=1)
        percentages = target_data.div(sums, axis=0)
        data[percentages.columns] = percentages
        data.insert(0, query_target[:-1] + "-total", sums)

        if 'is_percentage' not in data._metadata:
            data._metadata += ['is_percentage']
        data.is_percentage = True

    @staticmethod
    def percentage_inverse(data, query_target):
        """
        Convert the values of the specified query_target columns from percentages back to their original values.

        @param data: The input DataFrame with percentage values.
        @param query_target: A string used to filter columns in the DataFrame.
        @return: None. The input DataFrame is updated in-place.
        """
        sums = data[query_target[:-1] + '-total']
        data.drop(query_target[:-1] + '-total', axis=1, inplace=True)
        target_data = data.filter(like=query_target, axis=1)
        numbers = target_data.multiply(sums, axis=0)
        data[numbers.columns] = numbers

        if 'is_percentage' not in data._metadata:
            data._metadata += ['is_percentage']
        data.is_percentage = False

    @staticmethod
    def normalize(data, query_target):
        """
        Normalize the values of the specified query_target columns in the DataFrame.

        @param data: The input DataFrame.
        @param query_target: A string used to filter columns in the DataFrame.
        @return: None. The input DataFrame is updated in-place.
        """
        target_data = data.filter(like=query_target, axis=1)
        sums = target_data.sum(axis=1)
        percentages = target_data.div(sums, axis=0).mul(100)
        data[percentages.columns] = percentages
