"""Integration tests for Mypy tool."""

import contextlib
import os
import shutil
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest
from assertpy import assert_that

from lintro.models.core.tool_result import ToolResult
from lintro.tools.implementations.tool_mypy import MypyTool


@pytest.fixture(autouse=True)  # type: ignore[untyped-decorator]
def set_lintro_test_mode_env(lintro_test_mode: object) -> Iterator[None]:
    """Disable config injection for predictable CLI args in tests.

    Args:
        lintro_test_mode: Pytest fixture that enables lintro test mode.

    Yields:
        None: Allows the test to run with modified environment.
    """
    yield


@contextlib.contextmanager
def working_directory(path: Path) -> Iterator[None]:
    """Temporarily change the working directory.

    Args:
        path: Directory to make the temporary working directory.

    Yields:
        None: Restores the previous working directory after the context.
    """
    prev_cwd = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)


@pytest.fixture  # type: ignore[untyped-decorator]
def mypy_tool() -> MypyTool:
    """Create a MypyTool instance for testing.

    Returns:
        MypyTool: Configured tool instance for assertions.
    """
    return MypyTool()


@pytest.fixture  # type: ignore[untyped-decorator]
def mypy_violation_file() -> Iterator[str]:
    """Copy the mypy_violations.py sample to a temp directory for testing.

    Yields:
        str: Path to the temporary file containing known mypy violations.
    """
    repo_root = Path(__file__).resolve().parent.parent.parent
    src = repo_root / "test_samples" / "mypy_violations.py"
    with tempfile.TemporaryDirectory() as tmpdir:
        dst = os.path.join(tmpdir, "mypy_violations.py")
        shutil.copy(src, dst)
        yield dst


@pytest.fixture  # type: ignore[untyped-decorator]
def mypy_clean_file() -> Iterator[str]:
    """Create a temporary clean Python file for mypy.

    Yields:
        str: Path to a temporary Python file without mypy violations.
    """
    content = (
        "from typing import Annotated\n\n"
        "def add(a: int, b: int) -> int:\n"
        "    return a + b\n"
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(content)
        file_path = f.name
    try:
        yield file_path
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(file_path)


class TestMypyTool:
    """Test cases for MypyTool."""

    def test_tool_initialization_defaults(self, mypy_tool: MypyTool) -> None:
        """Ensure defaults align with pyproject and ignore missing imports.

        Args:
            mypy_tool: Tool instance under test.
        """
        assert_that(mypy_tool.name).is_equal_to("mypy")
        assert_that(mypy_tool.options["strict"]).is_true()
        assert_that(mypy_tool.options["ignore_missing_imports"]).is_true()

    def test_lint_check_clean_file(
        self,
        mypy_tool: MypyTool,
        mypy_clean_file: str,
    ) -> None:
        """Check a typed file should pass without issues.

        Args:
            mypy_tool: Tool instance under test.
            mypy_clean_file: Path to a clean file.
        """
        result = mypy_tool.check([mypy_clean_file])
        assert_that(isinstance(result, ToolResult)).is_true()
        assert_that(result.success).is_true()
        assert_that(result.issues_count).is_equal_to(0)

    def test_lint_check_violations(
        self,
        mypy_tool: MypyTool,
        mypy_violation_file: str,
    ) -> None:
        """Check a file with mypy violations should fail.

        Args:
            mypy_tool: Tool instance under test.
            mypy_violation_file: Path to a file with deliberate mypy errors.
        """
        result = mypy_tool.check([mypy_violation_file])
        assert_that(isinstance(result, ToolResult)).is_true()
        assert_that(result.success).is_false()
        assert_that(result.issues_count).is_greater_than(0)

    def test_config_file_autodiscovery(
        self,
        mypy_tool: MypyTool,
        tmp_path: Path,
    ) -> None:
        """Ensure pyproject discovery sets config_file and uses it.

        Args:
            mypy_tool: Tool instance under test.
            tmp_path: Temporary project directory path.
        """
        project_dir = tmp_path
        pyproject = project_dir / "pyproject.toml"
        pyproject.write_text(
            "[tool.mypy]\nstrict = true\nfiles = ['.']\n",
            encoding="utf-8",
        )
        source = project_dir / "typed.py"
        source.write_text(
            "def add(a: int, b: int) -> int:\n    return a + b\n",
            encoding="utf-8",
        )

        with working_directory(project_dir):
            result = mypy_tool.check(["."])

        assert_that(result.success).is_true()
        assert_that(mypy_tool.options["config_file"]).is_equal_to(
            str(pyproject.resolve()),
        )

    def test_respects_default_excludes(
        self,
        mypy_tool: MypyTool,
        tmp_path: Path,
    ) -> None:
        """Default excludes should drop test_samples-style paths.

        Args:
            mypy_tool: Tool instance under test.
            tmp_path: Temporary project directory path.
        """
        project_dir = tmp_path
        (project_dir / "pyproject.toml").write_text(
            "[tool.mypy]\nfiles = ['.']\n",
            encoding="utf-8",
        )
        excluded_dir = project_dir / "test_samples"
        excluded_dir.mkdir()
        excluded_file = excluded_dir / "skip.py"
        excluded_file.write_text("def bad(x):\n    return x\n", encoding="utf-8")

        with working_directory(project_dir):
            result = mypy_tool.check(["."])

        assert_that(result.success).is_true()
        assert_that(result.issues_count).is_equal_to(0)
        assert_that(result.output).contains("No Python files found")

    def test_strict_mode_failure_reporting(
        self,
        mypy_tool: MypyTool,
        tmp_path: Path,
    ) -> None:
        """Strict mode should surface untyped definitions as failures.

        Args:
            mypy_tool: Tool instance under test.
            tmp_path: Temporary project directory path.
        """
        project_dir = tmp_path
        (project_dir / "pyproject.toml").write_text(
            "[tool.mypy]\nstrict = true\nfiles = ['.']\n",
            encoding="utf-8",
        )
        failing = project_dir / "untyped.py"
        failing.write_text(
            "def greet(name):\n    return name\n",
            encoding="utf-8",
        )

        with working_directory(project_dir):
            result = mypy_tool.check(["."])

        assert_that(result.success).is_false()
        assert_that(result.issues_count).is_greater_than(0)

    def test_mypy_ini_config_discovery(
        self,
        mypy_tool: MypyTool,
        tmp_path: Path,
    ) -> None:
        """mypy.ini should be discovered and used as the config source.

        Args:
            mypy_tool: Tool instance under test.
            tmp_path: Temporary project directory path.
        """
        project_dir = tmp_path
        mypy_ini = project_dir / "mypy.ini"
        mypy_ini.write_text(
            "[mypy]\nfiles = .\n",
            encoding="utf-8",
        )
        source = project_dir / "main.py"
        source.write_text(
            "def add(a: int, b: int) -> int:\n    return a + b\n",
            encoding="utf-8",
        )

        with working_directory(project_dir):
            result = mypy_tool.check(["."])

        assert_that(result.success).is_true()
        assert_that(result.issues_count).is_equal_to(0)
        assert_that(mypy_tool.options["config_file"]).is_equal_to(
            str(mypy_ini.resolve()),
        )

    def test_setup_cfg_config_discovery(
        self,
        mypy_tool: MypyTool,
        tmp_path: Path,
    ) -> None:
        """setup.cfg should be discovered when pyproject is absent.

        Args:
            mypy_tool: Tool instance under test.
            tmp_path: Temporary project directory path.
        """
        project_dir = tmp_path
        setup_cfg = project_dir / "setup.cfg"
        setup_cfg.write_text(
            "[mypy]\nfiles = .\n",
            encoding="utf-8",
        )
        source = project_dir / "core.py"
        source.write_text(
            "def sub(a: int, b: int) -> int:\n    return a - b\n",
            encoding="utf-8",
        )

        with working_directory(project_dir):
            result = mypy_tool.check(["."])

        assert_that(result.success).is_true()
        assert_that(result.issues_count).is_equal_to(0)
        assert_that(mypy_tool.options["config_file"]).is_equal_to(
            str(setup_cfg.resolve()),
        )

    def test_config_excludes_override_defaults(
        self,
        tmp_path: Path,
    ) -> None:
        """User excludes prevent default test_samples exclusions.

        Args:
            tmp_path: Temporary project directory path.
        """
        project_dir = tmp_path
        mypy_ini = project_dir / "mypy.ini"
        mypy_ini.write_text(
            "[mypy]\nfiles = .\nexclude = tests/\n",
            encoding="utf-8",
        )
        (project_dir / ".lintro-ignore").write_text("", encoding="utf-8")
        included_dir = project_dir / "test_samples"
        included_dir.mkdir()
        included_file = included_dir / "included.py"
        included_file.write_text(
            "def ok(x: int) -> int:\n    return x\n",
            encoding="utf-8",
        )
        excluded_dir = project_dir / "tests"
        excluded_dir.mkdir()
        excluded_file = excluded_dir / "ignored.py"
        excluded_file.write_text(
            "def bad(x):\n    return x\n",
            encoding="utf-8",
        )

        with working_directory(project_dir):
            local_tool = MypyTool()
            result = local_tool.check(["."])

        assert_that(result.success).is_true()
        assert_that(result.issues_count).is_equal_to(0)
        assert_that(result.output).is_none()

    def test_lintro_ignore_respected(
        self,
        tmp_path: Path,
    ) -> None:
        """Files listed in .lintro-ignore should be skipped.

        Args:
            tmp_path: Temporary project directory path.
        """
        project_dir = tmp_path
        (project_dir / ".lintro-ignore").write_text("ignored.py\n", encoding="utf-8")
        (project_dir / "pyproject.toml").write_text(
            "[tool.mypy]\nfiles = ['.']\n",
            encoding="utf-8",
        )
        ignored = project_dir / "ignored.py"
        ignored.write_text(
            "def nope(x):\n    return x\n",
            encoding="utf-8",
        )

        with working_directory(project_dir):
            local_tool = MypyTool()
            result = local_tool.check(["."])

        assert_that(result.success).is_true()
        assert_that(result.issues_count).is_equal_to(0)
        assert_that(result.output).contains("No Python files found")

    def test_python_version_not_added_when_enforced(
        self,
        mypy_tool: MypyTool,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Avoid duplicate python-version args when enforce tier is active.

        Args:
            mypy_tool: Tool instance under test.
            monkeypatch: Pytest monkeypatch fixture to override tool behavior.
        """
        mypy_tool.set_options(python_version="3.13")
        monkeypatch.setattr(
            mypy_tool,
            "_get_enforced_settings",
            lambda: {"target_python"},
        )
        monkeypatch.setattr(mypy_tool, "_build_config_args", lambda: [])

        cmd = mypy_tool._build_command(files=["main.py"])

        assert_that("--python-version").is_not_in(cmd)

    def test_config_file_flag_not_duplicated(
        self,
        mypy_tool: MypyTool,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Ensure --config-file appears only once when injected.

        Args:
            mypy_tool: Tool instance under test.
            monkeypatch: Pytest monkeypatch fixture to override tool behavior.
        """
        config_path = "/tmp/custom-mypy.ini"
        mypy_tool.set_options(config_file=config_path)
        monkeypatch.setattr(
            mypy_tool,
            "_build_config_args",
            lambda: ["--config-file", config_path],
        )

        cmd = mypy_tool._build_command(files=["main.py"])

        assert_that(cmd.count("--config-file")).is_equal_to(1)
        assert_that(cmd).contains(config_path)
