from dataclasses import dataclass


@dataclass
class PrettierIssue:
    file: str
    line: int | None
    code: str
    message: str
    column: int | None = None
