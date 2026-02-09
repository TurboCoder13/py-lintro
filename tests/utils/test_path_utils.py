"""Tests for the path utilities module."""

from pathlib import Path
from unittest.mock import patch

import pytest
from assertpy import assert_that

from lintro.utils.path_utils import normalize_file_path_for_display


@pytest.mark.utils
def test_normalize_file_path_for_display_absolute(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test normalizing an absolute path."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "file.py").touch()

    monkeypatch.chdir(tmp_path)
    abs_path = str(tmp_path / "src" / "file.py")
    result = normalize_file_path_for_display(abs_path)
    assert_that(result).is_equal_to("./src/file.py")


@pytest.mark.utils
def test_normalize_file_path_for_display_relative(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test normalizing a relative path."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "file.py").touch()

    monkeypatch.chdir(tmp_path)
    result = normalize_file_path_for_display("src/file.py")
    assert_that(result).is_equal_to("./src/file.py")


@pytest.mark.utils
def test_normalize_file_path_for_display_current_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test normalizing a file in current directory."""
    (tmp_path / "file.py").touch()

    monkeypatch.chdir(tmp_path)
    result = normalize_file_path_for_display("file.py")
    assert_that(result).is_equal_to("./file.py")


@pytest.mark.utils
def test_normalize_file_path_for_display_parent_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test normalizing a path that goes up directories."""
    project_dir = tmp_path / "root"
    project_dir.mkdir()
    (tmp_path / "file.py").touch()

    monkeypatch.chdir(project_dir)
    result = normalize_file_path_for_display(str(tmp_path / "file.py"))
    assert_that(result).is_equal_to("../file.py")


@pytest.mark.utils
def test_normalize_file_path_for_display_already_relative(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test normalizing a path that already starts with './'."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "file.py").touch()

    monkeypatch.chdir(tmp_path)
    result = normalize_file_path_for_display("./src/file.py")
    assert_that(result).is_equal_to("./src/file.py")


@pytest.mark.utils
def test_normalize_file_path_for_display_error() -> None:
    """Test handling errors in path normalization."""
    with patch.object(
        Path,
        "resolve",
        side_effect=ValueError("Invalid path"),
    ):
        result = normalize_file_path_for_display("invalid/path")
    assert_that(result).is_equal_to("invalid/path")


@pytest.mark.utils
def test_normalize_file_path_for_display_os_error() -> None:
    """Test handling OS errors in path normalization."""
    with patch("os.getcwd", side_effect=OSError("Permission denied")):
        result = normalize_file_path_for_display("src/file.py")
    assert_that(result).is_equal_to("src/file.py")
