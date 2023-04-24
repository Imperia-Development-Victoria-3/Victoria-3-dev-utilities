from parse_decoder import decode_dictionary
import pandas as pd
import plotly.express as px
import copy
from data_utils.transformation import Transform


class BuyPackages:

    def __init__(self, dictionary):
        self._dictionary = dictionary
        self._interpret_buy_packages(dictionary)

        self._transforms = {}

    def _interpret_buy_packages(self, dictionary):
        self._dictionary = dictionary
        dictionary = copy.deepcopy(dictionary)
        packages = [0] * len(dictionary)
        for key, value in dictionary.items():
            if type(key) == str:
                name, index = key.split("_")
                # just getting rid of the popneed qualifier as it is uninformative
                for key_2, value_2 in list(value["goods"].items()):
                    del value["goods"][key_2]
                    value["goods"]["_".join(key_2.split("_")[1:])] = value_2
                packages[int(index) - 1] = value

        self.keys = set()
        for item in packages:
            self.keys |= set(item.keys())
            self.keys |= set(item["goods"].keys())

        self.df = pd.json_normalize(packages, sep='.')
        self.df = self.df.applymap(float)

    def get_iterable(self, key):
        if key not in self.keys:
            error_message = "Invalid key for buy packages. You tried: \"" + key + "\" but the options are: " + str(
                self.keys)
            raise ValueError(error_message)

        filtered = self.df.filter(like=key, axis=1)
        for row in filtered.itertuples(index=False):
            yield row

    def update_value(self, key, index, value):
        if value:
            value = float(value)
        self.df.at[index, key] = value

    def export_paradox(self, path):
        tmp_transforms = self._transforms
        self._transforms = {}
        for function, query in tmp_transforms.values():
            self.apply_transformation(function, query)

        info_list = self.df.to_dict("records")
        for index, item in enumerate(info_list, 1):
            for key, value in item.items():
                if value == value:
                    if "goods" in key:
                        self._dictionary["wealth_" + str(index)]["goods"]["popneed_" + key.split(".")[-1]] = str(
                            round(value))
                    else:
                        self._dictionary["wealth_" + str(index)][key] = str(value)
                else:
                    try:
                        if "goods" in key:
                            del self._dictionary["wealth_" + str(index)]["goods"]["popneed_" + key.split(".")[-1]]
                        else:
                            del self._dictionary["wealth_" + str(index)][key]
                    except KeyError:
                        ""
        string = decode_dictionary(self._dictionary)
        with open(path, "w") as file:
            file.write(string)

        tmp_transforms = self._transforms
        self._transforms = {}
        for function, query in tmp_transforms.values():
            self.apply_transformation(function, query)

    def apply_transformation(self, transformation_function, query):
        transformation_function(self.df, "goods")
        name = transformation_function.__name__
        if "forward" in name:
            inverse_function = getattr(Transform, '_'.join(name.split('_')[:-1] + ["inverse"]))
        elif "inverse" in name:
            inverse_function = getattr(Transform, '_'.join(name.split('_')[:-1] + ["forward"]))

        if self._transforms.get(inverse_function.__name__):
            del self._transforms[inverse_function.__name__]
        else:
            self._transforms[inverse_function.__name__] = (inverse_function, query)

        print(self._transforms)

class DashBuyPackages(BuyPackages):

    def __init__(self, dictionary):
        super().__init__(dictionary)
        self.figure_traces = dict()

    def get_ploty_plot(self, query, plot_type):
        filtered = self.df.filter(like=query, axis=1)
        if "goods" in query:
            renamed = filtered.rename(columns=lambda x: x.replace('goods.', ''))
        else:
            renamed = filtered
        if plot_type == "lines":
            fig = px.line(renamed)
            fig.update_traces(mode="markers+lines", hovertemplate=None)
            fig.update_layout(hovermode="x unified", yaxis_type='log')
        elif plot_type == "area":
            fig = px.area(renamed, groupnorm='percent')
            fig.update_traces(mode="markers+lines", hovertemplate=None)
            fig.update_layout(hovermode="x unified")
        else:
            raise ValueError("invalid ")
        self.figure_traces = {trace.name: i for i, trace in enumerate(fig["data"])}
        return fig

    def patch_ploty_plot(self, cell, patched_figure, percentages=False):
        # if not percentages:
        data = self.df.filter(like=cell["column_id"], axis=1)
        for key, index in self.figure_traces.items():
            if key in cell["column_id"]:
                patched_figure["data"][index]["y"][cell["row"]] = data.iat[cell["row"], 0]


