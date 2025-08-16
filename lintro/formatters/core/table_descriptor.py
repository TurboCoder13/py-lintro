from abc import ABC, abstractmethod
from typing import Any


class TableDescriptor(ABC):
    @abstractmethod
    def get_columns(self) -> list[str]:
        """Return the list of column names in order."""
        pass

    @abstractmethod
    def get_rows(
        self,
        issues: list[Any],
    ) -> list[list[Any]]:
        """Return the values for each column for a list of issues.

        Args:
            issues: List of issue objects to extract data from.

        Returns:
            list[list]: Nested list representing table rows and columns.
        """
        pass
