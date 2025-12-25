"""Sample file with pep8-naming (N) violations for testing Ruff.

Intentionally violates several N-rules, such as:
- N802: function name should be lowercase
- N803: argument name should be lowercase
- N806: variable in function should be lowercase
- N815: mixedCase variable in class scope
"""


def BadFunctionName(BadArg: int) -> int:  # N802, N803
    BadLocal = BadArg + 1  # N806
    return BadLocal


class SampleClass:
    camelCaseAttr = 1  # N815

    def GoodMethod(self, BadParam: int) -> int:  # N803
        BadLocalVar = BadParam * 2  # N806
        return BadLocalVar


CONSTANT_ok = 1  # not enforcing caps here; focus on N8xx basics
