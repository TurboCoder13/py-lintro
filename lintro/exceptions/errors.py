"""Custom exception types for Lintro."""

from __future__ import annotations


class LintroError(Exception):
    """Base exception for all Lintro-related errors."""


class InvalidToolConfigError(LintroError):
    """Raised when a tool's configuration is invalid."""


class InvalidToolOptionError(LintroError):
    """Raised when invalid options are provided to a tool."""


class ToolExecutionError(LintroError):
    """Raised when a tool fails to execute properly."""


class ToolTimeoutError(LintroError):
    """Raised when a tool execution times out."""


class ParserError(LintroError):
    """Raised when parsing tool output fails."""


class ConfigurationError(LintroError):
    """Raised when configuration loading or validation fails."""


class FileAccessError(LintroError):
    """Raised when file access operations fail."""
