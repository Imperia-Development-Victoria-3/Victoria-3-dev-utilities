def filter_and_score_objects(objects, object_name, attribute, era, attribute_config, filter_functions):
    data = {object_name: [], attribute: []}
    filter_conditions = attribute_config["config"]
    for name, object in objects.items():
        for condition_name, truth_value in filter_conditions.items():
            if condition_name and filter_functions[condition_name](object) != truth_value:
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
