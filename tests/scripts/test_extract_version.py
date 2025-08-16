from __future__ import annotations

import subprocess
from pathlib import Path


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False)


def test_extract_version_from_repo_root(tmp_path: Path) -> None:
    # Copy pyproject.toml into a temp dir to avoid modifying repo state
    repo_root = Path(__file__).resolve().parents[2]
    src = repo_root / "pyproject.toml"
    dst = tmp_path / "pyproject.toml"
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    script = repo_root / "scripts" / "utils" / "extract-version.py"
    result = run(["python", str(script)], cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith("version=")
    assert len(result.stdout.strip().split("=", 1)[1]) > 0


def test_extract_version_with_custom_file(tmp_path: Path) -> None:
    toml = tmp_path / "custom.toml"
    toml.write_text(
        """
[project]
version = "9.9.9"
""".strip(),
        encoding="utf-8",
    )

    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "scripts" / "utils" / "extract-version.py"
    result = run(["python", str(script), "--file", str(toml)], cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "version=9.9.9"
