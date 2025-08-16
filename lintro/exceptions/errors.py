"""Custom exception types for Lintro."""

from __future__ import annotations


class LintroError(Exception):
    """Base exception for all Lintro-related errors."""


class InvalidToolConfigError(LintroError):
    """Raised when a tool's configuration is invalid."""


class InvalidToolOptionError(LintroError):
    """Raised when invalid options are provided to a tool."""
