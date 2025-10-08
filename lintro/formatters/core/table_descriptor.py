"""Interfaces for describing table columns and rows for tool issues."""

from abc import ABC, abstractmethod
from typing import Any


class TableDescriptor(ABC):
    """Describe how to extract tabular data for a tool's issues.

    Concrete implementations define column ordering and how to map issue
    objects into a list of column values.
    """

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
