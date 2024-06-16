from deepdiff.path import _path_to_elements


def set_nested_obj(obj, path_string, value):
    elements = _path_to_elements(path_string, root_element=None)
    for depth, (elem, action) in enumerate(elements):
        if depth == len(elements) - 1:
            obj[elem] = value
            return
        if action == 'GET':
            obj = obj[elem]
        elif action == 'GETATTR':
            obj = getattr(obj, elem)


def del_nested_obj(obj, path_string):
    elements = _path_to_elements(path_string, root_element=None)
    for depth, (elem, action) in enumerate(elements):
        if depth == len(elements) - 1:
            del obj[elem]
            return
        if action == 'GET':
            obj = obj[elem]
        elif action == 'GETATTR':
            obj = getattr(obj, elem)


def exclude_int_keys_callback(_, path_string):
    elements = _path_to_elements(path_string, root_element=None)
    return type(elements[-1][0]) == int if elements else False
