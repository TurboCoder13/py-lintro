"""Tests for lintro.tools.core.option_spec module."""

from __future__ import annotations

import pytest
from assertpy import assert_that

from lintro.tools.core.option_spec import (
    OptionSpec,
    OptionType,
    ToolOptionsSpec,
    bool_option,
    enum_option,
    int_option,
    list_option,
    positive_int_option,
    str_option,
)


class TestOptionSpec:
    """Tests for OptionSpec class."""

    def test_bool_option_validates_true(self) -> None:
        """Bool option accepts True value."""
        spec = bool_option("preview", "--preview")
        spec.validate(True)  # Should not raise

    def test_bool_option_validates_false(self) -> None:
        """Bool option accepts False value."""
        spec = bool_option("preview", "--preview")
        spec.validate(False)  # Should not raise

    def test_bool_option_rejects_non_bool(self) -> None:
        """Bool option rejects non-boolean values."""
        spec = bool_option("preview", "--preview")
        with pytest.raises(ValueError, match="preview"):
            spec.validate("not a bool")

    def test_bool_option_to_cli_args_true(self) -> None:
        """Bool option converts True to CLI flag."""
        spec = bool_option("preview", "--preview")
        assert_that(spec.to_cli_args(True)).is_equal_to(["--preview"])

    def test_bool_option_to_cli_args_false(self) -> None:
        """Bool option converts False to empty list."""
        spec = bool_option("preview", "--preview")
        assert_that(spec.to_cli_args(False)).is_equal_to([])

    def test_bool_option_to_cli_args_none(self) -> None:
        """Bool option converts None to empty list."""
        spec = bool_option("preview", "--preview")
        assert_that(spec.to_cli_args(None)).is_equal_to([])

    def test_int_option_validates_valid_int(self) -> None:
        """Int option accepts valid integer."""
        spec = int_option("line_length", "--line-length", min_value=1, max_value=200)
        spec.validate(88)  # Should not raise

    def test_int_option_validates_min_boundary(self) -> None:
        """Int option accepts min boundary value."""
        spec = int_option("line_length", "--line-length", min_value=1, max_value=200)
        spec.validate(1)  # Should not raise

    def test_int_option_validates_max_boundary(self) -> None:
        """Int option accepts max boundary value."""
        spec = int_option("line_length", "--line-length", min_value=1, max_value=200)
        spec.validate(200)  # Should not raise

    def test_int_option_rejects_below_min(self) -> None:
        """Int option rejects value below minimum."""
        spec = int_option("line_length", "--line-length", min_value=1, max_value=200)
        with pytest.raises(ValueError, match="line_length"):
            spec.validate(0)

    def test_int_option_rejects_above_max(self) -> None:
        """Int option rejects value above maximum."""
        spec = int_option("line_length", "--line-length", min_value=1, max_value=200)
        with pytest.raises(ValueError, match="line_length"):
            spec.validate(201)

    def test_int_option_rejects_non_int(self) -> None:
        """Int option rejects non-integer values."""
        spec = int_option("line_length", "--line-length")
        with pytest.raises(ValueError, match="line_length"):
            spec.validate("not an int")

    def test_int_option_to_cli_args(self) -> None:
        """Int option converts to CLI args."""
        spec = int_option("line_length", "--line-length")
        assert_that(spec.to_cli_args(88)).is_equal_to(["--line-length", "88"])

    def test_positive_int_option_validates_positive(self) -> None:
        """Positive int option accepts positive integer."""
        spec = positive_int_option("timeout", "--timeout")
        spec.validate(30)  # Should not raise

    def test_positive_int_option_rejects_zero(self) -> None:
        """Positive int option rejects zero."""
        spec = positive_int_option("timeout", "--timeout")
        with pytest.raises(ValueError, match="timeout"):
            spec.validate(0)

    def test_positive_int_option_rejects_negative(self) -> None:
        """Positive int option rejects negative."""
        spec = positive_int_option("timeout", "--timeout")
        with pytest.raises(ValueError, match="timeout"):
            spec.validate(-1)

    def test_str_option_validates_string(self) -> None:
        """Str option accepts string value."""
        spec = str_option("target", "--target")
        spec.validate("py311")  # Should not raise

    def test_str_option_with_choices_validates_valid_choice(self) -> None:
        """Str option with choices accepts valid choice."""
        spec = str_option("target", "--target", choices=["py38", "py39", "py311"])
        spec.validate("py311")  # Should not raise

    def test_str_option_with_choices_rejects_invalid_choice(self) -> None:
        """Str option with choices rejects invalid choice."""
        spec = str_option("target", "--target", choices=["py38", "py39", "py311"])
        with pytest.raises(ValueError, match="target must be one of"):
            spec.validate("py37")

    def test_str_option_rejects_non_string(self) -> None:
        """Str option rejects non-string values."""
        spec = str_option("target", "--target")
        with pytest.raises(ValueError, match="target"):
            spec.validate(123)

    def test_str_option_to_cli_args(self) -> None:
        """Str option converts to CLI args."""
        spec = str_option("target", "--target")
        assert_that(spec.to_cli_args("py311")).is_equal_to(["--target", "py311"])

    def test_list_option_validates_list(self) -> None:
        """List option accepts list value."""
        spec = list_option("ignore", "--ignore")
        spec.validate(["E501", "W503"])  # Should not raise

    def test_list_option_validates_empty_list(self) -> None:
        """List option accepts empty list."""
        spec = list_option("ignore", "--ignore")
        spec.validate([])  # Should not raise

    def test_list_option_rejects_non_list(self) -> None:
        """List option rejects non-list values."""
        spec = list_option("ignore", "--ignore")
        with pytest.raises(ValueError, match="ignore"):
            spec.validate("not a list")

    def test_list_option_to_cli_args(self) -> None:
        """List option converts each item to CLI args."""
        spec = list_option("ignore", "--ignore")
        result = spec.to_cli_args(["E501", "W503"])
        assert_that(result).is_equal_to(["--ignore", "E501", "--ignore", "W503"])

    def test_list_option_to_cli_args_empty(self) -> None:
        """List option with empty list returns empty args."""
        spec = list_option("ignore", "--ignore")
        assert_that(spec.to_cli_args([])).is_equal_to([])

    def test_enum_option_validates_valid_choice(self) -> None:
        """Enum option accepts valid choice."""
        spec = enum_option("severity", "--severity", choices=["error", "warning"])
        spec.validate("error")  # Should not raise

    def test_enum_option_rejects_invalid_choice(self) -> None:
        """Enum option rejects invalid choice."""
        spec = enum_option("severity", "--severity", choices=["error", "warning"])
        with pytest.raises(ValueError, match="severity must be one of"):
            spec.validate("info")

    def test_required_option_validates_none(self) -> None:
        """Required option raises on None value."""
        spec: OptionSpec = OptionSpec(
            name="required_opt",
            cli_flag="--required",
            option_type=OptionType.STR,
            required=True,
        )
        with pytest.raises(ValueError, match="required_opt is required"):
            spec.validate(None)

    def test_optional_option_accepts_none(self) -> None:
        """Optional option accepts None value."""
        spec = str_option("optional", "--optional")
        spec.validate(None)  # Should not raise


class TestToolOptionsSpec:
    """Tests for ToolOptionsSpec class."""

    def test_add_returns_self_for_chaining(self) -> None:
        """Add method returns self for method chaining."""
        spec = ToolOptionsSpec()
        result = spec.add(bool_option("preview", "--preview"))
        assert_that(result).is_same_as(spec)

    def test_add_multiple_options_via_chaining(self) -> None:
        """Multiple options can be added via chaining."""
        spec = (
            ToolOptionsSpec()
            .add(bool_option("preview", "--preview"))
            .add(int_option("line_length", "--line-length", default=88))
            .add(str_option("target", "--target"))
        )
        assert_that(spec.options).contains_key("preview", "line_length", "target")

    def test_validate_all_valid_values(self) -> None:
        """Validate all passes for valid values."""
        spec = (
            ToolOptionsSpec()
            .add(bool_option("preview", "--preview"))
            .add(int_option("line_length", "--line-length"))
        )
        spec.validate_all({"preview": True, "line_length": 88})  # Should not raise

    def test_validate_all_rejects_invalid_value(self) -> None:
        """Validate all raises for invalid value."""
        spec = ToolOptionsSpec().add(
            int_option("line_length", "--line-length", min_value=1),
        )
        with pytest.raises(ValueError, match="line_length"):
            spec.validate_all({"line_length": 0})

    def test_validate_all_checks_required(self) -> None:
        """Validate all checks required options."""
        spec = ToolOptionsSpec().add(
            OptionSpec(
                name="required_opt",
                cli_flag="--required",
                option_type=OptionType.STR,
                required=True,
            ),
        )
        with pytest.raises(ValueError, match="required_opt is required"):
            spec.validate_all({})

    def test_validate_all_ignores_unknown_options(self) -> None:
        """Validate all ignores unknown options."""
        spec = ToolOptionsSpec().add(bool_option("known", "--known"))
        spec.validate_all({"known": True, "unknown": "value"})  # Should not raise

    def test_to_cli_args(self) -> None:
        """Convert all values to CLI args."""
        spec = (
            ToolOptionsSpec()
            .add(bool_option("preview", "--preview"))
            .add(int_option("line_length", "--line-length"))
        )
        result = spec.to_cli_args({"preview": True, "line_length": 88})
        assert_that(result).contains("--preview", "--line-length", "88")

    def test_to_cli_args_skips_false_bools(self) -> None:
        """CLI args skips False boolean values."""
        spec = ToolOptionsSpec().add(bool_option("preview", "--preview"))
        result = spec.to_cli_args({"preview": False})
        assert_that(result).is_empty()

    def test_to_cli_args_ignores_unknown_options(self) -> None:
        """CLI args ignores unknown options."""
        spec = ToolOptionsSpec().add(bool_option("known", "--known"))
        result = spec.to_cli_args({"known": True, "unknown": "value"})
        assert_that(result).is_equal_to(["--known"])

    def test_get_defaults(self) -> None:
        """Get defaults returns default values."""
        spec = (
            ToolOptionsSpec()
            .add(bool_option("preview", "--preview", default=False))
            .add(int_option("line_length", "--line-length", default=88))
            .add(str_option("target", "--target"))  # No default
        )
        defaults = spec.get_defaults()
        assert_that(defaults).is_equal_to({"preview": False, "line_length": 88})

    def test_get_defaults_empty_when_no_defaults(self) -> None:
        """Get defaults returns empty dict when no defaults."""
        spec = (
            ToolOptionsSpec()
            .add(bool_option("preview", "--preview"))
            .add(str_option("target", "--target"))
        )
        assert_that(spec.get_defaults()).is_empty()


class TestConvenienceBuilders:
    """Tests for convenience builder functions."""

    def test_bool_option_creates_correct_spec(self) -> None:
        """Bool option creates correct specification."""
        spec = bool_option("preview", "--preview", default=False, description="Enable")
        assert_that(spec.name).is_equal_to("preview")
        assert_that(spec.cli_flag).is_equal_to("--preview")
        assert_that(spec.option_type).is_equal_to(OptionType.BOOL)
        assert_that(spec.default).is_false()
        assert_that(spec.description).is_equal_to("Enable")

    def test_int_option_creates_correct_spec(self) -> None:
        """Int option creates correct specification."""
        spec = int_option("width", "--width", default=80, min_value=1, max_value=200)
        assert_that(spec.name).is_equal_to("width")
        assert_that(spec.option_type).is_equal_to(OptionType.INT)
        assert_that(spec.default).is_equal_to(80)
        assert_that(spec.min_value).is_equal_to(1)
        assert_that(spec.max_value).is_equal_to(200)

    def test_positive_int_option_creates_correct_spec(self) -> None:
        """Positive int option creates correct specification."""
        spec = positive_int_option("timeout", "--timeout", default=30)
        assert_that(spec.name).is_equal_to("timeout")
        assert_that(spec.option_type).is_equal_to(OptionType.POSITIVE_INT)
        assert_that(spec.default).is_equal_to(30)

    def test_str_option_creates_correct_spec(self) -> None:
        """Str option creates correct specification."""
        spec = str_option(
            "target",
            "--target",
            default="py311",
            choices=["py38", "py311"],
        )
        assert_that(spec.name).is_equal_to("target")
        assert_that(spec.option_type).is_equal_to(OptionType.STR)
        assert_that(spec.default).is_equal_to("py311")
        assert_that(spec.choices).is_equal_to(["py38", "py311"])

    def test_list_option_creates_correct_spec(self) -> None:
        """List option creates correct specification."""
        spec = list_option("ignore", "--ignore", default=["E501"])
        assert_that(spec.name).is_equal_to("ignore")
        assert_that(spec.option_type).is_equal_to(OptionType.LIST)
        assert_that(spec.default).is_equal_to(["E501"])

    def test_enum_option_creates_correct_spec(self) -> None:
        """Enum option creates correct specification."""
        spec = enum_option(
            "level",
            "--level",
            choices=["error", "warning"],
            default="error",
        )
        assert_that(spec.name).is_equal_to("level")
        assert_that(spec.option_type).is_equal_to(OptionType.ENUM)
        assert_that(spec.choices).is_equal_to(["error", "warning"])
        assert_that(spec.default).is_equal_to("error")
