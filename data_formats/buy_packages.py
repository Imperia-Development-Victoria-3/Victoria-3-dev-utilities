from dash.dash_table.Format import Format, Scheme, Trim
from dash.dash_table import FormatTemplate
from data_formats import DataFormat

from parse_decoder import decode_dictionary
import pandas as pd
import plotly.express as px
import os
from typing import Union
import numpy as np


class BuyPackages(DataFormat):
    prefixes = ["popneed_", "wealth_"]
    relative_file_location = os.path.normpath("common/buy_packages")

    def __init__(self, game_folder: str, mod_folder: str, prefixes: list = None):
        if not prefixes:
            prefixes = BuyPackages.prefixes
        else:
            prefixes += BuyPackages.prefixes

        game_version = os.path.join(game_folder, BuyPackages.relative_file_location)
        if mod_folder:
            mod_version = os.path.join(mod_folder, BuyPackages.relative_file_location)
        else:
            mod_version = None
        super().__init__(game_version, mod_version, prefixes=prefixes)

        self.data_frame = None
        self._transforms = dict()

        self.interpret()

    def interpret(self):
        super().interpret()

        tmp_data = DataFormat.copy_dict_with_string_keys(self.data, self._prefix_manager)

        packages = [{}] * len(tmp_data)
        for key, value in tmp_data.items():
            packages[int(key.split("_")[-1]) - 1] = value
        self.data_frame = pd.json_normalize(packages, sep='.')
        self.data_frame = self.data_frame.map(float)

    def update_value(self, key, index, value):
        if value:
            value = float(value)
        self.data_frame.at[index, key] = value

    def update_column(self, column_name, new_column):
        for i, value in enumerate(new_column):
            new_column[i] = float(value)
        self.data_frame[column_name] = new_column

    def export_paradox(self):
        for transform in sorted(self._transforms, key=lambda t: t.order):
            transform.apply(self.data_frame, reverse=True)

        info_list = self.data_frame.fillna(0)  # replacing Nans with 0
        for col in info_list.columns:
            if col.startswith("goods."):
                info_list[col] = info_list[col].astype(int)

        info_list = info_list.astype(str)
        info_list = info_list.replace("0", np.nan).to_dict("records")
        info_dict = {str(i + 1): value for i, value in enumerate(info_list)}
        for key, value in info_dict.items():
            info_dict[key] = self.inverse_json(value)

        self.data = DataFormat.copy_dict_with_string_keys_inverse(info_dict, self._prefix_manager)
        self.update_if_needed()

        for path, dictionary in self._mod_dictionary.items():
            folder_path = os.path.dirname(path)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            with open(path, 'w', encoding='utf-8-sig') as file:
                file.write(decode_dictionary(dictionary))

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

    @staticmethod
    def inverse_json(dataframe):
        out = {}
        for key, val in dataframe.items():
            parts = key.split('.')
            d = out
            for part in parts[:-1]:
                if part not in d:
                    d[part] = {}
                d = d[part]
            d[parts[-1]] = val
        return out


class DashBuyPackages(BuyPackages):

    def __init__(self, game_folder: str, mod_folder: str, prefixes: list = None):
        super().__init__(game_folder, mod_folder, prefixes)
        self.figure_traces = dict()

    def get_plotly_plot(self, query, plot_type):
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
            fig = px.area(renamed, groupnorm='percent', color_discrete_sequence=px.colors.qualitative.Alphabet)
            fig.update_traces(mode="markers+lines", hovertemplate=None)
            fig.update_layout(hovermode="x unified", xaxis_title="Wealth Level", yaxis_title="Consumption Percentage",
                              yaxis=dict(
                                  range=[0, 100]
                              ),
                              xaxis=dict(
                                  range=[0, 98]
                              ))
        else:
            raise ValueError("invalid ")
        self.figure_traces = {trace.name: i for i, trace in enumerate(fig["data"])}
        return fig

    def patch_plotly_plot_value(self, cell, patched_figure):
        # if not percentages:
        data = self.data_frame.filter(like=cell["column_id"], axis=1)
        for key, index in self.figure_traces.items():
            if key in cell["column_id"]:
                patched_figure["data"][index]["y"][cell["row"]] = data.iat[cell["row"], 0]

    def patch_plotly_plot_column(self, column_id, patched_figure):
        # if not percentages:
        data = self.data_frame.filter(like=column_id, axis=1)
        for key, index in self.figure_traces.items():
            if key in column_id:
                patched_figure["data"][index]["y"] = [value for value in data.to_dict()[column_id].values()]

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
