from flux0_core.types import JSONSerializable

from flux0_stream.types import JsonPatchOperation


def ensure_structure_for_patch(
    content: JSONSerializable,
    op: JsonPatchOperation,
) -> JSONSerializable:
    """
    Ensure that the parent structure for a JSON patch operation exists.

    Given a content object and a patch (with a "path" key), this function
    traverses the path (excluding the last segment) and creates missing containers.

    - If the first segment of the path is "-" or a digit, the root is ensured to be a list.
    - For non-numeric segments, a dict is used.
    - For a segment whose next segment is numeric, the default container is a list;
      otherwise, it is a dict.

    Returns the updated content.
    """
    path = op["path"]
    # Nothing to ensure at the root level.
    if path in ("", "/"):
        if content is None:
            content = {}  # default to dict at the root
        return content

    parts = path.strip("/").split("/")
    first = parts[0]
    # If content is missing, initialize based on the first segment.
    if content is None:
        content = [] if (first == "-" or first.isdigit()) else {}

    current: JSONSerializable = content
    # Traverse through all segments except the final one.
    for i, part in enumerate(parts[:-1]):
        next_part = parts[i + 1] if i + 1 < len(parts) else None

        if part == "-":
            raise ValueError(f"Invalid '-' in intermediate segment of path: {path}")

        if part.isdigit():
            # This segment should index into a list.
            if not isinstance(current, list):
                raise TypeError(
                    f"Expected list at segment '{part}' in path '{path}', got {type(current).__name__}"
                )
            index = int(part)
            # Extend the list until the index exists.
            while len(current) <= index:
                default: JSONSerializable = [] if (next_part and next_part.isdigit()) else {}
                current.append(default)
            current = current[index]
        else:
            # This segment should be a key in a dict.
            if not isinstance(current, dict):
                raise TypeError(
                    f"Expected dict at segment '{part}' in path '{path}', got {type(current).__name__}"
                )
            if part not in current:
                current[part] = [] if (next_part and next_part.isdigit()) else {}
            elif next_part and next_part.isdigit() and not isinstance(current[part], list):
                # If the next segment indicates a list but we have a dict, override.
                current[part] = []
            current = current[part]

    return content
