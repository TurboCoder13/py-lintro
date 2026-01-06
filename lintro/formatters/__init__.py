"""Formatters for converting tool outputs into human-friendly tables.

This module provides centralized exports for all formatter functions and
table descriptors.
"""

# Tool-specific formatters and descriptors
# Base classes and utilities
from lintro.formatters.core.table_descriptor import TableDescriptor
from lintro.formatters.tools.actionlint_formatter import (
    ActionlintTableDescriptor,
    format_actionlint_issues,
)
from lintro.formatters.tools.bandit_formatter import (
    BanditTableDescriptor,
    format_bandit_issues,
)
from lintro.formatters.tools.biome_formatter import (
    BiomeTableDescriptor,
    format_biome_issues,
)
from lintro.formatters.tools.black_formatter import (
    BlackTableDescriptor,
    format_black_issues,
)
from lintro.formatters.tools.clippy_formatter import (
    ClippyTableDescriptor,
    format_clippy_issues,
)
from lintro.formatters.tools.darglint_formatter import (
    DarglintTableDescriptor,
    format_darglint_issues,
)
from lintro.formatters.tools.hadolint_formatter import (
    HadolintTableDescriptor,
    format_hadolint_issues,
)
from lintro.formatters.tools.markdownlint_formatter import (
    MarkdownlintTableDescriptor,
    format_markdownlint_issues,
)
from lintro.formatters.tools.mypy_formatter import (
    MypyTableDescriptor,
    format_mypy_issues,
)
from lintro.formatters.tools.prettier_formatter import (
    PrettierTableDescriptor,
    format_prettier_issues,
)
from lintro.formatters.tools.pytest_formatter import (
    PytestFailuresTableDescriptor,
    format_pytest_issues,
)
from lintro.formatters.tools.ruff_formatter import (
    RuffTableDescriptor,
    format_ruff_issues,
)
from lintro.formatters.tools.yamllint_formatter import (
    YamllintTableDescriptor,
    format_yamllint_issues,
)

__all__ = [
    # Actionlint
    "ActionlintTableDescriptor",
    "format_actionlint_issues",
    # Bandit
    "BanditTableDescriptor",
    "format_bandit_issues",
    # Biome
    "BiomeTableDescriptor",
    "format_biome_issues",
    # Black
    "BlackTableDescriptor",
    "format_black_issues",
    # Clippy
    "ClippyTableDescriptor",
    "format_clippy_issues",
    # Darglint
    "DarglintTableDescriptor",
    "format_darglint_issues",
    # Hadolint
    "HadolintTableDescriptor",
    "format_hadolint_issues",
    # Markdownlint
    "MarkdownlintTableDescriptor",
    "format_markdownlint_issues",
    # Mypy
    "MypyTableDescriptor",
    "format_mypy_issues",
    # Prettier
    "PrettierTableDescriptor",
    "format_prettier_issues",
    # Pytest
    "PytestFailuresTableDescriptor",
    "format_pytest_issues",
    # Ruff
    "RuffTableDescriptor",
    "format_ruff_issues",
    # Yamllint
    "YamllintTableDescriptor",
    "format_yamllint_issues",
    # Base classes
    "TableDescriptor",
]
