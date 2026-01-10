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

import pytest
from assertpy import assert_that


def test_main_package_import() -> None:
    """Test that the main lintro package can be imported."""
    import lintro

    assert_that(lintro).is_not_none()


def test_parsers_package_import() -> None:
    """Test that lintro.parsers package can be imported without circular deps."""
    import lintro.parsers

    assert_that(lintro.parsers).is_not_none()


def test_parsers_submodules_accessible() -> None:
    """Test that all parser submodules are accessible via the parsers package."""
    import lintro.parsers

    # Verify all expected submodules are available
    assert_that(lintro.parsers, "actionlint")
    assert_that(lintro.parsers, "bandit")
    assert_that(lintro.parsers, "darglint")
    assert_that(lintro.parsers, "hadolint")
    assert_that(lintro.parsers, "prettier")
    assert_that(lintro.parsers, "ruff")
    assert_that(lintro.parsers, "yamllint")


def test_parser_submodule_direct_imports() -> None:
    """Test that parser submodules can be imported directly."""
    from lintro.parsers import (
        actionlint,
        bandit,
        darglint,
        hadolint,
        prettier,
        ruff,
        yamllint,
    )

    assert_that(actionlint).is_not_none()
    assert_that(bandit).is_not_none()
    assert_that(darglint).is_not_none()
    assert_that(hadolint).is_not_none()
    assert_that(prettier).is_not_none()
    assert_that(ruff).is_not_none()
    assert_that(yamllint).is_not_none()


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

    assert_that(parse_actionlint_output).is_not_none()
    assert_that(parse_bandit_output).is_not_none()
    assert_that(parse_darglint_output).is_not_none()
    assert_that(parse_hadolint_output).is_not_none()
    assert_that(parse_prettier_output).is_not_none()
    assert_that(parse_ruff_output).is_not_none()
    assert_that(parse_yamllint_output).is_not_none()


def test_tools_import_chain() -> None:
    """Test the full import chain from tools to parsers.

    This simulates what happens when lintro is used as a CLI or library,
    ensuring the tool -> parser import chain works without circular deps.
    """
    from lintro.plugins import ToolRegistry

    tool = ToolRegistry.get("actionlint")
    assert_that(tool).is_not_none()
    assert_that(tool.definition.name).is_equal_to("actionlint")


def test_cli_import_chain() -> None:
    """Test that the CLI can be imported (triggers full package initialization)."""
    from lintro.cli import cli

    assert_that(cli).is_not_none()


def test_formatters_package_import() -> None:
    """Test that formatters package imports work correctly."""
    import lintro.formatters

    assert_that(lintro.formatters).is_not_none()


def test_enums_package_import() -> None:
    """Test that enums package imports work correctly."""
    import lintro.enums

    assert_that(lintro.enums).is_not_none()


def test_models_package_import() -> None:
    """Test that models package imports work correctly."""
    import lintro.models

    assert_that(lintro.models).is_not_none()


def test_utils_package_import() -> None:
    """Test that utils package imports work correctly."""
    import lintro.utils

    assert_that(lintro.utils).is_not_none()


def test_cross_package_imports() -> None:
    """Test imports that cross multiple package boundaries.

    This is the most realistic test for how lintro would be used as a
    dependency, where multiple packages are imported in various orders.
    """
    # Import in various orders to catch potential circular deps
    from lintro.formatters.formatter import format_issues
    from lintro.parsers import bandit
    from lintro.plugins import ToolRegistry

    assert_that(bandit).is_not_none()
    assert_that(ToolRegistry.get("bandit")).is_not_none()
    assert_that(format_issues).is_not_none()


def test_bandit_parser_direct_import() -> None:
    """Test that bandit parser can be imported directly.

    This test specifically catches circular import issues that would occur
    when lintro is installed as a built package (wheel). The issue manifests
    when trying to import bandit parser submodules before the formatters
    have loaded, which triggers a specific circular dependency pattern.
    """
    # This import sequence triggers the circular import that was fixed
    from lintro.parsers.bandit import bandit_issue, bandit_parser

    assert_that(bandit_issue).is_not_none()
    assert_that(bandit_parser).is_not_none()


def test_parser_lazy_loading() -> None:
    """Test that parser submodules are lazily loaded, not eagerly imported.

    Verifies that accessing parser submodules through the parent package
    works via __getattr__ and doesn't cause circular imports.
    """
    import lintro.parsers

    # Access submodules via attribute access (triggers __getattr__)
    bandit = lintro.parsers.bandit
    actionlint = lintro.parsers.actionlint

    assert_that(bandit).is_not_none()
    assert_that(actionlint).is_not_none()


def test_parser_lazy_loading_attribute_error() -> None:
    """Test that accessing non-existent parser raises AttributeError.

    Verifies that the __getattr__ error handling works correctly.
    """
    import lintro.parsers

    # Accessing a non-existent submodule should raise AttributeError
    with pytest.raises(AttributeError) as exc_info:
        _ = lintro.parsers.nonexistent_parser

    assert_that(str(exc_info.value)).contains("nonexistent_parser")


def test_parser_dir_function() -> None:
    """Test that dir() works on parsers module.

    Verifies that the __dir__ function returns all available submodules.
    """
    import lintro.parsers

    # Get the directory listing of the parsers module
    dir_listing = dir(lintro.parsers)

    # All expected submodules should be in the directory
    expected_modules = {
        "actionlint",
        "bandit",
        "darglint",
        "hadolint",
        "prettier",
        "ruff",
        "yamllint",
    }

    for module in expected_modules:
        assert_that(dir_listing).contains(module)
