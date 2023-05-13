class BuildingGroup:
    default_alues = {
        "parent_group": "None",
        "always_possible": "no",
        "economy_of_scale": "no",
        "is_subsistence": "no",
        "default_building": "None",
        "lens": "None",
        "auto_place_buildings": "no",
        "capped_by_resources": "no",
        "discoverable_resource": "no",
        "depletable_resource": "no",
        "can_use_slaves": "no",
        "land_usage": None,
        "cash_reserves_max": "0",
        "inheritable_construction": "no",
        "stateregion_max_level": "no",
        "urbanization": "0",
        "should_auto_expand": {"should_auto_expand": {
            "default_auto_expand_rule": "yes"
        }},
        "hiring_rate": 0,
        "proportionality_limit": 0,
        "hires_unemployed_only": "no"
    }

    def __init__(self, *args, **kwargs):
        merged_dict = {}
        for arg in args:
            if isinstance(arg, dict):
                merged_dict.update(arg)

        merged_dict.update(kwargs)
        self.merged_dict = merged_dict
