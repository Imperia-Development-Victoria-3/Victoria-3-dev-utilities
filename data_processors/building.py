from .production_method_group import ProductionMethodGroup
from data_formats import Buildings
import pandas as pd
from plotly import graph_objects as go
import numpy as np


class Building:

    def __init__(self, raw_data):
        self._raw_data = raw_data
        self.production_method_groups = {}
        self.interpret()

    def interpret(self):
        for name, production_method_group in self._raw_data["production_method_groups"].items():
            self.production_method_groups[name] = ProductionMethodGroup(production_method_group)

    def era_available(self, era_number):
        era_number = int(era_number.split('_')[-1])
        min_era = -1
        technologies = self._raw_data.get("unlocking_technologies", {})
        for technology in technologies.values():
            era = int(technology["era"].split('_')[-1])
            if min_era < era:
                min_era = era

        if min_era <= era_number:
            return True
        else:
            return False

    def is_commercial(self):
        is_commercial = False
        for production_method_group in self.production_method_groups.values():
            is_commercial |= production_method_group.is_commercial()
        return is_commercial

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

    def reset_building(self, key):
        self._buildings[key] = Building(self.data[key])

    def make_elements(self):
        self._buildings = {name: Building(building) for name, building in self.data.items()}


    def get_plotly_plot(self, attribute, plot_type="Violin", selected_building: str = "",
                        eras: list = ["1", "2", "3", "4", "5"], commercial_only: bool = True,
                        no_unique_buildings: bool = True):
        traces = []  # Holds the plot data for all eras
        selected_data = {}
        for era in eras:
            if "profitability" == attribute:
                data = {"Building": [], "Profitability": []}
                for building_name, building_object in self._buildings.items():

                    if ((not no_unique_buildings or (not building_object._raw_data.get(
                            "unique") and building_object._raw_data.get("expandable",
                                                                        "yes") != "no")) and building_object.era_available(
                        era) and (not commercial_only or building_object.is_commercial())):
                        data["Building"].append(building_name)
                        building_object.apply_era(era)
                        data["Profitability"].append(building_object.calc_profitability())
                    if building_name == selected_building and plot_type == "Violin" and building_object.era_available(
                        era):
                        if plot_type == "Violin":
                            building_object.apply_era(era)
                            selected_data[era] = {building_name: building_object.calc_profitability()}
                        elif plot_type == "Bar" and not data["Building"] == selected_building and building_object.era_available(
                        era):
                            data["Building"].append(building_name)
                            building_object.apply_era(era)
                            data["Profitability"].append(building_object.calc_profitability())

                dataframe = pd.DataFrame(data)
                dataframe = dataframe.sort_values(by='Profitability')  # Sort dataframe by 'Profitability'
                if plot_type == "Bar":
                    colors = ['blue' if bld == selected_building else 'gray' for bld in dataframe['Building']]
                    dataframe = dataframe.sort_values(by='Profitability')
                    traces.append(
                        go.Bar(name=f'Era {era} Buildings', x=dataframe['Building'], y=dataframe['Profitability'],
                               marker_color=colors))

                elif plot_type == "Violin":
                    # Create violin plot for all profitability data
                    trace_all = go.Violin(
                        y=dataframe['Profitability'],
                        name=f"All Buildings Era {era}",
                        meanline_visible=True,
                        fillcolor='gray',
                    )
                    traces.append(trace_all)

        fig = go.Figure(data=traces)
        if plot_type == "Violin" and selected_building:
            for i, era in enumerate(eras):
                if selected_data.get(str(i)):
                    value = \
                        [value for value in selected_data[str(i)].values()][0]
                    fig.add_shape(
                        type="line",
                        x0=i - 0.45,  # Adjust these values as necessary to match your plot's scale
                        y0=value,
                        x1=i + 0.45,  # Adjust these values as necessary to match your plot's scale
                        y1=value,
                        line=dict(
                            color="Blue",
                            width=2,
                        ),
                    )
        return fig
