"""Parser modules for Lintro tools."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

from .base_issue import BaseIssue
from .streaming import (
    StreamingParser,
    collect_streaming_results,
    stream_json_array_fallback,
    stream_json_lines,
    stream_text_lines,
)

if TYPE_CHECKING:
    # Type checking imports
    from lintro.parsers import (
        actionlint,
        bandit,
        biome,
        black,
        hadolint,
        markdownlint,
        mypy,
        prettier,
        pydoclint,
        pytest,
        ruff,
        semgrep,
        yamllint,
    )

__all__ = [
    "BaseIssue",
    "StreamingParser",
    "actionlint",
    "bandit",
    "biome",
    "black",
    "collect_streaming_results",
    "hadolint",
    "markdownlint",
    "mypy",
    "prettier",
    "pydoclint",
    "pytest",
    "ruff",
    "semgrep",
    "stream_json_array_fallback",
    "stream_json_lines",
    "stream_text_lines",
    "yamllint",
]

# Lazy-load parser submodules to avoid circular imports
_SUBMODULES = {
    "actionlint",
    "bandit",
    "biome",
    "black",
    "hadolint",
    "markdownlint",
    "mypy",
    "prettier",
    "pydoclint",
    "pytest",
    "ruff",
    "semgrep",
    "yamllint",
}


def __getattr__(name: str) -> object:
    """Lazy-load parser submodules to avoid circular import issues.

    This function is called when an attribute is accessed that doesn't exist
    in the module. It allows accessing parser submodules without eagerly
    importing them all at package initialization time.

    Args:
        name: The name of the attribute being accessed.

    Returns:
        The imported submodule.

    Raises:
        AttributeError: If the requested name is not a known submodule.
    """
    if name in _SUBMODULES:
        # Safe: name validated against _SUBMODULES whitelist (internal modules only)
        module = import_module(f".{name}", __package__)  # nosemgrep: non-literal-import
        # Cache the module in this module's namespace for future access
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    """Return list of available attributes for this module.

    Returns:
        List of submodule names and other module attributes.
    """
    return list(__all__)
