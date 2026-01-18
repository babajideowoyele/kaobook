"""
Matrix class for network data representation.

Adapted from dna/python/dna_app/analysis/matrix.py
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

import numpy as np


@dataclass
class Matrix:
    """
    A network matrix with row/column labels and metadata.

    Can represent:
    - One-mode networks (square matrix, same labels for rows/columns)
    - Two-mode networks (rectangular matrix, different row/column labels)
    """

    data: np.ndarray
    row_labels: List[str]
    column_labels: List[str]
    integer: bool = True
    start_time: Optional[datetime] = None
    stop_time: Optional[datetime] = None
    mid_time: Optional[datetime] = None
    num_statements: int = 0
    row_variable: str = ""
    column_variable: str = ""
    qualifier_variable: str = ""
    aggregation: str = ""
    normalization: str = ""

    def __post_init__(self):
        """Validate matrix dimensions match labels."""
        if self.data.shape[0] != len(self.row_labels):
            raise ValueError(
                f"Row count {self.data.shape[0]} doesn't match "
                f"row labels count {len(self.row_labels)}"
            )
        if self.data.shape[1] != len(self.column_labels):
            raise ValueError(
                f"Column count {self.data.shape[1]} doesn't match "
                f"column labels count {len(self.column_labels)}"
            )

    @property
    def is_one_mode(self) -> bool:
        """Check if this is a one-mode (square) network."""
        return (
            self.data.shape[0] == self.data.shape[1] and
            self.row_labels == self.column_labels
        )

    @property
    def is_two_mode(self) -> bool:
        """Check if this is a two-mode (bipartite) network."""
        return not self.is_one_mode

    @property
    def num_rows(self) -> int:
        return self.data.shape[0]

    @property
    def num_columns(self) -> int:
        return self.data.shape[1]

    @property
    def num_edges(self) -> int:
        return int(np.count_nonzero(self.data))

    @property
    def density(self) -> float:
        """Network density."""
        if self.is_one_mode:
            n = self.num_rows
            possible = n * (n - 1)
        else:
            possible = self.num_rows * self.num_columns
        return self.num_edges / possible if possible > 0 else 0.0

    def get_value(self, row, col) -> float:
        """Get matrix value by index or label."""
        if isinstance(row, str):
            row = self.row_labels.index(row)
        if isinstance(col, str):
            col = self.column_labels.index(col)
        return float(self.data[row, col])

    def row_sums(self) -> np.ndarray:
        return np.sum(self.data, axis=1)

    def column_sums(self) -> np.ndarray:
        return np.sum(self.data, axis=0)

    def remove_isolates(self) -> "Matrix":
        """Remove nodes with no connections."""
        row_has_edges = np.any(self.data != 0, axis=1)
        col_has_edges = np.any(self.data != 0, axis=0)

        if self.is_one_mode:
            has_edges = row_has_edges | col_has_edges
            new_data = self.data[has_edges][:, has_edges]
            new_labels = [l for l, keep in zip(self.row_labels, has_edges) if keep]
            return Matrix(
                data=new_data,
                row_labels=new_labels,
                column_labels=new_labels,
                integer=self.integer,
                num_statements=self.num_statements,
                row_variable=self.row_variable,
                column_variable=self.column_variable,
                aggregation=self.aggregation,
                normalization=self.normalization,
            )
        else:
            new_data = self.data[row_has_edges][:, col_has_edges]
            new_row_labels = [l for l, keep in zip(self.row_labels, row_has_edges) if keep]
            new_col_labels = [l for l, keep in zip(self.column_labels, col_has_edges) if keep]
            return Matrix(
                data=new_data,
                row_labels=new_row_labels,
                column_labels=new_col_labels,
                integer=self.integer,
                num_statements=self.num_statements,
                row_variable=self.row_variable,
                column_variable=self.column_variable,
                aggregation=self.aggregation,
                normalization=self.normalization,
            )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "data": self.data.tolist(),
            "row_labels": self.row_labels,
            "column_labels": self.column_labels,
            "integer": self.integer,
            "num_rows": self.num_rows,
            "num_columns": self.num_columns,
            "num_edges": self.num_edges,
            "density": self.density,
            "is_one_mode": self.is_one_mode,
            "num_statements": self.num_statements,
            "row_variable": self.row_variable,
            "column_variable": self.column_variable,
            "aggregation": self.aggregation,
            "normalization": self.normalization,
        }

    @classmethod
    def zeros(cls, row_labels: List[str], column_labels: List[str], **kwargs) -> "Matrix":
        """Create a zero-filled matrix."""
        data = np.zeros((len(row_labels), len(column_labels)))
        return cls(data=data, row_labels=row_labels, column_labels=column_labels, **kwargs)
