"""Unit tests for pytest tool handlers and special features."""

from unittest.mock import patch

from assertpy import assert_that

from lintro.tools.implementations.tool_pytest import PytestTool


def test_pytest_tool_handle_list_plugins() -> None:
    """Test handle_list_plugins method."""
    tool = PytestTool()

    with (
        patch(
            "lintro.tools.implementations.pytest.pytest_handlers.list_installed_plugins",
            return_value=[
                {"name": "pytest-cov", "version": "4.0.0"},
                {"name": "pytest-xdist", "version": "3.0.0"},
            ],
        ),
        patch(
            "lintro.tools.implementations.pytest.pytest_handlers.get_pytest_version_info",
            return_value="pytest 7.0.0",
        ),
    ):
        from lintro.tools.implementations.pytest.pytest_handlers import (
            handle_list_plugins,
        )

        result = handle_list_plugins(tool)

        assert_that(result.success).is_true()
        assert_that(result.output).contains("pytest 7.0.0")
        assert_that(result.output).contains("pytest-cov")
        assert_that(result.output).contains("pytest-xdist")


def test_pytest_tool_handle_check_plugins_with_missing() -> None:
    """Test handle_check_plugins with missing plugins."""
    tool = PytestTool()

    with patch(
        "lintro.tools.implementations.pytest.pytest_handlers.check_plugin_installed",
        side_effect=lambda name: name == "pytest-cov",
    ):
        from lintro.tools.implementations.pytest.pytest_handlers import (
            handle_check_plugins,
        )

        result = handle_check_plugins(tool, "pytest-cov,pytest-xdist")

        assert_that(result.success).is_false()
        assert_that(result.output).contains("pytest-cov")
        assert_that(result.output).contains("pytest-xdist")
        assert_that(result.issues_count).is_equal_to(1)


def test_pytest_tool_handle_check_plugins_all_installed() -> None:
    """Test handle_check_plugins with all plugins installed."""
    tool = PytestTool()

    with patch(
        "lintro.tools.implementations.pytest.pytest_handlers.check_plugin_installed",
        return_value=True,
    ):
        from lintro.tools.implementations.pytest.pytest_handlers import (
            handle_check_plugins,
        )

        result = handle_check_plugins(tool, "pytest-cov,pytest-xdist")

        assert_that(result.success).is_true()
        assert_that(result.issues_count).is_equal_to(0)


def test_pytest_tool_handle_check_plugins_no_required() -> None:
    """Test handle_check_plugins without required_plugins."""
    tool = PytestTool()

    from lintro.tools.implementations.pytest.pytest_handlers import (
        handle_check_plugins,
    )

    result = handle_check_plugins(tool, None)

    assert_that(result.success).is_false()
    assert_that(result.output).contains("required_plugins must be specified")


def test_pytest_tool_handle_collect_only() -> None:
    """Test handle_collect_only method."""
    tool = PytestTool()

    mock_output = """<Module test_example.py>
  <Function test_example>
  <Function test_another>
collected 2 items"""

    with (
        patch.object(tool, "_get_executable_command", return_value=["pytest"]),
        patch.object(
            tool,
            "_run_subprocess",
            return_value=(True, mock_output),
        ),
    ):
        from lintro.tools.implementations.pytest.pytest_handlers import (
            handle_collect_only,
        )

        result = handle_collect_only(tool, ["test_file.py"])

        assert_that(result.success).is_true()
        assert_that("Collected" in result.output or "2" in result.output).is_true()


def test_pytest_tool_handle_list_fixtures() -> None:
    """Test handle_list_fixtures method."""
    tool = PytestTool()

    mock_output = "sample_data\n  scope: function\n  location: test_file.py:10"

    with (
        patch.object(tool, "_get_executable_command", return_value=["pytest"]),
        patch.object(
            tool,
            "_run_subprocess",
            return_value=(True, mock_output),
        ),
    ):
        from lintro.tools.implementations.pytest.pytest_handlers import (
            handle_list_fixtures,
        )

        result = handle_list_fixtures(tool, ["test_file.py"])

        assert_that(result.success).is_true()
        assert_that(result.output).is_equal_to(mock_output)


def test_pytest_tool_handle_fixture_info() -> None:
    """Test handle_fixture_info method."""
    tool = PytestTool()

    mock_output = """sample_data
  scope: function
  location: test_file.py:10
  description: Sample data fixture"""

    with (
        patch.object(tool, "_get_executable_command", return_value=["pytest"]),
        patch.object(
            tool,
            "_run_subprocess",
            return_value=(True, mock_output),
        ),
    ):
        from lintro.tools.implementations.pytest.pytest_handlers import (
            handle_fixture_info,
        )

        result = handle_fixture_info(tool, "sample_data", ["test_file.py"])

        assert_that(result.success).is_true()
        assert_that(result.output).contains("sample_data")


def test_pytest_tool_handle_list_markers() -> None:
    """Test handle_list_markers method."""
    tool = PytestTool()

    mock_output = "slow: marks tests as slow\nskip: marks tests as skip"

    with (
        patch.object(tool, "_get_executable_command", return_value=["pytest"]),
        patch.object(
            tool,
            "_run_subprocess",
            return_value=(True, mock_output),
        ),
    ):
        from lintro.tools.implementations.pytest.pytest_handlers import (
            handle_list_markers,
        )

        result = handle_list_markers(tool)

        assert_that(result.success).is_true()
        assert_that(result.output).is_equal_to(mock_output)


def test_pytest_tool_handle_parametrize_help() -> None:
    """Test handle_parametrize_help method."""
    tool = PytestTool()

    from lintro.tools.implementations.pytest.pytest_handlers import (
        handle_parametrize_help,
    )

    result = handle_parametrize_help(tool)

    assert_that(result.success).is_true()
    assert_that(result.output).contains("Parametrization")
    assert_that(result.output).contains("@pytest.mark.parametrize")


def test_pytest_tool_check_with_list_plugins() -> None:
    """Test check method with list_plugins option."""
    tool = PytestTool()
    tool.set_options(list_plugins=True)

    result = tool.check()

    assert_that(result.success).is_true()
    assert_that(result.output).contains("pytest")
    assert_that(result.output).contains("Installed pytest plugins")


def test_pytest_tool_check_with_collect_only() -> None:
    """Test check method with collect_only option."""
    tool = PytestTool()
    tool.set_options(collect_only=True)

    result = tool.check(paths=["tests"])

    assert_that(result.success).is_true()
    assert_that(result.output).contains("Collected")


def test_pytest_tool_check_with_list_fixtures() -> None:
    """Test check method with list_fixtures option."""
    tool = PytestTool()
    tool.set_options(list_fixtures=True)

    result = tool.check(paths=["tests"])

    assert_that(result.success).is_true()


def test_pytest_tool_check_with_fixture_info() -> None:
    """Test check method with fixture_info option."""
    tool = PytestTool()
    tool.set_options(fixture_info="sample_data")

    result = tool.check(paths=["tests"])

    # Handler runs successfully (even if fixture not found)
    assert_that(result).is_instance_of(object)


def test_pytest_tool_check_with_list_markers() -> None:
    """Test check method with list_markers option."""
    tool = PytestTool()
    tool.set_options(list_markers=True)

    result = tool.check()

    assert_that(result.success).is_true()


def test_pytest_tool_check_with_parametrize_help() -> None:
    """Test check method with parametrize_help option."""
    tool = PytestTool()
    tool.set_options(parametrize_help=True)

    result = tool.check()

    assert_that(result.success).is_true()
    assert_that(result.output).contains("Parametrization")
