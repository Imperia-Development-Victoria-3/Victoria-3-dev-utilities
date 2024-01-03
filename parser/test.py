import warnings
from ply import yacc, lex
from enum import IntEnum, auto

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


def reconstruct(parsed_data):
    def reconstruct_element(element, level=0, tabs_added=False):
        if not tabs_added:
            tabs = "\t" * level
        else:
            tabs = ""

        if isinstance(element, tuple):
            parse_type = element[0]
            if parse_type == ParseTypes.LIST:
                if tabs_added:
                    string = " "
                else:
                    string = ""
                for item in element[1]:
                    if tabs_added:
                        string += f"{reconstruct_element(item, level=level, tabs_added=tabs_added)} "
                    else:
                        string += f"{reconstruct_element(item, level=level, tabs_added=tabs_added)}"
                return string
            elif parse_type == ParseTypes.ASSIGNMENT:
                return f"{tabs}{element[2]} {element[1]} {reconstruct_element(element[3], level=level, tabs_added=True)}"
            elif parse_type == ParseTypes.ELEMENT:
                return f"{tabs}{element[1]}"
            elif parse_type == ParseTypes.FULL_LINE_COMMENT:
                tmp = element[1].split('\n')
                tmp[-1] = tabs + tmp[-1]
                return "\n".join(tmp)
            elif parse_type == ParseTypes.COMMENT:
                return f"{reconstruct_element(element[1], level=level, tabs_added=tabs_added)}\t{element[2]}"
            elif parse_type == ParseTypes.OBJECT:
                # if config["single_element_single_line"]:
                if not element[2]:
                    return f"{reconstruct_element(element[1], level=level, tabs_added=True)}{reconstruct_element(element[3], level=level, tabs_added=True)}"
                else:
                    if not any(item[0] == ParseTypes.NEW_LINE or item[0] == ParseTypes.DOUBLE_NEWLINE for item in
                               element[2][1]):
                        tabs_added = True
                    else:
                        tabs_added = False
                    return f"{reconstruct_element(element[1], level=level)}{reconstruct_element(element[2], level=level + 1, tabs_added=tabs_added)}{reconstruct_element(element[3], level=level, tabs_added=tabs_added)}"
            elif parse_type == ParseTypes.BEGIN:
                return f"{element[1]}"
            elif parse_type == ParseTypes.END:
                return f"{tabs}{element[1]}"
            elif parse_type == ParseTypes.BEGIN_COMMENT:
                return f"{element[1]}\t{element[2]}"
            elif parse_type == ParseTypes.END_COMMENT:
                return f"{tabs}{element[1]}\t{element[2]}"
            elif parse_type == ParseTypes.DOUBLE_NEWLINE:
                return f"\n{tabs}\n"
            elif parse_type == ParseTypes.NEW_LINE:
                return f"\n"
        return ""

    # Start processing from the outermost layer
    return reconstruct_element(parsed_data)


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
        # warnings.warn(context, UserWarning)
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
    reconstructed_text = reconstruct_func(parsed_data)
    reconstructed_parsed_data = parser_func.parse(reconstructed_text)

    return test_text_reconstruction(content, reconstructed_text), test_parsing_consistency(parsed_data,
                                                                                           reconstructed_parsed_data)


blacklist = {
    "coat_of_arms"
}


def test_all_txt_files(folder_path, parser_func, reconstruct_func):
    total_files = 0
    passed_reconstruction = 0
    passed_consistency = 0
    failed_files = []

    for root, dirs, files in os.walk(folder_path):
        for file_name in files:
            if file_name.endswith('.txt'):
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
                if not reconstruction_bool or not consistency_bool:
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
    reconstructed_text = reconstruct_func(original_parsed_data)
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

    process_all_txt_files(Test.mod_directory, parser, reconstruct)
    # print(test_all_txt_files(Test.mod_directory, parser, reconstruct))

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
