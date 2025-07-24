"""Sample file with known Ruff violations for testing."""

import sys, os
import json
from pathlib    import Path

def hello(name:str='World'):
    print(f'Hello, {name}!')
    unused_var = 42

if __name__=='__main__':
    hello() 