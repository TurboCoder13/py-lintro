"""Tests for lintro.utils.file_cache module."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

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


def test_tool_cache_empty_returns_all_files_as_changed() -> None:
    """Empty cache returns all files as changed."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as f:
        f.write(b"test content")
        temp_path = f.name

    try:
        cache = ToolCache(tool_name="test")
        changed = cache.get_changed_files([temp_path])
        assert_that(changed).contains(temp_path)
    finally:
        Path(temp_path).unlink()


def test_tool_cache_unchanged_file_not_returned() -> None:
    """File in cache with same mtime/size not returned as changed."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as f:
        f.write(b"test content")
        temp_path = f.name

    try:
        stat = Path(temp_path).stat()
        cache = ToolCache(tool_name="test")
        cache.fingerprints[temp_path] = FileFingerprint(
            path=temp_path,
            mtime=stat.st_mtime,
            size=stat.st_size,
        )
        changed = cache.get_changed_files([temp_path])
        assert_that(changed).does_not_contain(temp_path)
    finally:
        Path(temp_path).unlink()


def test_tool_cache_modified_file_returned() -> None:
    """File in cache with different mtime returned as changed."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as f:
        f.write(b"test content")
        temp_path = f.name

    try:
        stat = Path(temp_path).stat()
        cache = ToolCache(tool_name="test")
        cache.fingerprints[temp_path] = FileFingerprint(
            path=temp_path,
            mtime=stat.st_mtime - 100,
            size=stat.st_size,
        )
        changed = cache.get_changed_files([temp_path])
        assert_that(changed).contains(temp_path)
    finally:
        Path(temp_path).unlink()


def test_tool_cache_nonexistent_file_skipped() -> None:
    """Nonexistent file skipped in get_changed_files."""
    cache = ToolCache(tool_name="test")
    changed = cache.get_changed_files(["/nonexistent/file.py"])
    assert_that(changed).is_empty()


def test_tool_cache_update_adds_fingerprints() -> None:
    """Update adds fingerprints for files."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as f:
        f.write(b"test content")
        temp_path = f.name

    try:
        cache = ToolCache(tool_name="test")
        cache.update([temp_path])
        assert_that(cache.fingerprints).contains_key(temp_path)
    finally:
        Path(temp_path).unlink()


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


def test_tool_cache_save_and_load_roundtrip() -> None:
    """Save and load preserves cache data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir)

        with patch("lintro.utils.file_cache.CACHE_DIR", cache_dir):
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


def test_tool_cache_load_returns_empty_for_missing_file() -> None:
    """Load returns empty cache for missing cache file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir)

        with patch("lintro.utils.file_cache.CACHE_DIR", cache_dir):
            loaded = ToolCache.load("nonexistent_tool")
            assert_that(loaded.fingerprints).is_empty()


def test_clear_all_caches_deletes_files() -> None:
    """Clear all caches deletes all cache files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir)
        (cache_dir / "tool1.json").write_text('{"tool_name": "tool1"}')
        (cache_dir / "tool2.json").write_text('{"tool_name": "tool2"}')

        with patch("lintro.utils.file_cache.CACHE_DIR", cache_dir):
            clear_all_caches()
            assert_that(list(cache_dir.glob("*.json"))).is_empty()


def test_get_cache_stats_returns_file_counts() -> None:
    """Get cache stats returns file counts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir)
        cache_data = {
            "tool_name": "test_tool",
            "fingerprints": {
                "/file1.py": {"path": "/file1.py", "mtime": 1.0, "size": 100},
                "/file2.py": {"path": "/file2.py", "mtime": 2.0, "size": 200},
            },
        }
        (cache_dir / "test_tool.json").write_text(json.dumps(cache_data))

        with patch("lintro.utils.file_cache.CACHE_DIR", cache_dir):
            stats = get_cache_stats()
            assert_that(stats).contains_key("test_tool")
            assert_that(stats["test_tool"]).is_equal_to(2)


def test_get_cache_stats_returns_empty_for_nonexistent_dir() -> None:
    """Get cache stats returns empty dict for nonexistent directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir) / "nonexistent"

        with patch("lintro.utils.file_cache.CACHE_DIR", cache_dir):
            stats = get_cache_stats()
            assert_that(stats).is_empty()
