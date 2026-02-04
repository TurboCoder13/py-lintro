"""Complete environment report."""

from __future__ import annotations

from dataclasses import dataclass

from lintro.utils.environment.ci_environment import CIEnvironment
from lintro.utils.environment.go_info import GoInfo
from lintro.utils.environment.lintro_info import LintroInfo
from lintro.utils.environment.node_info import NodeInfo
from lintro.utils.environment.project_info import ProjectInfo
from lintro.utils.environment.python_info import PythonInfo
from lintro.utils.environment.ruby_info import RubyInfo
from lintro.utils.environment.rust_info import RustInfo
from lintro.utils.environment.system_info import SystemInfo


@dataclass
class EnvironmentReport:
    """Complete environment report."""

    lintro: LintroInfo
    system: SystemInfo
    python: PythonInfo
    node: NodeInfo | None
    rust: RustInfo | None
    ci: CIEnvironment | None
    env_vars: dict[str, str | None]
    go: GoInfo | None = None
    ruby: RubyInfo | None = None
    project: ProjectInfo | None = None
