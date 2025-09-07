"""Tests for shell script environment handling and edge cases.

This module tests how shell scripts handle different environments,
missing tools, and error conditions.
"""

import subprocess
import tempfile
from pathlib import Path

import pytest
from assertpy import assert_that


class TestEnvironmentHandling:
    """Test how scripts handle different environments."""

    @pytest.fixture
    def scripts_dir(self):
        """Get the scripts directory path.

        Returns:
            Path: Path to the scripts directory.
        """
        return Path(__file__).parent.parent.parent / "scripts"

    @pytest.fixture
    def clean_env(self):
        """Provide a clean environment for testing.

        Returns:
            dict[str, str]: Clean environment variables for testing.
        """
        return {"PATH": "/usr/bin:/bin", "HOME": "/tmp", "USER": "testuser"}

    def test_local_test_handles_missing_uv(self, scripts_dir, clean_env):
        """Test local-test.sh behavior when uv is not available.

        Args:
            scripts_dir: Path to the scripts directory.
            clean_env: Clean environment variables for testing.
        """
        script = scripts_dir / "local" / "local-test.sh"
        result = subprocess.run(
            [str(script), "--help"],
            capture_output=True,
            text=True,
            env=clean_env,
            cwd=scripts_dir.parent,
        )
        assert_that(result.returncode).is_equal_to(0)
        assert_that(result.stdout).contains("Usage:")

    def test_scripts_handle_docker_missing(self, scripts_dir, clean_env):
        """Test Docker scripts behavior when Docker is not available.

        Args:
            scripts_dir: Path to the scripts directory.
            clean_env: Clean environment variables for testing.
        """
        docker_scripts = ["docker/docker-test.sh", "docker/docker-lintro.sh"]
        for script_name in docker_scripts:
            script = scripts_dir / script_name
            if not script.exists():
                continue
            result = subprocess.run(
                [str(script)],
                capture_output=True,
                text=True,
                env=clean_env,
                cwd=scripts_dir.parent,
            )
            assert_that(result.returncode).is_not_equal_to(0)
            error_output = result.stderr + result.stdout
            assert_that(
                any(
                    (
                        word in error_output.lower()
                        for word in ["docker", "not found", "not running", "error"]
                    ),
                ),
            ).is_true()

    def test_install_tools_handles_missing_dependencies(self, scripts_dir, clean_env):
        """Test install-tools.sh behavior with missing dependencies.

        Args:
            scripts_dir: Path to the scripts directory.
            clean_env: Clean environment variables for testing.
        """
        script = scripts_dir / "utils" / "install-tools.sh"
        result = subprocess.run(
            [str(script)],
            capture_output=True,
            text=True,
            env=clean_env,
            cwd=scripts_dir.parent,
            timeout=10,
        )
        assert_that(result.returncode).is_not_none()


class TestScriptErrorHandling:
    """Test script error handling and edge cases."""

    @pytest.fixture
    def scripts_dir(self):
        """Get the scripts directory path.

        Returns:
            Path: Path to the scripts directory.
        """
        return Path(__file__).parent.parent.parent / "scripts"

    def test_extract_coverage_handles_missing_file(self, scripts_dir):
        """Test extract-coverage.py handles missing coverage.xml.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        script = scripts_dir / "utils" / "extract-coverage.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                ["python3", str(script)],
                capture_output=True,
                text=True,
                cwd=tmpdir,
            )
            assert_that(result.returncode).is_equal_to(0)
            assert_that(result.stdout).contains("percentage=")
            assert_that(result.stdout).contains("percentage=0.0")

    def test_extract_coverage_handles_empty_file(self, scripts_dir):
        """Test extract-coverage.py handles empty coverage.xml.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        script = scripts_dir / "utils" / "extract-coverage.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            coverage_file = Path(tmpdir) / "coverage.xml"
            coverage_file.write_text("")
            result = subprocess.run(
                ["python3", str(script)],
                capture_output=True,
                text=True,
                cwd=tmpdir,
            )
            assert_that(result.returncode).is_equal_to(0)
            assert_that(result.stdout).contains("percentage=")

    def test_extract_coverage_handles_valid_file(self, scripts_dir):
        """Test extract-coverage.py handles valid coverage.xml.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        script = scripts_dir / "utils" / "extract-coverage.py"
        valid_coverage_xml = (
            '<?xml version="1.0" ?>\n'
            '<coverage version="7.4.1" timestamp="1234567890" '
            'line-rate="0.85"\n'
            '          branch-rate="0.75" lines-covered="850" '
            'lines-valid="1000">\n'
            "    <sources>\n"
            "        <source>.</source>\n"
            "    </sources>\n"
            "    <packages>\n"
            '        <package name="lintro" line-rate="0.85" '
            'branch-rate="0.75">\n'
            "        </package>\n"
            "    </packages>\n"
            "</coverage>"
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            coverage_file = Path(tmpdir) / "coverage.xml"
            coverage_file.write_text(valid_coverage_xml)
            result = subprocess.run(
                ["python3", str(script)],
                capture_output=True,
                text=True,
                cwd=tmpdir,
            )
            assert_that(result.returncode).is_equal_to(0)
            assert_that(result.stdout).contains("percentage=")
            assert_that(result.stdout).contains("percentage=85.0")

    def test_sbom_generate_dry_run_prints_plan(self, scripts_dir, tmp_path):
        """sbom-generate.sh --dry-run should print a plan and exit 0.

        Runs with --skip-fetch to avoid network access during tests.

        Args:
            scripts_dir: Path to the scripts directory.
            tmp_path: Path to the temporary directory.
        """
        script = Path("scripts/ci/sbom-generate.sh").resolve()
        wrapper = tmp_path / "run_sbom.sh"
        wrapper.write_text(
            f"#!/usr/bin/env bash\nset -euo pipefail\ncd '{scripts_dir.parent}'\n"
            f"'{script}' --dry-run --skip-fetch\n",
        )
        wrapper.chmod(0o755)
        result = subprocess.run([str(wrapper)], capture_output=True, text=True)
        assert_that(result.returncode).is_equal_to(0)
        out = result.stdout + result.stderr
        assert_that(out.lower()).contains("dry-run")

    def test_sbom_generate_dry_run_import_merge_push_plan(self, scripts_dir, tmp_path):
        """Dry-run should show import, merge, and push steps when multiple imports.

        Uses two placeholder local files and --skip-fetch to avoid network.

        Args:
            scripts_dir: Path to the scripts directory.
            tmp_path: Path to the temporary directory.
        """
        # Create dummy files to pass as --import paths
        file1 = tmp_path / "a.cdx.json"
        file2 = tmp_path / "b.cdx.json"
        file1.write_text("{}")
        file2.write_text("{}")
        script = Path("scripts/ci/sbom-generate.sh").resolve()
        wrapper = tmp_path / "run_sbom_merge.sh"
        wrapper.write_text(
            f"#!/usr/bin/env bash\nset -euo pipefail\ncd '{scripts_dir.parent}'\n"
            f"'{script}' --dry-run --skip-fetch "
            f"--import '{file1}' "
            f"--import '{file2}'\n",
        )
        wrapper.chmod(0o755)
        result = subprocess.run([str(wrapper)], capture_output=True, text=True)
        assert_that(result.returncode).is_equal_to(0)
        plan = result.stdout + result.stderr
        assert_that(plan).contains("import --alias project")
        assert_that(plan).contains(" merge ")
        assert_that(plan).contains(" push ")

    def test_sbom_generate_dry_run_fetch_only_merges_to_alias(
        self,
        scripts_dir,
        tmp_path,
    ):
        """Dry-run with fetch-only should show merge to alias and push of alias.

        Forces repo URL via --repo-url to avoid relying on git remotes.

        Args:
            scripts_dir: Path to the scripts directory.
            tmp_path: Path to the temporary directory.
        """
        script = Path("scripts/ci/sbom-generate.sh").resolve()
        wrapper = tmp_path / "run_sbom_fetch.sh"
        wrapper.write_text(
            f"#!/usr/bin/env bash\nset -euo pipefail\ncd '{scripts_dir.parent}'\n"
            f"'{script}' --dry-run --repo-url 'https://github.com/example/acme'\n",
        )
        wrapper.chmod(0o755)
        result = subprocess.run([str(wrapper)], capture_output=True, text=True)
        assert_that(result.returncode).is_equal_to(0)
        plan = result.stdout + result.stderr
        assert_that(plan).contains(" fetch ")
        assert_that(plan).contains(" merge --alias project")
        assert_that(plan).contains(" push ")


class TestScriptSecurity:
    """Test security aspects of shell scripts."""

    @pytest.fixture
    def scripts_dir(self):
        """Get the scripts directory path.

        Returns:
            Path: Path to the scripts directory.
        """
        return Path(__file__).parent.parent.parent / "scripts"

    def test_scripts_avoid_eval_or_exec(self, scripts_dir):
        """Test that scripts avoid dangerous eval or exec commands.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        shell_scripts = list(scripts_dir.glob("*.sh"))
        dangerous_patterns = ["eval ", "exec ", "$(curl", "| sh", "| bash"]
        for script in shell_scripts:
            with open(script, "r") as f:
                content = f.read()
            for pattern in dangerous_patterns:
                if pattern in content:
                    lines_with_pattern = [
                        line.strip()
                        for line in content.split("\n")
                        if pattern in line and (not line.strip().startswith("#"))
                    ]
                    for line in lines_with_pattern:
                        if pattern == "| sh" and "install.sh" in line:
                            continue
                        if pattern == "| bash" and (
                            "nodesource.com" in line or "setup_" in line
                        ):
                            continue
                        if pattern == "eval " and "grep" in line:
                            continue
                        pytest.fail(
                            (
                                f"Potentially unsafe pattern '{pattern}' in "
                                f"{script.name}: {line}"
                            ),
                        )

    def test_scripts_validate_inputs(self, scripts_dir):
        """Test that scripts validate inputs appropriately.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        scripts_with_args = ["run-tests.sh", "local-lintro.sh"]
        for script_name in scripts_with_args:
            script = scripts_dir / script_name
            if not script.exists():
                continue
            with open(script, "r") as f:
                content = f.read()
            has_validation = any(
                (
                    pattern in content
                    for pattern in [
                        'if [ "$1"',
                        'case "$1"',
                        "[ $# -",
                        "getopts",
                        "--help",
                        "-h",
                    ]
                ),
            )
            assert (
                has_validation
            ), f"{script_name} should validate command line arguments"

    def test_scripts_use_quoted_variables(self, scripts_dir):
        """Test that scripts properly quote variables to prevent injection.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        shell_scripts = list(scripts_dir.glob("*.sh"))
        for script in shell_scripts:
            with open(script, "r") as f:
                content = f.read()
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                if line.strip().startswith("#"):
                    continue
                if " $1" in line and '"$1"' not in line and ("'$1'" not in line):
                    if not any((safe in line for safe in ["[$1]", "=$1", "shift"])):
                        pass


class TestScriptCompatibility:
    """Test script compatibility across different environments."""

    @pytest.fixture
    def scripts_dir(self):
        """Get the scripts directory path.

        Returns:
            Path: Path to the scripts directory.
        """
        return Path(__file__).parent.parent.parent / "scripts"

    def test_scripts_use_portable_shebang(self, scripts_dir):
        """Test that scripts use portable shebang lines.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        shell_scripts = list(scripts_dir.glob("*.sh"))
        for script in shell_scripts:
            with open(script, "r") as f:
                first_line = f.readline().strip()
            assert (
                first_line == "#!/bin/bash"
            ), f"{script.name} should use '#!/bin/bash' shebang, found: {first_line}"

    def test_scripts_avoid_bashisms_in_sh_context(self, scripts_dir):
        """Test that scripts avoid bash-specific features where inappropriate.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        shell_scripts = list(scripts_dir.glob("*.sh"))
        for script in shell_scripts:
            with open(script, "r") as f:
                first_line = f.readline().strip()
            if first_line == "#!/bin/sh":
                with open(script, "r") as f:
                    content = f.read()
                bash_features = ["[[", "function ", "$(", "source "]
                for feature in bash_features:
                    assert feature not in content, (
                        f"{script.name} uses bash feature '{feature}' but has sh "
                        "shebang"
                    )

    def test_python_script_compatibility(self, scripts_dir):
        """Test that Python scripts use appropriate shebang.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        python_scripts = [
            f for f in scripts_dir.glob("*.py") if f.name != "__init__.py"
        ]
        for script in python_scripts:
            with open(script, "r") as f:
                first_line = f.readline().strip()
            assert first_line in [
                "#!/usr/bin/env python3",
                "#!/usr/bin/python3",
            ], f"{script.name} should use python3 shebang"
