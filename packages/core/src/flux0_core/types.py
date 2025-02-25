from typing import Any, Dict, List, TypeAlias, Union

JSONSerializable: TypeAlias = Union[
    None,  # Maps to JSON `null`
    bool,
    int,
    float,
    str,
    List["JSONSerializable"],
    Dict[str, "JSONSerializable"],
]


def ensure_json_serializable(data: Any) -> JSONSerializable:
    """Recursively ensures data conforms to JSONSerializable."""
    if isinstance(data, (str, int, float, bool, type(None))):
        return data  # Already JSON-compatible

    elif isinstance(data, dict):
        return {str(k): ensure_json_serializable(v) for k, v in data.items()}  # Convert recursively

    elif isinstance(data, list):
        return [ensure_json_serializable(item) for item in data]  # Convert recursively

    else:
        raise TypeError(f"Unsupported type: {type(data).__name__}")
