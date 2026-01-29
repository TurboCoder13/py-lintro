"""Unit tests for TscPlugin temp tsconfig functionality."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from assertpy import assert_that

from lintro.tools.definitions.tsc import TscPlugin


class TestFindTsconfig:
    """Tests for TscPlugin._find_tsconfig method."""

    def test_finds_tsconfig_in_cwd(
        self,
        tsc_plugin: TscPlugin,
        tmp_path: Path,
    ) -> None:
        """Verify _find_tsconfig finds tsconfig.json in working directory.

        Args:
            tsc_plugin: Plugin instance fixture.
            tmp_path: Pytest temporary directory.
        """
        tsconfig = tmp_path / "tsconfig.json"
        tsconfig.write_text("{}")

        result = tsc_plugin._find_tsconfig(tmp_path)

        assert_that(result).is_equal_to(tsconfig)

    def test_returns_none_when_no_tsconfig(
        self,
        tsc_plugin: TscPlugin,
        tmp_path: Path,
    ) -> None:
        """Verify _find_tsconfig returns None when no tsconfig.json exists.

        Args:
            tsc_plugin: Plugin instance fixture.
            tmp_path: Pytest temporary directory.
        """
        result = tsc_plugin._find_tsconfig(tmp_path)

        assert_that(result).is_none()

    def test_uses_explicit_project_option(
        self,
        tsc_plugin: TscPlugin,
        tmp_path: Path,
    ) -> None:
        """Verify _find_tsconfig uses explicit project option over auto-discovery.

        Args:
            tsc_plugin: Plugin instance fixture.
            tmp_path: Pytest temporary directory.
        """
        # Create both default and custom tsconfig
        default_tsconfig = tmp_path / "tsconfig.json"
        default_tsconfig.write_text("{}")

        custom_tsconfig = tmp_path / "tsconfig.build.json"
        custom_tsconfig.write_text("{}")

        tsc_plugin.set_options(project="tsconfig.build.json")
        result = tsc_plugin._find_tsconfig(tmp_path)

        assert_that(result).is_equal_to(custom_tsconfig)


class TestCreateTempTsconfig:
    """Tests for TscPlugin._create_temp_tsconfig method."""

    def test_creates_temp_file_with_extends(
        self,
        tsc_plugin: TscPlugin,
        tmp_path: Path,
    ) -> None:
        """Verify temp tsconfig extends the base config.

        Args:
            tsc_plugin: Plugin instance fixture.
            tmp_path: Pytest temporary directory.
        """
        base_tsconfig = tmp_path / "tsconfig.json"
        base_tsconfig.write_text('{"compilerOptions": {"strict": true}}')

        temp_path = tsc_plugin._create_temp_tsconfig(
            base_tsconfig=base_tsconfig,
            files=["src/file.ts"],
            cwd=tmp_path,
        )

        try:
            assert_that(temp_path.exists()).is_true()

            content = json.loads(temp_path.read_text())
            assert_that(content["extends"]).is_equal_to("./tsconfig.json")
        finally:
            temp_path.unlink(missing_ok=True)

    def test_temp_config_includes_specified_files(
        self,
        tsc_plugin: TscPlugin,
        tmp_path: Path,
    ) -> None:
        """Verify temp tsconfig includes only specified files.

        Args:
            tsc_plugin: Plugin instance fixture.
            tmp_path: Pytest temporary directory.
        """
        base_tsconfig = tmp_path / "tsconfig.json"
        base_tsconfig.write_text("{}")

        files = ["src/a.ts", "src/b.ts", "lib/c.ts"]
        temp_path = tsc_plugin._create_temp_tsconfig(
            base_tsconfig=base_tsconfig,
            files=files,
            cwd=tmp_path,
        )

        try:
            content = json.loads(temp_path.read_text())
            assert_that(content["include"]).is_equal_to(files)
            assert_that(content["exclude"]).is_equal_to([])
        finally:
            temp_path.unlink(missing_ok=True)

    def test_temp_config_sets_no_emit(
        self,
        tsc_plugin: TscPlugin,
        tmp_path: Path,
    ) -> None:
        """Verify temp tsconfig sets noEmit compiler option.

        Args:
            tsc_plugin: Plugin instance fixture.
            tmp_path: Pytest temporary directory.
        """
        base_tsconfig = tmp_path / "tsconfig.json"
        base_tsconfig.write_text("{}")

        temp_path = tsc_plugin._create_temp_tsconfig(
            base_tsconfig=base_tsconfig,
            files=["file.ts"],
            cwd=tmp_path,
        )

        try:
            content = json.loads(temp_path.read_text())
            assert_that(content["compilerOptions"]["noEmit"]).is_true()
        finally:
            temp_path.unlink(missing_ok=True)

    def test_temp_file_created_in_cwd(
        self,
        tsc_plugin: TscPlugin,
        tmp_path: Path,
    ) -> None:
        """Verify temp tsconfig is created in the working directory.

        Args:
            tsc_plugin: Plugin instance fixture.
            tmp_path: Pytest temporary directory.
        """
        base_tsconfig = tmp_path / "tsconfig.json"
        base_tsconfig.write_text("{}")

        temp_path = tsc_plugin._create_temp_tsconfig(
            base_tsconfig=base_tsconfig,
            files=["file.ts"],
            cwd=tmp_path,
        )

        try:
            assert_that(temp_path.parent).is_equal_to(tmp_path)
            assert_that(temp_path.name).starts_with(".lintro-tsc-")
            assert_that(temp_path.name).ends_with(".json")
        finally:
            temp_path.unlink(missing_ok=True)


class TestSetOptions:
    """Tests for TscPlugin.set_options validation."""

    def test_validates_use_project_files_type(
        self,
        tsc_plugin: TscPlugin,
    ) -> None:
        """Verify set_options rejects non-boolean use_project_files.

        Args:
            tsc_plugin: Plugin instance fixture.
        """
        with pytest.raises(ValueError, match="use_project_files must be a boolean"):
            tsc_plugin.set_options(use_project_files="true")  # type: ignore[arg-type]

    def test_accepts_valid_use_project_files(
        self,
        tsc_plugin: TscPlugin,
    ) -> None:
        """Verify set_options accepts boolean use_project_files.

        Args:
            tsc_plugin: Plugin instance fixture.
        """
        tsc_plugin.set_options(use_project_files=True)
        assert_that(tsc_plugin.options.get("use_project_files")).is_true()

        tsc_plugin.set_options(use_project_files=False)
        assert_that(tsc_plugin.options.get("use_project_files")).is_false()


class TestDefaultOptions:
    """Tests for TscPlugin default option values."""

    def test_use_project_files_defaults_to_false(
        self,
        tsc_plugin: TscPlugin,
    ) -> None:
        """Verify use_project_files defaults to False for lintro-style targeting.

        Args:
            tsc_plugin: Plugin instance fixture.
        """
        default_options = tsc_plugin.definition.default_options
        assert_that(default_options.get("use_project_files")).is_false()
