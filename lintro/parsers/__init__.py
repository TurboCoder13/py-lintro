"""Parser modules for Lintro tools."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Type checking imports
    from lintro.parsers import (
        actionlint,
        bandit,
        darglint,
        eslint,
        hadolint,
        markdownlint,
        prettier,
        pytest,
        ruff,
        yamllint,
    )

__all__ = [
    "actionlint",
    "bandit",
    "darglint",
    "eslint",
    "hadolint",
    "markdownlint",
    "prettier",
    "pytest",
    "ruff",
    "yamllint",
]

# Lazy-load parser submodules to avoid circular imports
_SUBMODULES = {
    "actionlint",
    "bandit",
    "darglint",
    "eslint",
    "hadolint",
    "markdownlint",
    "prettier",
    "pytest",
    "ruff",
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
        module = import_module(f".{name}", __package__)
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
