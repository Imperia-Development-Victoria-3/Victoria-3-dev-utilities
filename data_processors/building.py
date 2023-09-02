from .production_method_group import ProductionMethodGroup
from .production_method import ProductionMethod
from data_formats import Buildings
from data_utils import filter_and_score_objects, add_selected_object_line
from constants import BuildingDesignerConstants
import pandas as pd
from plotly import graph_objects as go
import numpy as np
from app import cache
import operator
from collections import defaultdict

from dash import dcc, html
import dash_bootstrap_components as dbc


class BuildingRegistry:
    ATTRIBUTE_FUNCTIONS = {}
    FILTER_FUNCTIONS = {}

    @classmethod
    def register_attribute(cls, config):
        if type(config) is not dict:
            raise ValueError("Missing config argument")

        def inner_decorator(func):
            cls.ATTRIBUTE_FUNCTIONS["_".join(func.__name__.split("_")[1:])] = {"function": func,
                                                                               "config": config}
            return func

        return inner_decorator

    @classmethod
    def register_filter(cls, func):
        cls.FILTER_FUNCTIONS["_".join(func.__name__.split("_")[1:])] = func
        return func


class Building:
    ATTRIBUTE_FUNCTIONS = BuildingRegistry.ATTRIBUTE_FUNCTIONS
    FILTER_FUNCTIONS = BuildingRegistry.FILTER_FUNCTIONS
    register_attribute = BuildingRegistry.register_attribute
    register_filter = BuildingRegistry.register_filter

    def __init__(self, raw_data):
        self._raw_data = raw_data
        self.production_method_groups = {}
        self.interpret()

    def interpret(self):
        for name, production_method_group in list(self._raw_data["production_method_groups"].items()):
            if isinstance(production_method_group, bool):
                print(f"WARNING: you failed to define {name} (which is silly), ignoring it for now")
                del self._raw_data["production_method_groups"][name]
                continue
            self.production_method_groups[name] = ProductionMethodGroup(name, production_method_group)

    def era_available(self, era_number):
        era_number = int(era_number.split('_')[-1])
        min_era = -1
        technologies = self._raw_data.get("unlocking_technologies", {})
        for technology in technologies.values():
            era = int(technology["era"]["_name"].split('_')[-1])
            if min_era < era:
                min_era = era

        if min_era <= era_number:
            return True
        else:
            return False

    def apply_era(self, era):
        number = int(era.split('_')[-1])
        for production_method_group in self.production_method_groups.values():
            production_method_group.apply_era(int(number))
        self.data = self.get_data()

    def get_data(self):
        datapoints = []
        for production_method_group in self.production_method_groups.values():
            datapoints += production_method_group.get_data()

        # Detects duplicate entries
        mergers = {}
        for i, datapoint_1 in enumerate(datapoints):
            for j in range(i + 1, len(datapoints)):
                datapoint_2 = datapoints[j]
                for key in datapoint_1.keys():
                    if not key == "Value" and not key == "Name":
                        if datapoint_1[key] != datapoint_2[key]:
                            break
                else:
                    if not mergers.get(j):
                        mergers[j] = i

        # Combine the duplicate entries by adding them together
        new_datapoints = {}
        for i, datapoint in enumerate(datapoints):
            index = mergers.get(i)
            if index:
                new_datapoints[index]["Value"] += datapoint["Value"]
            else:
                new_datapoints[i] = datapoints[i].copy()

        datapoints = list(new_datapoints.values())
        return datapoints

    @staticmethod
    def find_in_list_of_dicts(data, conditions):
        new_data = []
        for element in data:
            for key, value in conditions.items():
                if element[key] != value:
                    break
            else:
                new_data.append(element)
        return new_data

    @staticmethod
    def _calculate_attribute(data, value_type, level=1):
        result_add = defaultdict(int)
        result_mult = defaultdict(lambda: 1)

        data_type = Building.find_in_list_of_dicts(data,
                                                   {"ValueType": ProductionMethod.value_type_to_id[value_type]})
        for operation, operator_func in [(operator.add.__name__, operator.add), (operator.mul.__name__, operator.mul)]:
            for row in Building.find_in_list_of_dicts(data_type, {"Operation": operation}):
                name, value, scale = row["Name"], row["Value"], row["ScaleID"]
                price = float(cache.get("Goods")[name]["cost"]) if cache.get("Goods") and cache.get("Goods").get(
                    name) else 1

                if operation == operator.add.__name__:
                    if scale != ProductionMethod.scales_to_id["unscaled"]:
                        result_add[name] += price * value * level
                    else:
                        result_add[name] += price * value

                elif operation == operator.mul.__name__:
                    if scale != ProductionMethod.scales_to_id["unscaled"]:
                        result_mult[name] *= value * level
                    else:
                        result_mult[name] *= value

        total = sum(add_val * result_mult[key] for key, add_val in result_add.items())
        return total

    @register_attribute(BuildingDesignerConstants.ECONOMICS_CONFIG)
    def calc_profitability(self):
        profit = self.calc_profit()
        employees = self.calc_employees()
        if employees:
            return profit / employees
        else:
            return np.nan

    @register_attribute(BuildingDesignerConstants.ECONOMICS_CONFIG)
    def calc_profit(self, level=1):
        data = Building.find_in_list_of_dicts(self.data,
                                              {'ClassificationID': ProductionMethod.classification_to_id["economic"]})
        total_input_cost = self._calculate_attribute(data, "input", level)
        total_output_revenue = self._calculate_attribute(data, "output", level)
        profit = total_output_revenue - total_input_cost
        return profit

    @register_attribute(BuildingDesignerConstants.ECONOMICS_CONFIG)
    def calc_employees(self, level=1):
        data = Building.find_in_list_of_dicts(self.data, {"ValueType": ProductionMethod.value_type_to_id["workforce"]})
        return self._calculate_attribute(data, "workforce", level)

    @register_attribute(BuildingDesignerConstants.MILITARY_CONFIG)
    def calc_offense(self, level=1):
        data = Building.find_in_list_of_dicts(self.data,
                                              {"ClassificationID": ProductionMethod.classification_to_id["military"]})
        data = [datapoint for datapoint in data if "offense" in datapoint["ID"]]
        return self._calculate_attribute(data, "other", level)

    @register_attribute(BuildingDesignerConstants.MILITARY_CONFIG)
    def calc_defense(self, level=1):
        data = Building.find_in_list_of_dicts(self.data,
                                              {"ClassificationID": ProductionMethod.classification_to_id["military"]})
        data = [datapoint for datapoint in data if "defense" in datapoint["ID"]]
        return self._calculate_attribute(data, "other", level)

    @register_attribute(BuildingDesignerConstants.MILITARY_CONFIG)
    def calc_army_power_projection(self, level=1):
        data = Building.find_in_list_of_dicts(self.data,
                                              {"ClassificationID": ProductionMethod.classification_to_id["military"]})
        data = [datapoint for datapoint in data if "army_power_projection" in datapoint["ID"]]
        return self._calculate_attribute(data, "other", level)

    @register_attribute(BuildingDesignerConstants.MILITARY_CONFIG)
    def calc_navy_power_projection(self, level=1):
        data = Building.find_in_list_of_dicts(self.data,
                                              {"ClassificationID": ProductionMethod.classification_to_id["military"]})
        data = [datapoint for datapoint in data if "navy_power_projection" in datapoint["ID"]]
        return self._calculate_attribute(data, "other", level)

    @register_attribute(BuildingDesignerConstants.MILITARY_CONFIG)
    def calc_navy_power_projection_cost_efficiency(self, level=1):
        cost = self.calc_profit()
        if cost:
            return self.calc_navy_power_projection() / -cost
        else:
            return np.nan

    @register_attribute(BuildingDesignerConstants.MILITARY_CONFIG)
    def calc_army_power_projection_cost_efficiency(self, level=1):
        cost = self.calc_profit()
        if cost:
            return self.calc_army_power_projection() / -cost
        else:
            return np.nan



    @staticmethod
    def get_unique_values(data, keys):
        unique_values = {key: set() for key in keys}

        for entry in data:
            for key in keys:
                unique_values[key].add(entry[key])

        return unique_values

    def get_summary(self, production_methods):
        tabs = []

        for production_method_group, production_method in production_methods.items():
            self.production_method_groups[production_method_group].select(production_method)
        self.data = self.get_data()
        unique_values = Building.get_unique_values(self.data, ["ScopeID"])

        for scope_id in unique_values["ScopeID"]:
            scope_data = Building.find_in_list_of_dicts(self.data, {"ScopeID": scope_id})

            scales = []
            unique_scale_values = Building.get_unique_values(scope_data, ["ScaleID"])

            for scale_id in unique_scale_values["ScaleID"]:
                scale_data = Building.find_in_list_of_dicts(scope_data, {"ValueType": scale_id})
                modifiers = []

                unique_values = Building.get_unique_values(scale_data, ["ValueType"])

                for value_id in unique_values["ValueType"]:
                    value_data = Building.find_in_list_of_dicts(scale_data, {"ValueType": value_id})

                    add_data = Building.find_in_list_of_dicts(value_data, {"Operation": operator.add.__name__})
                    mul_data = Building.find_in_list_of_dicts(value_data, {"Operation": operator.mul.__name__})

                    for item in mul_data:
                        thing = Building.find_in_list_of_dicts(add_data, {"ID": item["ID"]})
                        if thing:
                            thing[0]["Value"] *= item["Value"]

                    # Assuming you want to create a column for each ValueType
                    for item in add_data:
                        name = item["Name"]
                        value = item["Value"]
                        result_value = value
                        modifiers.append(
                            html.Div([
                                html.Span(f'{name}: {result_value}')
                            ])
                        )

                    scales.append(
                        html.Div([
                            html.Button(f'{ProductionMethod.id_to_scales[scale_id]}',
                                        id={'type': 'scale-button', 'index': f'{scope_id}-{scale_id}-{value_id}'},
                                        className='expand-button'),
                            dbc.Collapse(
                                children=modifiers,
                                id={'type': 'scale-collapse', 'index': f'{scope_id}-{scale_id}-{value_id}'},
                                is_open=True
                            )
                        ])
                    )

            tabs.append(dcc.Tab(
                label=ProductionMethod.id_to_scopes[scope_id],
                children=scales
            ))

        return dcc.Tabs(tabs)

    @register_filter
    def is_commercial(self):
        is_commercial = False
        for production_method_group in self.production_method_groups.values():
            is_commercial |= production_method_group.is_commercial()
        return is_commercial

    @register_filter
    def is_military(self):
        is_military = False
        for production_method_group in self.production_method_groups.values():
            is_military |= production_method_group.is_military()
        return is_military

    @register_filter
    def is_unique(self):
        return bool(self._raw_data.get("unique"))

    @register_filter
    def is_expandable(self):
        return bool(self._raw_data.get("expandable", "yes") != "no")


class DashBuildings(Buildings):

    def __init__(self, game_folder: str, mod_folder: str, prefixes: list = None, link_data: list = None):
        super().__init__(game_folder, mod_folder, prefixes, link_data)
        self._buildings = {}
        self.make_elements()

    def reset_building(self, key):
        self._buildings[key] = Building(self.data[key])

    def make_elements(self):
        self._buildings = {name: Building(building) for name, building in self.data.items()}

    def get_plotly_plot(self, attribute, config, plot_type="Violin", selected_building: str = "",
                        eras: list = ["1", "2", "3", "4", "5"]):
        traces = []
        selected_data = {}

        for era in sorted(eras, key=lambda x: int(x.split("_")[-1])):
            data = filter_and_score_objects(self._buildings, "Building", attribute, era, config, Building.FILTER_FUNCTIONS)

            try:
                selected_index = data["Building"].index(selected_building)
            except ValueError:
                selected_index = None

            if selected_index:
                selected_data[era] = data[attribute][selected_index]

            dataframe = pd.DataFrame(data).sort_values(by=attribute)

            if plot_type == "Bar":
                colors = ['blue' if bld == selected_building else 'gray' for bld in dataframe['Building']]
                traces.append(go.Bar(name=f'Era {era} Buildings', x=dataframe['Building'], y=dataframe[attribute],
                                     marker_color=colors))
            elif plot_type == "Violin":
                traces.append(go.Violin(y=dataframe[attribute], name=f"All Buildings {era}", meanline_visible=True,
                                        fillcolor='gray'))

        fig = go.Figure(data=traces)
        if plot_type == "Violin" and selected_building:
            add_selected_object_line(fig, eras, selected_data)

        return fig
