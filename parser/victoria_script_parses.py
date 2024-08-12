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
