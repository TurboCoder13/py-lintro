"""Unit tests for tsc plugin."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from assertpy import assert_that

from lintro.enums.tool_type import ToolType

if TYPE_CHECKING:
    from lintro.tools.definitions.tsc import TscPlugin


class TestTscPluginDefinition:
    """Tests for TscPlugin definition properties."""

    def test_plugin_name(self, tsc_plugin: TscPlugin) -> None:
        """Plugin name is 'tsc'.

        Args:
            tsc_plugin: The TscPlugin instance to test.
        """
        assert_that(tsc_plugin.definition.name).is_equal_to("tsc")

    def test_plugin_description(self, tsc_plugin: TscPlugin) -> None:
        """Plugin has a description.

        Args:
            tsc_plugin: The TscPlugin instance to test.
        """
        assert_that(tsc_plugin.definition.description).is_not_empty()
        assert_that(tsc_plugin.definition.description).contains("TypeScript")

    def test_plugin_can_fix(self, tsc_plugin: TscPlugin) -> None:
        """Plugin cannot fix issues.

        Args:
            tsc_plugin: The TscPlugin instance to test.
        """
        assert_that(tsc_plugin.definition.can_fix).is_false()

    def test_plugin_tool_type(self, tsc_plugin: TscPlugin) -> None:
        """Plugin is a linter and type checker.

        Args:
            tsc_plugin: The TscPlugin instance to test.
        """
        tool_type = tsc_plugin.definition.tool_type
        assert_that(ToolType.LINTER in tool_type).is_true()
        assert_that(ToolType.TYPE_CHECKER in tool_type).is_true()

    def test_plugin_file_patterns(self, tsc_plugin: TscPlugin) -> None:
        """Plugin handles TypeScript files.

        Args:
            tsc_plugin: The TscPlugin instance to test.
        """
        patterns = tsc_plugin.definition.file_patterns
        assert_that(patterns).contains("*.ts")
        assert_that(patterns).contains("*.tsx")
        assert_that(patterns).contains("*.mts")
        assert_that(patterns).contains("*.cts")

    def test_plugin_native_configs(self, tsc_plugin: TscPlugin) -> None:
        """Plugin recognizes tsconfig.json.

        Args:
            tsc_plugin: The TscPlugin instance to test.
        """
        assert_that(tsc_plugin.definition.native_configs).contains("tsconfig.json")

    def test_plugin_priority(self, tsc_plugin: TscPlugin) -> None:
        """Plugin has same priority as mypy (82).

        Args:
            tsc_plugin: The TscPlugin instance to test.
        """
        assert_that(tsc_plugin.definition.priority).is_equal_to(82)


class TestTscPluginSetOptions:
    """Tests for TscPlugin.set_options method."""

    @pytest.mark.parametrize(
        ("option_name", "option_value"),
        [
            ("project", "tsconfig.json"),
            ("strict", True),
            ("strict", False),
            ("skip_lib_check", True),
            ("skip_lib_check", False),
        ],
        ids=[
            "project_path",
            "strict_true",
            "strict_false",
            "skip_lib_check_true",
            "skip_lib_check_false",
        ],
    )
    def test_set_options_valid(
        self,
        tsc_plugin: TscPlugin,
        option_name: str,
        option_value: object,
    ) -> None:
        """Set valid options correctly.

        Args:
            tsc_plugin: The TscPlugin instance to test.
            option_name: The name of the option to set.
            option_value: The value to set for the option.
        """
        tsc_plugin.set_options(**{option_name: option_value})  # type: ignore[arg-type]
        assert_that(tsc_plugin.options.get(option_name)).is_equal_to(option_value)

    @pytest.mark.parametrize(
        ("option_name", "invalid_value", "error_match"),
        [
            ("project", 123, "project must be a string"),
            ("strict", "yes", "strict must be a boolean"),
            ("skip_lib_check", "yes", "skip_lib_check must be a boolean"),
        ],
        ids=[
            "invalid_project_type",
            "invalid_strict_type",
            "invalid_skip_lib_check_type",
        ],
    )
    def test_set_options_invalid_type(
        self,
        tsc_plugin: TscPlugin,
        option_name: str,
        invalid_value: object,
        error_match: str,
    ) -> None:
        """Raise ValueError for invalid option types.

        Args:
            tsc_plugin: The TscPlugin instance to test.
            option_name: The name of the option to test.
            invalid_value: An invalid value for the option.
            error_match: The expected error message pattern.
        """
        with pytest.raises(ValueError, match=error_match):
            tsc_plugin.set_options(**{option_name: invalid_value})  # type: ignore[arg-type]


class TestTscPluginGetCommand:
    """Tests for TscPlugin._get_tsc_command method."""

    def test_get_command_with_tsc_available(self, tsc_plugin: TscPlugin) -> None:
        """Return direct tsc command when available.

        Args:
            tsc_plugin: The TscPlugin instance to test.
        """
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/tsc"
            cmd = tsc_plugin._get_tsc_command()
            assert_that(cmd).is_equal_to(["tsc"])

    def test_get_command_with_bunx_fallback(self, tsc_plugin: TscPlugin) -> None:
        """Fall back to bunx when tsc not directly available.

        Args:
            tsc_plugin: The TscPlugin instance to test.
        """
        with patch("shutil.which") as mock_which:

            def which_side_effect(cmd: str) -> str | None:
                if cmd == "tsc":
                    return None
                if cmd == "bunx":
                    return "/usr/bin/bunx"
                return None

            mock_which.side_effect = which_side_effect
            cmd = tsc_plugin._get_tsc_command()
            assert_that(cmd).is_equal_to(["bunx", "tsc"])

    def test_get_command_with_npx_fallback(self, tsc_plugin: TscPlugin) -> None:
        """Fall back to npx when tsc and bunx not available.

        Args:
            tsc_plugin: The TscPlugin instance to test.
        """
        with patch("shutil.which") as mock_which:

            def which_side_effect(cmd: str) -> str | None:
                if cmd == "tsc":
                    return None
                if cmd == "bunx":
                    return None
                if cmd == "npx":
                    return "/usr/bin/npx"
                return None

            mock_which.side_effect = which_side_effect
            cmd = tsc_plugin._get_tsc_command()
            assert_that(cmd).is_equal_to(["npx", "tsc"])

    def test_get_command_fallback_to_tsc(self, tsc_plugin: TscPlugin) -> None:
        """Fall back to tsc when nothing else available.

        Args:
            tsc_plugin: The TscPlugin instance to test.
        """
        with patch("shutil.which", return_value=None):
            cmd = tsc_plugin._get_tsc_command()
            assert_that(cmd).is_equal_to(["tsc"])


class TestTscPluginBuildCommand:
    """Tests for TscPlugin._build_command method."""

    def test_build_command_basic(self, tsc_plugin: TscPlugin) -> None:
        """Build basic command with required flags.

        Args:
            tsc_plugin: The TscPlugin instance to test.
        """
        with patch.object(tsc_plugin, "_get_tsc_command", return_value=["tsc"]):
            cmd = tsc_plugin._build_command(files=["src/main.ts"])
            assert_that(cmd).contains("tsc")
            assert_that(cmd).contains("--noEmit")
            assert_that(cmd).contains("--pretty")
            assert_that(cmd).contains("false")
            assert_that(cmd).contains("--skipLibCheck")
            assert_that(cmd).contains("src/main.ts")

    def test_build_command_with_project(self, tsc_plugin: TscPlugin) -> None:
        """Build command with project option.

        Args:
            tsc_plugin: The TscPlugin instance to test.
        """
        tsc_plugin.set_options(project="tsconfig.build.json")
        with patch.object(tsc_plugin, "_get_tsc_command", return_value=["tsc"]):
            cmd = tsc_plugin._build_command(files=[])
            assert_that(cmd).contains("--project")
            assert_that(cmd).contains("tsconfig.build.json")

    def test_build_command_with_strict(self, tsc_plugin: TscPlugin) -> None:
        """Build command with strict mode enabled.

        Args:
            tsc_plugin: The TscPlugin instance to test.
        """
        tsc_plugin.set_options(strict=True)
        with patch.object(tsc_plugin, "_get_tsc_command", return_value=["tsc"]):
            cmd = tsc_plugin._build_command(files=["src/main.ts"])
            assert_that(cmd).contains("--strict")

    def test_build_command_without_strict(self, tsc_plugin: TscPlugin) -> None:
        """Build command with strict mode disabled.

        Args:
            tsc_plugin: The TscPlugin instance to test.
        """
        tsc_plugin.set_options(strict=False)
        with patch.object(tsc_plugin, "_get_tsc_command", return_value=["tsc"]):
            cmd = tsc_plugin._build_command(files=["src/main.ts"])
            assert_that(cmd).contains("--noStrict")

    def test_build_command_without_skip_lib_check(self, tsc_plugin: TscPlugin) -> None:
        """Build command without skip lib check.

        Args:
            tsc_plugin: The TscPlugin instance to test.
        """
        tsc_plugin.set_options(skip_lib_check=False)
        with patch.object(tsc_plugin, "_get_tsc_command", return_value=["tsc"]):
            cmd = tsc_plugin._build_command(files=["src/main.ts"])
            assert_that(cmd).does_not_contain("--skipLibCheck")


class TestTscPluginCheck:
    """Tests for TscPlugin.check method."""

    def test_check_no_issues(self, tsc_plugin: TscPlugin) -> None:
        """Return success when no issues found.

        Args:
            tsc_plugin: The TscPlugin instance to test.
        """
        mock_ctx = MagicMock()
        mock_ctx.should_skip = False
        mock_ctx.early_result = None
        mock_ctx.files = ["src/main.ts"]
        mock_ctx.rel_files = ["src/main.ts"]
        mock_ctx.cwd = "/project"
        mock_ctx.timeout = 60

        with (
            patch.object(tsc_plugin, "_prepare_execution", return_value=mock_ctx),
            patch.object(tsc_plugin, "_get_tsc_command", return_value=["tsc"]),
            patch.object(tsc_plugin, "_run_subprocess", return_value=(True, "")),
        ):
            result = tsc_plugin.check(paths=["src"], options={})

            assert_that(result.success).is_true()
            assert_that(result.issues_count).is_equal_to(0)

    def test_check_with_issues(self, tsc_plugin: TscPlugin) -> None:
        """Return issues when type errors found.

        Args:
            tsc_plugin: The TscPlugin instance to test.
        """
        mock_ctx = MagicMock()
        mock_ctx.should_skip = False
        mock_ctx.early_result = None
        mock_ctx.files = ["src/main.ts"]
        mock_ctx.rel_files = ["src/main.ts"]
        mock_ctx.cwd = "/project"
        mock_ctx.timeout = 60

        tsc_output = "src/main.ts(10,5): error TS2322: Type 'string' is not assignable to type 'number'."

        with (
            patch.object(tsc_plugin, "_prepare_execution", return_value=mock_ctx),
            patch.object(tsc_plugin, "_get_tsc_command", return_value=["tsc"]),
            patch.object(
                tsc_plugin,
                "_run_subprocess",
                return_value=(False, tsc_output),
            ),
        ):
            result = tsc_plugin.check(paths=["src"], options={})

            assert_that(result.success).is_false()
            assert_that(result.issues_count).is_equal_to(1)
            assert_that(result.issues).is_not_empty()
            assert result.issues is not None
            # Use to_display_row() to access code since BaseIssue doesn't expose it directly
            assert_that(result.issues[0].to_display_row()["code"]).is_equal_to("TS2322")

    def test_check_skip_when_no_files(self, tsc_plugin: TscPlugin) -> None:
        """Return early result when no files to check.

        Args:
            tsc_plugin: The TscPlugin instance to test.
        """
        from lintro.models.core.tool_result import ToolResult

        mock_ctx = MagicMock()
        mock_ctx.should_skip = True
        mock_ctx.early_result = ToolResult(
            name="tsc",
            success=True,
            output="No TypeScript files to check.",
            issues_count=0,
        )

        with patch.object(tsc_plugin, "_prepare_execution", return_value=mock_ctx):
            result = tsc_plugin.check(paths=["src"], options={})

            assert_that(result.success).is_true()
            assert_that(result.output).contains("No TypeScript files")


class TestTscPluginFix:
    """Tests for TscPlugin.fix method."""

    def test_fix_raises_not_implemented(self, tsc_plugin: TscPlugin) -> None:
        """Raise NotImplementedError when fix is called.

        Args:
            tsc_plugin: The TscPlugin instance to test.
        """
        with pytest.raises(NotImplementedError, match="cannot automatically fix"):
            tsc_plugin.fix(paths=["src"], options={})
