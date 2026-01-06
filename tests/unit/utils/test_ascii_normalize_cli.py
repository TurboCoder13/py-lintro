"""Unit tests for ascii_normalize_cli module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from assertpy import assert_that

from lintro.utils.ascii_normalize_cli import _ascii_art_dir, _write_sections, main

# --- _ascii_art_dir tests ---


def test_ascii_art_dir_returns_path() -> None:
    """Test that function returns a Path object."""
    result = _ascii_art_dir()
    assert_that(result).is_instance_of(Path)


def test_ascii_art_dir_points_to_ascii_art() -> None:
    """Test that path ends with ascii-art."""
    result = _ascii_art_dir()
    assert_that(str(result)).ends_with("ascii-art")


# --- _write_sections tests ---


def test_write_sections_single(tmp_path: Path) -> None:
    """Test writing a single section to file.

    Args:
        tmp_path: Temporary directory path for testing.
    """
    file_path = tmp_path / "test.txt"
    sections = [["line1", "line2", "line3"]]

    _write_sections(file_path, sections)

    content = file_path.read_text()
    assert_that(content).is_equal_to("line1\nline2\nline3\n")


def test_write_sections_multiple_with_blank_separator(tmp_path: Path) -> None:
    """Test that multiple sections are separated by blank line.

    Args:
        tmp_path: Temporary directory path for testing.
    """
    file_path = tmp_path / "test.txt"
    sections = [["sec1_line1", "sec1_line2"], ["sec2_line1", "sec2_line2"]]

    _write_sections(file_path, sections)

    content = file_path.read_text()
    assert_that(content).is_equal_to(
        "sec1_line1\nsec1_line2\n\nsec2_line1\nsec2_line2\n",
    )


def test_write_sections_empty(tmp_path: Path) -> None:
    """Test handling of empty sections list.

    Args:
        tmp_path: Temporary directory path for testing.
    """
    file_path = tmp_path / "test.txt"
    sections: list[list[str]] = []

    _write_sections(file_path, sections)

    content = file_path.read_text()
    assert_that(content).is_equal_to("\n")


# --- main tests ---


def test_main_returns_error_when_dir_not_found() -> None:
    """Test returns 1 when ascii-art directory not found."""
    with (
        patch(
            "lintro.utils.ascii_normalize_cli._ascii_art_dir",
            return_value=Path("/nonexistent/path"),
        ),
        patch(
            "lintro.utils.ascii_normalize_cli.argparse.ArgumentParser.parse_args",
        ) as mock_args,
    ):
        mock_args.return_value.files = []
        mock_args.return_value.width = 80
        mock_args.return_value.height = 20
        mock_args.return_value.align = "center"
        mock_args.return_value.valign = "middle"

        result = main()

        assert_that(result).is_equal_to(1)


def test_main_processes_specific_files(tmp_path: Path) -> None:
    """Test processing specific files.

    Args:
        tmp_path: Temporary directory path for testing.
    """
    test_file = tmp_path / "test.txt"
    test_file.write_text("test\n")

    with (
        patch(
            "lintro.utils.ascii_normalize_cli._ascii_art_dir",
            return_value=tmp_path,
        ),
        patch(
            "lintro.utils.ascii_normalize_cli.argparse.ArgumentParser.parse_args",
        ) as mock_args,
        patch(
            "lintro.utils.ascii_normalize_cli.normalize_ascii_file_sections",
            return_value=[["normalized"]],
        ),
        patch("lintro.utils.ascii_normalize_cli._write_sections") as mock_write,
    ):
        mock_args.return_value.files = ["test.txt"]
        mock_args.return_value.width = 80
        mock_args.return_value.height = 20
        mock_args.return_value.align = "center"
        mock_args.return_value.valign = "middle"

        result = main()

        assert_that(result).is_equal_to(0)
        mock_write.assert_called_once()


def test_main_processes_all_txt_files(tmp_path: Path) -> None:
    """Test processing all .txt files when no specific files given.

    Args:
        tmp_path: Temporary directory path for testing.
    """
    (tmp_path / "file1.txt").write_text("test1\n")
    (tmp_path / "file2.txt").write_text("test2\n")

    with (
        patch(
            "lintro.utils.ascii_normalize_cli._ascii_art_dir",
            return_value=tmp_path,
        ),
        patch(
            "lintro.utils.ascii_normalize_cli.argparse.ArgumentParser.parse_args",
        ) as mock_args,
        patch(
            "lintro.utils.ascii_normalize_cli.normalize_ascii_file_sections",
            return_value=[["normalized"]],
        ),
        patch("lintro.utils.ascii_normalize_cli._write_sections"),
    ):
        mock_args.return_value.files = []
        mock_args.return_value.width = 80
        mock_args.return_value.height = 20
        mock_args.return_value.align = "center"
        mock_args.return_value.valign = "middle"

        result = main()

        assert_that(result).is_equal_to(0)


def test_main_skips_files_with_no_sections(tmp_path: Path) -> None:
    """Test that files returning no sections are skipped.

    Args:
        tmp_path: Temporary directory path for testing.
    """
    (tmp_path / "empty.txt").write_text("")

    with (
        patch(
            "lintro.utils.ascii_normalize_cli._ascii_art_dir",
            return_value=tmp_path,
        ),
        patch(
            "lintro.utils.ascii_normalize_cli.argparse.ArgumentParser.parse_args",
        ) as mock_args,
        patch(
            "lintro.utils.ascii_normalize_cli.normalize_ascii_file_sections",
            return_value=[],
        ),
        patch("lintro.utils.ascii_normalize_cli._write_sections") as mock_write,
    ):
        mock_args.return_value.files = ["empty.txt"]
        mock_args.return_value.width = 80
        mock_args.return_value.height = 20
        mock_args.return_value.align = "center"
        mock_args.return_value.valign = "middle"

        result = main()

        assert_that(result).is_equal_to(0)
        mock_write.assert_not_called()
