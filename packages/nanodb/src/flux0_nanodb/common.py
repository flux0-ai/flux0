from typing import Any, Mapping, Type, get_type_hints


def validate_is_total(document: Mapping[str, Any], schema: Type[Mapping[str, Any]]) -> None:
    required_keys = get_type_hints(schema).keys()
    missing_keys = [key for key in required_keys if key not in document]

    if missing_keys:
        raise TypeError(
            f"TypedDict '{schema.__qualname__}' is missing required keys: {missing_keys}. "
            f"Expected at least the keys: {list(required_keys)}."
        )
