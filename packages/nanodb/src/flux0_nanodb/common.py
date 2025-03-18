from typing import Any, Dict, List, Mapping, Type, get_type_hints

from flux0_nanodb.types import JSONPatchOperation


def validate_is_total(document: Mapping[str, Any], schema: Type[Mapping[str, Any]]) -> None:
    # Use the __required_keys__ attribute if it exists, otherwise fall back to all type hints.
    required_keys = getattr(schema, "__required_keys__", get_type_hints(schema).keys())
    missing_keys = [key for key in required_keys if key not in document]

    if missing_keys:
        raise TypeError(
            f"TypedDict '{schema.__qualname__}' is missing required keys: {missing_keys}. "
            f"Expected at least the keys: {list(required_keys)}."
        )


def convert_patch(patch: List[JSONPatchOperation]) -> List[Dict[str, Any]]:
    converted = []
    for op in patch:
        # Create a shallow copy to avoid mutating the original.
        op_copy = dict(op)
        # For move and copy operations, rename "from_" to "from" as expected by jsonpatch.
        if op_copy.get("op") in ("move", "copy"):
            if "from_" in op_copy:
                op_copy["from"] = op_copy.pop("from_")
        converted.append(op_copy)
    return converted
