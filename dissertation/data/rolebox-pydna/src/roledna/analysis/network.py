"""
Network computation algorithms for Discourse Network Analysis.

Implements one-mode and two-mode network generation from statements.
Adapted from dna/python/dna_app/analysis/network.py
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Sequence, List, Dict

import numpy as np

from .matrix import Matrix


class Aggregation(str, Enum):
    """How to aggregate qualifier values when building networks."""
    IGNORE = "ignore"
    CONGRUENCE = "congruence"
    CONFLICT = "conflict"
    SUBTRACT = "subtract"
    COMBINE = "combine"


class Normalization(str, Enum):
    """How to normalize edge weights."""
    NONE = "no"
    AVERAGE = "average"
    JACCARD = "jaccard"
    COSINE = "cosine"
    ACTIVITY = "activity"
    PROMINENCE = "prominence"


class DuplicateHandling(str, Enum):
    """How to handle duplicate statements."""
    INCLUDE = "include"
    DOCUMENT = "document"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"
    ACROSSRANGE = "acrossrange"


@dataclass
class NetworkConfig:
    """Configuration for network generation."""
    row_variable: str = "actor"
    column_variable: str = "concept"
    qualifier_variable: str = "qualifier"
    one_mode: bool = False
    aggregation: Aggregation = Aggregation.CONGRUENCE
    normalization: Normalization = Normalization.NONE
    include_isolates: bool = True
    duplicate_handling: DuplicateHandling = DuplicateHandling.INCLUDE
    start_time: Optional[datetime] = None
    stop_time: Optional[datetime] = None


@dataclass
class StatementData:
    """Lightweight statement for network computation."""
    id: int
    document_id: int
    date_time: datetime
    values: Dict[str, str]
    document_date: Optional[datetime] = None


def extract_labels(statements: Sequence[StatementData], variable: str) -> List[str]:
    """Extract unique labels for a variable from statements."""
    values = set()
    for stmt in statements:
        value = stmt.values.get(variable)
        if value is not None and value != "":
            values.add(str(value))
    return sorted(values)


def create_count_array(
    statements: Sequence[StatementData],
    row_labels: List[str],
    col_labels: List[str],
    qualifier_labels: List[str],
    row_variable: str,
    col_variable: str,
    qualifier_variable: str,
) -> np.ndarray:
    """Create a 3D count array from statements."""
    array = np.zeros((len(row_labels), len(col_labels), len(qualifier_labels)))

    row_index = {label: i for i, label in enumerate(row_labels)}
    col_index = {label: i for i, label in enumerate(col_labels)}
    qual_index = {label: i for i, label in enumerate(qualifier_labels)}

    for stmt in statements:
        row_val = stmt.values.get(row_variable)
        col_val = stmt.values.get(col_variable)
        qual_val = stmt.values.get(qualifier_variable)

        if row_val is None or col_val is None:
            continue

        row_val = str(row_val)
        col_val = str(col_val)
        qual_val = str(qual_val) if qual_val is not None else "True"

        if row_val in row_index and col_val in col_index and qual_val in qual_index:
            i = row_index[row_val]
            j = col_index[col_val]
            k = qual_index[qual_val]
            array[i, j, k] += 1

    return array


def compute_two_mode_matrix(
    statements: Sequence[StatementData],
    config: NetworkConfig,
) -> Matrix:
    """Compute a two-mode (bipartite) network matrix."""
    row_labels = extract_labels(statements, config.row_variable)
    col_labels = extract_labels(statements, config.column_variable)

    if not row_labels or not col_labels:
        return Matrix.zeros(
            row_labels=row_labels or ["(none)"],
            column_labels=col_labels or ["(none)"],
            row_variable=config.row_variable,
            column_variable=config.column_variable,
        )

    qualifier_labels = extract_labels(statements, config.qualifier_variable)
    if not qualifier_labels:
        qualifier_labels = ["True"]

    array = create_count_array(
        statements, row_labels, col_labels, qualifier_labels,
        config.row_variable, config.column_variable, config.qualifier_variable
    )

    if config.aggregation == Aggregation.IGNORE:
        matrix_data = np.sum(array, axis=2)
    elif config.aggregation == Aggregation.SUBTRACT:
        if len(qualifier_labels) >= 2:
            pos_idx = qualifier_labels.index("True") if "True" in qualifier_labels else 0
            neg_idx = qualifier_labels.index("False") if "False" in qualifier_labels else 1
            matrix_data = array[:, :, pos_idx] - array[:, :, neg_idx]
        else:
            matrix_data = array[:, :, 0]
    else:
        matrix_data = np.sum(array, axis=2)

    if config.normalization == Normalization.ACTIVITY:
        row_sums = np.sum(matrix_data, axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1
        matrix_data = matrix_data / row_sums
    elif config.normalization == Normalization.PROMINENCE:
        col_sums = np.sum(matrix_data, axis=0, keepdims=True)
        col_sums[col_sums == 0] = 1
        matrix_data = matrix_data / col_sums

    result = Matrix(
        data=matrix_data,
        row_labels=row_labels,
        column_labels=col_labels,
        integer=(config.normalization == Normalization.NONE),
        num_statements=len(statements),
        row_variable=config.row_variable,
        column_variable=config.column_variable,
        qualifier_variable=config.qualifier_variable,
        aggregation=config.aggregation.value,
        normalization=config.normalization.value,
    )

    if not config.include_isolates:
        result = result.remove_isolates()

    return result


def compute_one_mode_matrix(
    statements: Sequence[StatementData],
    config: NetworkConfig,
) -> Matrix:
    """Compute a one-mode (projected) network matrix."""
    row_labels = extract_labels(statements, config.row_variable)
    col_labels = extract_labels(statements, config.column_variable)

    if not row_labels or not col_labels:
        return Matrix.zeros(
            row_labels=row_labels or ["(none)"],
            column_labels=row_labels or ["(none)"],
            row_variable=config.row_variable,
            column_variable=config.row_variable,
        )

    qualifier_labels = extract_labels(statements, config.qualifier_variable)
    if not qualifier_labels:
        qualifier_labels = ["True"]

    array = create_count_array(
        statements, row_labels, col_labels, qualifier_labels,
        config.row_variable, config.column_variable, config.qualifier_variable
    )

    n = len(row_labels)
    matrix_data = np.zeros((n, n))

    if config.aggregation == Aggregation.CONGRUENCE:
        for i1 in range(n):
            for i2 in range(n):
                if i1 == i2:
                    continue
                for j in range(len(col_labels)):
                    for k in range(len(qualifier_labels)):
                        matrix_data[i1, i2] += array[i1, j, k] * array[i2, j, k]

    elif config.aggregation == Aggregation.CONFLICT:
        for i1 in range(n):
            for i2 in range(n):
                if i1 == i2:
                    continue
                for j in range(len(col_labels)):
                    for k1 in range(len(qualifier_labels)):
                        for k2 in range(len(qualifier_labels)):
                            if k1 != k2:
                                matrix_data[i1, i2] += array[i1, j, k1] * array[i2, j, k2]

    else:  # IGNORE or SUBTRACT
        for i1 in range(n):
            for i2 in range(n):
                if i1 == i2:
                    continue
                for j in range(len(col_labels)):
                    count1 = np.sum(array[i1, j, :])
                    count2 = np.sum(array[i2, j, :])
                    matrix_data[i1, i2] += count1 * count2

    # Normalization
    activity = np.zeros(n)
    for i in range(n):
        activity[i] = np.sum(array[i, :, :])

    if config.normalization == Normalization.AVERAGE:
        for i1 in range(n):
            for i2 in range(n):
                if i1 != i2 and (activity[i1] + activity[i2]) > 0:
                    matrix_data[i1, i2] /= (activity[i1] + activity[i2]) / 2

    elif config.normalization == Normalization.JACCARD:
        for i1 in range(n):
            for i2 in range(n):
                if i1 != i2:
                    intersection = matrix_data[i1, i2]
                    union = activity[i1] + activity[i2] - intersection
                    matrix_data[i1, i2] = intersection / union if union > 0 else 0

    elif config.normalization == Normalization.COSINE:
        for i1 in range(n):
            for i2 in range(n):
                if i1 != i2:
                    denom = np.sqrt(activity[i1] * activity[i2])
                    matrix_data[i1, i2] = matrix_data[i1, i2] / denom if denom > 0 else 0

    result = Matrix(
        data=matrix_data,
        row_labels=row_labels,
        column_labels=row_labels,
        integer=(config.normalization == Normalization.NONE),
        num_statements=len(statements),
        row_variable=config.row_variable,
        column_variable=config.row_variable,
        qualifier_variable=config.qualifier_variable,
        aggregation=config.aggregation.value,
        normalization=config.normalization.value,
    )

    if not config.include_isolates:
        result = result.remove_isolates()

    return result


def compute_network(
    statements: Sequence[StatementData],
    config: NetworkConfig,
) -> Matrix:
    """Compute a network matrix based on configuration."""
    if config.one_mode:
        return compute_one_mode_matrix(statements, config)
    else:
        return compute_two_mode_matrix(statements, config)


def compute_actor_congruence_network(
    statements: Sequence[StatementData],
    actor_variable: str = "actor",
    concept_variable: str = "concept",
    agreement_variable: str = "qualifier",
    normalization: Normalization = Normalization.NONE,
    include_isolates: bool = True,
) -> Matrix:
    """Compute actor-actor congruence network."""
    config = NetworkConfig(
        row_variable=actor_variable,
        column_variable=concept_variable,
        qualifier_variable=agreement_variable,
        one_mode=True,
        aggregation=Aggregation.CONGRUENCE,
        normalization=normalization,
        include_isolates=include_isolates,
    )
    return compute_one_mode_matrix(statements, config)


def compute_actor_conflict_network(
    statements: Sequence[StatementData],
    actor_variable: str = "actor",
    concept_variable: str = "concept",
    agreement_variable: str = "qualifier",
    normalization: Normalization = Normalization.NONE,
    include_isolates: bool = True,
) -> Matrix:
    """Compute actor-actor conflict network."""
    config = NetworkConfig(
        row_variable=actor_variable,
        column_variable=concept_variable,
        qualifier_variable=agreement_variable,
        one_mode=True,
        aggregation=Aggregation.CONFLICT,
        normalization=normalization,
        include_isolates=include_isolates,
    )
    return compute_one_mode_matrix(statements, config)


def compute_affiliation_network(
    statements: Sequence[StatementData],
    actor_variable: str = "actor",
    concept_variable: str = "concept",
    include_isolates: bool = True,
) -> Matrix:
    """Compute actor-concept affiliation (two-mode) network."""
    config = NetworkConfig(
        row_variable=actor_variable,
        column_variable=concept_variable,
        one_mode=False,
        aggregation=Aggregation.IGNORE,
        normalization=Normalization.NONE,
        include_isolates=include_isolates,
    )
    return compute_two_mode_matrix(statements, config)
