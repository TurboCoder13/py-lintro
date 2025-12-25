"""Sample Python file with security violations for testing Bandit integration."""

import subprocess
import pickle
import os

# Hardcoded password (B105)
password = "secret123"

# Hardcoded password in dictionary (B106)
config = {"password": "admin123"}

# Hardcoded password in URL (B107)
database_url = "postgres://user:secret@localhost/db"


def run_command(user_input):
    """Function with command injection vulnerability (B602)."""
    # Command injection - subprocess with shell=True
    subprocess.call(user_input, shell=True)

    # Starting process with partial path (B607)
    subprocess.call("ls", shell=True)


def unsafe_deserialization(data):
    """Function with pickle vulnerability (B301)."""
    # Unsafe pickle deserialization
    return pickle.loads(data)


def hardcoded_secret():
    """Function with hardcoded secret (B105)."""
    api_key = "sk-1234567890abcdef"
    return api_key


if __name__ == "__main__":
    # Use of weak cryptographic hash (B303)
    import hashlib

    hash_obj = hashlib.md5()
    hash_obj.update(b"test")
