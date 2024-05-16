import warnings
from collections import namedtuple
from typing import List, Callable

from ply import yacc, lex
from enum import IntEnum, auto
from dataclasses import dataclass

# --- Tokenizer

# All tokens must be named in advance.
tokens = ('BASIC_WORD', 'DIVIDER', 'BEGIN_DICT', 'END_DICT', "COMMENT", "NEW_LINE")

# Ignored characters
t_ignore = ' \t'

# Token matching rules are written as regexs
t_BASIC_WORD = r'([\@\'\[\];\*\$:\w\.\/\"\|\(\)-]+)'
t_DIVIDER = r'[!<>\?=]+'
t_BEGIN_DICT = r'\{'
t_END_DICT = r'\}'


def t_COMMENT(t):
    r"""\#.*"""
    return t


def t_special_word(t):
    r"""(\@\[.*?\])"""
    t.type = "BASIC_WORD"
    return t


def t_special_word_2(t):
    r"""("[^\n]+")"""
    t.type = "BASIC_WORD"
    return t


def t_color_word(t):
    r"""((rgb)|((hsv)|((hsv360)))|(hsv360))\s*\{\s*\d+(\.\d+)*\s+\d+(\.\d+)*\s+\d+(\.\d+)*\s*\}"""
    t.type = "BASIC_WORD"
    return t


def t_newline(t):
    r"""\n"""
    t.lexer.lineno += 1
    t.type = "NEW_LINE"
    return t


# A function can be used if there is an associated action.
# Write the matching regex in the docstring.
def t_error(t):
    print(f'Illegal character {t.value[0]!r}')
    print(t.lexer.lineno)
    t.lexer.skip(1)


# Build the lexer object
lexer = lex.lex()


class ParseTypes(IntEnum):
    LIST = auto()
    ASSIGNMENT = auto()
    ELEMENT = auto()
    FULL_LINE_COMMENT = auto()
    COMMENT = auto()
    OBJECT = auto()
    BEGIN = auto()
    BEGIN_COMMENT = auto()
    END = auto()
    END_COMMENT = auto()
    DOUBLE_NEWLINE = auto()
    NEW_LINE = auto()


# Initialize a list with placeholders (None) for all enum values
reconstruction_functions: List[Callable] = [Callable] * len(ParseTypes)


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


# --- Parser
def p_program(p):
    """
    program : assignment
            | program assignment
    """
    if len(p) == 2:
        p[0] = (ParseTypes.LIST, [p[1]])
    else:
        p[0] = (ParseTypes.LIST, p[1][1] + [p[2]])


def p_assignment(p):
    """
    assignment : BASIC_WORD DIVIDER value
    """
    p[0] = (ParseTypes.ASSIGNMENT, p[2], p[1], p[3])


def p_assignment_identifier(p):
    """assignment : BASIC_WORD"""
    p[0] = (ParseTypes.ELEMENT, p[1])  # Or a default value instead of None


def p_standalone_comment(p):
    """assignment : NEW_LINE COMMENT
                  | double_newline COMMENT
                  | COMMENT"""
    if len(p) > 2:
        if isinstance(p[1], tuple):
            p[1] = p[1][1]
        p[0] = (ParseTypes.FULL_LINE_COMMENT, p[1] + p[2])  # Handling standalone comments
    else:
        p[0] = (ParseTypes.FULL_LINE_COMMENT, p[1])


def p_attached_comment_assignment(p):
    """assignment : assignment COMMENT """
    p[0] = (ParseTypes.COMMENT, p[1], p[2])  # Or a default value instead of None


def p_attached_comment_begin(p):
    """
    begin_dict : BEGIN_DICT COMMENT
               | BEGIN_DICT
    """
    if len(p) == 3:
        p[0] = (ParseTypes.BEGIN_COMMENT, p[1], p[2])
    else:
        p[0] = (ParseTypes.BEGIN, p[1])


def p_attached_comment_end(p):
    """
    end_dict : END_DICT COMMENT
             | END_DICT
    """
    if len(p) == 3:
        p[0] = (ParseTypes.END_COMMENT, p[1], p[2])
    else:
        p[0] = (ParseTypes.END, p[1])


def p_promote_2(p):
    """
    value : BASIC_WORD
    """
    p[0] = (ParseTypes.ELEMENT, p[1])


def p_promote(p):
    """
    value : object
    """
    p[0] = p[1]


def p_map(p):
    """
    object : begin_dict assignments end_dict
           | begin_dict end_dict
    """
    if len(p) == 4:
        p[0] = (ParseTypes.OBJECT, p[1], p[2], p[3])
    else:
        p[0] = (ParseTypes.OBJECT, p[1], [], p[2])


def p_assignments_single(p):
    """
    assignments : assignment
                | assignments assignment
    """
    if len(p) == 2:
        p[0] = (ParseTypes.LIST, [p[1]])
    else:
        p[0] = (ParseTypes.LIST, p[1][1] + [p[2]])


def p_assignments_object(p):
    """
    assignments : object
                | assignments object
    """
    if len(p) == 2:
        p[0] = (ParseTypes.LIST, [p[1]])
    else:
        p[0] = (ParseTypes.LIST, p[1][1] + [p[2]])


def p_double_new_line(p):
    """
    double_newline : NEW_LINE NEW_LINE
                   | double_newline NEW_LINE
    """
    if isinstance(p[1], tuple):
        p[1] = p[1][1]
    p[0] = (ParseTypes.DOUBLE_NEWLINE, p[1] + p[2])


def p_double_new_line_promote(p):
    """
    assignment : double_newline
    """
    p[0] = p[1]


def p_new_line(p):
    """
    assignment : NEW_LINE
    """
    p[0] = (ParseTypes.NEW_LINE, p[1])


def p_error(p):
    ""
    if p:
        print("Syntax error at token", p)
        # Access the parser state
        print("Parser state:", p.lexer.lexstate)
        # Print the stack state
        stack_state_str = ' '.join([str(x) for x in list(parser.symstack)])
        print("Stack state:", stack_state_str)
    else:
        print("Syntax error at EOF")


# Build the parser
parser = yacc.yacc()
""" 
    Todo: Configuration File passed down to the reconstruct function
        Todo: Same line configuration for all comments under the same object ( object = { item # same vertical line \n item # same vertical line } )
    
        Todo: one item correct to one line option, and other way around.
"""


def create_tabs(state):
    if not state.line_used_tabs:
        return "\t" * state.level
    else:
        return ""


@register_reconstruction_function
def reconstruct_list(element, state, config, function):
    if state.line_used_tabs:
        string = " "
    else:
        string = ""
    for item in element[1]:
        if state.line_used_tabs:
            string += f"{function(item, state=state, config=config)} "
        else:
            string += f"{function(item, state=state, config=config)}"
    return string


@register_reconstruction_function
def reconstruct_assignment(element, state, config, function):
    tabs = create_tabs(state)
    new_state = state._replace(line_used_tabs=True)
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
    return f"{function(element[1], state=state, config=config)}\t{element[2]}"


@register_reconstruction_function
def reconstruct_object(element, state, config, function):
    if not element[2]:
        new_state = state._replace(line_used_tabs=True)
        return f"{function(element[1], state=new_state, config=config)}{function(element[3], state=new_state, config=config)}"
    else:
        if not any(item[0] == ParseTypes.NEW_LINE or item[0] == ParseTypes.DOUBLE_NEWLINE for item in
                   element[2][1]):
            new_state = state._replace(line_used_tabs=True, level=state.level)
        else:
            new_state = state._replace(line_used_tabs=False, level=state.level)
        return f"{function(element[1], state=new_state, config=config)}{function(element[2], state=new_state._replace(level=state.level + 1), config=config)}{function(element[3], state=new_state, config=config)}"


@register_reconstruction_function
def reconstruct_begin(element, state, config, function):
    return element[1]


@register_reconstruction_function
def reconstruct_end(element, state, config, function):
    tabs = create_tabs(state)

    return f"{tabs}{element[1]}"


@register_reconstruction_function
def reconstruct_begin_comment(element, state, config, function):
    return f"{element[1]}\t{element[2]}"


@register_reconstruction_function
def reconstruct_end_comment(element, state, config, function):
    tabs = create_tabs(state)

    return f"{tabs}{element[1]}\t{element[2]}"


@register_reconstruction_function
def reconstruct_double_newline(element, state, config, function):
    tabs = create_tabs(state)

    config["tabs_added"] = False
    return f"\n{tabs}\n"


@register_reconstruction_function
def reconstruct_new_line(element, state, config, function):
    config["tabs_added"] = False
    return f"\n"


State = namedtuple('State', ['level', 'line_used_tabs'])


def reconstruct_any_object(element, state, config):
    if isinstance(element, tuple):
        return reconstruction_functions[element[0] - 1](element, state, config, reconstruct_any_object)
    return ""


def reconstruct(parsed_data, config):
    # Start processing from the outermost layer
    return reconstruct_any_object(parsed_data, State(0, False), config)


context_size = 100


def test_text_reconstruction(original_text, reconstructed_text):
    # Remove all whitespaces for comparison
    original_text_no_whitespace = ''.join(original_text.split())
    reconstructed_text_no_whitespace = ''.join(reconstructed_text.split())

    # Check if the texts are the same
    if original_text_no_whitespace != reconstructed_text_no_whitespace:
        # Find the position of the first difference
        for i, (orig_char, recon_char) in enumerate(
                zip(original_text_no_whitespace, reconstructed_text_no_whitespace)):
            if orig_char != recon_char:
                # Calculate the starting position for the 50 character context
                start = max(0, i - int(context_size / 2))
                # Extract the context from the original text
                context = original_text_no_whitespace[start:start + context_size]
                context_vs = reconstructed_text_no_whitespace[start:start + context_size]

                warnings.warn(f'\n{context}\nVS\n{context_vs}', UserWarning)
                # raise
                return False
        # In case the reconstructed text is shorter than the original
        context = original_text[-context_size:]
        warnings.warn(context, UserWarning)
        return False
    return True


def test_parsing_consistency(original_parsed_data, reconstructed_parsed_data):
    return original_parsed_data == reconstructed_parsed_data


test_input = """
decree_encourage_urban_services = {
	texture = "gfx/interface/icons/decree/urbans.dds"
	unlocking_technologies = { # somerhing
		urban_planning
	} # adesfjaef
	
	#	valid = {
	#		NOR = { 
	#			has_decree = decree_encourage_manufacturing_industry 
	#			has_decree = decree_encourage_agricultural_industry
	
	#			has_decree = decree_encourage_resource_industry
	#		}
	#	}
		
	modifier = {
		# building_group_bg_trade_throughput_add = 0.2 (non-functional)
		# Need to add urban center output, unsure how to go about it
		building_group_bg_service_throughput_add = 0.2
		building_port_throughput_add = 0.2
		building_railway_throughput_add = 0.2
		building_group_bg_monuments_throughput_add = 0.2
		building_group_bg_canals_throughput_add = 0.2
		building_group_bg_power_throughput_add = 0.2
	}
	cost = 35 # was 75
	ai_weight = {
		value = 0
		if = {
			limit = {
				any_scope_building = {
					is_building_group = bg_urban_facilities
				}
			}
			add = 50
		}
		if = {
			limit = {
				any_scope_building = {
					is_building_group = bg_urban_facilities
					count >= 3
				}
			}
			add = 50
		}
		if = {
			limit = {
				any_scope_building = {
					is_building_group = bg_urban_facilities
					count >= 5
				}
			}
			add = 50
		}
		if = {
			limit = {
				scope:country = {
					has_strategy = ai_strategy_placate_population
				}
			}
			multiply = 1.5
		}
	}
}"""


def test_file(file_path, parser_func, reconstruct_func):
    # Read the content
    with open(file_path, 'r', encoding='utf-8-sig') as file:
        content = file.read()

    parsed_data = parser_func.parse(content)
    reconstructed_text = reconstruct_func(parsed_data, {})
    reconstructed_parsed_data = parser_func.parse(reconstructed_text)

    return test_text_reconstruction(content, reconstructed_text), test_parsing_consistency(parsed_data,
                                                                                           reconstructed_parsed_data)


blacklist = {
    "common\\cultures\\00_additional_cultures.txt",
    "common\\cultures\\00_cultures.txt",
    'common\\genes\\02_genes_accessories_hairstyles.txt',
    'common\\genes\\03_genes_accessories_beards.txt',
    'common\\genes\\97_genes_accessories_clothes.txt',
    'common\\genes\\99_genes_special.txt',
    'common\\laws\\00_slavery.txt',
    'common\\mobilization_options\\00_mobilization_option.txt',
    'common\\named_colors\\00_formation_colors.txt',
    'common\\state_traits\\06_eastern_europe_traits.txt'
}


@dataclass
class Config:
    items_same_line: bool
    comments_same_level: bool


def test_all_txt_files(folder_path, parser_func, reconstruct_func):
    total_files = 0
    passed_reconstruction = 0
    passed_consistency = 0
    failed_files = []

    for root, dirs, files in os.walk(folder_path):
        for file_name in files:
            if file_name.endswith('.txt'):
                print(file_name)
                file_path = os.path.join(root, file_name)
                if os.path.getsize(file_path) <= 3:
                    continue

                total_files += 1

                print("Testing", file_path)
                try:
                    reconstruction_bool, consistency_bool = test_file(file_path, parser_func, reconstruct_func)
                except TypeError:
                    reconstruction_bool = False
                    consistency_bool = False
                # Track passed tests
                if reconstruction_bool:
                    passed_reconstruction += 1
                if consistency_bool:
                    passed_consistency += 1

                # Track failed files
                if not reconstruction_bool:
                    failed_files.append(file_path)

    # Calculate percentages
    reconstruction_percentage = (passed_reconstruction / total_files) * 100 if total_files > 0 else 0
    consistency_percentage = (passed_consistency / total_files) * 100 if total_files > 0 else 0

    # Produce report
    report = {
        'Reconstruction Test Pass Rate': reconstruction_percentage,
        'Parsing Consistency Test Pass Rate': consistency_percentage,
        'Failed Files': failed_files
    }

    return report


def process_file(file_path, parser_func, reconstruct_func):
    # Read the content
    with open(file_path, 'r', encoding='utf-8-sig') as file:
        content = file.read()

    original_parsed_data = parser_func.parse(content)
    reconstructed_text = reconstruct_func(original_parsed_data, {})
    #
    with open(file_path, 'w', encoding='utf-8-sig') as file:
        file.write(reconstructed_text)


def process_all_txt_files(folder_path, parser_func, reconstruct_func):
    for root, dirs, files in os.walk(folder_path):
        for file_name in files:
            if file_name.endswith('.txt'):
                file_path = os.path.join(root, file_name)
                print(f"Processing {file_path}:")
                decoded_content = process_file(file_path, parser_func, reconstruct_func)
                # return


if __name__ == '__main__':
    from constants import Test
    import os
    import re
    import pprint

    # print(re.search(t_PART_COMMENT,test_input ))
    from constants import Test
    import os

    # path = os.path.join(Test.game_directory, "common\\")
    # path = os.path.normpath(
    #     'C:\\Program Files (x86)\\Steam\\steamapps\\common\\Victoria 3\\game\\common\\coat_of_arms\\coat_of_arms\\02_countries.txt')

    path = os.path.normpath("C:\\Users\\hidde\\Documents\\Paradox Interactive\\Victoria 3\\mod\\External-mods\\events")
    process_all_txt_files(path, parser, reconstruct)
    # print(test_all_txt_files(path, parser, reconstruct))

    # with open(path, encoding='utf-8-sig') as file:
    #     file_string = file.read()
    # # print(path)

    # parsed_data = parser.parse(test_input)
    # reconstructed_text = reconstruct(parsed_data)
    # reconstructed_parsed_data = parser.parse(reconstructed_text)
    #
    # print(test_text_reconstruction(test_input, reconstructed_text))
    # print(test_parsing_consistency(parsed_data, reconstructed_parsed_data))
    # #
    # # print(file_string)
    # # Parse an expression
    # # pprint.pprint(reconstructed_parsed_data)
    # if parsed_data:
    #     thing = reconstruct(reconstructed_parsed_data)
    #     print(thing)
