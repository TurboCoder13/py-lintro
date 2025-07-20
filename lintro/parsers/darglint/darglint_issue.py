from dataclasses import dataclass


@dataclass
class DarglintIssue:
    file: str
    line: int
    code: str
    message: str
