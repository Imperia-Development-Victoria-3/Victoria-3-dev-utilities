import warnings
from ply import yacc, lex

### TODO: Something about color schemes; rgb{0 0 0} and hsv{0 0 0}

# --- Tokenizer

# All tokens must be named in advance.
# tokens = ('BASIC_WORD', 'DIVIDER', 'NOT_EQUAL', 'BEGIN_DICT', 'END_DICT', 'GREATER', 'EQUAL_OR_GREATER',
#           'EQUAL_OR_LESSER', 'LESSER', 'EQUAL_AND_EXISTS', 'COMMENT')

tokens = ('BASIC_WORD', 'DIVIDER', 'BEGIN_DICT', 'END_DICT', "FULL_COMMENT", "PART_COMMENT")

# Ignored characters
t_ignore = ' \t'

# Token matching rules are written as regexs
t_BASIC_WORD = r'([\'\[\];\*\@\!\$:\w\.\/\"\|(\(\)-]+)|' \
               r'(\"[^\n]+\")'
t_DIVIDER = r'[<>\?=]+'
t_BEGIN_DICT = r'\{'
t_END_DICT = r'\}'


# ORDER OF THE TWO COMMENTS MATTER, the more general should go first in order to be overwritten by the subset.
# WE CAN'T DO A SPECIAL CASE BECAUSE THE INFORMATION REQUIRED TO DETERMINE THAT ISN'T AVAILABLE IN THE GENERAL CASE.
def t_FULL_COMMENT(t):
    r"(\n|^)\s*\#.*"
    t.value = re.search(r"#.*", t.value).group(0)  # get rid of newline and whitespaces before comment
    return t


def t_PART_COMMENT(t):
    r"""\#.*"""
    # all the comments to be filtered by full comments
    return t


def t_special_word(t):
    r'(\@\[.*?\])'
    t.type = "BASIC_WORD"
    return t


def t_color_word(t):
    r'((rgb)|(hsv)|(hsv360))\s*\{\s*\d+(\.\d+)*\s+\d+(\.\d+)*\s+\d+(\.\d+)*\s*\}'
    t.type = "BASIC_WORD"
    return t


def t_ignore_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count('\n')


# A function can be used if there is an associated action.
# Write the matching regex in the docstring.
def t_error(t):
    print(f'Illegal character {t.value[0]!r}')
    print(t.lexer.lineno)
    t.lexer.skip(1)


# Build the lexer object
lexer = lex.lex()


# --- Parser

# Write functions for each grammar rule which is
# specified in the docstring.
# def p_comment_accumulator(p):
#     """
#     full_comment : FULL_COMMENT
#                  | FULL_COMMENT full_comment
#     """
#     p[0] = [p[1]] if len(p) == 2 else p[2] + [p[1]]


def p_program(p):
    """
    program : assignment
            | program assignment
    """
    p[0] = [p[1]] if len(p) == 2 else p[1] + [p[2]]


def p_assignment(p):
    """
    assignment : BASIC_WORD DIVIDER value
    """
    p[0] = ((p[2], p[1]), p[3])


def p_assignment_identifier(p):
    'assignment : BASIC_WORD'
    p[0] = (("=", p[1]), True)  # Or a default value instead of None


def p_standalone_comment(p):
    'assignment : FULL_COMMENT'
    p[0] = (('C', p[1]), True)  # Handling standalone comments


def p_attached_comment_assignment(p):
    """assignment : assignment PART_COMMENT """
    p[0] = (p[1][0], (("P", p[1][1]), p[2]))  # Or a default value instead of None


def p_attached_comment_begin(p):
    """
    begin_dict : BEGIN_DICT PART_COMMENT
               | BEGIN_DICT
    """
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = (("P", p[1]), p[2])


def p_attached_comment_end(p):
    """
    end_dict : END_DICT PART_COMMENT
             | END_DICT
    """
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = (("P", p[1]), p[2])


def p_promote_2(p):
    """
    value : BASIC_WORD
    """
    p[0] = p[1]


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
        p[0] = (p[1], p[2], p[3])
    else:
        p[0] = (p[1], [], p[2])


def p_assignments_single(p):
    """
    assignments : assignment
                | assignments assignment
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]


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
    def reconstruct_element(element, level=1):
        if isinstance(element, tuple):
            relationship, key = element[0][0], element[0][1]
            if relationship == 'C':  # Handle comments
                return key
            elif relationship == 'P':  # Handle post-item comments
                comment = element[1]
                if isinstance(key, bool):
                    return f'\t{comment}'
                return f'{key}\t{comment}'
            elif re.match(t_DIVIDER, relationship):  # Handle key-value pairs
                value = element[1]
                if isinstance(value, tuple) and len(value) == 3:
                    start_symbol, end_symbol = value[0], value[2]
                    value = value[1]

                if isinstance(value, list):  # If value is a list, recursively process it
                    value = reconstruct_element(start_symbol, level + 1) + '\n' + '\n'.join(
                        [level * '\t' + reconstruct_element(v, level + 1) for v in value]) + '\n' + (
                                    level - 1) * '\t' + reconstruct_element(end_symbol, level + 1)
                elif isinstance(value, bool):
                    return f'{key}'
                elif isinstance(value, tuple):
                    if isinstance(value[0][1], bool):
                        return f'{key}{reconstruct_element(value)}'
                    return f'{key} {relationship} {reconstruct_element(value)}'
                return f'{key} {relationship} {value}'
        elif isinstance(element, str):  # Handle simple strings
            return element
        return ''

    # Start processing from the outermost layer
    return '\n'.join([reconstruct_element(item) for item in parsed_data]) + '\n'


context_size = 100


def test_text_reconstruction(parser_func, reconstruct_func, original_text):
    parsed_data = parser_func.parse(original_text)
    reconstructed_text = reconstruct_func(parsed_data)

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


def test_parsing_consistency(parser_func, reconstruct_func, original_text):
    original_parsed_data = parser_func.parse(original_text)
    reconstructed_text = reconstruct_func(original_parsed_data)
    reconstructed_parsed_data = parser_func.parse(reconstructed_text)
    return original_parsed_data == reconstructed_parsed_data


test_input = """#something else

### asoerlae ###
## something else ##
building_university = {

	building_group = bg_technology

	city_type = city

	levels_per_mesh = 5

	unlocking_technologies = { 
		academia
	}
    # random comment
	production_method_groups = { 
		pmg_base_building_university = { hoela } # something
		pmg_base_building_university = peela # this goes right
		pmg_university_academia
	} 
	
	something # this goes wrong?
    this_does_not
	texture = "gfx/interface/icons/building_icons/building_university.dds"

	required_construction = construction_cost_medium
}
"""


def test_file(file_path, parser_func, reconstruct_func):
    # Read the content
    with open(file_path, 'r', encoding='utf-8-sig') as file:
        content = file.read()
    return test_text_reconstruction(parser, reconstruct, content), test_parsing_consistency(parser_func,
                                                                                            reconstruct_func, content)


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
                total_files += 1
                file_path = os.path.join(root, file_name)
                if os.path.getsize(file_path) == 0:
                    print("\n\n it works \n\n\n\n\n")
                    continue

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
                if not (reconstruction_bool and consistency_bool):
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

    # print(re.search(t_PART_COMMENT,test_input ))
    from constants import Test
    import os

    process_all_txt_files(Test.mod_directory, parser, reconstruct)

    # pprint.pprint(blacklist)
    # path = os.path.join(Test.game_directory,
    #                     os.path.normpath("common/"))
    # print(test_all_txt_files(path, parser, reconstruct))
    # print(os.path.getsize(blacklist[2]))
    # path = blacklist[8]
    # # path = os.path.normpath("C:\\Program Files (x86)\\Steam\\steamapps\\common\\Victoria 3\\game\\common\\on_actions\\00_code_on_actions.txt")
    # # path = os.path.join(Test.game_directory, "common\\buildings\\03_mines.txt")
    # with open(path, encoding='utf-8-sig') as file:
    #     file_string = file.read()
    # print(path)
    # print(test_text_reconstruction(parser, reconstruct, file_string))
    # print(test_parsing_consistency(parser, reconstruct, file_string))
    #
    # # print(file_string)
    # # Parse an expression
    # ast = parser.parse(file_string)
    # # pprint.pprint(ast)
    # if ast:
    #     thing = reconstruct(ast)
    #     # print(thing)
