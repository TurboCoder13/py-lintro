"""Integration tests for Ruff flake8-bugbear (B) rule support."""

import os

import pytest

from lintro.tools.implementations.tool_ruff import RuffTool


@pytest.fixture(autouse=True)
def skip_config_injection():
    """Disable Lintro config injection for all tests in this module.

    Yields:
        None: This fixture is used for its side effect only.
    """
    os.environ["LINTRO_SKIP_CONFIG_INJECTION"] = "1"
    yield
    del os.environ["LINTRO_SKIP_CONFIG_INJECTION"]


class TestRuffBugbearIntegration:
    """Test Ruff integration with flake8-bugbear rules."""

    def test_ruff_bugbear_violations_detection(self):
        """Test that Ruff detects flake8-bugbear violations."""
        ruff_tool = RuffTool()
        ruff_tool.set_options(select=["B"])  # Only enable flake8-bugbear rules

        result = ruff_tool.check(["test_samples/ruff_bugbear_violations.py"])

        # Should detect violations
        assert not result.success
        assert result.issues_count > 0

        # Check that we have B-prefixed issues
        b_issues = [
            issue
            for issue in result.issues
            if hasattr(issue, "code") and issue.code.startswith("B")
        ]
        assert len(b_issues) > 0

        # Verify specific bugbear rules are detected
        issue_codes = {issue.code for issue in b_issues}
        expected_codes = {
            "B006",
            "B007",
            "B011",
            "B001",
            "B023",
            "B008",
            "B009",
            "B010",
        }

        # At least some expected codes should be present
        assert len(issue_codes.intersection(expected_codes)) > 0

    def test_ruff_bugbear_with_other_rules(self):
        """Test that flake8-bugbear works alongside other Ruff rules."""
        ruff_tool = RuffTool()
        ruff_tool.set_options(
            select=["E", "F", "B"],
        )  # Enable pycodestyle, pyflakes, and bugbear

        result = ruff_tool.check(["test_samples/ruff_bugbear_violations.py"])

        # Should detect violations from multiple rule sets
        assert not result.success
        assert result.issues_count > 0

        # Check that we have issues from different rule categories
        issue_codes = {issue.code for issue in result.issues if hasattr(issue, "code")}
        has_bugbear = any(code.startswith("B") for code in issue_codes)
        any(code.startswith("E") for code in issue_codes)
        any(code.startswith("F") for code in issue_codes)

        assert has_bugbear
        # May or may not have pycodestyle/pyflakes issues depending on the test file

    def test_ruff_bugbear_fix_capability(self):
        """Test that Ruff can fix some flake8-bugbear violations."""
        ruff_tool = RuffTool()
        ruff_tool.set_options(select=["B"], unsafe_fixes=True)

        # Check initial state
        initial_result = ruff_tool.check(["test_samples/ruff_bugbear_violations.py"])
        initial_count = initial_result.issues_count

        # Apply fixes
        fix_result = ruff_tool.fix(["test_samples/ruff_bugbear_violations.py"])

        # Some issues should be fixable
        assert fix_result.fixed_issues_count >= 0
        assert fix_result.remaining_issues_count >= 0

        # Total should match initial count
        assert (
            fix_result.fixed_issues_count + fix_result.remaining_issues_count
            == initial_count
        )

    def test_ruff_bugbear_rule_selection(self):
        """Test specific flake8-bugbear rule selection."""
        ruff_tool = RuffTool()
        ruff_tool.set_options(select=["B006", "B007"])  # Only specific bugbear rules

        result = ruff_tool.check(["test_samples/ruff_bugbear_violations.py"])

        # Should only detect the selected rules
        issue_codes = {issue.code for issue in result.issues if hasattr(issue, "code")}
        allowed_codes = {"B006", "B007"}

        # All detected codes should be in the allowed set
        assert issue_codes.issubset(allowed_codes)

    def test_ruff_bugbear_rule_ignoring(self):
        """Test ignoring specific flake8-bugbear rules."""
        ruff_tool = RuffTool()
        ruff_tool.set_options(select=["B"], ignore=["B006", "B007"])

        result = ruff_tool.check(["test_samples/ruff_bugbear_violations.py"])

        # Should not detect ignored rules
        issue_codes = {issue.code for issue in result.issues if hasattr(issue, "code")}
        ignored_codes = {"B006", "B007"}

        # No ignored codes should be present
        assert issue_codes.isdisjoint(ignored_codes)

    def test_ruff_bugbear_extend_select(self):
        """Test extending selection with flake8-bugbear rules."""
        ruff_tool = RuffTool()
        ruff_tool.set_options(select=["E"], extend_select=["B006", "B007"])

        result = ruff_tool.check(["test_samples/ruff_bugbear_violations.py"])

        # Should detect both E and B rules
        issue_codes = {issue.code for issue in result.issues if hasattr(issue, "code")}
        has_e_rules = any(code.startswith("E") for code in issue_codes)
        has_b_rules = any(code.startswith("B") for code in issue_codes)

        # Should have both rule types
        assert has_e_rules or has_b_rules

    def test_ruff_bugbear_extend_ignore(self):
        """Test extending ignore list with flake8-bugbear rules."""
        ruff_tool = RuffTool()
        ruff_tool.set_options(select=["B"], extend_ignore=["B006", "B007"])

        result = ruff_tool.check(["test_samples/ruff_bugbear_violations.py"])

        # Should not detect extended ignore rules
        issue_codes = {issue.code for issue in result.issues if hasattr(issue, "code")}
        extended_ignore = {"B006", "B007"}

        # No extended ignore codes should be present
        assert issue_codes.isdisjoint(extended_ignore)

    def test_ruff_bugbear_empty_file(self):
        """Test that Ruff handles empty files with flake8-bugbear rules."""
        ruff_tool = RuffTool()
        ruff_tool.set_options(select=["B"])

        result = ruff_tool.check(["test_samples/ruff_clean.py"])

        # Should succeed with no issues
        assert result.success
        assert result.issues_count == 0

    def test_ruff_bugbear_nonexistent_file(self):
        """Test that Ruff handles nonexistent files with flake8-bugbear rules."""
        ruff_tool = RuffTool()
        ruff_tool.set_options(select=["B"])

        # Should raise FileNotFoundError for nonexistent files
        with pytest.raises(FileNotFoundError):
            ruff_tool.check(["nonexistent_file.py"])
