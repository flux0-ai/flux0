from typing import Any, Dict, Mapping

import pytest
from flux0_nanodb.projection import Projection, apply_projection


def test_inclusion_projection() -> None:
    doc: Mapping[str, Any] = {
        "_id": 1,
        "name": "Alice",
        "email": "alice@example.com",
        "age": 30,
        "address": {"city": "Wonderland", "zip": "12345"},
    }
    proj: Mapping[str, Projection] = {
        "name": Projection.INCLUDE,
        "address.city": Projection.INCLUDE,
    }
    projected: Dict[str, Any] = apply_projection(doc, proj)
    expected: Dict[str, Any] = {"_id": 1, "name": "Alice", "address": {"city": "Wonderland"}}
    assert projected == expected


def test_exclusion_projection() -> None:
    doc: Mapping[str, Any] = {
        "_id": 1,
        "name": "Alice",
        "email": "alice@example.com",
        "age": 30,
        "address": {"city": "Wonderland", "zip": "12345"},
    }
    proj: Mapping[str, Projection] = {
        "email": Projection.EXCLUDE,
        "address.zip": Projection.EXCLUDE,
    }
    projected: Dict[str, Any] = apply_projection(doc, proj)
    expected: Dict[str, Any] = {
        "_id": 1,
        "name": "Alice",
        "age": 30,
        "address": {"city": "Wonderland"},
    }
    assert projected == expected


def test_mix_projection_error() -> None:
    doc: Mapping[str, Any] = {"_id": 1, "a": "test", "b": "value"}
    proj: Mapping[str, Projection] = {"a": Projection.INCLUDE, "b": Projection.EXCLUDE}
    with pytest.raises(ValueError):
        apply_projection(doc, proj)
