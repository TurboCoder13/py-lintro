"""Tests for lintro init command."""

from pathlib import Path

import pytest
from assertpy import assert_that
from click.testing import CliRunner

from lintro.cli_utils.commands.init import (
    DEFAULT_CONFIG_TEMPLATE,
    MINIMAL_CONFIG_TEMPLATE,
    init_command,
)


@pytest.fixture
def runner() -> CliRunner:
    """Create a Click test runner.

    Returns:
        CliRunner: A Click test runner instance.
    """
    return CliRunner()


def test_creates_minimal_template(
    runner: CliRunner,
    tmp_path: Path,
) -> None:
    """Should use minimal template with --minimal flag.

    Args:
        runner: Click test runner instance.
        tmp_path: Temporary directory path for test files.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(init_command, ["--minimal"])

        config_file = Path(".lintro-config.yaml")
        content = config_file.read_text()

        # Minimal template should be shorter
        assert "# Lintro Configuration (Minimal)" in content
        # But still have core sections
        assert_that(content).contains("enforce:")
        assert_that(content).contains("tools:")
        # Minimal doesn't have all tools
        assert "bandit:" not in content


def test_refuses_to_overwrite_existing(
    runner: CliRunner,
    tmp_path: Path,
) -> None:
    """Should refuse to overwrite existing file without --force.

    Args:
        runner: Click test runner instance.
        tmp_path: Temporary directory path for test files.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Create existing file
        Path(".lintro-config.yaml").write_text("existing content")

        result = runner.invoke(init_command)

        assert_that(result.exit_code).is_equal_to(1)
        assert "already exists" in result.output
        assert "Use --force to overwrite" in result.output

        # Original content should be preserved
        content = Path(".lintro-config.yaml").read_text()
        assert_that(content).is_equal_to("existing content")


def test_force_overwrites_existing(
    runner: CliRunner,
    tmp_path: Path,
) -> None:
    """Should overwrite existing file with --force.

    Args:
        runner: Click test runner instance.
        tmp_path: Temporary directory path for test files.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Create existing file
        Path(".lintro-config.yaml").write_text("existing content")

        result = runner.invoke(init_command, ["--force"])

        assert_that(result.exit_code).is_equal_to(0)
        assert "Created .lintro-config.yaml" in result.output

        # Should have new template content
        content = Path(".lintro-config.yaml").read_text()
        assert_that(content).contains("enforce:")


def test_custom_output_path(
    runner: CliRunner,
    tmp_path: Path,
) -> None:
    """Should create file at custom path with --output.

    Args:
        runner: Click test runner instance.
        tmp_path: Temporary directory path for test files.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            init_command,
            ["--output", "custom-config.yaml"],
        )

        assert_that(result.exit_code).is_equal_to(0)
        assert "Created custom-config.yaml" in result.output

        config_file = Path("custom-config.yaml")
        assert config_file.exists()


def test_shows_next_steps(
    runner: CliRunner,
    tmp_path: Path,
) -> None:
    """Should show helpful next steps.

    Args:
        runner: Click test runner instance.
        tmp_path: Temporary directory path for test files.
    """
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(init_command)

        assert "Next steps:" in result.output
        assert "lintro config" in result.output
        assert "lintro check" in result.output


def test_default_template_is_valid_yaml() -> None:
    """Default template should be valid YAML."""
    import yaml

    parsed = yaml.safe_load(DEFAULT_CONFIG_TEMPLATE)

    assert_that(parsed).contains("enforce")
    assert_that(parsed).contains("execution")
    assert_that(parsed).contains("tools")


def test_minimal_template_is_valid_yaml() -> None:
    """Minimal template should be valid YAML."""
    import yaml

    parsed = yaml.safe_load(MINIMAL_CONFIG_TEMPLATE)

    assert_that(parsed).contains("enforce")
    assert_that(parsed).contains("tools")


def test_default_template_has_sensible_defaults() -> None:
    """Default template should have sensible default values."""
    import yaml

    parsed = yaml.safe_load(DEFAULT_CONFIG_TEMPLATE)

    assert parsed["enforce"]["line_length"] == 88
    assert parsed["enforce"]["target_python"] == "py313"
    assert parsed["execution"]["tool_order"] == "priority"
    assert parsed["tools"]["ruff"]["enabled"] is True
    assert parsed["defaults"]["mypy"]["strict"] is True
    assert parsed["defaults"]["mypy"]["ignore_missing_imports"] is True
