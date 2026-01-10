"""Test file with flake8-comprehensions (C4) rule violations for testing Ruff integration."""


def unnecessary_list_comprehension():
    """Function with unnecessary list comprehension."""
    numbers = [1, 2, 3, 4, 5]
    # C401: Unnecessary list comprehension - can be replaced with list()
    result = list(numbers)
    return result


def unnecessary_dict_comprehension():
    """Function with unnecessary dict comprehension."""
    data = {"a": 1, "b": 2, "c": 3}
    # C402: Unnecessary dict comprehension - can be replaced with dict()
    result = dict(data.items())
    return result


def unnecessary_set_comprehension():
    """Function with unnecessary set comprehension."""
    numbers = [1, 2, 3, 4, 5]
    # C403: Unnecessary set comprehension - can be replaced with set()
    result = set(numbers)
    return result


def unnecessary_generator_expression():
    """Function with unnecessary generator expression."""
    numbers = [1, 2, 3, 4, 5]
    # C404: Unnecessary generator expression - can be replaced with tuple()
    result = tuple(x for x in numbers)
    return result


def unnecessary_list_comprehension_with_condition():
    """Function with unnecessary list comprehension with condition."""
    numbers = [1, 2, 3, 4, 5]
    # C405: Unnecessary list comprehension with condition
    result = [x for x in numbers if x > 2]
    return result


def unnecessary_dict_comprehension_with_condition():
    """Function with unnecessary dict comprehension with condition."""
    data = {"a": 1, "b": 2, "c": 3}
    # C406: Unnecessary dict comprehension with condition
    result = {k: v for k, v in data.items() if v > 1}
    return result


def unnecessary_set_comprehension_with_condition():
    """Function with unnecessary set comprehension with condition."""
    numbers = [1, 2, 3, 4, 5]
    # C407: Unnecessary set comprehension with condition
    result = {x for x in numbers if x > 2}
    return result


def unnecessary_generator_expression_with_condition():
    """Function with unnecessary generator expression with condition."""
    numbers = [1, 2, 3, 4, 5]
    # C408: Unnecessary generator expression with condition
    result = tuple(x for x in numbers if x > 2)
    return result


def unnecessary_list_comprehension_with_multiple_conditions():
    """Function with unnecessary list comprehension with multiple conditions."""
    numbers = [1, 2, 3, 4, 5]
    # C409: Unnecessary list comprehension with multiple conditions
    result = [x for x in numbers if x > 2 if x < 5]
    return result


def unnecessary_dict_comprehension_with_multiple_conditions():
    """Function with unnecessary dict comprehension with multiple conditions."""
    data = {"a": 1, "b": 2, "c": 3}
    # C410: Unnecessary dict comprehension with multiple conditions
    result = {k: v for k, v in data.items() if v > 1 if v < 3}
    return result


def unnecessary_set_comprehension_with_multiple_conditions():
    """Function with unnecessary set comprehension with multiple conditions."""
    numbers = [1, 2, 3, 4, 5]
    # C411: Unnecessary set comprehension with multiple conditions
    result = {x for x in numbers if x > 2 if x < 5}
    return result


def unnecessary_generator_expression_with_multiple_conditions():
    """Function with unnecessary generator expression with multiple conditions."""
    numbers = [1, 2, 3, 4, 5]
    # C412: Unnecessary generator expression with multiple conditions
    result = tuple(x for x in numbers if x > 2 if x < 5)
    return result


def unnecessary_list_comprehension_with_complex_expression():
    """Function with unnecessary list comprehension with complex expression."""
    numbers = [1, 2, 3, 4, 5]
    # C413: Unnecessary list comprehension with complex expression
    result = [x * 2 for x in numbers]
    return result


def unnecessary_dict_comprehension_with_complex_expression():
    """Function with unnecessary dict comprehension with complex expression."""
    data = {"a": 1, "b": 2, "c": 3}
    # C414: Unnecessary dict comprehension with complex expression
    result = {k: v * 2 for k, v in data.items()}
    return result


def unnecessary_set_comprehension_with_complex_expression():
    """Function with unnecessary set comprehension with complex expression."""
    numbers = [1, 2, 3, 4, 5]
    # C415: Unnecessary set comprehension with complex expression
    result = {x * 2 for x in numbers}
    return result


def unnecessary_generator_expression_with_complex_expression():
    """Function with unnecessary generator expression with complex expression."""
    numbers = [1, 2, 3, 4, 5]
    # C416: Unnecessary generator expression with complex expression
    result = tuple(x * 2 for x in numbers)
    return result


def unnecessary_list_comprehension_with_nested_loop():
    """Function with unnecessary list comprehension with nested loop."""
    numbers1 = [1, 2, 3]
    numbers2 = [4, 5, 6]
    # C417: Unnecessary list comprehension with nested loop
    result = [x + y for x in numbers1 for y in numbers2]
    return result


def unnecessary_dict_comprehension_with_nested_loop():
    """Function with unnecessary dict comprehension with nested loop."""
    data1 = {"a": 1, "b": 2}
    data2 = {"c": 3, "d": 4}
    # C418: Unnecessary dict comprehension with nested loop
    result = {k1 + k2: v1 + v2 for k1, v1 in data1.items() for k2, v2 in data2.items()}
    return result


def unnecessary_set_comprehension_with_nested_loop():
    """Function with unnecessary set comprehension with nested loop."""
    numbers1 = [1, 2, 3]
    numbers2 = [4, 5, 6]
    # C419: Unnecessary set comprehension with nested loop
    result = {x + y for x in numbers1 for y in numbers2}
    return result


def unnecessary_generator_expression_with_nested_loop():
    """Function with unnecessary generator expression with nested loop."""
    numbers1 = [1, 2, 3]
    numbers2 = [4, 5, 6]
    # C420: Unnecessary generator expression with nested loop
    result = tuple(x + y for x in numbers1 for y in numbers2)
    return result


def unnecessary_list_comprehension_with_multiple_targets():
    """Function with unnecessary list comprehension with multiple targets."""
    data = [("a", 1), ("b", 2), ("c", 3)]
    # C421: Unnecessary list comprehension with multiple targets
    result = [k + str(v) for k, v in data]
    return result


def unnecessary_dict_comprehension_with_multiple_targets():
    """Function with unnecessary dict comprehension with multiple targets."""
    data = [("a", 1), ("b", 2), ("c", 3)]
    # C422: Unnecessary dict comprehension with multiple targets
    result = {k: v * 2 for k, v in data}
    return result


def unnecessary_set_comprehension_with_multiple_targets():
    """Function with unnecessary set comprehension with multiple targets."""
    data = [("a", 1), ("b", 2), ("c", 3)]
    # C423: Unnecessary set comprehension with multiple targets
    result = {k + str(v) for k, v in data}
    return result


def unnecessary_generator_expression_with_multiple_targets():
    """Function with unnecessary generator expression with multiple targets."""
    data = [("a", 1), ("b", 2), ("c", 3)]
    # C424: Unnecessary generator expression with multiple targets
    result = tuple(k + str(v) for k, v in data)
    return result


def unnecessary_list_comprehension_with_walrus_operator():
    """Function with unnecessary list comprehension with walrus operator."""
    numbers = [1, 2, 3, 4, 5]
    # C425: Unnecessary list comprehension with walrus operator
    result = [x for x in numbers if (_y := x * 2) > 4]
    return result


def unnecessary_dict_comprehension_with_walrus_operator():
    """Function with unnecessary dict comprehension with walrus operator."""
    data = {"a": 1, "b": 2, "c": 3}
    # C426: Unnecessary dict comprehension with walrus operator
    result = {k: v for k, v in data.items() if (_y := v * 2) > 2}
    return result


def unnecessary_set_comprehension_with_walrus_operator():
    """Function with unnecessary set comprehension with walrus operator."""
    numbers = [1, 2, 3, 4, 5]
    # C427: Unnecessary set comprehension with walrus operator
    result = {x for x in numbers if (_y := x * 2) > 4}
    return result


def unnecessary_generator_expression_with_walrus_operator():
    """Function with unnecessary generator expression with walrus operator."""
    numbers = [1, 2, 3, 4, 5]
    # C428: Unnecessary generator expression with walrus operator
    result = tuple(x for x in numbers if (_y := x * 2) > 4)
    return result


def unnecessary_list_comprehension_with_starred_expression():
    """Function with unnecessary list comprehension with starred expression."""
    numbers = [1, 2, 3, 4, 5]
    # C429: Unnecessary list comprehension with starred expression
    result = [*numbers]
    return result


def unnecessary_dict_comprehension_with_starred_expression():
    """Function with unnecessary dict comprehension with starred expression."""
    data = {"a": 1, "b": 2, "c": 3}
    # C430: Unnecessary dict comprehension with starred expression
    result = {**data}
    return result


def unnecessary_set_comprehension_with_starred_expression():
    """Function with unnecessary set comprehension with starred expression."""
    numbers = [1, 2, 3, 4, 5]
    # C431: Unnecessary set comprehension with starred expression
    result = {*numbers}
    return result


def unnecessary_generator_expression_with_starred_expression():
    """Function with unnecessary generator expression with starred expression."""
    numbers = [1, 2, 3, 4, 5]
    # C432: Unnecessary generator expression with starred expression
    result = tuple(*numbers)
    return result


def unnecessary_list_comprehension_with_slice():
    """Function with unnecessary list comprehension with slice."""
    numbers = [1, 2, 3, 4, 5]
    # C433: Unnecessary list comprehension with slice
    result = list(numbers[1:4])
    return result


def unnecessary_dict_comprehension_with_slice():
    """Function with unnecessary dict comprehension with slice."""
    data = {"a": 1, "b": 2, "c": 3}
    # C434: Unnecessary dict comprehension with slice
    result = dict(list(data.items())[1:3])
    return result


def unnecessary_set_comprehension_with_slice():
    """Function with unnecessary set comprehension with slice."""
    numbers = [1, 2, 3, 4, 5]
    # C435: Unnecessary set comprehension with slice
    result = set(numbers[1:4])
    return result


def unnecessary_generator_expression_with_slice():
    """Function with unnecessary generator expression with slice."""
    numbers = [1, 2, 3, 4, 5]
    # C436: Unnecessary generator expression with slice
    result = tuple(x for x in numbers[1:4])
    return result


def unnecessary_list_comprehension_with_enumerate():
    """Function with unnecessary list comprehension with enumerate."""
    numbers = [1, 2, 3, 4, 5]
    # C437: Unnecessary list comprehension with enumerate
    result = [i for i, x in enumerate(numbers)]
    return result


def unnecessary_dict_comprehension_with_enumerate():
    """Function with unnecessary dict comprehension with enumerate."""
    numbers = [1, 2, 3, 4, 5]
    # C438: Unnecessary dict comprehension with enumerate
    result = dict(enumerate(numbers))
    return result


def unnecessary_set_comprehension_with_enumerate():
    """Function with unnecessary set comprehension with enumerate."""
    numbers = [1, 2, 3, 4, 5]
    # C439: Unnecessary set comprehension with enumerate
    result = {i for i, x in enumerate(numbers)}
    return result


def unnecessary_generator_expression_with_enumerate():
    """Function with unnecessary generator expression with enumerate."""
    numbers = [1, 2, 3, 4, 5]
    # C440: Unnecessary generator expression with enumerate
    result = tuple(i for i, x in enumerate(numbers))
    return result


def unnecessary_list_comprehension_with_zip():
    """Function with unnecessary list comprehension with zip."""
    numbers1 = [1, 2, 3]
    numbers2 = [4, 5, 6]
    # C441: Unnecessary list comprehension with zip
    result = [x + y for x, y in zip(numbers1, numbers2, strict=False)]
    return result


def unnecessary_dict_comprehension_with_zip():
    """Function with unnecessary dict comprehension with zip."""
    keys = ["a", "b", "c"]
    values = [1, 2, 3]
    # C442: Unnecessary dict comprehension with zip
    result = dict(zip(keys, values, strict=False))
    return result


def unnecessary_set_comprehension_with_zip():
    """Function with unnecessary set comprehension with zip."""
    numbers1 = [1, 2, 3]
    numbers2 = [4, 5, 6]
    # C443: Unnecessary set comprehension with zip
    result = {x + y for x, y in zip(numbers1, numbers2, strict=False)}
    return result


def unnecessary_generator_expression_with_zip():
    """Function with unnecessary generator expression with zip."""
    numbers1 = [1, 2, 3]
    numbers2 = [4, 5, 6]
    # C444: Unnecessary generator expression with zip
    result = tuple(x + y for x, y in zip(numbers1, numbers2, strict=False))
    return result


def unnecessary_list_comprehension_with_range():
    """Function with unnecessary list comprehension with range."""
    # C445: Unnecessary list comprehension with range
    result = list(range(5))
    return result


def unnecessary_dict_comprehension_with_range():
    """Function with unnecessary dict comprehension with range."""
    # C446: Unnecessary dict comprehension with range
    result = {x: x * 2 for x in range(5)}
    return result


def unnecessary_set_comprehension_with_range():
    """Function with unnecessary set comprehension with range."""
    # C447: Unnecessary set comprehension with range
    result = set(range(5))
    return result


def unnecessary_generator_expression_with_range():
    """Function with unnecessary generator expression with range."""
    # C448: Unnecessary generator expression with range
    result = tuple(x for x in range(5))
    return result


def unnecessary_list_comprehension_with_string():
    """Function with unnecessary list comprehension with string."""
    text = "hello"
    # C449: Unnecessary list comprehension with string
    result = list(text)
    return result


def unnecessary_dict_comprehension_with_string():
    """Function with unnecessary dict comprehension with string."""
    text = "hello"
    # C450: Unnecessary dict comprehension with string
    result = dict(enumerate(text))
    return result


def unnecessary_set_comprehension_with_string():
    """Function with unnecessary set comprehension with string."""
    text = "hello"
    # C451: Unnecessary set comprehension with string
    result = set(text)
    return result


def unnecessary_generator_expression_with_string():
    """Function with unnecessary generator expression with string."""
    text = "hello"
    # C452: Unnecessary generator expression with string
    result = tuple(c for c in text)
    return result


def unnecessary_list_comprehension_with_list():
    """Function with unnecessary list comprehension with list."""
    numbers = [1, 2, 3, 4, 5]
    # C453: Unnecessary list comprehension with list
    result = list(numbers)
    return result


def unnecessary_dict_comprehension_with_list():
    """Function with unnecessary dict comprehension with list."""
    data = {"a": 1, "b": 2, "c": 3}
    # C454: Unnecessary dict comprehension with list
    result = dict(list(data.items()))
    return result


def unnecessary_set_comprehension_with_list():
    """Function with unnecessary set comprehension with list."""
    numbers = [1, 2, 3, 4, 5]
    # C455: Unnecessary set comprehension with list
    result = set(numbers)
    return result


def unnecessary_generator_expression_with_list():
    """Function with unnecessary generator expression with list."""
    numbers = [1, 2, 3, 4, 5]
    # C456: Unnecessary generator expression with list
    result = tuple(x for x in list(numbers))
    return result


def unnecessary_list_comprehension_with_dict():
    """Function with unnecessary list comprehension with dict."""
    data = {"a": 1, "b": 2, "c": 3}
    # C457: Unnecessary list comprehension with dict
    result = list(dict(data))
    return result


def unnecessary_dict_comprehension_with_dict():
    """Function with unnecessary dict comprehension with dict."""
    data = {"a": 1, "b": 2, "c": 3}
    # C458: Unnecessary dict comprehension with dict
    result = dict(dict(data).items())
    return result


def unnecessary_set_comprehension_with_dict():
    """Function with unnecessary set comprehension with dict."""
    data = {"a": 1, "b": 2, "c": 3}
    # C459: Unnecessary set comprehension with dict
    result = set(dict(data))
    return result


def unnecessary_generator_expression_with_dict():
    """Function with unnecessary generator expression with dict."""
    data = {"a": 1, "b": 2, "c": 3}
    # C460: Unnecessary generator expression with dict
    result = tuple(k for k in dict(data))
    return result


def unnecessary_list_comprehension_with_set():
    """Function with unnecessary list comprehension with set."""
    numbers = {1, 2, 3, 4, 5}
    # C461: Unnecessary list comprehension with set
    result = list(set(numbers))
    return result


def unnecessary_dict_comprehension_with_set():
    """Function with unnecessary dict comprehension with set."""
    data = {"a": 1, "b": 2, "c": 3}
    # C462: Unnecessary dict comprehension with set
    result = dict(set(data.items()))
    return result


def unnecessary_set_comprehension_with_set():
    """Function with unnecessary set comprehension with set."""
    numbers = {1, 2, 3, 4, 5}
    # C463: Unnecessary set comprehension with set
    result = set(numbers)
    return result


def unnecessary_generator_expression_with_set():
    """Function with unnecessary generator expression with set."""
    numbers = {1, 2, 3, 4, 5}
    # C464: Unnecessary generator expression with set
    result = tuple(x for x in set(numbers))
    return result


def unnecessary_list_comprehension_with_tuple():
    """Function with unnecessary list comprehension with tuple."""
    numbers = (1, 2, 3, 4, 5)
    # C465: Unnecessary list comprehension with tuple
    result = list(numbers)
    return result


def unnecessary_dict_comprehension_with_tuple():
    """Function with unnecessary dict comprehension with tuple."""
    data = {"a": 1, "b": 2, "c": 3}
    # C466: Unnecessary dict comprehension with tuple
    result = dict(tuple(data.items()))
    return result


def unnecessary_set_comprehension_with_tuple():
    """Function with unnecessary set comprehension with tuple."""
    numbers = (1, 2, 3, 4, 5)
    # C467: Unnecessary set comprehension with tuple
    result = set(numbers)
    return result


def unnecessary_generator_expression_with_tuple():
    """Function with unnecessary generator expression with tuple."""
    numbers = (1, 2, 3, 4, 5)
    # C468: Unnecessary generator expression with tuple
    result = tuple(x for x in tuple(numbers))
    return result


def unnecessary_list_comprehension_with_generator():
    """Function with unnecessary list comprehension with generator."""
    numbers = [1, 2, 3, 4, 5]
    # C469: Unnecessary list comprehension with generator
    result = [x * 2 for x in numbers]
    return result


def unnecessary_dict_comprehension_with_generator():
    """Function with unnecessary dict comprehension with generator."""
    data = {"a": 1, "b": 2, "c": 3}
    # C470: Unnecessary dict comprehension with generator
    result = {k: v * 2 for k, v in data.items()}
    return result


def unnecessary_set_comprehension_with_generator():
    """Function with unnecessary set comprehension with generator."""
    numbers = [1, 2, 3, 4, 5]
    # C471: Unnecessary set comprehension with generator
    result = {x * 2 for x in numbers}
    return result


def unnecessary_generator_expression_with_generator():
    """Function with unnecessary generator expression with generator."""
    numbers = [1, 2, 3, 4, 5]
    # C472: Unnecessary generator expression with generator
    result = tuple(x for x in (x * 2 for x in numbers))
    return result


def unnecessary_list_comprehension_with_filter():
    """Function with unnecessary list comprehension with filter."""
    numbers = [1, 2, 3, 4, 5]
    # C473: Unnecessary list comprehension with filter
    result = list(filter(lambda x: x > 2, numbers))
    return result


def unnecessary_dict_comprehension_with_filter():
    """Function with unnecessary dict comprehension with filter."""
    data = {"a": 1, "b": 2, "c": 3}
    # C474: Unnecessary dict comprehension with filter
    result = dict(filter(lambda item: item[1] > 1, data.items()))
    return result


def unnecessary_set_comprehension_with_filter():
    """Function with unnecessary set comprehension with filter."""
    numbers = [1, 2, 3, 4, 5]
    # C475: Unnecessary set comprehension with filter
    result = set(filter(lambda x: x > 2, numbers))
    return result


def unnecessary_generator_expression_with_filter():
    """Function with unnecessary generator expression with filter."""
    numbers = [1, 2, 3, 4, 5]
    # C476: Unnecessary generator expression with filter
    result = tuple(x for x in filter(lambda x: x > 2, numbers))
    return result


def unnecessary_list_comprehension_with_map():
    """Function with unnecessary list comprehension with map."""
    numbers = [1, 2, 3, 4, 5]
    # C477: Unnecessary list comprehension with map
    result = [x * 2 for x in numbers]
    return result


def unnecessary_dict_comprehension_with_map():
    """Function with unnecessary dict comprehension with map."""
    data = {"a": 1, "b": 2, "c": 3}
    # C478: Unnecessary dict comprehension with map
    result = {item[0]: item[1] * 2 for item in data.items()}
    return result


def unnecessary_set_comprehension_with_map():
    """Function with unnecessary set comprehension with map."""
    numbers = [1, 2, 3, 4, 5]
    # C479: Unnecessary set comprehension with map
    result = {x * 2 for x in numbers}
    return result


def unnecessary_generator_expression_with_map():
    """Function with unnecessary generator expression with map."""
    numbers = [1, 2, 3, 4, 5]
    # C480: Unnecessary generator expression with map
    result = tuple(x for x in (x * 2 for x in numbers))
    return result


def unnecessary_list_comprehension_with_sorted():
    """Function with unnecessary list comprehension with sorted."""
    numbers = [3, 1, 4, 1, 5]
    # C481: Unnecessary list comprehension with sorted
    result = sorted(numbers)
    return result


def unnecessary_dict_comprehension_with_sorted():
    """Function with unnecessary dict comprehension with sorted."""
    data = {"c": 3, "a": 1, "b": 2}
    # C482: Unnecessary dict comprehension with sorted
    result = dict(sorted(data.items()))
    return result


def unnecessary_set_comprehension_with_sorted():
    """Function with unnecessary set comprehension with sorted."""
    numbers = [3, 1, 4, 1, 5]
    # C483: Unnecessary set comprehension with sorted
    result = set(numbers)
    return result


def unnecessary_generator_expression_with_sorted():
    """Function with unnecessary generator expression with sorted."""
    numbers = [3, 1, 4, 1, 5]
    # C484: Unnecessary generator expression with sorted
    result = tuple(x for x in sorted(numbers))
    return result


def unnecessary_list_comprehension_with_reversed():
    """Function with unnecessary list comprehension with reversed."""
    numbers = [1, 2, 3, 4, 5]
    # C485: Unnecessary list comprehension with reversed
    result = list(reversed(numbers))
    return result


def unnecessary_dict_comprehension_with_reversed():
    """Function with unnecessary dict comprehension with reversed."""
    data = {"a": 1, "b": 2, "c": 3}
    # C486: Unnecessary dict comprehension with reversed
    result = dict(reversed(list(data.items())))
    return result


def unnecessary_set_comprehension_with_reversed():
    """Function with unnecessary set comprehension with reversed."""
    numbers = [1, 2, 3, 4, 5]
    # C487: Unnecessary set comprehension with reversed
    result = set(numbers)
    return result


def unnecessary_generator_expression_with_reversed():
    """Function with unnecessary generator expression with reversed."""
    numbers = [1, 2, 3, 4, 5]
    # C488: Unnecessary generator expression with reversed
    result = tuple(x for x in reversed(numbers))
    return result


def unnecessary_list_comprehension_with_any():
    """Function with unnecessary list comprehension with any."""
    numbers = [1, 2, 3, 4, 5]
    # C489: Unnecessary list comprehension with any
    result = [x for x in numbers if any(x > y for y in numbers)]
    return result


def unnecessary_dict_comprehension_with_any():
    """Function with unnecessary dict comprehension with any."""
    data = {"a": 1, "b": 2, "c": 3}
    # C490: Unnecessary dict comprehension with any
    result = {k: v for k, v in data.items() if any(v > x for x in [1, 2])}
    return result


def unnecessary_set_comprehension_with_any():
    """Function with unnecessary set comprehension with any."""
    numbers = [1, 2, 3, 4, 5]
    # C491: Unnecessary set comprehension with any
    result = {x for x in numbers if any(x > y for y in numbers)}
    return result


def unnecessary_generator_expression_with_any():
    """Function with unnecessary generator expression with any."""
    numbers = [1, 2, 3, 4, 5]
    # C492: Unnecessary generator expression with any
    result = tuple(x for x in numbers if any(x > y for y in numbers))
    return result


def unnecessary_list_comprehension_with_all():
    """Function with unnecessary list comprehension with all."""
    numbers = [1, 2, 3, 4, 5]
    # C493: Unnecessary list comprehension with all
    result = [x for x in numbers if all(x > y for y in [0, 1])]
    return result


def unnecessary_dict_comprehension_with_all():
    """Function with unnecessary dict comprehension with all."""
    data = {"a": 1, "b": 2, "c": 3}
    # C494: Unnecessary dict comprehension with all
    result = {k: v for k, v in data.items() if all(v > x for x in [0, 1])}
    return result


def unnecessary_set_comprehension_with_all():
    """Function with unnecessary set comprehension with all."""
    numbers = [1, 2, 3, 4, 5]
    # C495: Unnecessary set comprehension with all
    result = {x for x in numbers if all(x > y for y in [0, 1])}
    return result


def unnecessary_generator_expression_with_all():
    """Function with unnecessary generator expression with all."""
    numbers = [1, 2, 3, 4, 5]
    # C496: Unnecessary generator expression with all
    result = tuple(x for x in numbers if all(x > y for y in [0, 1]))
    return result


def unnecessary_list_comprehension_with_sum():
    """Function with unnecessary list comprehension with sum."""
    numbers = [1, 2, 3, 4, 5]
    # C497: Unnecessary list comprehension with sum
    result = [x for x in numbers if sum(x > y for y in numbers) > 0]
    return result


def unnecessary_dict_comprehension_with_sum():
    """Function with unnecessary dict comprehension with sum."""
    data = {"a": 1, "b": 2, "c": 3}
    # C498: Unnecessary dict comprehension with sum
    result = {k: v for k, v in data.items() if sum(v > x for x in [1, 2]) > 0}
    return result


def unnecessary_set_comprehension_with_sum():
    """Function with unnecessary set comprehension with sum."""
    numbers = [1, 2, 3, 4, 5]
    # C499: Unnecessary set comprehension with sum
    result = {x for x in numbers if sum(x > y for y in numbers) > 0}
    return result


def unnecessary_generator_expression_with_sum():
    """Function with unnecessary generator expression with sum."""
    numbers = [1, 2, 3, 4, 5]
    # C500: Unnecessary generator expression with sum
    result = tuple(x for x in numbers if sum(x > y for y in numbers) > 0)
    return result
