"""Tool definitions for Lintro.

This package contains the tool definitions - small files that declare
what a tool IS (metadata, capabilities) without the implementation details.

Each tool has a definition file that:
1. Uses the @register_tool decorator to register with ToolRegistry
2. Defines a ToolDefinition with all metadata
3. Delegates actual execution to implementations/

Example:
    >>> # tools/definitions/hadolint.py
    >>> from lintro.plugins import register_tool, ToolDefinition
    >>> from lintro.plugins.base import BaseToolPlugin
    >>>
    >>> @register_tool
    ... class HadolintPlugin(BaseToolPlugin):
    ...     @property
    ...     def definition(self) -> ToolDefinition:
    ...         return ToolDefinition(
    ...             name="hadolint",
    ...             description="Dockerfile linter",
    ...             file_patterns=["Dockerfile", "Dockerfile.*"],
    ...         )

The definitions are loaded by the discovery system when Lintro starts.
External plugins can follow the same pattern and register via entry points.
"""

# Tool definitions are loaded dynamically by discovery.py
# This file just documents the package structure
