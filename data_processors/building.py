from .production_method_group import ProductionMethodGroup
from data_formats import Buildings
import pandas as pd
from plotly import graph_objects as go
import numpy as np


class Building:

    def __init__(self, raw_data):
        self.raw_data = raw_data
        self.production_method_groups = {}
        self.interpret()

    def interpret(self):
        for name, production_method_group in self.raw_data["production_method_groups"].items():
            self.production_method_groups[name] = ProductionMethodGroup(production_method_group)

    def apply_era(self, era):
        number = int(era.split('_')[-1])
        for production_method_group in self.production_method_groups.values():
            production_method_group.apply_era(int(number))

    def calc_profit(self):
        profit = 0
        for production_method_group in self.production_method_groups.values():
            profit += production_method_group.calc_profit()
        return profit

    def calc_total_employees(self):
        total_employees = 0
        for production_method_group in self.production_method_groups.values():
            total_employees += production_method_group.calc_total_employees()
        return total_employees

    def calc_profitability(self):
        profit = self.calc_profit()
        employees = self.calc_total_employees()
        if employees:
            return profit / employees
        else:
            return np.nan


class DashBuildings(Buildings):

    def __init__(self, game_folder: str, mod_folder: str, prefixes: list = None, link_data: list = None):
        super().__init__(game_folder, mod_folder, prefixes, link_data)
        self._buildings = {}
        self.make_elements()

    def make_elements(self):
        self._buildings = {name: Building(building) for name, building in self.data.items()}

    def get_plotly_plot(self, attribute, selected_building: str = "", era: str = "5"):

        if "profitability" == attribute:
            data = {"Building": [], "Profitability": []}
            for building_name, building_object in self._buildings.items():
                data["Building"].append(building_name)
                building_object.apply_era(era)
                data["Profitability"].append(building_object.calc_profitability())

            dataframe = pd.DataFrame(data)
            colors = ['blue' if bld == selected_building else 'gray' for bld in dataframe['Building']]
            dataframe = dataframe.sort_values(by='Profitability')
            return go.Figure(data=[
                go.Bar(name='Buildings', x=dataframe['Building'], y=dataframe['Profitability'], marker_color=colors)
            ])
        return []

        #     renamed = filtered.rename(columns=lambda x: x.replace('goods.', ''))
        # else:
        #     renamed = filtered
        # if plot_type == "lines":
        #     fig = px.line(renamed)
        #     fig.update_traces(mode="markers+lines", hovertemplate=None)
        #     fig.update_layout(hovermode="x unified", yaxis_type='log')
        # elif plot_type == "area":
        #     fig = px.area(renamed, groupnorm='percent')
        #     fig.update_traces(mode="markers+lines", hovertemplate=None)
        #     fig.update_layout(hovermode="x unified")
        # else:
        #     raise ValueError("invalid ")
        # self.figure_traces = {trace.name: i for i, trace in enumerate(fig["data"])}
        # return fig
