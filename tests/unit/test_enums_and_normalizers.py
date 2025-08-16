"""Tests for enums and normalizer functions."""

from lintro.enums.darglint_strictness import (
    DarglintStrictness,
    normalize_darglint_strictness,
)
from lintro.enums.group_by import GroupBy, normalize_group_by
from lintro.enums.hadolint_enums import (
    HadolintFailureThreshold,
    HadolintFormat,
    normalize_hadolint_format,
    normalize_hadolint_threshold,
)
from lintro.enums.output_format import OutputFormat, normalize_output_format
from lintro.enums.tool_name import ToolName, normalize_tool_name
from lintro.enums.yamllint_format import YamllintFormat, normalize_yamllint_format


def test_output_format_normalization():
    assert normalize_output_format("grid") == OutputFormat.GRID
    assert normalize_output_format(OutputFormat.JSON) == OutputFormat.JSON
    # fallback
    assert normalize_output_format("unknown") == OutputFormat.GRID


def test_group_by_normalization():
    assert normalize_group_by("file") == GroupBy.FILE
    assert normalize_group_by(GroupBy.AUTO) == GroupBy.AUTO
    assert normalize_group_by("bad") == GroupBy.FILE


def test_tool_name_normalization():
    assert normalize_tool_name("ruff") == ToolName.RUFF
    assert normalize_tool_name(ToolName.PRETTIER) == ToolName.PRETTIER


def test_yamllint_format_normalization():
    assert normalize_yamllint_format("parsable") == YamllintFormat.PARSABLE
    assert normalize_yamllint_format(YamllintFormat.GITHUB) == YamllintFormat.GITHUB


def test_hadolint_normalization():
    assert normalize_hadolint_format("json") == HadolintFormat.JSON
    assert normalize_hadolint_threshold("warning") == HadolintFailureThreshold.WARNING
    # defaults
    assert normalize_hadolint_format("bogus") == HadolintFormat.TTY
    assert normalize_hadolint_threshold("bogus") == HadolintFailureThreshold.INFO


def test_darglint_strictness_normalization():
    assert normalize_darglint_strictness("full") == DarglintStrictness.FULL
    assert normalize_darglint_strictness(DarglintStrictness.SHORT) == (
        DarglintStrictness.SHORT
    )
