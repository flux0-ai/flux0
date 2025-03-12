# projection.py
from enum import Enum
from typing import Any, Dict, Mapping


class Projection(Enum):
    INCLUDE = 1
    EXCLUDE = 0


def apply_projection(
    document: Mapping[str, Any], projection: Mapping[str, Projection]
) -> Dict[str, Any]:
    """
    Applies a projection on a document.

    - Inclusion: Only the specified fields are returned (plus _id by default).
    - Exclusion: All fields are returned except the ones specified.

    Deep selection (e.g. "address.city") is supported.
    """
    if not projection:
        return dict(document)

    # Determine inclusion or exclusion (ignoring _id)
    include_keys = [
        key for key, val in projection.items() if key != "_id" and val == Projection.INCLUDE
    ]
    exclude_keys = [
        key for key, val in projection.items() if key != "_id" and val == Projection.EXCLUDE
    ]
    if include_keys and exclude_keys:
        raise ValueError("Cannot mix inclusion and exclusion in projection (except for _id).")

    is_inclusion: bool = bool(include_keys)

    if is_inclusion:
        result: Dict[str, Any] = {}
        # Include _id by default unless explicitly excluded.
        if projection.get("_id", Projection.INCLUDE) != Projection.EXCLUDE and "_id" in document:
            result["_id"] = document["_id"]

        for proj_key, proj_val in projection.items():
            if proj_key == "_id" or proj_val != Projection.INCLUDE:
                continue
            parts = proj_key.split(".")
            src: Any = document
            valid = True
            for part in parts:
                if isinstance(src, dict) and part in src:
                    src = src[part]
                else:
                    valid = False
                    break
            if valid:
                current = result
                for part in parts[:-1]:
                    if part not in current or not isinstance(current[part], dict):
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = src
        return result

    else:
        # Exclusion: start with a copy of the document and remove specified keys.
        result = dict(document)
        if projection.get("_id", Projection.INCLUDE) == Projection.EXCLUDE:
            result.pop("_id", None)
        for proj_key, proj_val in projection.items():
            if proj_key == "_id" or proj_val != Projection.EXCLUDE:
                continue
            parts = proj_key.split(".")
            if len(parts) == 1:
                result.pop(proj_key, None)
            else:
                current_result: Any = result
                for part in parts[:-1]:
                    if part in current_result and isinstance(current_result[part], dict):
                        current_result = current_result[part]
                    else:
                        current_result = None
                        break
                if current_result is not None:
                    current_result.pop(parts[-1], None)
        return result
