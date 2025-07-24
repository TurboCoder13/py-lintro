from abc import ABC, abstractmethod
from typing import Any, List


class OutputStyle(ABC):
    @abstractmethod
    def format(
        self,
        columns: List[str],
        rows: List[List[Any]],
    ) -> str:
        """Format a table given columns and rows.

        Args:
            columns: List of column header names.
            rows: List of rows, where each row is a list of values.

        Returns:
            str: Formatted table as a string.
        """
        pass
