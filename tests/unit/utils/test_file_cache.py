"""Tests for lintro.utils.file_cache module."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from assertpy import assert_that

from lintro.utils.file_cache import (
    FileFingerprint,
    ToolCache,
    clear_all_caches,
    get_cache_stats,
)


def test_file_fingerprint_to_dict() -> None:
    """Convert fingerprint to dictionary."""
    fp = FileFingerprint(path="/test/file.py", mtime=1234567890.0, size=1024)
    result = fp.to_dict()

    assert_that(result).is_equal_to({
        "path": "/test/file.py",
        "mtime": 1234567890.0,
        "size": 1024,
    })


def test_file_fingerprint_from_dict() -> None:
    """Create fingerprint from dictionary."""
    data = {"path": "/test/file.py", "mtime": 1234567890.0, "size": 1024}
    fp = FileFingerprint.from_dict(data)

    assert_that(fp.path).is_equal_to("/test/file.py")
    assert_that(fp.mtime).is_equal_to(1234567890.0)
    assert_that(fp.size).is_equal_to(1024)


def test_file_fingerprint_roundtrip() -> None:
    """Roundtrip through to_dict and from_dict."""
    original = FileFingerprint(path="/test/file.py", mtime=1234567890.0, size=1024)
    result = FileFingerprint.from_dict(original.to_dict())

    assert_that(result.path).is_equal_to(original.path)
    assert_that(result.mtime).is_equal_to(original.mtime)
    assert_that(result.size).is_equal_to(original.size)


def test_tool_cache_empty_returns_all_files_as_changed(tmp_path: Path) -> None:
    """Empty cache returns all files as changed."""
    temp_file = tmp_path / "test.py"
    temp_file.write_text("test content")

    cache = ToolCache(tool_name="test")
    changed = cache.get_changed_files([str(temp_file)])
    assert_that(changed).contains(str(temp_file))


def test_tool_cache_unchanged_file_not_returned(tmp_path: Path) -> None:
    """File in cache with same mtime/size not returned as changed."""
    temp_file = tmp_path / "test.py"
    temp_file.write_text("test content")

    stat = temp_file.stat()
    cache = ToolCache(tool_name="test")
    cache.fingerprints[str(temp_file)] = FileFingerprint(
        path=str(temp_file),
        mtime=stat.st_mtime,
        size=stat.st_size,
    )
    changed = cache.get_changed_files([str(temp_file)])
    assert_that(changed).does_not_contain(str(temp_file))


def test_tool_cache_modified_file_returned(tmp_path: Path) -> None:
    """File in cache with different mtime returned as changed."""
    temp_file = tmp_path / "test.py"
    temp_file.write_text("test content")

    stat = temp_file.stat()
    cache = ToolCache(tool_name="test")
    cache.fingerprints[str(temp_file)] = FileFingerprint(
        path=str(temp_file),
        mtime=stat.st_mtime - 100,
        size=stat.st_size,
    )
    changed = cache.get_changed_files([str(temp_file)])
    assert_that(changed).contains(str(temp_file))


def test_tool_cache_nonexistent_file_skipped() -> None:
    """Nonexistent file skipped in get_changed_files."""
    cache = ToolCache(tool_name="test")
    changed = cache.get_changed_files(["/nonexistent/file.py"])
    assert_that(changed).is_empty()


def test_tool_cache_update_adds_fingerprints(tmp_path: Path) -> None:
    """Update adds fingerprints for files."""
    temp_file = tmp_path / "test.py"
    temp_file.write_text("test content")

    cache = ToolCache(tool_name="test")
    cache.update([str(temp_file)])
    assert_that(cache.fingerprints).contains_key(str(temp_file))


def test_tool_cache_clear_removes_all_fingerprints() -> None:
    """Clear removes all fingerprints."""
    cache = ToolCache(tool_name="test")
    cache.fingerprints["file1.py"] = FileFingerprint(
        path="file1.py",
        mtime=1234567890.0,
        size=100,
    )
    cache.clear()
    assert_that(cache.fingerprints).is_empty()


def test_tool_cache_save_and_load_roundtrip(tmp_path: Path) -> None:
    """Save and load preserves cache data."""
    with patch("lintro.utils.file_cache.CACHE_DIR", tmp_path):
        cache = ToolCache(tool_name="test_tool")
        cache.fingerprints["/test/file.py"] = FileFingerprint(
            path="/test/file.py",
            mtime=1234567890.0,
            size=1024,
        )
        cache.save()

        loaded = ToolCache.load("test_tool")
        assert_that(loaded.tool_name).is_equal_to("test_tool")
        assert_that(loaded.fingerprints).contains_key("/test/file.py")


def test_tool_cache_load_returns_empty_for_missing_file(tmp_path: Path) -> None:
    """Load returns empty cache for missing cache file."""
    with patch("lintro.utils.file_cache.CACHE_DIR", tmp_path):
        loaded = ToolCache.load("nonexistent_tool")
        assert_that(loaded.fingerprints).is_empty()


def test_clear_all_caches_deletes_files(tmp_path: Path) -> None:
    """Clear all caches deletes all cache files."""
    (tmp_path / "tool1.json").write_text('{"tool_name": "tool1"}')
    (tmp_path / "tool2.json").write_text('{"tool_name": "tool2"}')

    with patch("lintro.utils.file_cache.CACHE_DIR", tmp_path):
        clear_all_caches()
        assert_that(list(tmp_path.glob("*.json"))).is_empty()


def test_get_cache_stats_returns_file_counts(tmp_path: Path) -> None:
    """Get cache stats returns file counts."""
    cache_data = {
        "tool_name": "test_tool",
        "fingerprints": {
            "/file1.py": {"path": "/file1.py", "mtime": 1.0, "size": 100},
            "/file2.py": {"path": "/file2.py", "mtime": 2.0, "size": 200},
        },
    }
    (tmp_path / "test_tool.json").write_text(json.dumps(cache_data))

    with patch("lintro.utils.file_cache.CACHE_DIR", tmp_path):
        stats = get_cache_stats()
        assert_that(stats).contains_key("test_tool")
        assert_that(stats["test_tool"]).is_equal_to(2)


def test_get_cache_stats_returns_empty_for_nonexistent_dir(tmp_path: Path) -> None:
    """Get cache stats returns empty dict for nonexistent directory."""
    nonexistent_dir = tmp_path / "nonexistent"

    with patch("lintro.utils.file_cache.CACHE_DIR", nonexistent_dir):
        stats = get_cache_stats()
        assert_that(stats).is_empty()
