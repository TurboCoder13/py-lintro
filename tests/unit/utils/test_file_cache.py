"""Tests for lintro.utils.file_cache module."""

from __future__ import annotations

import json
import tempfile
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


class TestFileFingerprint:
    """Tests for FileFingerprint dataclass."""

    def test_to_dict(self) -> None:
        """Convert fingerprint to dictionary."""
        fp = FileFingerprint(path="/test/file.py", mtime=1234567890.0, size=1024)
        result = fp.to_dict()

        assert_that(result).is_equal_to({
            "path": "/test/file.py",
            "mtime": 1234567890.0,
            "size": 1024,
        })

    def test_from_dict(self) -> None:
        """Create fingerprint from dictionary."""
        data = {"path": "/test/file.py", "mtime": 1234567890.0, "size": 1024}
        fp = FileFingerprint.from_dict(data)

        assert_that(fp.path).is_equal_to("/test/file.py")
        assert_that(fp.mtime).is_equal_to(1234567890.0)
        assert_that(fp.size).is_equal_to(1024)

    def test_roundtrip(self) -> None:
        """Roundtrip through to_dict and from_dict."""
        original = FileFingerprint(path="/test/file.py", mtime=1234567890.0, size=1024)
        result = FileFingerprint.from_dict(original.to_dict())

        assert_that(result.path).is_equal_to(original.path)
        assert_that(result.mtime).is_equal_to(original.mtime)
        assert_that(result.size).is_equal_to(original.size)


class TestToolCache:
    """Tests for ToolCache class."""

    def test_empty_cache_returns_all_files_as_changed(self) -> None:
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

    def test_cached_unchanged_file_not_returned(self) -> None:
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

    def test_cached_modified_file_returned(self) -> None:
        """File in cache with different mtime returned as changed."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as f:
            f.write(b"test content")
            temp_path = f.name

        try:
            stat = Path(temp_path).stat()
            cache = ToolCache(tool_name="test")
            # Cache with old mtime
            cache.fingerprints[temp_path] = FileFingerprint(
                path=temp_path,
                mtime=stat.st_mtime - 100,  # Old mtime
                size=stat.st_size,
            )

            changed = cache.get_changed_files([temp_path])

            assert_that(changed).contains(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_cached_different_size_file_returned(self) -> None:
        """File in cache with different size returned as changed."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as f:
            f.write(b"test content")
            temp_path = f.name

        try:
            stat = Path(temp_path).stat()
            cache = ToolCache(tool_name="test")
            # Cache with wrong size
            cache.fingerprints[temp_path] = FileFingerprint(
                path=temp_path,
                mtime=stat.st_mtime,
                size=stat.st_size + 100,  # Wrong size
            )

            changed = cache.get_changed_files([temp_path])

            assert_that(changed).contains(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_nonexistent_file_skipped(self) -> None:
        """Nonexistent file skipped in get_changed_files."""
        cache = ToolCache(tool_name="test")
        changed = cache.get_changed_files(["/nonexistent/file.py"])

        assert_that(changed).is_empty()

    def test_update_adds_fingerprints(self) -> None:
        """Update adds fingerprints for files."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as f:
            f.write(b"test content")
            temp_path = f.name

        try:
            cache = ToolCache(tool_name="test")
            cache.update([temp_path])

            assert_that(cache.fingerprints).contains_key(temp_path)
            assert_that(cache.fingerprints[temp_path].path).is_equal_to(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_update_removes_deleted_files(self) -> None:
        """Update removes fingerprints for deleted files."""
        cache = ToolCache(tool_name="test")
        cache.fingerprints["/deleted/file.py"] = FileFingerprint(
            path="/deleted/file.py",
            mtime=1234567890.0,
            size=100,
        )

        cache.update(["/deleted/file.py"])

        assert_that(cache.fingerprints).does_not_contain_key("/deleted/file.py")

    def test_clear_removes_all_fingerprints(self) -> None:
        """Clear removes all fingerprints."""
        cache = ToolCache(tool_name="test")
        cache.fingerprints["file1.py"] = FileFingerprint(
            path="file1.py",
            mtime=1234567890.0,
            size=100,
        )
        cache.fingerprints["file2.py"] = FileFingerprint(
            path="file2.py",
            mtime=1234567890.0,
            size=200,
        )

        cache.clear()

        assert_that(cache.fingerprints).is_empty()

    def test_save_and_load_roundtrip(self) -> None:
        """Save and load preserves cache data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)

            with patch("lintro.utils.file_cache.CACHE_DIR", cache_dir):
                # Create and save cache
                cache = ToolCache(tool_name="test_tool")
                cache.fingerprints["/test/file.py"] = FileFingerprint(
                    path="/test/file.py",
                    mtime=1234567890.0,
                    size=1024,
                )
                cache.save()

                # Load cache
                loaded = ToolCache.load("test_tool")

                assert_that(loaded.tool_name).is_equal_to("test_tool")
                assert_that(loaded.fingerprints).contains_key("/test/file.py")
                assert_that(loaded.fingerprints["/test/file.py"].mtime).is_equal_to(
                    1234567890.0,
                )

    def test_load_returns_empty_for_missing_file(self) -> None:
        """Load returns empty cache for missing cache file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)

            with patch("lintro.utils.file_cache.CACHE_DIR", cache_dir):
                loaded = ToolCache.load("nonexistent_tool")

                assert_that(loaded.tool_name).is_equal_to("nonexistent_tool")
                assert_that(loaded.fingerprints).is_empty()

    def test_load_handles_corrupted_file(self) -> None:
        """Load returns empty cache for corrupted cache file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            cache_file = cache_dir / "corrupted_tool.json"
            cache_file.write_text("not valid json")

            with patch("lintro.utils.file_cache.CACHE_DIR", cache_dir):
                loaded = ToolCache.load("corrupted_tool")

                assert_that(loaded.fingerprints).is_empty()


class TestClearAllCaches:
    """Tests for clear_all_caches function."""

    def test_clears_all_cache_files(self) -> None:
        """Clear all caches deletes all cache files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            # Create some cache files
            (cache_dir / "tool1.json").write_text('{"tool_name": "tool1"}')
            (cache_dir / "tool2.json").write_text('{"tool_name": "tool2"}')

            with patch("lintro.utils.file_cache.CACHE_DIR", cache_dir):
                clear_all_caches()

                assert_that(list(cache_dir.glob("*.json"))).is_empty()

    def test_handles_nonexistent_cache_dir(self) -> None:
        """Clear all caches handles nonexistent cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "nonexistent"

            with patch("lintro.utils.file_cache.CACHE_DIR", cache_dir):
                # Should not raise
                clear_all_caches()


class TestGetCacheStats:
    """Tests for get_cache_stats function."""

    def test_returns_stats_for_cache_files(self) -> None:
        """Get cache stats returns file counts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            # Create cache files with fingerprints
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

    def test_returns_empty_for_nonexistent_dir(self) -> None:
        """Get cache stats returns empty dict for nonexistent directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "nonexistent"

            with patch("lintro.utils.file_cache.CACHE_DIR", cache_dir):
                stats = get_cache_stats()

                assert_that(stats).is_empty()

    def test_handles_corrupted_cache_file(self) -> None:
        """Get cache stats skips corrupted files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            (cache_dir / "corrupted.json").write_text("not valid json")

            with patch("lintro.utils.file_cache.CACHE_DIR", cache_dir):
                stats = get_cache_stats()

                assert_that(stats).does_not_contain_key("corrupted")
