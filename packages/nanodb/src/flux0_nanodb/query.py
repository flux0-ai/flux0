from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Literal, Mapping, Union

# Basic literal types that can be used in comparisons.
LiteralValue = Union[str, int, float, bool]

# Supported operators, now including "$in".
Operator = Literal["$eq", "$ne", "$gt", "$gte", "$lt", "$lte", "$in"]


@dataclass(frozen=True)
class Comparison:
    """
    Represents a filter that compares a path to a literal value.
    For the "$in" operator, `value` should be a list of literal values.
    """

    path: str
    op: Operator
    value: Union[LiteralValue, List[LiteralValue]]


@dataclass(frozen=True)
class And:
    """
    A logical 'AND' of a list of query expressions.
    """

    expressions: List[QueryFilter]


@dataclass(frozen=True)
class Or:
    """
    A logical 'OR' of a list of query expressions.
    """

    expressions: List[QueryFilter]


# A query filter can be a comparison or a logical combination.
QueryFilter = Union[Comparison, And, Or]


def matches_query(query: QueryFilter, candidate: Mapping[str, Any]) -> bool:
    if isinstance(query, Comparison):
        path_value = candidate.get(query.path)

        # Ensure path_value is one of the allowed types.
        if not isinstance(path_value, (str, int, float, bool)):
            return False  # Reject invalid types

        if query.op == "$eq":
            return path_value == query.value
        elif query.op == "$ne":
            return path_value != query.value
        elif query.op == "$in":
            # Ensure that query.value is a list before checking containment
            if isinstance(query.value, list):
                return path_value in query.value
            else:
                raise TypeError("$in operator requires a list as the value.")

        # Ensure ordered comparisons are done only for int and float.
        if isinstance(path_value, (int, float)) and isinstance(query.value, (int, float)):
            if query.op == "$gt":
                return path_value > query.value
            elif query.op == "$gte":
                return path_value >= query.value
            elif query.op == "$lt":
                return path_value < query.value
            elif query.op == "$lte":
                return path_value <= query.value

        # If comparison is invalid (e.g., str compared with int), return False.
        return False

    elif isinstance(query, And):
        return all(matches_query(expr, candidate) for expr in query.expressions)
    elif isinstance(query, Or):
        return any(matches_query(expr, candidate) for expr in query.expressions)
    else:
        raise TypeError("Invalid query filter type.")
