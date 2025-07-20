from dataclasses import dataclass
from typing import Optional


@dataclass
class PrettierIssue:
    file: str
    line: Optional[int]
    code: str
    message: str
    column: Optional[int] = None
