"""Unit tests for pytest tool initialization and basic functionality."""

import pytest
from assertpy import assert_that

from lintro.enums.tool_type import ToolType
from lintro.tools.implementations.tool_pytest import PytestTool


def test_pytest_tool_initialization() -> None:
    """Test that PytestTool initializes correctly."""
    tool = PytestTool()

    assert_that(tool.name).is_equal_to("pytest")
    assert_that(tool.description).contains("Python testing tool")
    assert_that(tool.can_fix).is_false()
    assert_that(tool.config.tool_type).is_equal_to(ToolType.TEST_RUNNER)
    assert_that(tool._default_timeout).is_equal_to(300)
    assert_that(tool.config.priority).is_equal_to(90)
    # File patterns may be loaded from config, so just check that patterns exist
    assert_that(tool.config.file_patterns).is_not_empty()
    assert_that(
        any("test" in pattern for pattern in tool.config.file_patterns),
    ).is_true()


def test_pytest_tool_set_options_valid() -> None:
    """Test setting valid options."""
    tool = PytestTool()

    tool.set_options(
        verbose=True,
        tb="short",
        maxfail=5,
        no_header=False,
        disable_warnings=True,
        json_report=True,
        junitxml="report.xml",
    )

    assert_that(tool.options["verbose"]).is_true()
    assert_that(tool.options["tb"]).is_equal_to("short")
    assert_that(tool.options["maxfail"]).is_equal_to(5)
    assert_that(tool.options["no_header"]).is_false()
    assert_that(tool.options["disable_warnings"]).is_true()
    assert_that(tool.options["json_report"]).is_true()
    assert_that(tool.options["junitxml"]).is_equal_to("report.xml")


def test_pytest_tool_set_options_invalid_verbose() -> None:
    """Test setting invalid verbose option."""
    tool = PytestTool()

    with pytest.raises(ValueError, match="verbose must be a boolean"):
        tool.set_options(verbose="invalid")


def test_pytest_tool_set_options_invalid_tb() -> None:
    """Test setting invalid tb option."""
    tool = PytestTool()

    with pytest.raises(ValueError, match="tb must be one of"):
        tool.set_options(tb="invalid")


def test_pytest_tool_set_options_invalid_maxfail() -> None:
    """Test setting invalid maxfail option."""
    tool = PytestTool()

    with pytest.raises(ValueError, match="maxfail must be a positive integer"):
        tool.set_options(maxfail="invalid")


def test_pytest_tool_set_options_invalid_no_header() -> None:
    """Test setting invalid no_header option."""
    tool = PytestTool()

    with pytest.raises(ValueError, match="no_header must be a boolean"):
        tool.set_options(no_header="invalid")


def test_pytest_tool_set_options_invalid_disable_warnings() -> None:
    """Test setting invalid disable_warnings option."""
    tool = PytestTool()

    with pytest.raises(ValueError, match="disable_warnings must be a boolean"):
        tool.set_options(disable_warnings="invalid")


def test_pytest_tool_set_options_invalid_json_report() -> None:
    """Test setting invalid json_report option."""
    tool = PytestTool()

    with pytest.raises(ValueError, match="json_report must be a boolean"):
        tool.set_options(json_report="invalid")


def test_pytest_tool_set_options_invalid_junitxml() -> None:
    """Test setting invalid junitxml option."""
    tool = PytestTool()

    with pytest.raises(ValueError, match="junitxml must be a string"):
        tool.set_options(junitxml=123)


def test_pytest_tool_set_options_invalid_run_docker_tests() -> None:
    """Test setting invalid run_docker_tests option."""
    tool = PytestTool()

    with pytest.raises(ValueError, match="run_docker_tests must be a boolean"):
        tool.set_options(run_docker_tests="invalid")


def test_pytest_tool_set_options_plugin_support() -> None:
    """Test setting plugin support options."""
    tool = PytestTool()

    tool.set_options(
        list_plugins=True,
        check_plugins=True,
        required_plugins="pytest-cov,pytest-xdist",
    )

    assert_that(tool.options["list_plugins"]).is_true()
    assert_that(tool.options["check_plugins"]).is_true()
    assert_that(tool.options["required_plugins"]).is_equal_to("pytest-cov,pytest-xdist")


def test_pytest_tool_set_options_invalid_list_plugins() -> None:
    """Test setting invalid list_plugins option."""
    tool = PytestTool()

    with pytest.raises(ValueError, match="list_plugins must be a boolean"):
        tool.set_options(list_plugins="invalid")


def test_pytest_tool_set_options_invalid_check_plugins() -> None:
    """Test setting invalid check_plugins option."""
    tool = PytestTool()

    with pytest.raises(ValueError, match="check_plugins must be a boolean"):
        tool.set_options(check_plugins="invalid")


def test_pytest_tool_set_options_invalid_required_plugins() -> None:
    """Test setting invalid required_plugins option."""
    tool = PytestTool()

    with pytest.raises(ValueError, match="required_plugins must be a string"):
        tool.set_options(required_plugins=123)


def test_pytest_tool_set_options_coverage_reports() -> None:
    """Test setting coverage report options."""
    tool = PytestTool()

    tool.set_options(
        coverage_html="htmlcov",
        coverage_xml="coverage.xml",
        coverage_report=True,
    )

    assert_that(tool.options["coverage_html"]).is_equal_to("htmlcov")
    assert_that(tool.options["coverage_xml"]).is_equal_to("coverage.xml")
    assert_that(tool.options["coverage_report"]).is_true()


def test_pytest_tool_set_options_invalid_coverage_html() -> None:
    """Test setting invalid coverage_html option."""
    tool = PytestTool()

    with pytest.raises(ValueError, match="coverage_html must be a string"):
        tool.set_options(coverage_html=123)


def test_pytest_tool_set_options_invalid_coverage_xml() -> None:
    """Test setting invalid coverage_xml option."""
    tool = PytestTool()

    with pytest.raises(ValueError, match="coverage_xml must be a string"):
        tool.set_options(coverage_xml=123)


def test_pytest_tool_set_options_invalid_coverage_report() -> None:
    """Test setting invalid coverage_report option."""
    tool = PytestTool()

    with pytest.raises(ValueError, match="coverage_report must be a boolean"):
        tool.set_options(coverage_report="invalid")


def test_pytest_tool_set_options_discovery_and_inspection() -> None:
    """Test setting discovery and inspection options."""
    tool = PytestTool()

    tool.set_options(
        collect_only=True,
        list_fixtures=True,
        fixture_info="sample_data",
        list_markers=True,
        parametrize_help=True,
    )

    assert_that(tool.options["collect_only"]).is_true()
    assert_that(tool.options["list_fixtures"]).is_true()
    assert_that(tool.options["fixture_info"]).is_equal_to("sample_data")
    assert_that(tool.options["list_markers"]).is_true()
    assert_that(tool.options["parametrize_help"]).is_true()
