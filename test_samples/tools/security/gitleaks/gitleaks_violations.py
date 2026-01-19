# Sample file with fake secrets for gitleaks testing.
# WARNING: These are FAKE credentials for testing purposes only!
# This file intentionally contains patterns that trigger gitleaks detection rules.
"""A module with intentional fake secrets for testing gitleaks detection."""

# AWS Access Key pattern (triggers aws-access-token rule)
# This is a FAKE key following the AKIA prefix format
AWS_ACCESS_KEY = "AKIAZ7QRSTUVWXY23456"

# GitHub PAT pattern (triggers github-pat rule)
# This is a FAKE token following the ghp_ prefix format
GITHUB_TOKEN = "ghp_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8"

# Private key pattern (triggers private-key rule)
# This is a FAKE key with invalid content
PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIIBOgIBAAJBALRiMLAHudeSA2ai2TuYkPk
-----END RSA PRIVATE KEY-----"""
