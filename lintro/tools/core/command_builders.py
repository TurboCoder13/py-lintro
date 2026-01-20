"""Command builder registry for language-specific tool execution.

This module provides a registry pattern for determining how to invoke
external tools based on their runtime environment (Python, Node.js, Cargo, etc.).

The registry pattern:
- Satisfies ISP (BaseToolPlugin doesn't know about any language)
- Satisfies OCP (add new languages without modifying existing code)
- Provides extensibility for future languages (Go, Ruby, etc.)

Example:
    # Register a new language builder
    @register_command_builder
    class GoBuilder(CommandBuilder):
        def can_handle(self, tool_name_enum: ToolName | None) -> bool:
            return tool_name_enum in {ToolName.GOLINT, ToolName.STATICCHECK}

        def get_command(
            self,
            tool_name: str,
            tool_name_enum: ToolName | None,
        ) -> list[str]:
            return [tool_name]
"""

from __future__ import annotations

import shutil
import sys
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from lintro.enums.tool_name import ToolName


class CommandBuilder(ABC):
    """Abstract base for language-specific command builders.

    Subclasses implement language-specific logic for determining
    how to invoke tools (e.g., via Python module, npx, cargo).
    """

    @abstractmethod
    def can_handle(self, tool_name_enum: ToolName | None) -> bool:
        """Check if this builder can handle the given tool.

        Args:
            tool_name_enum: Tool name enum, or None if unknown.

        Returns:
            True if this builder should handle the tool.
        """
        ...

    @abstractmethod
    def get_command(
        self,
        tool_name: str,
        tool_name_enum: ToolName | None,
    ) -> list[str]:
        """Get the command to execute the tool.

        Args:
            tool_name: String name of the tool.
            tool_name_enum: Tool name enum, or None if unknown.

        Returns:
            Command list to execute the tool.
        """
        ...


class CommandBuilderRegistry:
    """Registry for command builders.

    Builders are checked in registration order. First builder that
    can_handle() the tool wins.

    This is a class-level registry that accumulates builders as they
    are registered via the @register_command_builder decorator.
    """

    _builders: list[CommandBuilder] = []

    @classmethod
    def register(cls, builder: CommandBuilder) -> None:
        """Register a command builder.

        Args:
            builder: The command builder instance to register.
        """
        cls._builders.append(builder)

    @classmethod
    def get_command(
        cls,
        tool_name: str,
        tool_name_enum: ToolName | None,
    ) -> list[str]:
        """Get command for a tool using registered builders.

        Iterates through registered builders in order, returning the
        command from the first builder that can handle the tool.

        Args:
            tool_name: String name of the tool.
            tool_name_enum: Tool name enum, or None if unknown.

        Returns:
            Command list, or [tool_name] as fallback.
        """
        for builder in cls._builders:
            if builder.can_handle(tool_name_enum):
                return builder.get_command(tool_name, tool_name_enum)

        # Fallback: just use the tool name directly
        return [tool_name]

    @classmethod
    def clear(cls) -> None:
        """Clear all registered builders (for testing)."""
        cls._builders = []

    @classmethod
    def is_registered(cls, tool_name_enum: ToolName | None) -> bool:
        """Check if any builder can handle the given tool.

        Args:
            tool_name_enum: Tool name enum to check.

        Returns:
            True if a builder exists for this tool.
        """
        return any(b.can_handle(tool_name_enum) for b in cls._builders)


def register_command_builder(cls: type[CommandBuilder]) -> type[CommandBuilder]:
    """Decorator to register a command builder.

    Args:
        cls: The CommandBuilder subclass to register.

    Returns:
        The same class, unmodified.
    """
    CommandBuilderRegistry.register(cls())
    return cls


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------


def _is_compiled_binary() -> bool:
    """Detect if running as a Nuitka-compiled binary.

    When compiled with Nuitka, sys.executable points to the lintro binary
    itself, not a Python interpreter.

    Returns:
        True if running as a compiled binary, False otherwise.
    """
    from lintro.plugins.subprocess_executor import is_compiled_binary

    return is_compiled_binary()


# -----------------------------------------------------------------------------
# Built-in Builders
# -----------------------------------------------------------------------------


@register_command_builder
class PythonBundledBuilder(CommandBuilder):
    """Builder for Python tools bundled with Lintro.

    Handles: ruff, black, bandit, yamllint, mypy, darglint.

    When running as a compiled binary, uses runtime discovery to find
    tools in PATH. Otherwise, uses Python module execution.
    """

    _tools: frozenset[ToolName] | None = None

    @property
    def tools(self) -> frozenset[ToolName]:
        """Get the set of tools this builder handles.

        Returns:
            Frozen set of ToolName enums for Python bundled tools.
        """
        if self._tools is None:
            from lintro.enums.tool_name import ToolName

            self._tools = frozenset(
                {
                    ToolName.RUFF,
                    ToolName.BLACK,
                    ToolName.BANDIT,
                    ToolName.YAMLLINT,
                    ToolName.MYPY,
                },
            )
        return self._tools

    def can_handle(self, tool_name_enum: ToolName | None) -> bool:
        """Check if this builder handles the tool.

        Args:
            tool_name_enum: Tool name enum to check.

        Returns:
            True if tool is a Python bundled tool.
        """
        return tool_name_enum in self.tools

    def get_command(
        self,
        tool_name: str,
        tool_name_enum: ToolName | None,
    ) -> list[str]:
        """Get command for Python bundled tool.

        Args:
            tool_name: String name of the tool.
            tool_name_enum: Tool name enum.

        Returns:
            Command list to execute the tool.
        """
        if _is_compiled_binary():
            from lintro.tools.core.runtime_discovery import get_tool_path

            tool_path = get_tool_path(tool_name)
            if tool_path:
                return [tool_path]
            logger.debug(f"Tool {tool_name} not found in PATH, using name directly")
            return [tool_name]

        # Normal mode: use Python module execution
        python_exe = sys.executable
        if python_exe:
            return [python_exe, "-m", tool_name]
        return [tool_name]


@register_command_builder
class PytestBuilder(CommandBuilder):
    """Builder for pytest (special case of Python tool).

    Pytest is handled separately because it uses a different module
    invocation pattern and requires special handling for compiled binaries.
    """

    def can_handle(self, tool_name_enum: ToolName | None) -> bool:
        """Check if this builder handles pytest.

        Args:
            tool_name_enum: Tool name enum to check.

        Returns:
            True if tool is pytest.
        """
        from lintro.enums.tool_name import ToolName

        return tool_name_enum == ToolName.PYTEST

    def get_command(
        self,
        tool_name: str,
        tool_name_enum: ToolName | None,
    ) -> list[str]:
        """Get command for pytest.

        Args:
            tool_name: String name of the tool.
            tool_name_enum: Tool name enum.

        Returns:
            Command list to execute pytest.
        """
        if _is_compiled_binary():
            from lintro.tools.core.runtime_discovery import get_tool_path

            tool_path = get_tool_path("pytest")
            if tool_path:
                return [tool_path]
            return ["pytest"]

        # Normal mode: use Python module execution
        python_exe = sys.executable
        if python_exe:
            return [python_exe, "-m", "pytest"]
        return ["pytest"]


@register_command_builder
class NodeJSBuilder(CommandBuilder):
    """Builder for Node.js tools (Prettier, Biome, Markdownlint).

    Uses bunx to run Node.js tools when available, falling back to
    direct tool invocation if bunx is not found.
    """

    _package_names: dict[ToolName, str] | None = None

    @property
    def package_names(self) -> dict[ToolName, str]:
        """Get mapping of tools to package names.

        Returns:
            Dictionary mapping ToolName to package name.
        """
        if self._package_names is None:
            from lintro.enums.tool_name import ToolName

            self._package_names = {
                ToolName.BIOME: "@biomejs/biome",
                ToolName.PRETTIER: "prettier",
                ToolName.MARKDOWNLINT: "markdownlint-cli2",
            }
        return self._package_names

    def can_handle(self, tool_name_enum: ToolName | None) -> bool:
        """Check if this builder handles the tool.

        Args:
            tool_name_enum: Tool name enum to check.

        Returns:
            True if tool is a Node.js tool.
        """
        return tool_name_enum in self.package_names

    def get_command(
        self,
        tool_name: str,
        tool_name_enum: ToolName | None,
    ) -> list[str]:
        """Get command for Node.js tool.

        Args:
            tool_name: String name of the tool.
            tool_name_enum: Tool name enum.

        Returns:
            Command list to execute the tool via bunx or directly.
        """
        if tool_name_enum is None:
            return [tool_name]
        package_name = self.package_names.get(tool_name_enum, tool_name)
        # Prefer bunx (bun), fall back to npx (npm), then direct tool invocation
        if shutil.which("bunx"):
            return ["bunx", package_name]
        if shutil.which("npx"):
            return ["npx", package_name]
        return [tool_name]


@register_command_builder
class CargoBuilder(CommandBuilder):
    """Builder for Cargo/Rust tools (Clippy, cargo-audit).

    Invokes Rust tools via cargo subcommands.
    """

    def can_handle(self, tool_name_enum: ToolName | None) -> bool:
        """Check if this builder handles the tool.

        Args:
            tool_name_enum: Tool name enum to check.

        Returns:
            True if tool is a Cargo/Rust tool.
        """
        from lintro.enums.tool_name import ToolName

        return tool_name_enum in {ToolName.CLIPPY, ToolName.CARGO_AUDIT}

    def get_command(
        self,
        tool_name: str,
        tool_name_enum: ToolName | None,
    ) -> list[str]:
        """Get command for Cargo tool.

        Args:
            tool_name: String name of the tool.
            tool_name_enum: Tool name enum.

        Returns:
            Command list to execute the tool via cargo.
        """
        from lintro.enums.tool_name import ToolName

        if tool_name_enum is None:
            return ["cargo", "clippy"]

        # Mapping of cargo tools to their subcommands for extensibility
        cargo_subcommands: dict[ToolName, str] = {
            ToolName.CARGO_AUDIT: "audit",
            ToolName.CLIPPY: "clippy",
        }
        subcommand = cargo_subcommands.get(tool_name_enum, "clippy")
        return ["cargo", subcommand]


@register_command_builder
class StandaloneBuilder(CommandBuilder):
    """Builder for standalone binary tools (Hadolint, Actionlint).

    These tools are invoked directly by name without any wrapper.
    """

    _tools: frozenset[ToolName] | None = None

    @property
    def tools(self) -> frozenset[ToolName]:
        """Get the set of tools this builder handles.

        Returns:
            Frozen set of ToolName enums for standalone tools.
        """
        if self._tools is None:
            from lintro.enums.tool_name import ToolName

            self._tools = frozenset(
                {
                    ToolName.HADOLINT,
                    ToolName.ACTIONLINT,
                    ToolName.DARGLINT,
                },
            )
        return self._tools

    def can_handle(self, tool_name_enum: ToolName | None) -> bool:
        """Check if this builder handles the tool.

        Args:
            tool_name_enum: Tool name enum to check.

        Returns:
            True if tool is a standalone binary.
        """
        return tool_name_enum in self.tools

    def get_command(
        self,
        tool_name: str,
        tool_name_enum: ToolName | None,
    ) -> list[str]:
        """Get command for standalone tool.

        Args:
            tool_name: String name of the tool.
            tool_name_enum: Tool name enum.

        Returns:
            Command list containing just the tool name.
        """
        return [tool_name]
