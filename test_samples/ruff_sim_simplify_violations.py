"""Test file with flake8-simplify (SIM) rule violations for testing Ruff integration."""

from typing import Any


def unnecessary_if_else():
    """Function with unnecessary if-else."""
    x = 5
    # SIM101: Unnecessary if-else - can be simplified
    if x > 0:
        result = True
    else:
        result = False
    return result


def unnecessary_if_else_with_return():
    """Function with unnecessary if-else with return."""
    x = 5
    # SIM102: Unnecessary if-else with return - can be simplified
    if x > 0:
        return True
    else:
        return False


def unnecessary_if_else_with_assign():
    """Function with unnecessary if-else with assignment."""
    x = 5
    # SIM103: Unnecessary if-else with assignment - can be simplified
    if x > 0:
        y = 1
    else:
        y = 0
    return y


def unnecessary_if_else_with_binary_operator():
    """Function with unnecessary if-else with binary operator."""
    x = 5
    # SIM104: Unnecessary if-else with binary operator - can be simplified
    if x > 0:
        result = x > 0 or x <= 0
    else:
        result = x > 0 or x <= 0
    return result


def unnecessary_if_else_with_ternary_operator():
    """Function with unnecessary if-else with ternary operator."""
    x = 5
    # SIM105: Unnecessary if-else with ternary operator - can be simplified
    if x > 0:
        result = True if x > 0 else False
    else:
        result = True if x > 0 else False
    return result


def unnecessary_if_else_with_string():
    """Function with unnecessary if-else with string."""
    x = 5
    # SIM106: Unnecessary if-else with string - can be simplified
    if x > 0:
        result = "positive" if x > 0 else "negative"
    else:
        result = "positive" if x > 0 else "negative"
    return result


def unnecessary_if_else_with_list():
    """Function with unnecessary if-else with list."""
    x = 5
    # SIM107: Unnecessary if-else with list - can be simplified
    if x > 0:
        result = [1, 2, 3] if x > 0 else [4, 5, 6]
    else:
        result = [1, 2, 3] if x > 0 else [4, 5, 6]
    return result


def unnecessary_if_else_with_dict():
    """Function with unnecessary if-else with dict."""
    x = 5
    # SIM108: Unnecessary if-else with dict - can be simplified
    if x > 0:
        result = {"a": 1} if x > 0 else {"b": 2}
    else:
        result = {"a": 1} if x > 0 else {"b": 2}
    return result


def unnecessary_if_else_with_set():
    """Function with unnecessary if-else with set."""
    x = 5
    # SIM109: Unnecessary if-else with set - can be simplified
    if x > 0:
        result = {1, 2, 3} if x > 0 else {4, 5, 6}
    else:
        result = {1, 2, 3} if x > 0 else {4, 5, 6}
    return result


def unnecessary_if_else_with_tuple():
    """Function with unnecessary if-else with tuple."""
    x = 5
    # SIM110: Unnecessary if-else with tuple - can be simplified
    if x > 0:
        result = (1, 2, 3) if x > 0 else (4, 5, 6)
    else:
        result = (1, 2, 3) if x > 0 else (4, 5, 6)
    return result


def unnecessary_if_else_with_none():
    """Function with unnecessary if-else with None."""
    x = 5
    # SIM111: Unnecessary if-else with None - can be simplified
    if x > 0:
        result = None if x > 0 else None
    else:
        result = None if x > 0 else None
    return result


def unnecessary_if_else_with_zero():
    """Function with unnecessary if-else with zero."""
    x = 5
    # SIM112: Unnecessary if-else with zero - can be simplified
    if x > 0:
        result = 0 if x > 0 else 0
    else:
        result = 0 if x > 0 else 0
    return result


def unnecessary_if_else_with_empty_string():
    """Function with unnecessary if-else with empty string."""
    x = 5
    # SIM113: Unnecessary if-else with empty string - can be simplified
    if x > 0:
        result = "" if x > 0 else ""
    else:
        result = "" if x > 0 else ""
    return result


def unnecessary_if_else_with_empty_list():
    """Function with unnecessary if-else with empty list."""
    x = 5
    # SIM114: Unnecessary if-else with empty list - can be simplified
    if x > 0:
        result = [] if x > 0 else []
    else:
        result = [] if x > 0 else []
    return result


def unnecessary_if_else_with_empty_dict():
    """Function with unnecessary if-else with empty dict."""
    x = 5
    # SIM115: Unnecessary if-else with empty dict - can be simplified
    if x > 0:
        result = {} if x > 0 else {}
    else:
        result = {} if x > 0 else {}
    return result


def unnecessary_if_else_with_empty_set():
    """Function with unnecessary if-else with empty set."""
    x = 5
    # SIM116: Unnecessary if-else with empty set - can be simplified
    if x > 0:
        result = set() if x > 0 else set()
    else:
        result = set() if x > 0 else set()
    return result


def unnecessary_if_else_with_empty_tuple():
    """Function with unnecessary if-else with empty tuple."""
    x = 5
    # SIM117: Unnecessary if-else with empty tuple - can be simplified
    if x > 0:
        result = () if x > 0 else ()
    else:
        result = () if x > 0 else ()
    return result


def unnecessary_if_else_with_arithmetic():
    """Function with unnecessary if-else with arithmetic."""
    x = 5
    # SIM118: Unnecessary if-else with arithmetic - can be simplified
    if x > 0:
        result = x * 2 + 1 if x > 0 else x * 2 + 1
    else:
        result = x * 2 + 1 if x > 0 else x * 2 + 1
    return result


def unnecessary_if_else_with_function_call():
    """Function with unnecessary if-else with function call."""
    x = 5
    # SIM119: Unnecessary if-else with function call - can be simplified
    if x > 0:
        result = abs(x) if x > 0 else abs(x)
    else:
        result = abs(x) if x > 0 else abs(x)
    return result


def unnecessary_if_else_with_method_call():
    """Function with unnecessary if-else with method call."""
    x = "hello"
    # SIM120: Unnecessary if-else with method call - can be simplified
    if len(x) > 0:
        result = x.upper() if len(x) > 0 else x.upper()
    else:
        result = x.upper() if len(x) > 0 else x.upper()
    return result


def unnecessary_if_else_with_attribute_access():
    """Function with unnecessary if-else with attribute access."""

    class TestClass:
        def __init__(self):
            self.value = 5

    obj = TestClass()
    # SIM121: Unnecessary if-else with attribute access - can be simplified
    if obj.value > 0:
        result = obj.value if obj.value > 0 else obj.value
    else:
        result = obj.value if obj.value > 0 else obj.value
    return result


def unnecessary_if_else_with_subscript():
    """Function with unnecessary if-else with subscript."""
    data = [1, 2, 3, 4, 5]
    # SIM122: Unnecessary if-else with subscript - can be simplified
    if len(data) > 0:
        result = data[0] if len(data) > 0 else data[0]
    else:
        result = data[0] if len(data) > 0 else data[0]
    return result


def unnecessary_if_else_with_slice():
    """Function with unnecessary if-else with slice."""
    data = [1, 2, 3, 4, 5]
    # SIM123: Unnecessary if-else with slice - can be simplified
    if len(data) > 0:
        result = data[:3] if len(data) > 0 else data[:3]
    else:
        result = data[:3] if len(data) > 0 else data[:3]
    return result


def unnecessary_if_else_with_comprehension():
    """Function with unnecessary if-else with comprehension."""
    data = [1, 2, 3, 4, 5]
    # SIM124: Unnecessary if-else with comprehension - can be simplified
    if len(data) > 0:
        result = [x * 2 for x in data] if len(data) > 0 else [x * 2 for x in data]
    else:
        result = [x * 2 for x in data] if len(data) > 0 else [x * 2 for x in data]
    return result


def unnecessary_if_else_with_generator():
    """Function with unnecessary if-else with generator."""
    data = [1, 2, 3, 4, 5]
    # SIM125: Unnecessary if-else with generator - can be simplified
    if len(data) > 0:
        result = (x * 2 for x in data) if len(data) > 0 else (x * 2 for x in data)
    else:
        result = (x * 2 for x in data) if len(data) > 0 else (x * 2 for x in data)
    return result


def unnecessary_if_else_with_lambda():
    """Function with unnecessary if-else with lambda."""
    x = 5
    # SIM126: Unnecessary if-else with lambda - can be simplified
    if x > 0:
        result = (lambda y: y * 2) if x > 0 else lambda y: y * 2
    else:
        result = (lambda y: y * 2) if x > 0 else lambda y: y * 2
    return result


def unnecessary_if_else_with_class_instantiation():
    """Function with unnecessary if-else with class instantiation."""
    x = 5
    # SIM127: Unnecessary if-else with class instantiation - can be simplified
    if x > 0:
        result = TestClass() if x > 0 else TestClass()
    else:
        result = TestClass() if x > 0 else TestClass()
    return result


def unnecessary_if_else_with_module_attribute():
    """Function with unnecessary if-else with module attribute."""
    import os

    # SIM128: Unnecessary if-else with module attribute - can be simplified
    if os.name == "nt":
        result = os.name if os.name == "nt" else os.name
    else:
        result = os.name if os.name == "nt" else os.name
    return result


def unnecessary_if_else_with_complex_expression():
    """Function with unnecessary if-else with complex expression."""
    x = 5
    # SIM129: Unnecessary if-else with complex expression - can be simplified
    if x > 0:
        result = (x * 2 + 1) ** 2 if x > 0 else (x * 2 + 1) ** 2
    else:
        result = (x * 2 + 1) ** 2 if x > 0 else (x * 2 + 1) ** 2
    return result


def unnecessary_if_else_with_multiple_conditions():
    """Function with unnecessary if-else with multiple conditions."""
    x = 5
    y = 10
    # SIM130: Unnecessary if-else with multiple conditions - can be simplified
    if x > 0 and y > 0:
        result = True if x > 0 and y > 0 else False
    else:
        result = True if x > 0 and y > 0 else False
    return result


def unnecessary_if_else_with_or_conditions():
    """Function with unnecessary if-else with or conditions."""
    x = 5
    y = 10
    # SIM131: Unnecessary if-else with or conditions - can be simplified
    if x > 0 or y > 0:
        result = True if x > 0 or y > 0 else False
    else:
        result = True if x > 0 or y > 0 else False
    return result


def unnecessary_if_else_with_not_condition():
    """Function with unnecessary if-else with not condition."""
    x = 5
    # SIM132: Unnecessary if-else with not condition - can be simplified
    if not x > 0:
        result = False if not x > 0 else True
    else:
        result = False if not x > 0 else True
    return result


def unnecessary_if_else_with_is_condition():
    """Function with unnecessary if-else with is condition."""
    x = None
    # SIM133: Unnecessary if-else with is condition - can be simplified
    if x is None:
        result = True if x is None else False
    else:
        result = True if x is None else False
    return result


def unnecessary_if_else_with_is_not_condition():
    """Function with unnecessary if-else with is not condition."""
    x = None
    # SIM134: Unnecessary if-else with is not condition - can be simplified
    if x is not None:
        result = True if x is not None else False
    else:
        result = True if x is not None else False
    return result


def unnecessary_if_else_with_in_condition():
    """Function with unnecessary if-else with in condition."""
    x = 5
    data = [1, 2, 3, 4, 5]
    # SIM135: Unnecessary if-else with in condition - can be simplified
    if x in data:
        result = True if x in data else False
    else:
        result = True if x in data else False
    return result


def unnecessary_if_else_with_not_in_condition():
    """Function with unnecessary if-else with not in condition."""
    x = 5
    data = [1, 2, 3, 4, 5]
    # SIM136: Unnecessary if-else with not in condition - can be simplified
    if x not in data:
        result = True if x not in data else False
    else:
        result = True if x not in data else False
    return result


def unnecessary_if_else_with_comparison():
    """Function with unnecessary if-else with comparison."""
    x = 5
    y = 10
    # SIM137: Unnecessary if-else with comparison - can be simplified
    if x > y:
        result = True if x > y else False
    else:
        result = True if x > y else False
    return result


def unnecessary_if_else_with_equality():
    """Function with unnecessary if-else with equality."""
    x = 5
    y = 5
    # SIM138: Unnecessary if-else with equality - can be simplified
    if x == y:
        result = True if x == y else False
    else:
        result = True if x == y else False
    return result


def unnecessary_if_else_with_inequality():
    """Function with unnecessary if-else with inequality."""
    x = 5
    y = 10
    # SIM139: Unnecessary if-else with inequality - can be simplified
    if x != y:
        result = True if x != y else False
    else:
        result = True if x != y else False
    return result


def unnecessary_if_else_with_less_than():
    """Function with unnecessary if-else with less than."""
    x = 5
    y = 10
    # SIM140: Unnecessary if-else with less than - can be simplified
    if x < y:
        result = True if x < y else False
    else:
        result = True if x < y else False
    return result


def unnecessary_if_else_with_less_equal():
    """Function with unnecessary if-else with less equal."""
    x = 5
    y = 10
    # SIM141: Unnecessary if-else with less equal - can be simplified
    if x <= y:
        result = True if x <= y else False
    else:
        result = True if x <= y else False
    return result


def unnecessary_if_else_with_greater_than():
    """Function with unnecessary if-else with greater than."""
    x = 5
    y = 10
    # SIM142: Unnecessary if-else with greater than - can be simplified
    if x > y:
        result = True if x > y else False
    else:
        result = True if x > y else False
    return result


def unnecessary_if_else_with_greater_equal():
    """Function with unnecessary if-else with greater equal."""
    x = 5
    y = 10
    # SIM143: Unnecessary if-else with greater equal - can be simplified
    if x >= y:
        result = True if x >= y else False
    else:
        result = True if x >= y else False
    return result


def unnecessary_if_else_with_multiple_operators():
    """Function with unnecessary if-else with multiple operators."""
    x = 5
    y = 10
    z = 15
    # SIM144: Unnecessary if-else with multiple operators - can be simplified
    if x > y and y > z:
        result = True if x > y and y > z else False
    else:
        result = True if x > y and y > z else False
    return result


def unnecessary_if_else_with_parentheses():
    """Function with unnecessary if-else with parentheses."""
    x = 5
    y = 10
    # SIM145: Unnecessary if-else with parentheses - can be simplified
    if x > y:
        result = True if (x > y) else False
    else:
        result = True if (x > y) else False
    return result


def unnecessary_if_else_with_nested_parentheses():
    """Function with unnecessary if-else with nested parentheses."""
    x = 5
    y = 10
    z = 15
    # SIM146: Unnecessary if-else with nested parentheses - can be simplified
    if (x > y) and (y > z):
        result = True if ((x > y) and (y > z)) else False
    else:
        result = True if ((x > y) and (y > z)) else False
    return result


def unnecessary_if_else_with_arithmetic_in_condition():
    """Function with unnecessary if-else with arithmetic in condition."""
    x = 5
    # SIM147: Unnecessary if-else with arithmetic in condition - can be simplified
    if x + 1 > 5:
        result = True if x + 1 > 5 else False
    else:
        result = True if x + 1 > 5 else False
    return result


def unnecessary_if_else_with_function_call_in_condition():
    """Function with unnecessary if-else with function call in condition."""
    x = 5
    # SIM148: Unnecessary if-else with function call in condition - can be simplified
    if abs(x) > 3:
        result = True if abs(x) > 3 else False
    else:
        result = True if abs(x) > 3 else False
    return result


def unnecessary_if_else_with_method_call_in_condition():
    """Function with unnecessary if-else with method call in condition."""
    x = "hello"
    # SIM149: Unnecessary if-else with method call in condition - can be simplified
    if x.upper() == "HELLO":
        result = True if x.upper() == "HELLO" else False
    else:
        result = True if x.upper() == "HELLO" else False
    return result


def unnecessary_if_else_with_attribute_access_in_condition():
    """Function with unnecessary if-else with attribute access in condition."""

    class TestClass:
        def __init__(self):
            self.value = 5

    obj = TestClass()
    # SIM150: Unnecessary if-else with attribute access in condition - can be simplified
    if obj.value > 3:
        result = True if obj.value > 3 else False
    else:
        result = True if obj.value > 3 else False
    return result


def unnecessary_if_else_with_subscript_in_condition():
    """Function with unnecessary if-else with subscript in condition."""
    data = [1, 2, 3, 4, 5]
    # SIM151: Unnecessary if-else with subscript in condition - can be simplified
    if data[0] > 0:
        result = True if data[0] > 0 else False
    else:
        result = True if data[0] > 0 else False
    return result


def unnecessary_if_else_with_slice_in_condition():
    """Function with unnecessary if-else with slice in condition."""
    data = [1, 2, 3, 4, 5]
    # SIM152: Unnecessary if-else with slice in condition - can be simplified
    if len(data[:3]) > 0:
        result = True if len(data[:3]) > 0 else False
    else:
        result = True if len(data[:3]) > 0 else False
    return result


def unnecessary_if_else_with_comprehension_in_condition():
    """Function with unnecessary if-else with comprehension in condition."""
    data = [1, 2, 3, 4, 5]
    # SIM153: Unnecessary if-else with comprehension in condition - can be simplified
    if len([x for x in data if x > 2]) > 0:
        result = True if len([x for x in data if x > 2]) > 0 else False
    else:
        result = True if len([x for x in data if x > 2]) > 0 else False
    return result


def unnecessary_if_else_with_generator_in_condition():
    """Function with unnecessary if-else with generator in condition."""
    data = [1, 2, 3, 4, 5]
    # SIM154: Unnecessary if-else with generator in condition - can be simplified
    if any(x > 2 for x in data):
        result = True if any(x > 2 for x in data) else False
    else:
        result = True if any(x > 2 for x in data) else False
    return result


def unnecessary_if_else_with_lambda_in_condition():
    """Function with unnecessary if-else with lambda in condition."""
    x = 5
    # SIM155: Unnecessary if-else with lambda in condition - can be simplified
    if (lambda y: y > 3)(x):
        result = True if (lambda y: y > 3)(x) else False
    else:
        result = True if (lambda y: y > 3)(x) else False
    return result


def unnecessary_if_else_with_class_instantiation_in_condition():
    """Function with unnecessary if-else with class instantiation in condition."""
    # SIM156: Unnecessary if-else with class instantiation in condition - can be simplified
    if TestClass():
        result = True if TestClass() else False
    else:
        result = True if TestClass() else False
    return result


def unnecessary_if_else_with_module_attribute_in_condition():
    """Function with unnecessary if-else with module attribute in condition."""
    import os

    # SIM157: Unnecessary if-else with module attribute in condition - can be simplified
    if os.name == "nt":
        result = True if os.name == "nt" else False
    else:
        result = True if os.name == "nt" else False
    return result


def unnecessary_if_else_with_complex_expression_in_condition():
    """Function with unnecessary if-else with complex expression in condition."""
    x = 5
    # SIM158: Unnecessary if-else with complex expression in condition - can be simplified
    if (x * 2 + 1) ** 2 > 100:
        result = True if (x * 2 + 1) ** 2 > 100 else False
    else:
        result = True if (x * 2 + 1) ** 2 > 100 else False
    return result


def unnecessary_if_else_with_multiple_conditions_in_condition():
    """Function with unnecessary if-else with multiple conditions in condition."""
    x = 5
    y = 10
    # SIM159: Unnecessary if-else with multiple conditions in condition - can be simplified
    if x > 0 and y > 0:
        result = True if x > 0 and y > 0 else False
    else:
        result = True if x > 0 and y > 0 else False
    return result


def unnecessary_if_else_with_or_conditions_in_condition():
    """Function with unnecessary if-else with or conditions in condition."""
    x = 5
    y = 10
    # SIM160: Unnecessary if-else with or conditions in condition - can be simplified
    if x > 0 or y > 0:
        result = True if x > 0 or y > 0 else False
    else:
        result = True if x > 0 or y > 0 else False
    return result


def unnecessary_if_else_with_not_condition_in_condition():
    """Function with unnecessary if-else with not condition in condition."""
    x = 5
    # SIM161: Unnecessary if-else with not condition in condition - can be simplified
    if not x > 0:
        result = True if not x > 0 else False
    else:
        result = True if not x > 0 else False
    return result


def unnecessary_if_else_with_is_condition_in_condition():
    """Function with unnecessary if-else with is condition in condition."""
    x = None
    # SIM162: Unnecessary if-else with is condition in condition - can be simplified
    if x is None:
        result = True if x is None else False
    else:
        result = True if x is None else False
    return result


def unnecessary_if_else_with_is_not_condition_in_condition():
    """Function with unnecessary if-else with is not condition in condition."""
    x = None
    # SIM163: Unnecessary if-else with is not condition in condition - can be simplified
    if x is not None:
        result = True if x is not None else False
    else:
        result = True if x is not None else False
    return result


def unnecessary_if_else_with_in_condition_in_condition():
    """Function with unnecessary if-else with in condition in condition."""
    x = 5
    data = [1, 2, 3, 4, 5]
    # SIM164: Unnecessary if-else with in condition in condition - can be simplified
    if x in data:
        result = True if x in data else False
    else:
        result = True if x in data else False
    return result


def unnecessary_if_else_with_not_in_condition_in_condition():
    """Function with unnecessary if-else with not in condition in condition."""
    x = 5
    data = [1, 2, 3, 4, 5]
    # SIM165: Unnecessary if-else with not in condition in condition - can be simplified
    if x not in data:
        result = True if x not in data else False
    else:
        result = True if x not in data else False
    return result


def unnecessary_if_else_with_comparison_in_condition():
    """Function with unnecessary if-else with comparison in condition."""
    x = 5
    y = 10
    # SIM166: Unnecessary if-else with comparison in condition - can be simplified
    if x > y:
        result = True if x > y else False
    else:
        result = True if x > y else False
    return result


def unnecessary_if_else_with_equality_in_condition():
    """Function with unnecessary if-else with equality in condition."""
    x = 5
    y = 5
    # SIM167: Unnecessary if-else with equality in condition - can be simplified
    if x == y:
        result = True if x == y else False
    else:
        result = True if x == y else False
    return result


def unnecessary_if_else_with_inequality_in_condition():
    """Function with unnecessary if-else with inequality in condition."""
    x = 5
    y = 10
    # SIM168: Unnecessary if-else with inequality in condition - can be simplified
    if x != y:
        result = True if x != y else False
    else:
        result = True if x != y else False
    return result


def unnecessary_if_else_with_less_than_in_condition():
    """Function with unnecessary if-else with less than in condition."""
    x = 5
    y = 10
    # SIM169: Unnecessary if-else with less than in condition - can be simplified
    if x < y:
        result = True if x < y else False
    else:
        result = True if x < y else False
    return result


def unnecessary_if_else_with_less_equal_in_condition():
    """Function with unnecessary if-else with less equal in condition."""
    x = 5
    y = 10
    # SIM170: Unnecessary if-else with less equal in condition - can be simplified
    if x <= y:
        result = True if x <= y else False
    else:
        result = True if x <= y else False
    return result


def unnecessary_if_else_with_greater_than_in_condition():
    """Function with unnecessary if-else with greater than in condition."""
    x = 5
    y = 10
    # SIM171: Unnecessary if-else with greater than in condition - can be simplified
    if x > y:
        result = True if x > y else False
    else:
        result = True if x > y else False
    return result


def unnecessary_if_else_with_greater_equal_in_condition():
    """Function with unnecessary if-else with greater equal in condition."""
    x = 5
    y = 10
    # SIM172: Unnecessary if-else with greater equal in condition - can be simplified
    if x >= y:
        result = True if x >= y else False
    else:
        result = True if x >= y else False
    return result


def unnecessary_if_else_with_multiple_operators_in_condition():
    """Function with unnecessary if-else with multiple operators in condition."""
    x = 5
    y = 10
    z = 15
    # SIM173: Unnecessary if-else with multiple operators in condition - can be simplified
    if x > y and y > z:
        result = True if x > y and y > z else False
    else:
        result = True if x > y and y > z else False
    return result


def unnecessary_if_else_with_parentheses_in_condition():
    """Function with unnecessary if-else with parentheses in condition."""
    x = 5
    y = 10
    # SIM174: Unnecessary if-else with parentheses in condition - can be simplified
    if x > y:
        result = True if (x > y) else False
    else:
        result = True if (x > y) else False
    return result


def unnecessary_if_else_with_nested_parentheses_in_condition():
    """Function with unnecessary if-else with nested parentheses in condition."""
    x = 5
    y = 10
    z = 15
    # SIM175: Unnecessary if-else with nested parentheses in condition - can be simplified
    if (x > y) and (y > z):
        result = True if ((x > y) and (y > z)) else False
    else:
        result = True if ((x > y) and (y > z)) else False
    return result


def unnecessary_if_else_with_arithmetic_in_condition_in_condition():
    """Function with unnecessary if-else with arithmetic in condition in condition."""
    x = 5
    # SIM176: Unnecessary if-else with arithmetic in condition in condition - can be simplified
    if x + 1 > 5:
        result = True if x + 1 > 5 else False
    else:
        result = True if x + 1 > 5 else False
    return result


def unnecessary_if_else_with_function_call_in_condition_in_condition():
    """Function with unnecessary if-else with function call in condition in condition."""
    x = 5
    # SIM177: Unnecessary if-else with function call in condition in condition - can be simplified
    if abs(x) > 3:
        result = True if abs(x) > 3 else False
    else:
        result = True if abs(x) > 3 else False
    return result


def unnecessary_if_else_with_method_call_in_condition_in_condition():
    """Function with unnecessary if-else with method call in condition in condition."""
    x = "hello"
    # SIM178: Unnecessary if-else with method call in condition in condition - can be simplified
    if x.upper() == "HELLO":
        result = True if x.upper() == "HELLO" else False
    else:
        result = True if x.upper() == "HELLO" else False
    return result


def unnecessary_if_else_with_attribute_access_in_condition_in_condition():
    """Function with unnecessary if-else with attribute access in condition in condition."""

    class TestClass:
        def __init__(self):
            self.value = 5

    obj = TestClass()
    # SIM179: Unnecessary if-else with attribute access in condition in condition - can be simplified
    if obj.value > 3:
        result = True if obj.value > 3 else False
    else:
        result = True if obj.value > 3 else False
    return result


def unnecessary_if_else_with_subscript_in_condition_in_condition():
    """Function with unnecessary if-else with subscript in condition in condition."""
    data = [1, 2, 3, 4, 5]
    # SIM180: Unnecessary if-else with subscript in condition in condition - can be simplified
    if data[0] > 0:
        result = True if data[0] > 0 else False
    else:
        result = True if data[0] > 0 else False
    return result


def unnecessary_if_else_with_slice_in_condition_in_condition():
    """Function with unnecessary if-else with slice in condition in condition."""
    data = [1, 2, 3, 4, 5]
    # SIM181: Unnecessary if-else with slice in condition in condition - can be simplified
    if len(data[:3]) > 0:
        result = True if len(data[:3]) > 0 else False
    else:
        result = True if len(data[:3]) > 0 else False
    return result


def unnecessary_if_else_with_comprehension_in_condition_in_condition():
    """Function with unnecessary if-else with comprehension in condition in condition."""
    data = [1, 2, 3, 4, 5]
    # SIM182: Unnecessary if-else with comprehension in condition in condition - can be simplified
    if len([x for x in data if x > 2]) > 0:
        result = True if len([x for x in data if x > 2]) > 0 else False
    else:
        result = True if len([x for x in data if x > 2]) > 0 else False
    return result


def unnecessary_if_else_with_generator_in_condition_in_condition():
    """Function with unnecessary if-else with generator in condition in condition."""
    data = [1, 2, 3, 4, 5]
    # SIM183: Unnecessary if-else with generator in condition in condition - can be simplified
    if any(x > 2 for x in data):
        result = True if any(x > 2 for x in data) else False
    else:
        result = True if any(x > 2 for x in data) else False
    return result


def unnecessary_if_else_with_lambda_in_condition_in_condition():
    """Function with unnecessary if-else with lambda in condition in condition."""
    x = 5
    # SIM184: Unnecessary if-else with lambda in condition in condition - can be simplified
    if (lambda y: y > 3)(x):
        result = True if (lambda y: y > 3)(x) else False
    else:
        result = True if (lambda y: y > 3)(x) else False
    return result


def unnecessary_if_else_with_class_instantiation_in_condition_in_condition():
    """Function with unnecessary if-else with class instantiation in condition in condition."""
    # SIM185: Unnecessary if-else with class instantiation in condition in condition - can be simplified
    if TestClass():
        result = True if TestClass() else False
    else:
        result = True if TestClass() else False
    return result


def unnecessary_if_else_with_module_attribute_in_condition_in_condition():
    """Function with unnecessary if-else with module attribute in condition in condition."""
    import os

    # SIM186: Unnecessary if-else with module attribute in condition in condition - can be simplified
    if os.name == "nt":
        result = True if os.name == "nt" else False
    else:
        result = True if os.name == "nt" else False
    return result


def unnecessary_if_else_with_complex_expression_in_condition_in_condition():
    """Function with unnecessary if-else with complex expression in condition in condition."""
    x = 5
    # SIM187: Unnecessary if-else with complex expression in condition in condition - can be simplified
    if (x * 2 + 1) ** 2 > 100:
        result = True if (x * 2 + 1) ** 2 > 100 else False
    else:
        result = True if (x * 2 + 1) ** 2 > 100 else False
    return result


def unnecessary_if_else_with_multiple_conditions_in_condition_in_condition():
    """Function with unnecessary if-else with multiple conditions in condition in condition."""
    x = 5
    y = 10
    # SIM188: Unnecessary if-else with multiple conditions in condition in condition - can be simplified
    if x > 0 and y > 0:
        result = True if x > 0 and y > 0 else False
    else:
        result = True if x > 0 and y > 0 else False
    return result


def unnecessary_if_else_with_or_conditions_in_condition_in_condition():
    """Function with unnecessary if-else with or conditions in condition in condition."""
    x = 5
    y = 10
    # SIM189: Unnecessary if-else with or conditions in condition in condition - can be simplified
    if x > 0 or y > 0:
        result = True if x > 0 or y > 0 else False
    else:
        result = True if x > 0 or y > 0 else False
    return result


def unnecessary_if_else_with_not_condition_in_condition_in_condition():
    """Function with unnecessary if-else with not condition in condition in condition."""
    x = 5
    # SIM190: Unnecessary if-else with not condition in condition in condition - can be simplified
    if not x > 0:
        result = True if not x > 0 else False
    else:
        result = True if not x > 0 else False
    return result


def unnecessary_if_else_with_is_condition_in_condition_in_condition():
    """Function with unnecessary if-else with is condition in condition in condition."""
    x = None
    # SIM191: Unnecessary if-else with is condition in condition in condition - can be simplified
    if x is None:
        result = True if x is None else False
    else:
        result = True if x is None else False
    return result


def unnecessary_if_else_with_is_not_condition_in_condition_in_condition():
    """Function with unnecessary if-else with is not condition in condition in condition."""
    x = None
    # SIM192: Unnecessary if-else with is not condition in condition in condition - can be simplified
    if x is not None:
        result = True if x is not None else False
    else:
        result = True if x is not None else False
    return result


def unnecessary_if_else_with_in_condition_in_condition_in_condition():
    """Function with unnecessary if-else with in condition in condition in condition."""
    x = 5
    data = [1, 2, 3, 4, 5]
    # SIM193: Unnecessary if-else with in condition in condition in condition - can be simplified
    if x in data:
        result = True if x in data else False
    else:
        result = True if x in data else False
    return result


def unnecessary_if_else_with_not_in_condition_in_condition_in_condition():
    """Function with unnecessary if-else with not in condition in condition in condition."""
    x = 5
    data = [1, 2, 3, 4, 5]
    # SIM194: Unnecessary if-else with not in condition in condition in condition - can be simplified
    if x not in data:
        result = True if x not in data else False
    else:
        result = True if x not in data else False
    return result


def unnecessary_if_else_with_comparison_in_condition_in_condition():
    """Function with unnecessary if-else with comparison in condition in condition."""
    x = 5
    y = 10
    # SIM195: Unnecessary if-else with comparison in condition in condition - can be simplified
    if x > y:
        result = True if x > y else False
    else:
        result = True if x > y else False
    return result


def unnecessary_if_else_with_equality_in_condition_in_condition():
    """Function with unnecessary if-else with equality in condition in condition."""
    x = 5
    y = 5
    # SIM196: Unnecessary if-else with equality in condition in condition - can be simplified
    if x == y:
        result = True if x == y else False
    else:
        result = True if x == y else False
    return result


def unnecessary_if_else_with_inequality_in_condition_in_condition():
    """Function with unnecessary if-else with inequality in condition in condition."""
    x = 5
    y = 10
    # SIM197: Unnecessary if-else with inequality in condition in condition - can be simplified
    if x != y:
        result = True if x != y else False
    else:
        result = True if x != y else False
    return result


def unnecessary_if_else_with_less_than_in_condition_in_condition():
    """Function with unnecessary if-else with less than in condition in condition."""
    x = 5
    y = 10
    # SIM198: Unnecessary if-else with less than in condition in condition - can be simplified
    if x < y:
        result = True if x < y else False
    else:
        result = True if x < y else False
    return result


def unnecessary_if_else_with_less_equal_in_condition_in_condition():
    """Function with unnecessary if-else with less equal in condition in condition."""
    x = 5
    y = 10
    # SIM199: Unnecessary if-else with less equal in condition in condition - can be simplified
    if x <= y:
        result = True if x <= y else False
    else:
        result = True if x <= y else False
    return result


def unnecessary_if_else_with_greater_than_in_condition_in_condition():
    """Function with unnecessary if-else with greater than in condition in condition."""
    x = 5
    y = 10
    # SIM200: Unnecessary if-else with greater than in condition in condition - can be simplified
    if x > y:
        result = True if x > y else False
    else:
        result = True if x > y else False
    return result
