#!/usr/bin/env python3
"""Test file for semgrep."""

import ast
import subprocess


# Security issue: Hardcoded password
PASSWORD = "super_secret_password"


def run_command(cmd):
    """Run a shell command."""
    # Fix: Use shell=False and pass command as a list to prevent shell injection
    if isinstance(cmd, str):
        cmd_list = cmd.split()
    else:
        cmd_list = cmd
    result = subprocess.call(cmd_list, shell=False)
    return result


def get_user_input():
    """Get user input."""
    # Fix: Use ast.literal_eval instead of eval for safer evaluation
    user_input = input("Enter expression: ")
    try:
        # ast.literal_eval only evaluates literals like strings, numbers, tuples, etc.
        # It won't execute arbitrary code like eval() would
        result = ast.literal_eval(user_input)
        return result
    except (ValueError, SyntaxError):
        return "Invalid input: only literals allowed"


class TestClass:
    """Test class."""

    def __init__(self):
        """Initialize the class."""
        self.password = "another_hardcoded_password"

    def test_method(self, user_input):
        """Test method with potential SQL injection."""
        # Fix: Use parameterized query to prevent SQL injection
        query = "SELECT * FROM users WHERE username = %s"
        params = (user_input,)
        # Execute query (commented out for testing)
        # db.execute(query, params)
        return f"Query: {query}, Params: {params}"


if __name__ == "__main__":
    test = TestClass()
    print(test.test_method("admin"))
