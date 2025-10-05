#!/usr/bin/env python3
"""Tests for GitHub comment utility scripts.

Tests the functionality of find_comment_with_marker.py, extract_comment_body.py,
and json_encode_body.py utilities used by ci-post-pr-comment.sh.

Google-style docstrings are used per project standards.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from assertpy import assert_that


@pytest.fixture
def find_comment_script_path() -> Path:
    """Get path to find_comment_with_marker.py script.

    Returns:
        Path: Absolute path to the script.
    """
    return (
        Path(__file__).parent.parent.parent
        / "scripts"
        / "utils"
        / "find_comment_with_marker.py"
    )


@pytest.fixture
def extract_comment_script_path() -> Path:
    """Get path to extract_comment_body.py script.

    Returns:
        Path: Absolute path to the script.
    """
    return (
        Path(__file__).parent.parent.parent
        / "scripts"
        / "utils"
        / "extract_comment_body.py"
    )


@pytest.fixture
def json_encode_script_path() -> Path:
    """Get path to json_encode_body.py script.

    Returns:
        Path: Absolute path to the script.
    """
    return (
        Path(__file__).parent.parent.parent
        / "scripts"
        / "utils"
        / "json_encode_body.py"
    )


@pytest.fixture
def sample_data_dir() -> Path:
    """Get path to test_samples directory.

    Returns:
        Path: Absolute path to test_samples directory.
    """
    return Path(__file__).parent.parent.parent / "test_samples"


# Tests for find_comment_with_marker.py


def test_find_comment_with_marker_success(
    find_comment_script_path: Path,
    sample_data_dir: Path,
) -> None:
    """Test finding comment with marker in array response.

    Args:
        find_comment_script_path (Path): Path to the script being tested.
        sample_data_dir (Path): Path to test sample files.
    """
    json_file = sample_data_dir / "github_comments_with_marker.json"
    json_data = json_file.read_text(encoding="utf-8")

    result = subprocess.run(
        [str(find_comment_script_path), "<!-- coverage-report -->"],
        input=json_data,
        capture_output=True,
        text=True,
        check=True,
    )

    # Should return the most recent comment ID (54321)
    assert_that(result.stdout.strip()).is_equal_to("54321")
    assert_that(result.returncode).is_equal_to(0)


def test_find_comment_with_marker_paginated(
    find_comment_script_path: Path,
    sample_data_dir: Path,
) -> None:
    """Test finding comment with marker in paginated response.

    Args:
        find_comment_script_path (Path): Path to the script being tested.
        sample_data_dir (Path): Path to test sample files.
    """
    json_file = sample_data_dir / "github_comments_paginated.json"
    json_data = json_file.read_text(encoding="utf-8")

    result = subprocess.run(
        [str(find_comment_script_path), "<!-- test-marker -->"],
        input=json_data,
        capture_output=True,
        text=True,
        check=True,
    )

    # Should return the comment ID from paginated response (87654)
    assert_that(result.stdout.strip()).is_equal_to("87654")
    assert_that(result.returncode).is_equal_to(0)


def test_find_comment_no_marker_found(
    find_comment_script_path: Path,
    sample_data_dir: Path,
) -> None:
    """Test when no comment contains the marker.

    Args:
        find_comment_script_path (Path): Path to the script being tested.
        sample_data_dir (Path): Path to test sample files.
    """
    json_file = sample_data_dir / "github_comments_no_marker.json"
    json_data = json_file.read_text(encoding="utf-8")

    result = subprocess.run(
        [str(find_comment_script_path), "<!-- coverage-report -->"],
        input=json_data,
        capture_output=True,
        text=True,
        check=True,
    )

    # Should return empty string when no marker found
    assert_that(result.stdout.strip()).is_equal_to("")
    assert_that(result.returncode).is_equal_to(0)


def test_find_comment_invalid_json(find_comment_script_path: Path) -> None:
    """Test handling of invalid JSON input.

    Args:
        find_comment_script_path (Path): Path to the script being tested.
    """
    result = subprocess.run(
        [str(find_comment_script_path), "<!-- marker -->"],
        input="invalid json",
        capture_output=True,
        text=True,
        check=True,
    )

    # Should return empty string for invalid JSON
    assert_that(result.stdout.strip()).is_equal_to("")
    assert_that(result.returncode).is_equal_to(0)


def test_find_comment_empty_marker(
    find_comment_script_path: Path,
    sample_data_dir: Path,
) -> None:
    """Test handling of empty marker.

    Args:
        find_comment_script_path (Path): Path to the script being tested.
        sample_data_dir (Path): Path to test sample files.
    """
    json_file = sample_data_dir / "github_comments_with_marker.json"
    json_data = json_file.read_text(encoding="utf-8")

    result = subprocess.run(
        [str(find_comment_script_path), ""],
        input=json_data,
        capture_output=True,
        text=True,
        check=True,
    )

    # Should return empty string for empty marker
    assert_that(result.stdout.strip()).is_equal_to("")
    assert_that(result.returncode).is_equal_to(0)


# Tests for extract_comment_body.py


def test_extract_comment_body_success(
    extract_comment_script_path: Path,
    sample_data_dir: Path,
) -> None:
    """Test extracting comment body by ID from array response.

    Args:
        extract_comment_script_path (Path): Path to the script being tested.
        sample_data_dir (Path): Path to test sample files.
    """
    json_file = sample_data_dir / "github_comments_with_marker.json"
    json_data = json_file.read_text(encoding="utf-8")

    result = subprocess.run(
        [str(extract_comment_script_path), "54321"],
        input=json_data,
        capture_output=True,
        text=True,
        check=True,
    )

    expected_body = (
        "<!-- coverage-report -->\n\n"
        "This is the most recent comment with marker\n\n"
        "## Coverage Report\n"
        "- Line coverage: 95%\n"
        "- Branch coverage: 90%"
    )

    assert_that(result.stdout).is_equal_to(expected_body)
    assert_that(result.returncode).is_equal_to(0)


def test_extract_comment_body_paginated(
    extract_comment_script_path: Path,
    sample_data_dir: Path,
) -> None:
    """Test extracting comment body from paginated response.

    Args:
        extract_comment_script_path (Path): Path to the script being tested.
        sample_data_dir (Path): Path to test sample files.
    """
    json_file = sample_data_dir / "github_comments_paginated.json"
    json_data = json_file.read_text(encoding="utf-8")

    result = subprocess.run(
        [str(extract_comment_script_path), "87654"],
        input=json_data,
        capture_output=True,
        text=True,
        check=True,
    )

    expected_body = (
        "<!-- test-marker -->\n\n"
        "Paginated response with marker\n\n"
        "Test content here."
    )

    assert_that(result.stdout).is_equal_to(expected_body)
    assert_that(result.returncode).is_equal_to(0)


def test_extract_comment_body_not_found(
    extract_comment_script_path: Path,
    sample_data_dir: Path,
) -> None:
    """Test extracting non-existent comment ID.

    Args:
        extract_comment_script_path (Path): Path to the script being tested.
        sample_data_dir (Path): Path to test sample files.
    """
    json_file = sample_data_dir / "github_comments_with_marker.json"
    json_data = json_file.read_text(encoding="utf-8")

    result = subprocess.run(
        [str(extract_comment_script_path), "99999"],
        input=json_data,
        capture_output=True,
        text=True,
        check=True,
    )

    # Should return empty string for non-existent ID
    assert_that(result.stdout).is_equal_to("")
    assert_that(result.returncode).is_equal_to(0)


def test_extract_comment_body_invalid_json(extract_comment_script_path: Path) -> None:
    """Test handling of invalid JSON input.

    Args:
        extract_comment_script_path (Path): Path to the script being tested.
    """
    result = subprocess.run(
        [str(extract_comment_script_path), "12345"],
        input="invalid json",
        capture_output=True,
        text=True,
        check=True,
    )

    # Should return empty string for invalid JSON
    assert_that(result.stdout).is_equal_to("")
    assert_that(result.returncode).is_equal_to(0)


# Tests for json_encode_body.py


def test_json_encode_simple_body(
    json_encode_script_path: Path,
    sample_data_dir: Path,
) -> None:
    """Test JSON encoding of simple comment body from file.

    Args:
        json_encode_script_path (Path): Path to the script being tested.
        sample_data_dir (Path): Path to test sample files.
    """
    body_file = sample_data_dir / "comment_body_simple.txt"

    result = subprocess.run(
        [str(json_encode_script_path), str(body_file)],
        capture_output=True,
        text=True,
        check=True,
    )

    # Parse the JSON output to verify it's valid
    json_output = json.loads(result.stdout)
    assert_that(json_output).contains("body")

    # Verify the content
    expected_content = body_file.read_text(encoding="utf-8")
    assert_that(json_output["body"]).is_equal_to(expected_content)
    assert_that(result.returncode).is_equal_to(0)


def test_json_encode_special_chars(
    json_encode_script_path: Path,
    sample_data_dir: Path,
) -> None:
    """Test JSON encoding of comment body with special characters.

    Args:
        json_encode_script_path (Path): Path to the script being tested.
        sample_data_dir (Path): Path to test sample files.
    """
    body_file = sample_data_dir / "comment_body_with_quotes.txt"

    result = subprocess.run(
        [str(json_encode_script_path), str(body_file)],
        capture_output=True,
        text=True,
        check=True,
    )

    # Parse the JSON output to verify it's valid
    json_output = json.loads(result.stdout)
    assert_that(json_output).contains("body")

    # Verify special characters are properly escaped
    body_content = json_output["body"]
    assert_that(body_content).contains('"quoted text"')
    assert_that(body_content).contains("'single quoted'")
    assert_that(body_content).contains("\\path\\to\\file")
    assert_that(body_content).contains("ñáéíóú")
    assert_that(result.returncode).is_equal_to(0)


def test_json_encode_from_stdin(json_encode_script_path: Path) -> None:
    """Test JSON encoding from stdin input.

    Args:
        json_encode_script_path (Path): Path to the script being tested.
    """
    test_body = 'Test content from stdin\nWith newlines and special chars: "quotes"'

    result = subprocess.run(
        [str(json_encode_script_path)],
        input=test_body,
        capture_output=True,
        text=True,
        check=True,
    )

    # Parse the JSON output to verify it's valid
    json_output = json.loads(result.stdout)
    assert_that(json_output).contains("body")
    assert_that(json_output["body"]).is_equal_to(test_body)
    assert_that(result.returncode).is_equal_to(0)


def test_json_encode_nonexistent_file(json_encode_script_path: Path) -> None:
    """Test handling of non-existent file.

    Args:
        json_encode_script_path (Path): Path to the script being tested.
    """
    result = subprocess.run(
        [str(json_encode_script_path), "/nonexistent/file.txt"],
        capture_output=True,
        text=True,
    )

    # Should exit with error code for non-existent file
    assert_that(result.returncode).is_equal_to(1)
    assert_that(result.stderr).contains("Error reading file")


def test_json_encode_empty_body(json_encode_script_path: Path) -> None:
    """Test JSON encoding of empty body from stdin.

    Args:
        json_encode_script_path (Path): Path to the script being tested.
    """
    result = subprocess.run(
        [str(json_encode_script_path)],
        input="",
        capture_output=True,
        text=True,
        check=True,
    )

    # Parse the JSON output to verify it's valid
    json_output = json.loads(result.stdout)
    assert_that(json_output).contains("body")
    assert_that(json_output["body"]).is_equal_to("")
    assert_that(result.returncode).is_equal_to(0)
