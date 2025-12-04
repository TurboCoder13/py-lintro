"""Tests for the unified configuration manager."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from lintro.utils.unified_config import (
    DEFAULT_TOOL_PRIORITIES,
    GLOBAL_SETTINGS,
    ToolConfigInfo,
    ToolOrderStrategy,
    UnifiedConfigManager,
    get_effective_line_length,
    get_ordered_tools,
    get_tool_priority,
    is_tool_injectable,
    validate_config_consistency,
)


class TestToolOrderStrategy:
    """Tests for ToolOrderStrategy enum."""

    def test_has_priority_strategy(self) -> None:
        """Verify priority strategy exists."""
        assert ToolOrderStrategy.PRIORITY is not None

    def test_has_alphabetical_strategy(self) -> None:
        """Verify alphabetical strategy exists."""
        assert ToolOrderStrategy.ALPHABETICAL is not None

    def test_has_custom_strategy(self) -> None:
        """Verify custom strategy exists."""
        assert ToolOrderStrategy.CUSTOM is not None


class TestToolConfigInfo:
    """Tests for ToolConfigInfo dataclass."""

    def test_default_values(self) -> None:
        """Verify default values are set correctly."""
        info = ToolConfigInfo(tool_name="ruff")

        assert info.tool_name == "ruff"
        assert info.native_config == {}
        assert info.lintro_tool_config == {}
        assert info.effective_config == {}
        assert info.warnings == []
        assert info.is_injectable is True

    def test_custom_values(self) -> None:
        """Verify custom values are stored correctly."""
        info = ToolConfigInfo(
            tool_name="prettier",
            native_config={"printWidth": 100},
            is_injectable=False,
            warnings=["test warning"],
        )

        assert info.tool_name == "prettier"
        assert info.native_config == {"printWidth": 100}
        assert info.is_injectable is False
        assert info.warnings == ["test warning"]


class TestGlobalSettings:
    """Tests for GLOBAL_SETTINGS configuration."""

    def test_line_length_setting_exists(self) -> None:
        """Verify line_length setting is defined."""
        assert "line_length" in GLOBAL_SETTINGS

    def test_line_length_has_tools(self) -> None:
        """Verify line_length has tool mappings."""
        assert "tools" in GLOBAL_SETTINGS["line_length"]
        tools = GLOBAL_SETTINGS["line_length"]["tools"]

        assert "ruff" in tools
        assert "black" in tools
        assert "markdownlint" in tools
        assert "prettier" in tools
        assert "yamllint" in tools

    def test_line_length_has_injectable_tools(self) -> None:
        """Verify injectable tools are defined."""
        assert "injectable" in GLOBAL_SETTINGS["line_length"]
        injectable = GLOBAL_SETTINGS["line_length"]["injectable"]

        assert "ruff" in injectable
        assert "black" in injectable
        assert "markdownlint" in injectable
        # Prettier and yamllint should NOT be injectable
        assert "prettier" not in injectable
        assert "yamllint" not in injectable


class TestDefaultToolPriorities:
    """Tests for DEFAULT_TOOL_PRIORITIES."""

    def test_formatters_have_lower_priority(self) -> None:
        """Formatters should run before linters (lower priority value)."""
        assert DEFAULT_TOOL_PRIORITIES["prettier"] < DEFAULT_TOOL_PRIORITIES["ruff"]
        assert (
            DEFAULT_TOOL_PRIORITIES["black"] < DEFAULT_TOOL_PRIORITIES["markdownlint"]
        )

    def test_pytest_runs_last(self) -> None:
        """Pytest should have highest priority value (runs last)."""
        pytest_priority = DEFAULT_TOOL_PRIORITIES["pytest"]
        for tool, priority in DEFAULT_TOOL_PRIORITIES.items():
            if tool != "pytest":
                assert priority < pytest_priority


class TestIsToolInjectable:
    """Tests for is_tool_injectable function."""

    def test_ruff_is_injectable(self) -> None:
        """Ruff supports config injection."""
        assert is_tool_injectable("ruff") is True

    def test_black_is_injectable(self) -> None:
        """Black supports config injection."""
        assert is_tool_injectable("black") is True

    def test_markdownlint_is_injectable(self) -> None:
        """Markdownlint supports config injection."""
        assert is_tool_injectable("markdownlint") is True

    def test_prettier_is_not_injectable(self) -> None:
        """Prettier does not support config injection."""
        assert is_tool_injectable("prettier") is False

    def test_yamllint_is_not_injectable(self) -> None:
        """Yamllint does not support config injection."""
        assert is_tool_injectable("yamllint") is False

    def test_case_insensitive(self) -> None:
        """Injectable check should be case insensitive."""
        assert is_tool_injectable("RUFF") is True
        assert is_tool_injectable("Ruff") is True


class TestGetToolPriority:
    """Tests for get_tool_priority function."""

    @patch("lintro.utils.unified_config.get_tool_order_config")
    def test_returns_default_priority(
        self,
        mock_config: MagicMock,
    ) -> None:
        """Returns default priority when no override.

        Args:
            mock_config: Mock for get_tool_order_config function.
        """
        mock_config.return_value = {"priority_overrides": {}}

        priority = get_tool_priority("ruff")

        assert priority == DEFAULT_TOOL_PRIORITIES["ruff"]

    @patch("lintro.utils.unified_config.get_tool_order_config")
    def test_returns_override_priority(
        self,
        mock_config: MagicMock,
    ) -> None:
        """Returns override priority when configured.

        Args:
            mock_config: Mock for get_tool_order_config function.
        """
        mock_config.return_value = {"priority_overrides": {"ruff": 5}}

        priority = get_tool_priority("ruff")

        assert priority == 5

    @patch("lintro.utils.unified_config.get_tool_order_config")
    def test_returns_default_for_unknown_tool(
        self,
        mock_config: MagicMock,
    ) -> None:
        """Returns default 50 for unknown tools.

        Args:
            mock_config: Mock for get_tool_order_config function.
        """
        mock_config.return_value = {"priority_overrides": {}}

        priority = get_tool_priority("unknown_tool")

        assert priority == 50


class TestGetOrderedTools:
    """Tests for get_ordered_tools function."""

    @patch("lintro.utils.unified_config.get_tool_order_config")
    @patch("lintro.utils.unified_config.get_tool_priority")
    def test_priority_ordering(
        self,
        mock_priority: MagicMock,
        mock_config: MagicMock,
    ) -> None:
        """Tools are ordered by priority (lower first).

        Args:
            mock_priority: Mock for get_tool_priority function.
            mock_config: Mock for get_tool_order_config function.
        """
        mock_config.return_value = {"strategy": "priority"}
        mock_priority.side_effect = lambda t: {
            "prettier": 10,
            "ruff": 20,
            "bandit": 45,
        }[t]

        result = get_ordered_tools(["ruff", "bandit", "prettier"])

        assert result == ["prettier", "ruff", "bandit"]

    @patch("lintro.utils.unified_config.get_tool_order_config")
    def test_alphabetical_ordering(
        self,
        mock_config: MagicMock,
    ) -> None:
        """Tools are ordered alphabetically.

        Args:
            mock_config: Mock for get_tool_order_config function.
        """
        mock_config.return_value = {"strategy": "alphabetical"}

        result = get_ordered_tools(["ruff", "bandit", "prettier"])

        assert result == ["bandit", "prettier", "ruff"]

    @patch("lintro.utils.unified_config.get_tool_order_config")
    def test_custom_ordering(
        self,
        mock_config: MagicMock,
    ) -> None:
        """Tools follow custom order with remaining tools sorted alphabetically.

        Args:
            mock_config: Mock for get_tool_order_config function.
        """
        mock_config.return_value = {
            "strategy": "custom",
            "custom_order": ["ruff", "prettier"],
        }

        result = get_ordered_tools(["bandit", "ruff", "prettier"])

        # ruff and prettier in custom order, then bandit alphabetically
        assert result == ["ruff", "prettier", "bandit"]

    @patch("lintro.utils.unified_config.get_tool_order_config")
    def test_custom_ordering_partial_list(
        self,
        mock_config: MagicMock,
    ) -> None:
        """Custom order handles partial tool lists correctly.

        Args:
            mock_config: Mock for get_tool_order_config function.
        """
        mock_config.return_value = {
            "strategy": "custom",
            "custom_order": ["prettier", "black", "ruff"],
        }

        # Only ruff and prettier are in input, black is not
        result = get_ordered_tools(["ruff", "prettier"])

        assert result == ["prettier", "ruff"]


class TestGetEffectiveLineLength:
    """Tests for get_effective_line_length function."""

    @patch("lintro.utils.unified_config.load_lintro_tool_config")
    @patch("lintro.utils.unified_config.load_lintro_global_config")
    @patch("lintro.utils.unified_config._load_pyproject")
    @patch("lintro.utils.unified_config._load_native_tool_config")
    def test_tool_specific_config_wins(
        self,
        mock_native: MagicMock,
        mock_pyproject: MagicMock,
        mock_global: MagicMock,
        mock_tool: MagicMock,
    ) -> None:
        """Tool-specific lintro config has highest priority.

        Args:
            mock_native: Mock for _load_native_tool_config function.
            mock_pyproject: Mock for _load_pyproject function.
            mock_global: Mock for load_lintro_global_config function.
            mock_tool: Mock for load_lintro_tool_config function.
        """
        mock_tool.return_value = {"line_length": 100}
        mock_global.return_value = {"line_length": 88}

        result = get_effective_line_length("ruff")

        assert result == 100

    @patch("lintro.utils.unified_config.load_lintro_tool_config")
    @patch("lintro.utils.unified_config.load_lintro_global_config")
    @patch("lintro.utils.unified_config._load_pyproject")
    def test_global_config_fallback(
        self,
        mock_pyproject: MagicMock,
        mock_global: MagicMock,
        mock_tool: MagicMock,
    ) -> None:
        """Global lintro config is used when no tool-specific config.

        Args:
            mock_pyproject: Mock for _load_pyproject function.
            mock_global: Mock for load_lintro_global_config function.
            mock_tool: Mock for load_lintro_tool_config function.
        """
        mock_tool.return_value = {}
        mock_global.return_value = {"line_length": 88}
        mock_pyproject.return_value = {}

        result = get_effective_line_length("black")

        assert result == 88

    @patch("lintro.utils.unified_config.load_lintro_tool_config")
    @patch("lintro.utils.unified_config.load_lintro_global_config")
    @patch("lintro.utils.unified_config._load_pyproject")
    def test_ruff_config_fallback(
        self,
        mock_pyproject: MagicMock,
        mock_global: MagicMock,
        mock_tool: MagicMock,
    ) -> None:
        """Ruff's line-length is used as fallback.

        Args:
            mock_pyproject: Mock for _load_pyproject function.
            mock_global: Mock for load_lintro_global_config function.
            mock_tool: Mock for load_lintro_tool_config function.
        """
        mock_tool.return_value = {}
        mock_global.return_value = {}
        mock_pyproject.return_value = {"tool": {"ruff": {"line-length": 120}}}

        result = get_effective_line_length("black")

        assert result == 120


class TestValidateConfigConsistency:
    """Tests for validate_config_consistency function."""

    @patch("lintro.utils.unified_config.get_effective_line_length")
    @patch("lintro.utils.unified_config._load_native_tool_config")
    def test_no_warnings_when_consistent(
        self,
        mock_native: MagicMock,
        mock_effective: MagicMock,
    ) -> None:
        """No warnings when all configs are consistent.

        Args:
            mock_native: Mock for _load_native_tool_config function.
            mock_effective: Mock for get_effective_line_length function.
        """
        mock_effective.return_value = 88
        mock_native.return_value = {}

        warnings = validate_config_consistency()

        # Should have no warnings about native configs
        assert all("differs from" not in w for w in warnings)

    @patch("lintro.utils.unified_config.get_effective_line_length")
    @patch("lintro.utils.unified_config._load_native_tool_config")
    def test_warns_about_injectable_mismatch(
        self,
        mock_native: MagicMock,
        mock_effective: MagicMock,
    ) -> None:
        """Warns when injectable tool has different native config.

        Args:
            mock_native: Mock for _load_native_tool_config function.
            mock_effective: Mock for get_effective_line_length function.
        """
        mock_effective.return_value = 88

        def native_config(tool_name: str) -> dict:
            if tool_name == "black":
                return {"line-length": 100}
            return {}

        mock_native.side_effect = native_config

        warnings = validate_config_consistency()

        # Should have warning for black
        black_warnings = [w for w in warnings if "black" in w.lower()]
        assert len(black_warnings) > 0

    @patch("lintro.utils.unified_config.get_effective_line_length")
    def test_no_warnings_when_no_central_config(
        self,
        mock_effective: MagicMock,
    ) -> None:
        """No warnings when no central line_length is configured.

        Args:
            mock_effective: Mock for get_effective_line_length function.
        """
        mock_effective.return_value = None

        warnings = validate_config_consistency()

        assert warnings == []


class TestUnifiedConfigManager:
    """Tests for UnifiedConfigManager class."""

    @patch("lintro.utils.unified_config.load_lintro_global_config")
    @patch("lintro.utils.unified_config.get_tool_config_summary")
    @patch("lintro.utils.unified_config.validate_config_consistency")
    def test_initialization(
        self,
        mock_validate: MagicMock,
        mock_summary: MagicMock,
        mock_global: MagicMock,
    ) -> None:
        """Manager initializes and loads config.

        Args:
            mock_validate: Mock for validate_config_consistency function.
            mock_summary: Mock for get_tool_config_summary function.
            mock_global: Mock for load_lintro_global_config function.
        """
        mock_global.return_value = {"line_length": 88}
        mock_summary.return_value = {}
        mock_validate.return_value = []

        manager = UnifiedConfigManager()

        assert manager.global_config == {"line_length": 88}

    @patch("lintro.utils.unified_config.load_lintro_global_config")
    @patch("lintro.utils.unified_config.get_tool_config_summary")
    @patch("lintro.utils.unified_config.validate_config_consistency")
    @patch("lintro.utils.unified_config.get_ordered_tools")
    def test_get_ordered_tools(
        self,
        mock_ordered: MagicMock,
        mock_validate: MagicMock,
        mock_summary: MagicMock,
        mock_global: MagicMock,
    ) -> None:
        """Manager delegates to get_ordered_tools.

        Args:
            mock_ordered: Mock for get_ordered_tools function.
            mock_validate: Mock for validate_config_consistency function.
            mock_summary: Mock for get_tool_config_summary function.
            mock_global: Mock for load_lintro_global_config function.
        """
        mock_global.return_value = {}
        mock_summary.return_value = {}
        mock_validate.return_value = []
        mock_ordered.return_value = ["prettier", "ruff"]

        manager = UnifiedConfigManager()
        result = manager.get_ordered_tools(["ruff", "prettier"])

        assert result == ["prettier", "ruff"]
        mock_ordered.assert_called_once_with(["ruff", "prettier"])

    @patch("lintro.utils.unified_config.load_lintro_global_config")
    @patch("lintro.utils.unified_config.get_tool_config_summary")
    @patch("lintro.utils.unified_config.validate_config_consistency")
    @patch("lintro.utils.unified_config.get_effective_line_length")
    @patch("lintro.utils.unified_config.is_tool_injectable")
    @patch("lintro.utils.unified_config.load_lintro_tool_config")
    def test_apply_config_to_tool(
        self,
        mock_lintro_tool: MagicMock,
        mock_injectable: MagicMock,
        mock_line_length: MagicMock,
        mock_validate: MagicMock,
        mock_summary: MagicMock,
        mock_global: MagicMock,
    ) -> None:
        """Manager applies effective config to tool.

        Args:
            mock_lintro_tool: Mock for load_lintro_tool_config function.
            mock_injectable: Mock for is_tool_injectable function.
            mock_line_length: Mock for get_effective_line_length function.
            mock_validate: Mock for validate_config_consistency function.
            mock_summary: Mock for get_tool_config_summary function.
            mock_global: Mock for load_lintro_global_config function.
        """
        mock_global.return_value = {}
        mock_summary.return_value = {}
        mock_validate.return_value = []
        mock_injectable.return_value = True
        mock_line_length.return_value = 88
        mock_lintro_tool.return_value = {"select": ["E", "F"]}

        # Create mock tool
        mock_tool = MagicMock()
        mock_tool.name = "ruff"

        manager = UnifiedConfigManager()
        manager.apply_config_to_tool(tool=mock_tool)

        mock_tool.set_options.assert_called_once()
        call_kwargs = mock_tool.set_options.call_args[1]
        assert call_kwargs["line_length"] == 88
        assert call_kwargs["select"] == ["E", "F"]

    @patch("lintro.utils.unified_config.load_lintro_global_config")
    @patch("lintro.utils.unified_config.get_tool_config_summary")
    @patch("lintro.utils.unified_config.validate_config_consistency")
    @patch("lintro.utils.unified_config.get_effective_line_length")
    @patch("lintro.utils.unified_config.is_tool_injectable")
    @patch("lintro.utils.unified_config.load_lintro_tool_config")
    def test_cli_overrides_take_precedence(
        self,
        mock_lintro_tool: MagicMock,
        mock_injectable: MagicMock,
        mock_line_length: MagicMock,
        mock_validate: MagicMock,
        mock_summary: MagicMock,
        mock_global: MagicMock,
    ) -> None:
        """CLI overrides have highest priority.

        Args:
            mock_lintro_tool: Mock for load_lintro_tool_config function.
            mock_injectable: Mock for is_tool_injectable function.
            mock_line_length: Mock for get_effective_line_length function.
            mock_validate: Mock for validate_config_consistency function.
            mock_summary: Mock for get_tool_config_summary function.
            mock_global: Mock for load_lintro_global_config function.
        """
        mock_global.return_value = {}
        mock_summary.return_value = {}
        mock_validate.return_value = []
        mock_injectable.return_value = True
        mock_line_length.return_value = 88
        mock_lintro_tool.return_value = {"line_length": 88}

        mock_tool = MagicMock()
        mock_tool.name = "ruff"

        manager = UnifiedConfigManager()
        manager.apply_config_to_tool(
            tool=mock_tool,
            cli_overrides={"line_length": 120},
        )

        call_kwargs = mock_tool.set_options.call_args[1]
        # CLI override should win
        assert call_kwargs["line_length"] == 120
