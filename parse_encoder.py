import re
from constants import *

symbol_searches = [
    (r"([\w\.-]+)|(\"[^\n]+\")", WORD_TYPE),
    (r"=", EQUAL_TYPE),
    (r"{", BEGIN_DICT_TYPE),
    (r"}", END_DICT_TYPE)
]

comment_symbol_searches = [
    (r"^[ \t]*#.*$", FULL_LINE_COMMENT_TYPE),
    (r"#.*$", ALL_COMMENT_TYPE)
]


def _read_file_as_string(location):
    with open(location, encoding='utf-8-sig') as file:
        file_string = file.read()
    return file_string


def parse_text_file(file_path):
    file_string = _read_file_as_string(file_path)
    return parse_text(file_string)


def parse_text(file_string):
    remove_symbols = []
    remove_symbols += process_comments(file_string)
    removed_symbols = sorted(remove_symbols, key=lambda x: x[0])

    offset = 0
    for index, symbol in enumerate(removed_symbols):
        removed_symbols[index] = (symbol[0] - offset, symbol[1] - offset, symbol[2], symbol[3])
        offset += symbol[1] - symbol[0]  # update offset to account for removed characters

    for pattern, symbol_type in comment_symbol_searches:
        file_string = re.sub(pattern, '', file_string, flags=re.MULTILINE)

    symbols = []
    for pattern, symbol_type in symbol_searches:
        symbols += [(match.start(), match.end(), match.group(), symbol_type) for match in
                    re.finditer(pattern, file_string)]

    symbols = sorted(symbols + removed_symbols, key=lambda x: x[0])
    result = {}
    stack = [result]
    iteration = [0]
    while symbols:
        encode_symbol(symbols, stack, iteration)

    # print(result)
    # for key, value in result.items():
    #     print(key, value)

    return result


def encode_symbol(symbols, stack, iteration):
    while symbols[0][3] == PART_LINE_COMMENT_TYPE or symbols[0][3] == FULL_LINE_COMMENT_TYPE:
        symbol = symbols.pop(0)
        stack[-1][iteration[0]] = symbol
        iteration[0] += 1

    symbol = symbols.pop(0)
    if symbol[3] == WORD_TYPE:
        comments = []
        while symbols[0][3] == PART_LINE_COMMENT_TYPE or symbols[0][3] == FULL_LINE_COMMENT_TYPE:
            comments.append(symbols.pop(0))

        if symbols[0][3] == EQUAL_TYPE:
            if symbols[1][3] == BEGIN_DICT_TYPE:
                dictionary = dict()
                if not stack[-1].get(symbol[2]):
                    stack[-1][symbol[2]] = dictionary
                elif type(stack[-1][symbol[2]]) == list:
                    stack[-1][symbol[2]].append(dictionary)
                else:
                    stack[-1][symbol[2]] = [stack[-1][symbol[2]], dictionary]

                stack.append(dictionary)
            elif symbols[1][3] == WORD_TYPE:
                stack[-1][symbol[2]] = symbols[1][2]
            symbols.pop(0)
            symbols.pop(0)
        elif symbols[0][3] == WORD_TYPE or symbols[0][3] == END_DICT_TYPE:
            stack[-1][symbol[2]] = True

        for comment in comments:
            stack[-1][iteration[0]] = comment
            iteration[0] += 1

    elif symbol[3] == END_DICT_TYPE:
        stack.pop()


def process_comments(file_string):
    comment_symbols = []
    comment_symbols += [(match.start(), match.end(), match.group(), FULL_LINE_COMMENT_TYPE) for match in
                        re.finditer(r"^[ \t]*#.*$", file_string, re.MULTILINE)]

    lookup = set()
    for fulline_comment in comment_symbols:
        lookup.add(fulline_comment[1])

    comment_symbols += [(match.start(), match.end(), match.group(), PART_LINE_COMMENT_TYPE) for match in
                        re.finditer(r"#.*$", file_string, re.MULTILINE) if match.end() not in lookup]
    return comment_symbols


if __name__ == '__main__':
    from parse_decoder import decode_dictionary

    # Test the parsing function
    dictionary = parse_text_file("00_pop_needs.txt")
    print(dictionary)
    print(decode_dictionary(dictionary))

    # dictionary = parse_text_file("05_military.txt")
    # text = write_text(dictionary)
    # print(text)

    # dictionary = parse_text_file("00_goods.txt")
    # print(dictionary)
    # text = write_text(dictionary)
    # print(text)
