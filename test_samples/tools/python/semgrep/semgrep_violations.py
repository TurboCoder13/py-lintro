"""Sample Python file with security violations for testing Semgrep integration.

This file contains intentional security issues that Semgrep should detect
using its default rules (auto config) or Python-specific rulesets.
"""

import hashlib
import os
import pickle
import subprocess
import xml.etree.ElementTree as ET  # noqa: N817


# SQL Injection vulnerability (python.lang.security.audit.dangerous-subprocess-use)
def search_users(query: str) -> list[str]:
    """Execute a database query with user input."""
    # Dangerous: SQL injection via string formatting
    sql = f"SELECT * FROM users WHERE name = '{query}'"  # noqa: S608
    return [sql]


# Command injection vulnerability (python.lang.security.audit.dangerous-subprocess-use)
def run_command(user_input: str) -> int:
    """Run a shell command with user input."""
    # Dangerous: Command injection with shell=True
    result = subprocess.call(user_input, shell=True)  # noqa: S602, S603
    return result


# Hardcoded credentials (python.lang.security.audit.hardcoded-credentials)
def connect_database() -> dict[str, str]:
    """Return database connection parameters."""
    # Dangerous: Hardcoded password
    return {
        "host": "localhost",
        "user": "admin",
        "password": "secret123",  # noqa: S105
    }


# Insecure deserialization (python.lang.security.audit.insecure-deserialization)
def load_data(data: bytes) -> object:
    """Deserialize data from bytes."""
    # Dangerous: Pickle deserialization of untrusted data
    return pickle.loads(data)  # noqa: S301


# Weak cryptographic hash (python.lang.security.audit.weak-cryptography)
def hash_password(password: str) -> str:
    """Hash a password using MD5."""
    # Dangerous: MD5 is cryptographically weak
    return hashlib.md5(password.encode()).hexdigest()  # noqa: S324


# Path traversal vulnerability
def read_file(filename: str) -> str:
    """Read a file based on user input."""
    # Dangerous: Path traversal without sanitization
    base_path = "/var/data"
    full_path = os.path.join(base_path, filename)
    with open(full_path) as f:
        return f.read()


# XXE vulnerability (python.lang.security.audit.insecure-xml-parsing)
def parse_xml(xml_string: str) -> ET.Element:
    """Parse XML string."""
    # Dangerous: XML parsing vulnerable to XXE attacks
    return ET.fromstring(xml_string)  # noqa: S314


# SSRF vulnerability hint
def fetch_url(url: str) -> str:
    """Fetch content from a URL."""
    # Dangerous: No URL validation - potential SSRF
    import urllib.request

    return urllib.request.urlopen(url).read().decode()  # noqa: S310


# Insecure random number generation
def generate_token() -> str:
    """Generate a random token."""
    import random

    # Dangerous: Using random instead of secrets for security tokens
    return "".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=32))  # noqa: S311


if __name__ == "__main__":
    # Example usage (do not run in production)
    print(search_users("admin"))
    print(hash_password("test"))
