"""Tool-related models for Lintro."""

from abc import abstractmethod
from typing import Protocol, runtime_checkable

from lintro.models.core.tool_config import ToolConfig
from lintro.models.core.tool_result import ToolResult


@runtime_checkable
class Tool(Protocol):
    """Protocol for all linting and formatting tools.

    This protocol defines the interface that all tools must implement.
    Tools can be implemented as classes that inherit from this protocol.

    Attributes:
        name: Tool name
        description: Tool description
        can_fix: Whether the core can fix issues
        config: Tool configuration
    """

    name: str
    description: str
    can_fix: bool
    config: ToolConfig

    def set_options(
        self,
        **kwargs: object,
    ) -> None:
        """Set core options.

        Args:
            **kwargs: Tool-specific options
        """
        ...

    @abstractmethod
    def check(
        self,
        paths: list[str],
    ) -> ToolResult:
        """Check files for issues.

        Args:
            paths: List of file paths to check.

        Returns:
            Result of the check operation.

        Raises:
            FileNotFoundError: If the core executable is not found
            subprocess.TimeoutExpired: If the core execution times out
            subprocess.CalledProcessError: If the core execution fails
        """
        ...

    @abstractmethod
    def fix(
        self,
        paths: list[str],
    ) -> ToolResult:
        """Fix issues in files.

        Args:
            paths: List of file paths to fix.

        Returns:
            Result of the fix operation.

        Raises:
            FileNotFoundError: If the core executable is not found
            subprocess.TimeoutExpired: If the core execution times out
            subprocess.CalledProcessError: If the core execution fails
            NotImplementedError: If the core does not support fixing issues
        """
        ...

    @staticmethod
    def to_result(
        name: str,
        success: bool,
        output: str,
        issues_count: int,
    ) -> ToolResult:
        """Convert core operation result to a ToolResult.

        Args:
            name: Tool name
            success: Whether the operation was successful
            output: Output from the core
            issues_count: Number of issues found or fixed

        Returns:
            Result object
        """
        return ToolResult(
            name=name,
            success=success,
            output=output,
            issues_count=issues_count,
        )
