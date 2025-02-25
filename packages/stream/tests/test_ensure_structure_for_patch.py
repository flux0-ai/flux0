from typing import cast

import pytest
from flux0_core.types import JSONSerializable
from flux0_stream.patches import ensure_structure_for_patch
from flux0_stream.types import AddOperation, JsonPatchOperation


def make_op(path: str) -> JsonPatchOperation:
    # Cast our dummy operation to PatchOperation for testing purposes.
    return AddOperation(op="add", path=path, value="dummy")


def test_empty_path() -> None:
    op = make_op("")
    result = ensure_structure_for_patch(None, op)
    # When the path is empty, the function defaults to a dict.
    assert isinstance(result, dict)


def test_root_slash() -> None:
    op = make_op("/")
    result = ensure_structure_for_patch(None, op)
    assert isinstance(result, dict)


def test_numeric_first_segment_creates_list() -> None:
    op = make_op("/0")
    result = ensure_structure_for_patch(None, op)
    # When the first segment is numeric, a list is created.
    assert isinstance(result, list)
    assert len(result) == 0


def test_nested_dict_structure() -> None:
    op = make_op("/user/name")
    initial_content: JSONSerializable = {}
    result = ensure_structure_for_patch(initial_content, op)
    # The key "user" should exist and be a dict.
    assert isinstance(result, dict)
    assert "user" in result
    assert isinstance(result["user"], dict)


def test_very_nested_dict_structure() -> None:
    op = make_op("/user/name/first")
    initial_content: JSONSerializable = {}
    result = ensure_structure_for_patch(initial_content, op)
    # The key "user" should exist and be a dict.
    assert isinstance(result, dict)
    assert "user" in result
    assert isinstance(result["user"], dict)
    assert "name" in result["user"]
    assert isinstance(result["user"]["name"], dict)
    with pytest.raises(KeyError):
        assert result["user"]["name"]["first"]


def test_nested_list_structure() -> None:
    op = make_op("/user/0")
    initial_content: JSONSerializable = {}
    result = ensure_structure_for_patch(initial_content, op)
    # The key "user" should exist and be a list.
    assert isinstance(result, dict)
    assert "user" in result
    assert isinstance(result["user"], list)
    assert len(result["user"]) == 0


def test_existing_structure_not_overwritten() -> None:
    # If the structure already exists, it should not be overwritten.
    initial_content: JSONSerializable = {"user": {"name": "Alice"}}
    op = make_op("/user/name")
    result = ensure_structure_for_patch(initial_content, op)
    # The existing "user" dict remains intact.
    assert cast(dict[str, JSONSerializable], result)["user"] == {"name": "Alice"}
