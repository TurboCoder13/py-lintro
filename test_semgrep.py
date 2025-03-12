#!/usr/bin/env python3
"""Test file for semgrep."""

import os
import sys
import subprocess

# Security issue: Hardcoded password
PASSWORD = "super_secret_password"

def run_command(cmd):
    """Run a shell command."""
    # Security issue: Shell injection vulnerability
    result = subprocess.call(cmd, shell=True)
    return result

def get_user_input():
    """Get user input."""
    # Security issue: Potential eval injection
    user_input = input("Enter expression: ")
    result = eval(user_input)
    return result

class TestClass:
    """Test class."""
    
    def __init__(self):
        """Initialize the class."""
        self.password = "another_hardcoded_password"
    
    def test_method(self, user_input):
        """Test method with potential SQL injection."""
        query = f"SELECT * FROM users WHERE username = '{user_input}'"
        # Execute query (commented out for testing)
        # db.execute(query)
        return query

if __name__ == "__main__":
    test = TestClass()
    print(test.test_method("admin")) 