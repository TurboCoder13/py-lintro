"""Hadolint parser module."""

from lintro.parsers.hadolint.hadolint_issue import HadolintIssue
from lintro.parsers.hadolint.hadolint_parser import parse_hadolint_output

__all__ = ["HadolintIssue", "parse_hadolint_output"]


def __getattr__(name: str) -> type[HadolintIssue]:
    """Handle deprecated attribute access.

    Args:
        name: str: Name of the attribute being accessed.

    Returns:
        type: HadolintIssue class if name is "HadolintOutput".

    Raises:
        AttributeError: If the attribute name is not "HadolintOutput".
    """
    if name == "HadolintOutput":
        import warnings

        warnings.warn(
            "HadolintOutput is deprecated, use HadolintIssue instead. "
            "HadolintOutput will be removed in a future version.",
            DeprecationWarning,
            stacklevel=2,
        )
        return HadolintIssue
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
