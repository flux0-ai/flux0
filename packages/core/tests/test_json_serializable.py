import json

import pytest
from flux0_core.types import JSONSerializable


@pytest.mark.parametrize(
    "valid_data",
    [
        {
            "name": "Alice",
            "age": 30,
            "is_active": True,
            "scores": [100, 95.5, None],
            "metadata": {"verified": False, "rank": None},
        },
        {"empty_list": [], "empty_dict": {}, "null_value": None},
        {"nested": {"level1": {"level2": [{"level3": None}, {"level3": 42.0}]}}},
        [1, "string", 3.14, None, False, {"key": "value"}, [1, 2, 3]],
        None,  # Edge case: None alone should be serializable
    ],
)
def test_valid_json_serializable(valid_data: JSONSerializable) -> None:
    """Test that valid JSONSerializable data types pass serialization"""
    # Removed isinstance check for JSONSerializable as it is a generic type
    json_str = json.dumps(valid_data)  # Ensure JSON serialization works
    assert isinstance(json_str, str)


@pytest.mark.parametrize(
    "invalid_data",
    [
        {"name": set(["Alice", "Bob"])},  # Sets are not JSON serializable
        {"key": object()},  # Objects are not JSON serializable
        {"lambda": lambda x: x},  # Functions are not JSON serializable
    ],
)
def test_invalid_json_serializable(invalid_data: JSONSerializable) -> None:
    """Test that invalid JSONSerializable data types raise errors"""
    with pytest.raises(TypeError):
        json.dumps(invalid_data)  # Should raise TypeError


def test_empty_structures() -> None:
    """Test serialization of empty JSON structures"""
    empty_dict: JSONSerializable = {}
    empty_list: JSONSerializable = []
    null_value: JSONSerializable = None

    assert json.dumps(empty_dict) == "{}"
    assert json.dumps(empty_list) == "[]"
    assert json.dumps(null_value) == "null"


@pytest.mark.parametrize(
    "nested_data",
    [
        {"level1": {"level2": [{"level3": None}, {"level3": 42.0}]}},
        {"deep": {"a": {"b": {"c": {"d": {"e": "final"}}}}}},
    ],
)
def test_nested_json_serializable(nested_data: JSONSerializable) -> None:
    """Test deeply nested JSON-serializable structures"""
    json_str = json.dumps(nested_data)
    assert isinstance(json_str, str)
