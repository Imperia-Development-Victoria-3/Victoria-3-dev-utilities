import numpy as np
import plotly.graph_objs as go
from parse_decoder import decode_dictionary
import copy


class BuyPackages:

    def __init__(self, dictionary):
        self._dictionary = dictionary
        self._intepret_buy_packages(dictionary)
        self._construct_arrays()

    def _intepret_buy_packages(self, dictionary):
        self.packages = [0] * len(dictionary)
        for key, value in dictionary.items():
            if type(key) == str:
                name, index = key.split("_")

                # just getting rid of the popneed qualifier as it is uninformative
                for key_2, value_2 in list(value["goods"].items()):
                    del value["goods"][key_2]
                    value["goods"]["_".join(key_2.split("_")[1:])] = value_2
                self.packages[int(index) - 1] = value

        self.keys = set()
        for key, value in dictionary.items():
            if type(key) == str:
                self.keys |= set(value.keys())
                self.keys |= set(value["goods"].keys())

    def _construct_arrays(self):
        self.arrays = {}
        for key in self.keys:
            if key != "goods":
                self.arrays[key] = np.array(list(self.get_iterable(key)))

        goods_matrix = np.zeros([len(self.keys) - 2, len(self.packages)])
        index = 0
        for key in self.keys:
            if key != "goods" and key != "political_strength":
                goods_matrix[index] = np.array(list(self.get_iterable(key)))
                index += 1
        self.arrays["goods"] = goods_matrix

    def get_percentages(self):
        goods_matrix = self.arrays["goods"]
        return goods_matrix / np.sum(goods_matrix, axis=0)

    def get_iterable(self, key):
        if key not in self.keys:
            error_message = "Invalid key for buy packages. You tried: \"" + key + "\" but the options are: " + str(
                self.keys)
            raise ValueError(error_message)

        if key == "political_strength" or key == "goods":
            for item in self.packages:
                if key == "political_strength":
                    yield float(item[key])
                else:
                    yield item[key]
        else:
            for item in self.packages:
                yield float(item["goods"].get(key, 0))

    def get_array(self, key):
        return self.arrays[key]

    def update_value(self, key, index, value):
        if key == "political_strength" or key == "goods":
            if value:
                self.packages[index][key] = value
            else:
                if self.packages[index].get(key):
                    del self.packages[index][key]
        else:
            if value:
                self.packages[index]["goods"][key] = value
            else:
                if self.packages[index].get(key):
                    del self.packages[index][key]

        self._construct_arrays()

    def export_paradox(self, path):
        print(self._dictionary["wealth_1"])
        dictionary = copy.deepcopy(self._dictionary)
        packages = copy.deepcopy(self.packages)
        for index, value in enumerate(packages, 1):
            for key_2, value_2 in list(value["goods"].items()):
                del value["goods"][key_2]
                value["goods"]["popneed_" + key_2] = value_2
            dictionary["wealth_" + str(index)] = value

        string = decode_dictionary(dictionary)
        with open(path, "w") as file:
            file.write(string)


class DashBuyPackages(BuyPackages):

    def __init__(self, dictionary):
        super().__init__(dictionary)

    def get_formatted_keys(self):
        columns = []
        for key in self.keys:
            if key != "goods" and key != "political_strength":
                columns.append({"name": key, "id": key})
        return columns

    def get_formatted_goods_data(self):
        return list(self.get_iterable("goods"))

    # def get_formmatted_goods_percentage_data(self):
    #     data = []
    #     percentage_matrix = self.get_percentages()
    #     index = 0
    #     for key in self.keys:
    #         if key != "goods" and key != "political_strength":
    #             data.append({key : percentage_matrix[index]})
    #             index += 1
    #     return data

    def get_ploty_plot(self, percentages=False):
        x = np.linspace(1, 99, 99)
        if not percentages:
            traces = []
            for key in self.keys:
                if key != "goods" and key != "political_strength":
                    trace = go.Scatter(x=x, y=self.get_array(key), mode='markers+lines', name=key)
                    traces.append(trace)
            layout = go.Layout(title='Buy Packages', yaxis_type='log', legend=dict(x=0, y=1), dragmode='lasso')
            fig = go.Figure(data=traces, layout=layout)
        else:
            traces = []
            percentage_matrix = self.get_percentages()
            index = 0
            for key in self.keys:
                if key != "goods" and key != "political_strength":
                    trace = go.Scatter(x=x, y=self.get_array(key), name=key, stackgroup='one', groupnorm='percent',
                                       hoveron='points+fills', hoverinfo='text+x+y')
                    traces.append(trace)
                    index += 1
            layout = go.Layout(title='Buy Packages', legend=dict(x=0, y=1), dragmode='lasso')
            fig = go.Figure(data=traces, layout=layout)
        return fig

    def patch_ploty_plot(self, cell, patched_figure, percentages=False):
        # if not percentages:
        patched_figure["data"][cell["column"]]["y"][cell["row"]] = self.packages[cell["row"]]["goods"].get(
            cell["column_id"])
        # else:
        #     percentage_matrix = self.get_percentages()
        #     print(percentage_matrix.shape)
        #     print(percentage_matrix[:, :3])
        #     index = 0
        #     for key in self.keys:
        #         if key != "goods" and key != "political_strength":
        #             patched_figure["data"][index]["y"][cell["row"]] = percentage_matrix[index, cell["row"]]
        #             index += 1
