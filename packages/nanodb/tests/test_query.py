from typing import Any, Mapping

import pytest
from flux0_nanodb.query import (
    And,
    Comparison,
    Or,
    QueryFilter,
    matches_query,
)


def test_comparison_eq_true() -> None:
    query: QueryFilter = Comparison(path="name", op="$eq", value="Alice")
    candidate: Mapping[str, Any] = {"name": "Alice"}
    assert matches_query(query, candidate)


def test_comparison_eq_false() -> None:
    query: QueryFilter = Comparison(path="name", op="$eq", value="Alice")
    candidate: Mapping[str, Any] = {"name": "Bob"}
    assert not matches_query(query, candidate)


def test_comparison_ne_true() -> None:
    query: QueryFilter = Comparison(path="age", op="$ne", value=30)
    candidate: Mapping[str, Any] = {"age": 25}
    assert matches_query(query, candidate)


def test_comparison_ne_false() -> None:
    query: QueryFilter = Comparison(path="age", op="$ne", value=30)
    candidate: Mapping[str, Any] = {"age": 30}
    assert not matches_query(query, candidate)


def test_comparison_gt_true() -> None:
    query: QueryFilter = Comparison(path="score", op="$gt", value=50)
    candidate: Mapping[str, Any] = {"score": 60}
    assert matches_query(query, candidate)


def test_comparison_gt_false() -> None:
    query: QueryFilter = Comparison(path="score", op="$gt", value=50)
    candidate: Mapping[str, Any] = {"score": 40}
    assert not matches_query(query, candidate)


def test_comparison_gte_true() -> None:
    query: QueryFilter = Comparison(path="score", op="$gte", value=50)
    candidate: Mapping[str, Any] = {"score": 50}
    assert matches_query(query, candidate)


def test_comparison_lt_true() -> None:
    query: QueryFilter = Comparison(path="score", op="$lt", value=50)
    candidate: Mapping[str, Any] = {"score": 40}
    assert matches_query(query, candidate)


def test_comparison_lte_true() -> None:
    query: QueryFilter = Comparison(path="score", op="$lte", value=50)
    candidate: Mapping[str, Any] = {"score": 50}
    assert matches_query(query, candidate)


def test_comparison_in_true() -> None:
    query: QueryFilter = Comparison(path="age", op="$in", value=[25, 30, 35])
    candidate: Mapping[str, Any] = {"age": 30}
    assert matches_query(query, candidate)


def test_comparison_in_false() -> None:
    query: QueryFilter = Comparison(path="age", op="$in", value=[25, 30, 35])
    candidate: Mapping[str, Any] = {"age": 40}
    assert not matches_query(query, candidate)


def test_invalid_path_type() -> None:
    # When the candidate path value isn't one of the allowed literal types,
    # matches_query should return False.
    query: QueryFilter = Comparison(path="active", op="$eq", value=True)
    candidate: Mapping[str, Any] = {"active": [True]}  # List is not an allowed literal type.
    assert not matches_query(query, candidate)


def test_missing_path() -> None:
    query: QueryFilter = Comparison(path="nonexistent", op="$eq", value="test")
    candidate: Mapping[str, Any] = {"name": "Alice"}
    assert not matches_query(query, candidate)


def test_and_query_true() -> None:
    query: QueryFilter = And(
        expressions=[
            Comparison(path="age", op="$eq", value=30),
            Comparison(path="name", op="$eq", value="Alice"),
        ]
    )
    candidate: Mapping[str, Any] = {"age": 30, "name": "Alice"}
    assert matches_query(query, candidate)


def test_and_query_false() -> None:
    query: QueryFilter = And(
        expressions=[
            Comparison(path="age", op="$eq", value=30),
            Comparison(path="name", op="$eq", value="Alice"),
        ]
    )
    candidate: Mapping[str, Any] = {"age": 30, "name": "Bob"}
    assert not matches_query(query, candidate)


def test_or_query_true() -> None:
    query: QueryFilter = Or(
        expressions=[
            Comparison(path="age", op="$eq", value=25),
            Comparison(path="name", op="$eq", value="Alice"),
        ]
    )
    candidate: Mapping[str, Any] = {"age": 30, "name": "Alice"}
    assert matches_query(query, candidate)


def test_or_query_false() -> None:
    query: QueryFilter = Or(
        expressions=[
            Comparison(path="age", op="$eq", value=25),
            Comparison(path="name", op="$eq", value="Bob"),
        ]
    )
    candidate: Mapping[str, Any] = {"age": 30, "name": "Alice"}
    assert not matches_query(query, candidate)


def test_nested_query_true() -> None:
    # Nested query: (age == 30 OR age == 40) AND name == "Alice"
    nested_or: QueryFilter = Or(
        expressions=[
            Comparison(path="age", op="$eq", value=30),
            Comparison(path="age", op="$eq", value=40),
        ]
    )
    query: QueryFilter = And(
        expressions=[
            nested_or,
            Comparison(path="name", op="$eq", value="Alice"),
        ]
    )
    candidate: Mapping[str, Any] = {"age": 30, "name": "Alice"}
    assert matches_query(query, candidate)


def test_nested_query_false() -> None:
    # Nested query: (age == 30 OR age == 40) AND name == "Alice"
    nested_or: QueryFilter = Or(
        expressions=[
            Comparison(path="age", op="$eq", value=30),
            Comparison(path="age", op="$eq", value=40),
        ]
    )
    query: QueryFilter = And(
        expressions=[
            nested_or,
            Comparison(path="name", op="$eq", value="Alice"),
        ]
    )
    candidate: Mapping[str, Any] = {"age": 50, "name": "Alice"}
    assert not matches_query(query, candidate)


def test_invalid_query_filter_type() -> None:
    # Passing a type that is not a valid QueryFilter should raise a TypeError.
    with pytest.raises(TypeError):
        matches_query(42, {"dummy": "data"})  # type: ignore
