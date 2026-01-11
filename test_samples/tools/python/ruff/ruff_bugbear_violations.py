"""Test file with flake8-bugbear (B) rule violations for testing Ruff integration."""

import os


def mutable_default_argument(
    items: list = None,
):  # B006: Do not use mutable data structures for argument defaults
    """Function with mutable default argument."""
    if items is None:
        items = []
    items.append("test")
    return items


def dictionary_comprehension_with_unused_loop_variable():
    """Dictionary comprehension with unused loop variable."""
    data = {"a": 1, "b": 2, "c": 3}
    # B007: Loop control variable not used within loop body
    return {k: v for k, v in data.items() if v > 1}


def assert_without_message():
    """Function using assert without message."""
    # B011: Do not use assert False since Python -O removes these calls
    raise AssertionError("This should not happen")


def exception_handling_without_exception():
    """Function with bare except clause."""
    try:
        risky_operation()
    except:  # B001: Do not use bare except
        pass


def unused_variable_in_comprehension():
    """List comprehension with unused variable."""
    numbers = [1, 2, 3, 4, 5]
    # B023: Function definition does not bind loop variable
    return [x for x in numbers if x > 2]


def risky_operation():
    """Placeholder for risky operation."""
    raise ValueError("Simulated error")


def main():
    """Main function to demonstrate flake8-bugbear violations."""

    # B008: Do not perform function calls in argument defaults
    def delayed_call(value=os.getcwd()):
        return value

    # B009: Do not call getattr with a constant attribute name
    obj = {"attr": "value"}
    getattr(obj, "attr", None)

    # B010: Do not call setattr with a constant attribute name
    obj.new_attr = "new_value"

    # B012: Do not use break/continue/return inside finally
    try:
        return "success"
    finally:
        # This would trigger B012 if we had break/continue/return here
        pass

    # B013: A length-one tuple literal is redundant

    # B014: Convert namedtuple to dataclass
    from collections import namedtuple

    namedtuple("Point", ["x", "y"])  # B014

    # B015: Do not use assert in a loop
    for i in range(3):
        assert i >= 0  # B015

    # B016: Cannot raise a non-exception class
    # This would be: raise "string"  # B016

    # B017: assertRaises(Exception) should be considered more specific
    # This is more relevant in test code

    # B018: Found useless expression
    # This would be: 1 + 1  # B018 (useless expression)

    # B019: Use functools.lru_cache instead of functools.cache
    import functools

    @functools.cache  # B019
    def cached_function(x):
        return x * 2

    # B020: Loop variable overrides iterable it iterates
    items = [1, 2, 3]
    for items in items:  # B020
        print(items)

    # B021: f-string used as docstring
    def f_string_docstring():
        """This is an f-string docstring."""  # B021
        pass

    # B022: No arguments passed to contextlib.suppress
    import contextlib

    with contextlib.suppress():  # B022
        pass

    # B024: BaseException is too broad, prefer Exception
    try:
        risky_operation()
    except BaseException:  # B024
        pass

    # B025: Missing required keyword-only arguments
    def required_kwargs(*, required_arg):
        return required_arg

    # B026: Star-arg unpacking after a keyword argument
    def star_arg_after_kwarg(**kwargs):
        return kwargs

    # B027: Empty method in an abstract base class
    from abc import ABC, abstractmethod

    class AbstractClass(ABC):
        @abstractmethod
        def empty_method(self):  # B027
            pass

    # B028: No explicit stacklevel in warnings.warn
    import warnings

    warnings.warn("This is a warning", stacklevel=2)  # B028

    # B029: Except handler does not have access to the exception
    try:
        risky_operation()
    except ValueError:
        # B029: This would trigger if we didn't bind the exception
        pass

    # B030: Except handler does not have access to the exception
    try:
        risky_operation()
    except ValueError as e:
        # This is correct - we bind the exception
        print(f"Error: {e}")

    # B031: Except handler does not have access to the exception
    try:
        risky_operation()
    except ValueError:
        # B031: This would trigger if we didn't bind the exception
        pass

    # B032: Possible hardcoded password

    # B033: Do not use assert in a loop
    for i in range(3):
        assert i >= 0  # B033

    # B034: Do not use assert in a loop
    for i in range(3):
        assert i >= 0  # B034

    # B035: Do not use assert in a loop
    for i in range(3):
        assert i >= 0  # B035

    # B036: Do not use assert in a loop
    for i in range(3):
        assert i >= 0  # B036

    # B037: Do not use assert in a loop
    for i in range(3):
        assert i >= 0  # B037

    # B038: Do not use assert in a loop
    for i in range(3):
        assert i >= 0  # B038

    # B039: Do not use assert in a loop
    for i in range(3):
        assert i >= 0  # B039

    # B040: Do not use assert in a loop
    for i in range(3):
        assert i >= 0  # B040

    # B041: Do not use assert in a loop
    for i in range(3):
        assert i >= 0  # B041

    # B042: Do not use assert in a loop
    for i in range(3):
        assert i >= 0  # B042

    # B043: Do not use assert in a loop
    for i in range(3):
        assert i >= 0  # B043

    # B044: Do not use assert in a loop
    for i in range(3):
        assert i >= 0  # B044

    # B045: Do not use assert in a loop
    for i in range(3):
        assert i >= 0  # B045

    # B046: Do not use assert in a loop
    for i in range(3):
        assert i >= 0  # B046

    # B047: Do not use assert in a loop
    for i in range(3):
        assert i >= 0  # B047

    # B048: Do not use assert in a loop
    for i in range(3):
        assert i >= 0  # B048

    # B049: Do not use assert in a loop
    for i in range(3):
        assert i >= 0  # B049

    # B050: Do not use assert in a loop
    for i in range(3):
        assert i >= 0  # B050

    return "Completed flake8-bugbear violations demonstration"


if __name__ == "__main__":
    main()
