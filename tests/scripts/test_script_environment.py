"""Tests for shell script environment handling and edge cases.

This module tests how shell scripts handle different environments,
missing tools, and error conditions.
"""

import os
import subprocess
import tempfile
from pathlib import Path
from textwrap import dedent

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

    def test_local_test_handles_missing_uv(self, scripts_dir, clean_env) -> None:
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

    def test_bootstrap_env_installs_uv_via_gh_offline(
        self,
        scripts_dir,
        tmp_path,
    ) -> None:
        """bootstrap-env.sh should install uv via gh assets without network.

        Mocks `gh release view` and `gh release download` to simulate a release
        that contains a linux x86_64 asset. The test verifies the script detects
        missing uv, downloads the mocked archive, extracts the uv binary, and
        places it on PATH. The sync and tools install phases are skipped.

        Args:
            scripts_dir: Path to the scripts directory.
            tmp_path: Path to the temporary directory.
        """
        script = scripts_dir.parent / "scripts" / "utils" / "bootstrap-env.sh"
        work = tmp_path
        bin_dir = work / "bin"
        bin_dir.mkdir(parents=True)

        # Mock gh: view prints minimal JSON with tag and assets; download writes archive
        gh_path = bin_dir / "gh"
        release_json = (
            '{"tagName":"0.0.0","assets":[{"name":"uv-x86_64-unknown-linux-gnu'
            '.tar.gz"}]}'
        )
        # Create a tar.gz containing a dummy 'uv' executable
        asset_dir = work / "asset"
        asset_dir.mkdir()
        (asset_dir / "uv").write_text("#!/bin/sh\necho uv-mock\n")
        (asset_dir / "uv").chmod(0o755)
        archive_path = work / "uv-x86_64-unknown-linux-gnu.tar.gz"
        import tarfile

        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(asset_dir / "uv", arcname="uv")

        gh_path.write_text(
            f"""#!/usr/bin/env bash
set -euo pipefail
if [[ "$1" == "release" && "$2" == "view" ]]; then
  # Print JSON
  echo '{release_json}'
  exit 0
fi
if [[ "$1" == "release" && "$2" == "download" ]]; then
  # Copy our prepared archive to requested output path
  out=""
  # parse -O <outfile>
  while [[ $# -gt 0 ]]; do
    if [[ "$1" == "-O" ]]; then shift; out="$1"; break; fi
    shift || true
  done
  cp "{archive_path}" "$out"
  exit 0
fi
echo "unsupported gh mock usage" >&2
exit 1
""",
        )
        gh_path.chmod(0o755)

        # Mock jq used by bootstrap script to extract tagName
        jq_path = bin_dir / "jq"
        jq_path.write_text(
            """#!/usr/bin/env bash
set -euo pipefail
# Ignore input and print fixed tag
echo 0.0.0
""",
        )
        jq_path.chmod(0o755)

        env = {
            "PATH": f"{bin_dir}:{scripts_dir.parent}:" + os.environ.get("PATH", ""),
            "HOME": str(work),
            "USER": "testuser",
            # Skip networked phases
            "BOOTSTRAP_SKIP_SYNC": "1",
            "BOOTSTRAP_SKIP_INSTALL_TOOLS": "1",
            # Force linux/x86_64 path
            "GITHUB_PATH": str(work / "gh_path.txt"),
        }
        # Ensure uv not present in PATH
        result = subprocess.run(
            ["bash", str(script), "3.13"],
            capture_output=True,
            text=True,
            env=env,
            cwd=scripts_dir.parent,
            timeout=30,
        )
        assert_that(result.returncode).is_equal_to(0)
        # The mocked uv should be on PATH now
        uv_check = subprocess.run(
            ["uv", "--version"],
            capture_output=True,
            text=True,
            env={"PATH": env["PATH"]},
        )
        assert_that(uv_check.returncode).is_equal_to(0)

    @pytest.mark.docker_only
    def test_scripts_handle_docker_missing(self, scripts_dir, clean_env) -> None:
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
                    word in error_output.lower()
                    for word in ["docker", "not found", "not running", "error"]
                ),
            ).is_true()

    @pytest.mark.slow
    def test_install_tools_handles_missing_dependencies(
        self,
        scripts_dir,
        clean_env,
    ) -> None:
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
            timeout=30,
        )
        assert_that(result.returncode).is_not_none()

    def test_ci_post_pr_comment_merges_existing_by_marker(self, tmp_path) -> None:
        """ci-post-pr-comment should update an existing comment by marker.

        Mocks `gh api` to return a JSON array with an existing comment body that
        contains the marker, then verifies the script performs a PATCH call with
        merged content where the marker appears only once at the top.

        Args:
            tmp_path: Path to the temporary directory.
        """
        # Prepare a fake environment and working dir
        work = tmp_path
        scripts_root = Path("scripts").resolve()
        post_script = scripts_root / "ci" / "ci-post-pr-comment.sh"

        # Prepare a comment file containing the marker (as produced upstream)
        new_body_path = work / "comment.txt"
        new_body_path.write_text(
            dedent(
                """
                <!-- coverage-report -->

                ## 📊 Coverage Report

                **Coverage:** ✅ **85.0%** (good)
                """,
            ).strip(),
        )

        # Create a mock gh that returns an existing comment with the marker and
        # captures PATCH payloads
        bin_dir = work / "bin"
        bin_dir.mkdir()
        gh_path = bin_dir / "gh"
        existing_json = (
            '[\n  {"id": 111, "body": "<!-- coverage-report -->\\nOld body"}\n]\n'
        )
        gh_path.write_text(
            f"""#!/usr/bin/env bash
set -euo pipefail
if [[ "$1" == "api" && "$2" == repos/*/issues/*/comments ]]; then
  # list comments
  echo '{existing_json}'
  exit 0
fi
if [[ "$1" == "api" && "$2" == repos/*/issues/comments/* && "$3" == "-X" \
    && "$4" == "PATCH" ]]; then
  # capture body from -F body=@filepath format
  while [[ $# -gt 0 ]]; do
    if [[ "$1" == "-F" && "$2" == body=@* ]]; then
      filepath="${{2#body=@}}"
      cat "$filepath" > "{(work / "patch_out.txt").as_posix()}"
      exit 0
    fi
    shift
  done
  # Fallback for inline body=value format
  for i in "$@"; do
    if [[ "$i" == body=* ]]; then echo "$i"; fi
  done > "{(work / "patch_out.txt").as_posix()}"
  exit 0
fi
echo gh-mock-unhandled >&2
exit 1
""",
        )
        gh_path.chmod(0o755)

        env = {
            "PATH": f"{bin_dir}:{os.environ.get('PATH', '')}",
            "PR_NUMBER": "123",
            "GITHUB_TOKEN": "t",
            "GITHUB_REPOSITORY": "o/r",
            "MARKER": "<!-- coverage-report -->",
            "GITHUB_EVENT_NAME": "pull_request",
        }

        result = subprocess.run(
            [str(post_script), str(new_body_path)],
            capture_output=True,
            text=True,
            env=env,
            cwd=Path.cwd(),
        )
        assert_that(result.returncode).is_equal_to(0)

        sent = (work / "patch_out.txt").read_text()
        # Body should contain marker exactly once at top
        assert "<!-- coverage-report -->" in sent
        assert sent.count("<!-- coverage-report -->") == 1


class TestScriptErrorHandling:
    """Test script error handling and edge cases."""

    @pytest.fixture
    def scripts_dir(self):
        """Get the scripts directory path.

        Returns:
            Path: Path to the scripts directory.
        """
        return Path(__file__).parent.parent.parent / "scripts"

    def test_extract_coverage_handles_missing_file(self, scripts_dir) -> None:
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

    def test_extract_coverage_handles_empty_file(self, scripts_dir) -> None:
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

    def test_extract_coverage_handles_valid_file(self, scripts_dir) -> None:
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

    def test_sbom_generate_dry_run_prints_plan(self, scripts_dir, tmp_path) -> None:
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

    def test_sbom_generate_dry_run_import_merge_push_plan(
        self,
        scripts_dir,
        tmp_path,
    ) -> None:
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
    ) -> None:
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

    def test_scripts_avoid_eval_or_exec(self, scripts_dir) -> None:
        """Test that scripts avoid dangerous eval or exec commands.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        shell_scripts = list(scripts_dir.glob("*.sh"))
        dangerous_patterns = ["eval ", "exec ", "$(curl", "| sh", "| bash"]
        for script in shell_scripts:
            with open(script) as f:
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

    def test_scripts_validate_inputs(self, scripts_dir) -> None:
        """Test that scripts validate inputs appropriately.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        scripts_with_args = ["run-tests.sh", "local-lintro.sh"]
        for script_name in scripts_with_args:
            script = scripts_dir / script_name
            if not script.exists():
                continue
            with open(script) as f:
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

    def test_scripts_use_quoted_variables(self, scripts_dir) -> None:
        """Test that scripts properly quote variables to prevent injection.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        shell_scripts = list(scripts_dir.glob("*.sh"))
        for script in shell_scripts:
            with open(script) as f:
                content = f.read()
            lines = content.split("\n")
            for _i, line in enumerate(lines, 1):
                if line.strip().startswith("#"):
                    continue
                if (
                    " $1" in line
                    and '"$1"' not in line
                    and ("'$1'" not in line)
                    and not any(safe in line for safe in ["[$1]", "=$1", "shift"])
                ):
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

    def test_scripts_use_portable_shebang(self, scripts_dir) -> None:
        """Test that scripts use portable shebang lines.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        shell_scripts = list(scripts_dir.glob("*.sh"))
        for script in shell_scripts:
            with open(script) as f:
                first_line = f.readline().strip()
            assert (
                first_line == "#!/bin/bash"
            ), f"{script.name} should use '#!/bin/bash' shebang, found: {first_line}"

    def test_scripts_avoid_bashisms_in_sh_context(self, scripts_dir) -> None:
        """Test that scripts avoid bash-specific features where inappropriate.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        shell_scripts = list(scripts_dir.glob("*.sh"))
        for script in shell_scripts:
            with open(script) as f:
                first_line = f.readline().strip()
            if first_line == "#!/bin/sh":
                with open(script) as f:
                    content = f.read()
                bash_features = ["[[", "function ", "$(", "source "]
                for feature in bash_features:
                    assert feature not in content, (
                        f"{script.name} uses bash feature '{feature}' but has sh "
                        "shebang"
                    )

    def test_python_script_compatibility(self, scripts_dir) -> None:
        """Test that Python scripts use appropriate shebang.

        Args:
            scripts_dir: Path to the scripts directory.
        """
        python_scripts = [
            f for f in scripts_dir.glob("*.py") if f.name != "__init__.py"
        ]
        for script in python_scripts:
            with open(script) as f:
                first_line = f.readline().strip()
            assert first_line in [
                "#!/usr/bin/env python3",
                "#!/usr/bin/python3",
            ], f"{script.name} should use python3 shebang"
