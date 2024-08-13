from collections import namedtuple
from typing import Callable, List

from victoria_script_parses import ParseTypes

reconstruction_functions: List[Callable] = [Callable] * len(ParseTypes)
State = namedtuple('State', ['level', 'no_new_lines', 'after_end_of_object', 'after_last_object', 'currently_no_newlines_in_list', 'item_count_object'])


def register_reconstruction_function(func):
    # Get the function name, convert it to upper case to match the enum member
    func_name = func.__name__.upper()
    func_name = "_".join(func_name.split("_")[1:])
    try:
        # Match the function name with the ParseTypes enum
        parse_type = ParseTypes[func_name]
        # Register the function in the appropriate position in the list
        reconstruction_functions[parse_type - 1] = func
    except KeyError:
        raise ValueError(f"No matching ParseTypes member for function name: {func_name}")
    return func


def create_tabs(state):
    if not state.no_new_lines:
        return "\t" * state.level
    else:
        return ""


@register_reconstruction_function
def reconstruct_list(element, state, config, function):
    final_list = element[1]
    currently_no_newlines_in_list = True
    if config["force_single_line_until_item_count"] is not None or config[
        "force_multi_line_from_item_count"] is not None:
        count = 0
        for e in element[1]:
            if e[0] != ParseTypes.NEW_LINE and e[0] != ParseTypes.DOUBLE_NEWLINE:
                count += 1
            else:
                currently_no_newlines_in_list = False

    if config["force_single_line_until_item_count"] is not None and count <= config[
        "force_single_line_until_item_count"]:
        final_list = [e for e in element[1] if e[0] != ParseTypes.NEW_LINE and e[0] != ParseTypes.DOUBLE_NEWLINE]
        new_final_list = []
        for e in final_list:
            new_final_list.append(e)
            if e[0] == ParseTypes.FULL_LINE_COMMENT or e[0] == ParseTypes.COMMENT:
                new_final_list.append((ParseTypes.NEW_LINE, "\n"))
        final_list = new_final_list

    elif config["force_multi_line_from_item_count"] is not None and count > config["force_multi_line_from_item_count"]:
        final_list = [(ParseTypes.NEW_LINE, "\n"), element[1][0]] if state.level > 0 and not (
                element[1][0][0] == ParseTypes.NEW_LINE or element[1][0][0] == ParseTypes.DOUBLE_NEWLINE or
                element[1][0][0] == ParseTypes.FULL_LINE_COMMENT) else [element[1][0]]
        for i, e in enumerate(element[1][1:], start=1):
            if not (element[1][i - 1][0] == ParseTypes.NEW_LINE or element[1][i - 1][0] == ParseTypes.DOUBLE_NEWLINE or
                    element[1][i - 1][0] == ParseTypes.FULL_LINE_COMMENT) and not (
                    element[1][i][0] == ParseTypes.NEW_LINE or element[1][i][0] == ParseTypes.DOUBLE_NEWLINE or
                    element[1][i][0] == ParseTypes.FULL_LINE_COMMENT):
                final_list.append((ParseTypes.NEW_LINE, "\n"))
            final_list.append(e)
        if not (final_list[-1][0] == ParseTypes.NEW_LINE or final_list[-1][0] == ParseTypes.DOUBLE_NEWLINE or
                final_list[-1][0] == ParseTypes.FULL_LINE_COMMENT):
            final_list.append((ParseTypes.NEW_LINE, "\n"))

    if not final_list:
        return ""


    default_no_new_lines = not (final_list[0][0] == ParseTypes.NEW_LINE or final_list[0][
        0] == ParseTypes.DOUBLE_NEWLINE or final_list[0][0] == ParseTypes.FULL_LINE_COMMENT) and state.level > 0

    new_state = state._replace(no_new_lines=default_no_new_lines, currently_no_newlines_in_list=currently_no_newlines_in_list)
    string = ""
    if new_state.no_new_lines:
        string += " "

    for i, item in enumerate(final_list):
        if item[0] == ParseTypes.ASSIGNMENT and item[3][0] == ParseTypes.OBJECT and item[3][2]:
            count = 0
            for e in item[3][2][1]:
                if e[0] != ParseTypes.NEW_LINE and e[0] != ParseTypes.DOUBLE_NEWLINE:
                    count += 1
            new_state = new_state._replace(item_count_object=count)

        string += f"{function(item, state=new_state, config=config)}"

        if new_state.no_new_lines:
            string += " "

        # Objects after Objects should have a whitespace between them
        if len(item) > 3 and item[3][0] == ParseTypes.OBJECT and len(final_list) > i + 2 and len(
                final_list[i + 2]) > 3 and final_list[i + 2][3][0] == ParseTypes.OBJECT:
            if config["force_single_line_until_item_count"] and count <= config["force_single_line_until_item_count"]:
                newline = False
            else:
                newline = True
            new_state = new_state._replace(after_end_of_object=newline, after_last_object=i >= (len(final_list) - 2))
        else:
            new_state = new_state._replace(after_end_of_object=False, after_last_object=False)

    return string


@register_reconstruction_function
def reconstruct_assignment(element, state, config, function):
    tabs = create_tabs(state)
    new_state = state._replace(no_new_lines=True)
    return f"{tabs}{element[2]} {element[1]} {function(element[3], state=new_state, config=config)}"


# assumed endpoint
@register_reconstruction_function
def reconstruct_element(element, state, config, function):
    tabs = create_tabs(state)
    return f"{tabs}{element[1]}"


# Contains possibly multiple lines of comment
@register_reconstruction_function
def reconstruct_full_line_comment(element, state, config, function):
    tabs = create_tabs(state)
    string_list = element[1].split('\n')
    string_list[-1] = tabs + string_list[-1]
    return "\n".join(string_list)


@register_reconstruction_function
def reconstruct_comment(element, state, config, function):
    return f"{function(element[1], state=state, config=config)}{config['partial_comment_seperator']}{element[2]}"


@register_reconstruction_function
def reconstruct_object(element, state, config, function):
    if not element[2]:  # empty
        new_state = state._replace(no_new_lines=True)
        return f"{function(element[1], state=new_state, config=config)}{function(element[3], state=new_state, config=config)}"
    else:
        # newline before object close
        if (element[2][1][-1][0] == ParseTypes.NEW_LINE or element[2][1][-1][
            0] == ParseTypes.DOUBLE_NEWLINE) and state.level > 0:
            no_new_lines = False
        else:
            no_new_lines = True
        comment_always_newline = False

        if config["force_single_line_until_item_count"] is not None or config[
            "force_multi_line_from_item_count"] is not None:
            count = 0
            last_item = None
            for e in element[2][1]:
                if e[0] != ParseTypes.NEW_LINE and e[0] != ParseTypes.DOUBLE_NEWLINE:
                    count += 1
                    last_item = e

            # anticipate single line
            if config["force_single_line_until_item_count"] is not None and count <= config[
                "force_single_line_until_item_count"]:
                no_new_lines = True
                comment_always_newline = True

            # anticipate multiline
            elif config["force_multi_line_from_item_count"] is not None and count > config[
                "force_multi_line_from_item_count"]:
                no_new_lines = False

            # exception for comment as last element, which always needs a newline because how comments work.
            if last_item and (last_item[0] == ParseTypes.FULL_LINE_COMMENT or last_item[0] == ParseTypes.COMMENT):
                no_new_lines = False

        new_begin_state = state._replace(no_new_lines=comment_always_newline)
        new_state = state._replace(no_new_lines=False, level= state.level + 1)
        new_end_state = state._replace(no_new_lines=no_new_lines)

        return f"{function(element[1], state=new_begin_state, config=config)}{function(element[2], state=new_state, config=config)}{function(element[3], state=new_end_state, config=config)}"


@register_reconstruction_function
def reconstruct_begin(element, state, config, function):
    return element[1]


@register_reconstruction_function
def reconstruct_end(element, state, config, function):
    tabs = create_tabs(state)
    return f"{tabs}{element[1]}"


@register_reconstruction_function
def reconstruct_begin_comment(element, state, config, function):
    # print(state)
    string = f"{element[1]}\t{element[2]}"
    if state.no_new_lines:
        state = state._replace(no_new_lines=False, level=state.level+1)
        string += f"\n{create_tabs(state)}"
    return string


@register_reconstruction_function
def reconstruct_end_comment(element, state, config, function):
    tabs = create_tabs(state)
    return f"{tabs}{element[1]}{config['partial_comment_seperator']}{element[2]}"


@register_reconstruction_function
def reconstruct_double_newline(element, state, config, function):
    tabs = create_tabs(state)
    if (state.after_last_object # never a double line just before }
            or (config["default_no_double_line"] and not (config["object_yes_double_line"] and state.after_end_of_object)) # overwrite default for objects if specified
            or (config["force_single_line_until_item_count"] and state.item_count_object <= config["force_single_line_until_item_count"])): # no double newline after a single line object
        return f"\n"
    return f"\n{tabs}\n"


@register_reconstruction_function
def reconstruct_new_line(element, state, config, function):
    if (not state.after_last_object # never a double line just before }
        and ((
            config["default_yes_double_line"]
             or (config["object_yes_double_line"] and state.after_end_of_object and state.currently_no_newlines_in_list)
             or (config["force_multi_line_from_item_count"] and state.item_count_object > config["force_multi_line_from_item_count"] and state.after_end_of_object)) # overwrite default for object if specified
        )):
        tabs = create_tabs(state)
        return f"\n{tabs}\n"
    return f"\n"


def reconstruct_any_object(element, state, config):
    if isinstance(element, tuple):
        return reconstruction_functions[element[0] - 1](element, state, config, reconstruct_any_object)
    return ""


def reconstruct(parsed_data, config):
    # Start processing from the outermost layer
    return reconstruct_any_object(parsed_data, State(0, False, False, False, False, 10000), config)
