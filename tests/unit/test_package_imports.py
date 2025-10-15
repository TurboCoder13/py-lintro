"""Tests for package-level imports to prevent circular dependencies.

This module tests that lintro can be imported as it would be when installed
as a dependency in another project, preventing circular import issues.

Note: These tests may not catch all circular import issues when running from
source (editable install), as the issue primarily manifests when the package
is installed as a built distribution. However, these tests serve as:
1. Documentation of expected import patterns
2. Basic smoke tests for package structure
3. Regression prevention for obvious import issues
"""

from __future__ import annotations


def test_main_package_import() -> None:
    """Test that the main lintro package can be imported."""
    import lintro

    assert lintro is not None


def test_parsers_package_import() -> None:
    """Test that lintro.parsers package can be imported without circular deps."""
    import lintro.parsers

    assert lintro.parsers is not None


def test_parsers_submodules_accessible() -> None:
    """Test that all parser submodules are accessible via the parsers package."""
    import lintro.parsers

    # Verify all expected submodules are available
    assert hasattr(lintro.parsers, "actionlint")
    assert hasattr(lintro.parsers, "bandit")
    assert hasattr(lintro.parsers, "darglint")
    assert hasattr(lintro.parsers, "hadolint")
    assert hasattr(lintro.parsers, "prettier")
    assert hasattr(lintro.parsers, "ruff")
    assert hasattr(lintro.parsers, "yamllint")


def test_parser_submodule_direct_imports() -> None:
    """Test that parser submodules can be imported directly."""
    from lintro.parsers import actionlint
    from lintro.parsers import bandit
    from lintro.parsers import darglint
    from lintro.parsers import hadolint
    from lintro.parsers import prettier
    from lintro.parsers import ruff
    from lintro.parsers import yamllint

    assert actionlint is not None
    assert bandit is not None
    assert darglint is not None
    assert hadolint is not None
    assert prettier is not None
    assert ruff is not None
    assert yamllint is not None


def test_parser_functions_importable() -> None:
    """Test that parser functions can be imported from submodules.

    This simulates the pattern used in tool implementations where specific
    parser functions are imported directly.
    """
    from lintro.parsers.actionlint.actionlint_parser import parse_actionlint_output
    from lintro.parsers.bandit.bandit_parser import parse_bandit_output
    from lintro.parsers.darglint.darglint_parser import parse_darglint_output
    from lintro.parsers.hadolint.hadolint_parser import parse_hadolint_output
    from lintro.parsers.prettier.prettier_parser import parse_prettier_output
    from lintro.parsers.ruff.ruff_parser import parse_ruff_output
    from lintro.parsers.yamllint.yamllint_parser import parse_yamllint_output

    assert parse_actionlint_output is not None
    assert parse_bandit_output is not None
    assert parse_darglint_output is not None
    assert parse_hadolint_output is not None
    assert parse_prettier_output is not None
    assert parse_ruff_output is not None
    assert parse_yamllint_output is not None


def test_tools_import_chain() -> None:
    """Test the full import chain from tools to parsers.

    This simulates what happens when lintro is used as a CLI or library,
    ensuring the tool -> parser import chain works without circular deps.
    """
    from lintro.tools.implementations.tool_actionlint import ActionlintTool

    tool = ActionlintTool()
    assert tool is not None
    assert tool.name == "actionlint"


def test_cli_import_chain() -> None:
    """Test that the CLI can be imported (triggers full package initialization)."""
    from lintro.cli import cli

    assert cli is not None


def test_formatters_package_import() -> None:
    """Test that formatters package imports work correctly."""
    import lintro.formatters

    assert lintro.formatters is not None


def test_enums_package_import() -> None:
    """Test that enums package imports work correctly."""
    import lintro.enums

    assert lintro.enums is not None


def test_models_package_import() -> None:
    """Test that models package imports work correctly."""
    import lintro.models

    assert lintro.models is not None


def test_utils_package_import() -> None:
    """Test that utils package imports work correctly."""
    import lintro.utils

    assert lintro.utils is not None


def test_cross_package_imports() -> None:
    """Test imports that cross multiple package boundaries.

    This is the most realistic test for how lintro would be used as a
    dependency, where multiple packages are imported in various orders.
    """
    # Import in various orders to catch potential circular deps
    from lintro.parsers import bandit
    from lintro.tools.implementations.tool_bandit import BanditTool
    from lintro.formatters.tools.bandit_formatter import BanditTableDescriptor

    assert bandit is not None
    assert BanditTool is not None
    assert BanditTableDescriptor is not None

