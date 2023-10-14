from collections import defaultdict
from dash.exceptions import PreventUpdate

import numpy as np


def filter_and_score_objects(objects, object_name, attribute, era, attribute_config, filter_functions):
    data = {object_name: [], attribute: []}
    filter_conditions = attribute_config["config"]
    for name, object in objects.items():
        for condition_name, truth_value in filter_conditions.items():
            condition_value = filter_functions[condition_name](object)
            if truth_value == "include":
                truth_value = True
            elif truth_value == "exclude":
                truth_value = False
            elif truth_value == "indifferent":
                continue

            if condition_name and condition_value != truth_value:
                break
        else:
            data[object_name].append(name)
            object.apply_era(era)
            data[attribute].append(attribute_config["function"](object))
    return data


def add_selected_object_line(fig, eras, selected_data):
    for i, era in enumerate(eras):
        if selected_data.get(era):
            value = selected_data[era]
            fig.add_shape(
                type="line",
                x0=i - 0.45,
                y0=value,
                x1=i + 0.45,
                y1=value,
                line=dict(color="Blue", width=2),
            )


def extract_active_cells_info(active_cells, data):
    columns = defaultdict(list)
    for cell in active_cells:
        columns[cell["column_id"]].append(cell["row"])

    for column_id, column in columns.items():
        min_row = min(column)
        max_row = max(column)
        min_row_value = data[min_row].get(column_id, None)
        max_row_value = data[max_row].get(column_id, None)
        yield column_id, min_row, max_row, min_row_value, max_row_value


def update_table_fill(n_clicks, active_cells, data, patched_table, fill_function):
    if n_clicks > 0:
        if not active_cells:
            raise PreventUpdate

    for column_id, min_row, max_row, min_row_value, max_row_value in extract_active_cells_info(active_cells, data):
        new_values = fill_function(min_row_value, max_row_value, min_row, max_row)
        for i, value in enumerate(new_values):
            patched_table[min_row + i][column_id] = value
    return patched_table


# Linear fill function
def linear_fill(min_value, max_value, min_row, max_row):
    return np.linspace(start=min_value, stop=max_value, num=max_row - min_row + 1)


# Exponential fill function
def exponential_fill(min_value, max_value, min_row, max_row):
    x = np.linspace(start=min_row, stop=max_row, num=max_row - min_row + 1)

    def find_exponential_constants(x1, y1, x2, y2):
        b = np.log(y2 / y1) / (x2 - x1)
        a = y1 / np.exp(b * x1)
        return a, b

    a, b = find_exponential_constants(min_row, min_value, max_row, max_value)
    return a * np.exp(b * x)
