"""Registry for tool output parsers and fixability predicates.

This module provides a registry pattern for O(1) lookup of tool parsers
and fixability predicates, replacing the O(n) if/elif chains.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    ParserFunc = Callable[[str], Sequence[Any]]
    FixabilityPredicate = Callable[[object], bool]


@dataclass(frozen=True)
class ParserEntry:
    """Registry entry for a tool parser.

    Attributes:
        parse_func: Function to parse tool output into issues.
        is_fixable: Optional predicate to determine if an issue is fixable.
    """

    parse_func: ParserFunc
    is_fixable: FixabilityPredicate | None = None


class ParserRegistry:
    """O(1) lookup registry for tool output parsers.

    This registry stores parser functions and fixability predicates for each
    tool, enabling efficient dispatch without long if/elif chains.

    Example:
        >>> ParserRegistry.register("ruff", parse_ruff_output, is_fixable=ruff_fixable)
        >>> issues = ParserRegistry.parse("ruff", output)
    """

    _parsers: dict[str, ParserEntry] = {}

    @classmethod
    def register(
        cls,
        tool_name: str,
        parse_func: ParserFunc,
        is_fixable: FixabilityPredicate | None = None,
    ) -> None:
        """Register a parser for a tool.

        Args:
            tool_name: Name of the tool (case-insensitive).
            parse_func: Function that parses tool output into issues.
            is_fixable: Optional predicate to check if an issue is fixable.
        """
        cls._parsers[tool_name.lower()] = ParserEntry(
            parse_func=parse_func,
            is_fixable=is_fixable,
        )

    @classmethod
    def get(cls, tool_name: str) -> ParserEntry | None:
        """Get parser entry for a tool.

        Args:
            tool_name: Name of the tool (case-insensitive).

        Returns:
            ParserEntry if registered, None otherwise.
        """
        return cls._parsers.get(tool_name.lower())

    @classmethod
    def parse(cls, tool_name: str, output: str) -> list[Any]:
        """Parse output using registered parser.

        Args:
            tool_name: Name of the tool (case-insensitive).
            output: Raw output string from the tool.

        Returns:
            List of parsed issues, or empty list if no parser registered.
        """
        entry = cls.get(tool_name)
        if entry is None:
            return []
        return list(entry.parse_func(output))

    @classmethod
    def get_fixability_predicate(
        cls,
        tool_name: str,
    ) -> FixabilityPredicate | None:
        """Get fixability predicate for a tool.

        Args:
            tool_name: Name of the tool (case-insensitive).

        Returns:
            Fixability predicate function, or None if not registered.
        """
        entry = cls.get(tool_name)
        return entry.is_fixable if entry else None

    @classmethod
    def clear(cls) -> None:
        """Clear all registered parsers.

        Primarily useful for testing to reset registry state.
        """
        cls._parsers = {}

    @classmethod
    def is_registered(cls, tool_name: str) -> bool:
        """Check if a tool has a registered parser.

        Args:
            tool_name: Name of the tool (case-insensitive).

        Returns:
            True if the tool has a registered parser.
        """
        return tool_name.lower() in cls._parsers
