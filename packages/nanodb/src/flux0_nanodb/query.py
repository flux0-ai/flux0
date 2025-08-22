from __future__ import annotations

from collections.abc import Mapping as AbcMapping
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

_MISSING = object()


def _get_by_path(obj: Mapping[str, Any], path: str) -> Any:
    """
    Resolve a dotted path like 'user.name.first' into nested mappings.
    Returns _MISSING if any segment is absent or a non-mapping is encountered.
    """
    cur: Any = obj
    for part in path.split("."):
        if isinstance(cur, AbcMapping) and part in cur:
            cur = cur[part]
        else:
            return _MISSING
    return cur


def matches_query(query: QueryFilter, candidate: Mapping[str, Any]) -> bool:
    if isinstance(query, Comparison):
        path_value = _get_by_path(candidate, query.path)
        if path_value is _MISSING:
            return False

        # Ensure path_value is one of the allowed types.
        if not isinstance(path_value, (str, int, float, bool)):
            return False

        if query.op == "$eq":
            return path_value == query.value
        elif query.op == "$ne":
            return path_value != query.value
        elif query.op == "$in":
            if isinstance(query.value, list):
                return path_value in query.value
            raise TypeError("$in operator requires a list as the value.")

        # Ordered comparisons only for int/float on both sides
        if isinstance(path_value, (int, float)) and isinstance(query.value, (int, float)):
            if query.op == "$gt":
                return path_value > query.value
            elif query.op == "$gte":
                return path_value >= query.value
            elif query.op == "$lt":
                return path_value < query.value
            elif query.op == "$lte":
                return path_value <= query.value

        return False

    elif isinstance(query, And):
        return all(matches_query(expr, candidate) for expr in query.expressions)
    elif isinstance(query, Or):
        return any(matches_query(expr, candidate) for expr in query.expressions)
    else:
        raise TypeError("Invalid query filter type.")
