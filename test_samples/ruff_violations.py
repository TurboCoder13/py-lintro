"""Sample file with multiple Ruff violations for testing."""

import sys, os
import json
from pathlib    import Path
import unused_module  # Unused import
from typing import List, Dict  # Unused imports

def hello(name:str='World'):  # Missing spaces around operators
    print(f'Hello, {name}!')
    unused_var = 42  # Unused variable
    undefined_var = some_undefined_function()  # Undefined name
    return None

def bad_function(  # Too many arguments
    arg1, arg2, arg3, arg4, arg5, arg6, arg7, arg8, arg9, arg10, arg11, arg12
):
    """Function with too many arguments."""
    pass

def another_function():
    x=1+2  # Missing spaces around operators
    y=3*4  # Missing spaces around operators
    z=5/6  # Missing spaces around operators
    return x+y+z

if __name__=='__main__':  # Missing spaces around operators
    hello()
    print("This line is too long and should trigger a line length violation because it exceeds the maximum allowed line length for this project") 