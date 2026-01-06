"""Tests for the delete-previous-lintro-comments.py script.

This module tests that the script correctly deletes only comments containing the marker.
"""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any
from unittest import mock

import pytest
from assertpy import assert_that

script_path = (
    Path(__file__).parent.parent.parent
    / "scripts"
    / "utils"
    / "delete-previous-lintro-comments.py"
)
spec = importlib.util.spec_from_file_location("del_script", str(script_path))
if spec is None or spec.loader is None:
    raise ImportError("Failed to load delete-previous-lintro-comments.py script")
del_script: ModuleType = importlib.util.module_from_spec(spec)
sys.modules["del_script"] = del_script
spec.loader.exec_module(del_script)


@pytest.fixture(autouse=True)
def patch_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch environment variables for the script.

    Args:
        monkeypatch: Pytest fixture for monkeypatching.
    """
    monkeypatch.setenv("GITHUB_TOKEN", "dummy-token")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("PR_NUMBER", "123")


def test_deletes_only_marker_comments(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that only comments with the marker are deleted.

    Args:
        monkeypatch: Pytest fixture for monkeypatching.
    """
    comments: list[dict[str, Any]] = [
        {"id": 1, "body": "Hello world"},
        {"id": 2, "body": "<!-- lintro-report --> Lint results"},
        {"id": 3, "body": "<!-- lintro-report --> Another lint comment"},
        {"id": 4, "body": "Unrelated comment"},
    ]
    deleted: list[int] = []

    def mock_get_pr_comments(
        repo: str,
        pr_number: str,
        token: str,
    ) -> list[dict[str, Any]]:
        return comments

    def mock_delete_comment(repo: str, comment_id: int, token: str) -> None:
        deleted.append(comment_id)

    monkeypatch.setattr(del_script, "get_pr_comments", mock_get_pr_comments)
    monkeypatch.setattr(del_script, "delete_comment", mock_delete_comment)
    import sys

    monkeypatch.setattr(
        sys,
        "argv",
        ["delete-previous-lintro-comments.py", "<!-- lintro-report -->"],
    )
    with mock.patch("sys.stdout", new_callable=lambda: sys.__stdout__):
        del_script.main()
    assert_that(set(deleted)).is_equal_to({2, 3})


def test_no_marker_comments(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that script prints message if no marker comments are found.

    Args:
        monkeypatch: Pytest fixture for monkeypatching.
    """
    comments: list[dict[str, Any]] = [
        {"id": 1, "body": "Hello world"},
        {"id": 4, "body": "Unrelated comment"},
    ]
    deleted: list[int] = []

    def mock_get_pr_comments(
        repo: str,
        pr_number: str,
        token: str,
    ) -> list[dict[str, Any]]:
        return comments

    def mock_delete_comment(repo: str, comment_id: int, token: str) -> None:
        deleted.append(comment_id)

    monkeypatch.setattr(del_script, "get_pr_comments", mock_get_pr_comments)
    monkeypatch.setattr(del_script, "delete_comment", mock_delete_comment)
    with mock.patch("sys.stdout", new_callable=lambda: sys.__stdout__):
        del_script.main()
    assert_that(deleted).is_equal_to([])
