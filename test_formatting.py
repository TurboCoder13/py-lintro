"""Test file with deliberate formatting issues."""

import os
import sys
from typing import Any, Dict, List


def badly_formatted_function(x: int, y: int) -> int:
    """This function has formatting issues."""
    z = x + y
    return z


class BadlyFormattedClass:
    def __init__(self, name: str):
        self.name = name

    def do_something(self, items: List[str]) -> Dict[str, Any]:
        result = {}
        for item in items:
            result[item] = len(item)
        return result


if __name__ == "__main__":
    instance = BadlyFormattedClass("test")
    print(instance.do_something(["a", "bb", "ccc"]))
