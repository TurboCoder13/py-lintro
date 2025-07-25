from abc import ABC, abstractmethod
from typing import Any, List


class TableDescriptor(ABC):
    @abstractmethod
    def get_columns(self) -> List[str]:
        """Return the list of column names in order."""
        pass

    @abstractmethod
    def get_rows(
        self,
        issues: List[Any],
    ) -> List[List[Any]]:
        """Return the values for each column for a list of issues.

        Args:
            issues: List of issue objects to extract data from.

        Returns:
            List[List[Any]]: Nested list representing table rows and columns.
        """
        pass
