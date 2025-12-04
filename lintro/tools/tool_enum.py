"""ToolEnum for all Lintro tools, mapping to their classes."""

from enum import Enum

from lintro.tools.implementations.tool_actionlint import ActionlintTool
from lintro.tools.implementations.tool_bandit import BanditTool
from lintro.tools.implementations.tool_black import BlackTool
from lintro.tools.implementations.tool_darglint import DarglintTool
from lintro.tools.implementations.tool_hadolint import HadolintTool
from lintro.tools.implementations.tool_markdownlint import MarkdownlintTool
from lintro.tools.implementations.tool_prettier import PrettierTool
from lintro.tools.implementations.tool_pytest import PytestTool
from lintro.tools.implementations.tool_ruff import RuffTool
from lintro.tools.implementations.tool_yamllint import YamllintTool


class ToolEnum(Enum):
    """Enumeration mapping tool names to their implementation classes."""

    BLACK = BlackTool
    DARGLINT = DarglintTool
    HADOLINT = HadolintTool
    MARKDOWNLINT = MarkdownlintTool
    PRETTIER = PrettierTool
    PYTEST = PytestTool
    RUFF = RuffTool
    YAMLLINT = YamllintTool
    ACTIONLINT = ActionlintTool
    BANDIT = BanditTool
