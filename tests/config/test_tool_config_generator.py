"""Tests for tool_config_generator module."""

import json
from pathlib import Path

import pytest

from lintro.config.lintro_config import EnforceConfig, LintroConfig
from lintro.config.tool_config_generator import (
    cleanup_temp_config,
    generate_defaults_config,
    get_defaults_injection_args,
    get_enforce_cli_args,
    has_native_config,
)


class TestGetEnforceCliArgs:
    """Tests for get_enforce_cli_args."""

    def test_returns_empty_when_no_enforce_settings(self) -> None:
        """Should return empty list when no enforce settings."""
        lintro_config = LintroConfig()

        args = get_enforce_cli_args(
            tool_name="ruff",
            lintro_config=lintro_config,
        )

        assert args == []

    def test_injects_line_length_for_ruff(self) -> None:
        """Should inject --line-length for ruff."""
        lintro_config = LintroConfig(
            enforce=EnforceConfig(line_length=100),
        )

        args = get_enforce_cli_args(
            tool_name="ruff",
            lintro_config=lintro_config,
        )

        assert args == ["--line-length", "100"]

    def test_injects_line_length_for_black(self) -> None:
        """Should inject --line-length for black."""
        lintro_config = LintroConfig(
            enforce=EnforceConfig(line_length=88),
        )

        args = get_enforce_cli_args(
            tool_name="black",
            lintro_config=lintro_config,
        )

        assert args == ["--line-length", "88"]

    def test_injects_print_width_for_prettier(self) -> None:
        """Should inject --print-width for prettier."""
        lintro_config = LintroConfig(
            enforce=EnforceConfig(line_length=120),
        )

        args = get_enforce_cli_args(
            tool_name="prettier",
            lintro_config=lintro_config,
        )

        assert args == ["--print-width", "120"]

    def test_injects_target_version_for_ruff(self) -> None:
        """Should inject --target-version for ruff."""
        lintro_config = LintroConfig(
            enforce=EnforceConfig(target_python="py312"),
        )

        args = get_enforce_cli_args(
            tool_name="ruff",
            lintro_config=lintro_config,
        )

        assert args == ["--target-version", "py312"]

    def test_injects_target_version_for_black(self) -> None:
        """Should inject --target-version for black."""
        lintro_config = LintroConfig(
            enforce=EnforceConfig(target_python="py313"),
        )

        args = get_enforce_cli_args(
            tool_name="black",
            lintro_config=lintro_config,
        )

        assert args == ["--target-version", "py313"]

    def test_injects_both_line_length_and_target_version(self) -> None:
        """Should inject both settings when both are set."""
        lintro_config = LintroConfig(
            enforce=EnforceConfig(
                line_length=100,
                target_python="py313",
            ),
        )

        args = get_enforce_cli_args(
            tool_name="ruff",
            lintro_config=lintro_config,
        )

        assert "--line-length" in args
        assert "100" in args
        assert "--target-version" in args
        assert "py313" in args

    def test_returns_empty_for_unsupported_tool(self) -> None:
        """Should return empty list for tools without CLI mappings."""
        lintro_config = LintroConfig(
            enforce=EnforceConfig(line_length=100),
        )

        args = get_enforce_cli_args(
            tool_name="yamllint",
            lintro_config=lintro_config,
        )

        # yamllint doesn't support --line-length CLI flag
        assert args == []


class TestHasNativeConfig:
    """Tests for has_native_config."""

    def test_finds_prettier_config(
        self,
        tmp_path: Path,
        monkeypatch: "pytest.MonkeyPatch",
    ) -> None:
        """Should find .prettierrc file.

        Args:
            tmp_path: Temporary directory path for test files.
            monkeypatch: Pytest monkeypatch fixture.
        """
        config_file = tmp_path / ".prettierrc"
        config_file.write_text('{"singleQuote": true}')

        monkeypatch.chdir(tmp_path)
        result = has_native_config("prettier")
        assert result is True

    def test_finds_markdownlint_config(
        self,
        tmp_path: Path,
        monkeypatch: "pytest.MonkeyPatch",
    ) -> None:
        """Should find .markdownlint-cli2.jsonc file.

        Args:
            tmp_path: Temporary directory path for test files.
            monkeypatch: Pytest monkeypatch fixture.
        """
        config_file = tmp_path / ".markdownlint-cli2.jsonc"
        config_file.write_text('{"config": {"MD013": {"line_length": 88}}}')

        monkeypatch.chdir(tmp_path)
        result = has_native_config("markdownlint")
        assert result is True

    def test_finds_yamllint_config(
        self,
        tmp_path: Path,
        monkeypatch: "pytest.MonkeyPatch",
    ) -> None:
        """Should find .yamllint file.

        Args:
            tmp_path: Temporary directory path for test files.
            monkeypatch: Pytest monkeypatch fixture.
        """
        config_file = tmp_path / ".yamllint"
        config_file.write_text("extends: default")

        monkeypatch.chdir(tmp_path)
        result = has_native_config("yamllint")
        assert result is True

    def test_returns_false_for_unknown_tool(
        self,
        tmp_path: Path,
        monkeypatch: "pytest.MonkeyPatch",
    ) -> None:
        """Should return False for tools without patterns.

        Args:
            tmp_path: Temporary directory path for test files.
            monkeypatch: Pytest monkeypatch fixture.
        """
        monkeypatch.chdir(tmp_path)
        result = has_native_config("unknown_tool")
        assert result is False

    def test_returns_false_when_not_found(
        self,
        tmp_path: Path,
        monkeypatch: "pytest.MonkeyPatch",
    ) -> None:
        """Should return False when no config file exists.

        Args:
            tmp_path: Temporary directory path for test files.
            monkeypatch: Pytest monkeypatch fixture.
        """
        monkeypatch.chdir(tmp_path)
        # Create empty directory, no config files
        result = has_native_config("prettier")
        # Should return False since no config exists in empty tmp_path
        assert result is False


class TestGenerateDefaultsConfig:
    """Tests for generate_defaults_config."""

    def test_generates_defaults_when_no_native_config(
        self,
        tmp_path: Path,
        monkeypatch: "pytest.MonkeyPatch",
    ) -> None:
        """Should generate defaults config when no native config exists.

        Args:
            tmp_path: Temporary directory path for test files.
            monkeypatch: Pytest monkeypatch fixture.
        """
        lintro_config = LintroConfig(
            defaults={
                "prettier": {
                    "singleQuote": True,
                    "tabWidth": 2,
                },
            },
        )

        monkeypatch.chdir(tmp_path)
        config_path = generate_defaults_config(
            tool_name="prettier",
            lintro_config=lintro_config,
        )

        assert config_path is not None
        assert config_path.exists()
        assert config_path.suffix == ".json"

        content = json.loads(config_path.read_text())
        assert content["singleQuote"] is True
        assert content["tabWidth"] == 2

        cleanup_temp_config(config_path)

    def test_returns_none_when_native_config_exists(
        self,
        tmp_path: Path,
        monkeypatch: "pytest.MonkeyPatch",
    ) -> None:
        """Should return None when tool has native config.

        Args:
            tmp_path: Temporary directory path for test files.
            monkeypatch: Pytest monkeypatch fixture.
        """
        # Create native config
        native_config = tmp_path / ".prettierrc"
        native_config.write_text('{"singleQuote": false}')

        lintro_config = LintroConfig(
            defaults={
                "prettier": {
                    "singleQuote": True,
                },
            },
        )

        monkeypatch.chdir(tmp_path)
        config_path = generate_defaults_config(
            tool_name="prettier",
            lintro_config=lintro_config,
        )

        # Should return None because native config exists
        assert config_path is None

    def test_returns_none_when_no_defaults_defined(
        self,
        tmp_path: Path,
        monkeypatch: "pytest.MonkeyPatch",
    ) -> None:
        """Should return None when no defaults are defined.

        Args:
            tmp_path: Temporary directory path for test files.
            monkeypatch: Pytest monkeypatch fixture.
        """
        lintro_config = LintroConfig()

        monkeypatch.chdir(tmp_path)
        config_path = generate_defaults_config(
            tool_name="prettier",
            lintro_config=lintro_config,
        )

        assert config_path is None

    def test_generates_yaml_for_yamllint(
        self,
        tmp_path: Path,
        monkeypatch: "pytest.MonkeyPatch",
    ) -> None:
        """Should generate YAML format for yamllint.

        Args:
            tmp_path: Temporary directory path for test files.
            monkeypatch: Pytest monkeypatch fixture.
        """
        lintro_config = LintroConfig(
            defaults={
                "yamllint": {
                    "extends": "default",
                    "rules": {"line-length": {"max": 100}},
                },
            },
        )

        monkeypatch.chdir(tmp_path)
        config_path = generate_defaults_config(
            tool_name="yamllint",
            lintro_config=lintro_config,
        )

        assert config_path is not None
        assert config_path.exists()
        assert config_path.suffix == ".yaml"

        cleanup_temp_config(config_path)


class TestGetDefaultsInjectionArgs:
    """Tests for get_defaults_injection_args."""

    def test_returns_empty_for_none_path(self) -> None:
        """Should return empty list when no config path."""
        args = get_defaults_injection_args(
            tool_name="prettier",
            config_path=None,
        )

        assert args == []

    def test_prettier_args(self, tmp_path: Path) -> None:
        """Should return --config for Prettier.

        Args:
            tmp_path: Temporary directory path for test files.
        """
        config_path = tmp_path / "config.json"

        args = get_defaults_injection_args(
            tool_name="prettier",
            config_path=config_path,
        )

        assert args == ["--config", str(config_path)]

    def test_yamllint_args(self, tmp_path: Path) -> None:
        """Should return -c for yamllint.

        Args:
            tmp_path: Temporary directory path for test files.
        """
        config_path = tmp_path / "config.yaml"

        args = get_defaults_injection_args(
            tool_name="yamllint",
            config_path=config_path,
        )

        assert args == ["-c", str(config_path)]

    def test_markdownlint_args(self, tmp_path: Path) -> None:
        """Should return --config for markdownlint.

        Args:
            tmp_path: Temporary directory path for test files.
        """
        config_path = tmp_path / "config.json"

        args = get_defaults_injection_args(
            tool_name="markdownlint",
            config_path=config_path,
        )

        assert args == ["--config", str(config_path)]

    def test_hadolint_args(self, tmp_path: Path) -> None:
        """Should return --config for hadolint.

        Args:
            tmp_path: Temporary directory path for test files.
        """
        config_path = tmp_path / "config.yaml"

        args = get_defaults_injection_args(
            tool_name="hadolint",
            config_path=config_path,
        )

        assert args == ["--config", str(config_path)]

    def test_bandit_args(self, tmp_path: Path) -> None:
        """Should return -c for Bandit.

        Args:
            tmp_path: Temporary directory path for test files.
        """
        config_path = tmp_path / "config.yaml"

        args = get_defaults_injection_args(
            tool_name="bandit",
            config_path=config_path,
        )

        assert args == ["-c", str(config_path)]


class TestCleanupTempConfig:
    """Tests for cleanup_temp_config."""

    def test_removes_file(self, tmp_path: Path) -> None:
        """Should remove the temp file.

        Args:
            tmp_path: Temporary directory path for test files.
        """
        config_file = tmp_path / "test-config.json"
        config_file.write_text("{}")

        cleanup_temp_config(config_file)

        assert not config_file.exists()

    def test_handles_missing_file(self, tmp_path: Path) -> None:
        """Should not raise for missing file.

        Args:
            tmp_path: Temporary directory path for test files.
        """
        config_file = tmp_path / "nonexistent.json"

        # Should not raise
        cleanup_temp_config(config_file)
