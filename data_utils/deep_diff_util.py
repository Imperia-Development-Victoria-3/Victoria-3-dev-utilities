from deepdiff import path


def set_nested_obj(obj, path_string, value):
    elements = path._path_to_elements(path_string, root_element=None)
    for depth, (elem, action) in enumerate(elements):
        if depth == len(elements) - 1:
            obj[elem] = value
            return
        if action == 'GET':
            obj = obj[elem]
        elif action == 'GETATTR':
            obj = getattr(obj, elem)


def _is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def exclude_int_keys_callback(_, path_string):
    elements = path._path_to_elements(path_string, root_element=None)
    return type(elements[-1][0]) == int if elements else False
