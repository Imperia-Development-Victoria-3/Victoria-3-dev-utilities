from dash.dash_table.Format import Format, Scheme, Trim
from dash.dash_table import FormatTemplate
from data_formats import DataFormat, DataFormatFolder

from parse_decoder import decode_dictionary
import pandas as pd
import plotly.express as px
import os
from typing import Union


class BuyPackages(DataFormat):
    prefixes = ["popneed_", "wealth_"]
    relative_file_location = os.path.normpath("common/buy_packages/00_buy_packages.txt")

    def __init__(self, data: Union[dict, str]):
        super().__init__(data, BuyPackages.prefixes)
        self.data_frame = None

        self.interpret()
        self._transforms = dict()

    def interpret(self):
        super().interpret()

        packages = [0] * len(self.data)
        for key, value in self.data.items():
            packages[int(key) - 1] = value

        self.data_frame = pd.json_normalize(packages, sep='.')
        self.data_frame = self.data_frame.applymap(float)

    def update_value(self, key, index, value):
        if value:
            value = float(value)
        self.data_frame.at[index, key] = value

    def update_column(self, column_name, new_column):
        for i, value in enumerate(new_column):
            new_column[i] = float(value)
        self.data_frame[column_name] = new_column

    def export_paradox(self, path):
        for transform in sorted(self._transforms, key=lambda t: t.order):
            transform.apply(self.data_frame, reverse=True)

        info_list = self.data_frame.to_dict("records")
        self.update_dict_with_string_keys(info_list, self._prefix_manager)

        string = decode_dictionary(self._dictionary)
        with open(path, "w") as file:
            file.write(string)

        for transform in sorted(self._transforms, key=lambda t: t.order, reverse=True):
            transform.apply(self.data_frame)

    def apply_transformation(self, transformation: "Transform", forward=True):
        transformation.is_forward = forward
        if self._transforms.get(transformation):
            transformation = self._transforms[transformation]
            if forward == transformation.is_forward:
                raise Exception("Transformation already in desired state")
            else:
                self.remove_transformation(transformation)
        else:
            self.add_transformation(transformation)

    def remove_transformation(self, transformation: "Transform"):
        if not self._transforms.get(transformation):
            raise Exception("Transformation doesn't exist")

        for transform in sorted(self._transforms, key=lambda t: t.order):
            if transform.order < transformation.order:
                transform.apply(self.data_frame, reverse=True)
            if transform == transformation:
                transform.apply(self.data_frame, reverse=True)
                del self._transforms[transform]
                break

        for transform in sorted(self._transforms, key=lambda t: t.order, reverse=True):
            if transform.order < transformation.order:
                transform.apply(self.data_frame)

    def add_transformation(self, transformation: "Transform"):
        if self._transforms.get(transformation):
            raise Exception("Transformation already exists")

        for transform in sorted(self._transforms, key=lambda t: t.order):
            if transform.order < transformation.order:
                transform.apply(self.data_frame, reverse=True)
            else:
                transformation.apply(self.data_frame)
                self._transforms[transformation] = transformation
                break
        else:
            transformation.apply(self.data_frame)
            self._transforms[transformation] = transformation

        for transform in sorted(self._transforms, key=lambda t: t.order, reverse=True):
            if transform.order < transformation.order:
                transform.apply(self.data_frame)


class DashBuyPackages(BuyPackages):

    def __init__(self, data: Union[dict, str]):
        super().__init__(data)
        self.figure_traces = dict()

    def get_ploty_plot(self, query, plot_type):
        filtered = self.data_frame.filter(like=query, axis=1)
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

    def patch_ploty_plot_value(self, cell, patched_figure):
        # if not percentages:
        data = self.data_frame.filter(like=cell["column_id"], axis=1)
        for key, index in self.figure_traces.items():
            if key in cell["column_id"]:
                patched_figure["data"][index]["y"][cell["row"]] = data.iat[cell["row"], 0]

    def patch_ploty_plot_column(self, column_id, patched_figure):
        # if not percentages:
        data = self.data_frame.filter(like=column_id, axis=1)
        print(data, data.to_dict())
        for key, index in self.figure_traces.items():
            if key in column_id:
                patched_figure["data"][index]["y"] = [value for value in data.to_dict()[column_id].values() ]

    def get_table_formatting(self):
        if hasattr(self.data_frame, "is_percentage") and self.data_frame.is_percentage:
            columns = []
            for name in self.data_frame.columns:
                if "political" in name or "total" in name:
                    columns.append({"name": name, "id": name, "selectable": True, "type": 'numeric',
                                    "format": Format(precision=2, scheme=Scheme.fixed, trim=Trim.yes)})
                else:
                    columns.append(
                        {"name": name, "id": name, "selectable": True, "type": 'numeric',
                         "format": FormatTemplate.percentage(2)})
        else:
            columns = [
                {"name": i, "id": i, "selectable": True, "type": 'numeric',
                 "format": Format(precision=2, scheme=Scheme.fixed, trim=Trim.yes)}
                for i in self.data_frame.columns]
        return columns
