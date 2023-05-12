from dash.dash_table.Format import Format, Scheme, Trim
from dash.dash_table import FormatTemplate

from parse_decoder import decode_dictionary
import pandas as pd
import plotly.express as px
import copy
from data_utils.transformation import Transform


class BuyPackages:

    def __init__(self, dictionary):
        self._dictionary = dictionary
        self._interpret_buy_packages(dictionary)

        self._transforms = dict()

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
        yield from filtered.itertuples(index=False)

    def update_value(self, key, index, value):
        if value:
            value = float(value)
        self.df.at[index, key] = value

    def export_paradox(self, path):

        for transform in sorted(self._transforms, key=lambda t: t.order):
            transform.apply(self.df, reverse=True)

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

        for transform in sorted(self._transforms, key=lambda t: t.order, reverse=True):
            transform.apply(self.df)

    def apply_transformation(self, transformation: Transform, forward=True):
        transformation.is_forward = forward
        if self._transforms.get(transformation):
            transformation = self._transforms[transformation]
            if forward == transformation.is_forward:
                raise Exception("Transformation already in desired state")
            else:
                self.remove_transformation(transformation)
        else:
            self.add_transformation(transformation)

    def remove_transformation(self, transformation: Transform):
        if not self._transforms.get(transformation):
            raise Exception("Transformation doesn't exist")

        for transform in sorted(self._transforms, key=lambda t: t.order):
            if transform.order < transformation.order:
                transform.apply(self.df, reverse=True)
            if transform == transformation:
                transform.apply(self.df, reverse=True)
                del self._transforms[transform]
                break

        for transform in sorted(self._transforms, key=lambda t: t.order, reverse=True):
            if transform.order < transformation.order:
                transform.apply(self.df)

    def add_transformation(self, transformation: Transform):
        if self._transforms.get(transformation):
            raise Exception("Transformation already exists")

        for transform in sorted(self._transforms, key=lambda t: t.order):
            if transform.order < transformation.order:
                transform.apply(self.df, reverse=True)
            else:
                transformation.apply(self.df)
                self._transforms[transformation] = transformation
                break
        else:
            transformation.apply(self.df)
            self._transforms[transformation] = transformation

        for transform in sorted(self._transforms, key=lambda t: t.order, reverse=True):
            if transform.order < transformation.order:
                transform.apply(self.df)


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

    def patch_ploty_plot(self, cell, patched_figure):
        # if not percentages:
        data = self.df.filter(like=cell["column_id"], axis=1)
        for key, index in self.figure_traces.items():
            if key in cell["column_id"]:
                patched_figure["data"][index]["y"][cell["row"]] = data.iat[cell["row"], 0]

    def get_table_formatting(self):
        if self.df.is_percentage:
            columns = []
            for name in self.df.columns:
                if "political" in name or "total" in name:
                    columns.append({"name": name, "id": name, "type": 'numeric',
                                    "format": Format(precision=2, scheme=Scheme.fixed, trim=Trim.yes)})
                else:
                    columns.append(
                        {"name": name, "id": name, "type": 'numeric', "format": FormatTemplate.percentage(2)})
        else:
            columns = [
                {"name": i, "id": i, "type": 'numeric',
                 "format": Format(precision=2, scheme=Scheme.fixed, trim=Trim.yes)}
                for i in self.df.columns]
        return columns
