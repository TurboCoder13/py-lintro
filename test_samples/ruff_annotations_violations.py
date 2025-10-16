"""Sample file with flake8-annotations (ANN) violations for testing Ruff.

Intentionally violates several ANN-rules, such as:
- ANN101: missing type annotation for self
- ANN102: missing type annotation for cls
- ANN201: missing return type annotation for public function
- ANN204: missing return type annotation for special method
- ANN205: missing return type annotation for static method
- ANN003: missing type annotation for **kwargs
"""

from typing import Any


class SampleClass:
    """Sample class with annotation violations."""

    def __init__(self, value: int):  # ANN101: missing type for self
        self.value = value

    @classmethod
    def from_string(cls, s: str):  # ANN102: missing type for cls
        return cls(int(s))

    @staticmethod
    def helper_func(x: int):  # ANN205: missing return type
        return x * 2

    def __str__(self):  # ANN204: missing return type for special method
        return f"SampleClass({self.value})"

    def public_method(self, data: list[str]):  # ANN201: missing return type
        return len(data)

    def kwargs_method(self, **kwargs):  # ANN003: missing type for **kwargs
        return kwargs


def public_function(a: int, b: str):  # ANN201: missing return type
    """Public function without return type annotation."""
    return f"{a}: {b}"


def kwargs_function(**kwargs):  # ANN003: missing type for **kwargs
    """Function with kwargs without type annotation."""
    return kwargs


def nested_function():
    """Function that returns a nested function."""

    def inner(x: int):  # ANN201: missing return type
        return x + 1

    return inner
