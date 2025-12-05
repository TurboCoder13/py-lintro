"""Tests for the init command."""

import json
from pathlib import Path

from assertpy import assert_that
from click.testing import CliRunner

from lintro.cli import cli
from lintro.cli_utils.commands.init import init_command


class TestInitCommand:
    """Tests for the init command."""

    def test_init_command_help(self) -> None:
        """Test that init command displays help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["init", "--help"])
        assert_that(result.exit_code).is_equal_to(0)
        assert_that(result.output).contains("Initialize Lintro configuration")
        assert_that(result.output).contains("--with-native-configs")

    def test_init_creates_default_config(self) -> None:
        """Test that init creates .lintro-config.yaml with defaults."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(init_command)
            assert_that(result.exit_code).is_equal_to(0)
            assert_that(Path(".lintro-config.yaml").exists()).is_true()

            content = Path(".lintro-config.yaml").read_text()
            assert_that(content).contains("line_length: 88")
            assert_that(content).contains("tool_order:")
            assert_that(content).contains("ruff:")
            assert_that(content).contains("prettier:")

    def test_init_creates_minimal_config(self) -> None:
        """Test that init --minimal creates minimal config."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(init_command, ["--minimal"])
            assert_that(result.exit_code).is_equal_to(0)
            assert_that(Path(".lintro-config.yaml").exists()).is_true()

            content = Path(".lintro-config.yaml").read_text()
            assert_that(content).contains("line_length: 88")
            # Minimal config should be shorter
            assert_that(len(content)).is_less_than(500)

    def test_init_refuses_overwrite_without_force(self) -> None:
        """Test that init refuses to overwrite existing config without --force."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create existing config
            Path(".lintro-config.yaml").write_text("existing: true")

            result = runner.invoke(init_command)
            assert_that(result.exit_code).is_equal_to(1)
            assert_that(result.output).contains("already exists")
            assert_that(result.output).contains("--force")

            # Original content should be preserved
            content = Path(".lintro-config.yaml").read_text()
            assert_that(content).is_equal_to("existing: true")

    def test_init_overwrites_with_force(self) -> None:
        """Test that init --force overwrites existing config."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create existing config
            Path(".lintro-config.yaml").write_text("existing: true")

            result = runner.invoke(init_command, ["--force"])
            assert_that(result.exit_code).is_equal_to(0)

            # Content should be replaced
            content = Path(".lintro-config.yaml").read_text()
            assert_that(content).contains("line_length: 88")
            assert_that(content).does_not_contain("existing: true")

    def test_init_custom_output_path(self) -> None:
        """Test that init respects --output option."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                init_command,
                ["--output", "custom-lintro.yaml"],
            )
            assert_that(result.exit_code).is_equal_to(0)
            assert_that(Path("custom-lintro.yaml").exists()).is_true()
            assert_that(Path(".lintro-config.yaml").exists()).is_false()


class TestInitWithNativeConfigs:
    """Tests for the --with-native-configs option."""

    def test_with_native_configs_creates_all_files(self) -> None:
        """Test that --with-native-configs creates native tool config files."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(init_command, ["--with-native-configs"])
            assert_that(result.exit_code).is_equal_to(0)

            # Check all files were created
            assert_that(Path(".lintro-config.yaml").exists()).is_true()
            assert_that(Path(".prettierrc.json").exists()).is_true()
            assert_that(Path(".prettierignore").exists()).is_true()
            assert_that(Path(".markdownlint-cli2.jsonc").exists()).is_true()

    def test_prettierrc_has_correct_content(self) -> None:
        """Test that .prettierrc.json has correct content."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(init_command, ["--with-native-configs"])
            assert_that(result.exit_code).is_equal_to(0)

            content = json.loads(Path(".prettierrc.json").read_text())
            assert_that(content["printWidth"]).is_equal_to(88)
            assert_that(content["semi"]).is_true()
            assert_that(content["singleQuote"]).is_true()

    def test_prettierignore_has_correct_content(self) -> None:
        """Test that .prettierignore has correct content."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(init_command, ["--with-native-configs"])
            assert_that(result.exit_code).is_equal_to(0)

            content = Path(".prettierignore").read_text()
            assert_that(content).contains("node_modules")
            assert_that(content).contains(".venv")
            assert_that(content).contains("dist")

    def test_markdownlint_has_correct_content(self) -> None:
        """Test that .markdownlint-cli2.jsonc has correct content."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(init_command, ["--with-native-configs"])
            assert_that(result.exit_code).is_equal_to(0)

            content = json.loads(Path(".markdownlint-cli2.jsonc").read_text())
            assert_that(content["config"]["MD013"]["line_length"]).is_equal_to(88)
            assert_that(content["config"]["MD013"]["code_blocks"]).is_false()
            assert_that(content["config"]["MD013"]["tables"]).is_false()

    def test_native_configs_skips_existing_without_force(self) -> None:
        """Test that native configs are skipped if they exist without --force."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create existing prettier config
            Path(".prettierrc.json").write_text('{"existing": true}')

            result = runner.invoke(init_command, ["--with-native-configs"])
            assert_that(result.exit_code).is_equal_to(0)
            assert_that(result.output).contains("Skipped .prettierrc.json")

            # Original content should be preserved
            content = Path(".prettierrc.json").read_text()
            assert_that(content).is_equal_to('{"existing": true}')

    def test_native_configs_overwrites_with_force(self) -> None:
        """Test that --force overwrites existing native configs."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create existing prettier config
            Path(".prettierrc.json").write_text('{"existing": true}')

            result = runner.invoke(
                init_command,
                ["--with-native-configs", "--force"],
            )
            assert_that(result.exit_code).is_equal_to(0)

            # Content should be replaced
            content = json.loads(Path(".prettierrc.json").read_text())
            assert_that(content).does_not_contain_key("existing")
            assert_that(content["printWidth"]).is_equal_to(88)

    def test_output_shows_all_created_files(self) -> None:
        """Test that output lists all created files."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(init_command, ["--with-native-configs"])
            assert_that(result.exit_code).is_equal_to(0)
            # Should show multiple files were created
            assert_that(result.output).matches(r"Created \d+ files")
            assert_that(result.output).contains(".lintro-config.yaml")
            assert_that(result.output).contains(".prettierrc.json")
            assert_that(result.output).contains(".prettierignore")
            assert_that(result.output).contains(".markdownlint-cli2.jsonc")


class TestInitIntegration:
    """Integration tests for the init command via CLI."""

    def test_init_via_cli(self) -> None:
        """Test that init works via the main CLI."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["init"])
            assert_that(result.exit_code).is_equal_to(0)
            assert_that(Path(".lintro-config.yaml").exists()).is_true()

    def test_init_with_native_configs_via_cli(self) -> None:
        """Test that init --with-native-configs works via the main CLI."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["init", "--with-native-configs"])
            assert_that(result.exit_code).is_equal_to(0)
            assert_that(Path(".lintro-config.yaml").exists()).is_true()
            assert_that(Path(".prettierrc.json").exists()).is_true()
