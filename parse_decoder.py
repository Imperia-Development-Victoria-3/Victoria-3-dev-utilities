from constants import *


def decode_dictionary(dictionary, depth=0):
    result = ""
    for key, value in dictionary.items():
        operator = " = "
        if isinstance(key, tuple):
            if key[-1] == Constants.EQUAL_TYPE:
                operator = " = "
            elif key[-1] == Constants.EQUAL_OR_GREATER_TYPE:
                operator = " >= "
            elif key[-1] == Constants.EQUAL_OR_LESSER_TYPE:
                operator = " <= "
            elif key[-1] == Constants.LESSER_TYPE:
                operator = " < "
            elif key[-1] == Constants.GREATER_TYPE:
                operator = " > "
            elif key[-1] == Constants.EQUAL_AND_EXISTS_TYPE:
                operator = " ?= "
            elif key[-1] == Constants.NOT_EQUAL_TYPE:
                operator = " != "
            key = str(key[2])
        if type(value) == dict:
            if len(result) >= 2 and result[-2] == "}":
                result += "\n"
            result += "\t" * depth + key + operator + "{" + "\n"
            result += decode_dictionary(value, depth + 1)
        elif type(value) == list:
            for element in value:
                result += "\t" * depth + key + operator + "{" + "\n"
                result += decode_dictionary(element, depth + 1)
        elif type(value) == str:
            result += "\t" * depth + key + operator + value + "\n"
        elif type(value) == bool:
            result += "\t" * depth + key + "\n"
        elif type(key) == int:
            if value[3] == Constants.PART_LINE_COMMENT_TYPE:
                result = result[:-1] + " " + value[2] + "\n"
            if value[3] == Constants.FULL_LINE_COMMENT_TYPE:
                result += value[2] + "\n"
    if depth > 0:
        result += "\t" * (depth - 1) + "}" + "\n"
    return result
