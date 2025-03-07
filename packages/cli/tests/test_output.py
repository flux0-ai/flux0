import json
from typing import Any, List

import click
import pytest
from flux0_cli.utils.output import OutputFormatter
from pydantic import BaseModel
from rich.table import Table


class Item(BaseModel):
    name: str
    value: int


def test_json_output() -> None:
    """Ensure single model outputs as a JSON object, not an array."""
    item = Item(name="test", value=42)
    result: str = OutputFormatter.format(item, output_format="json")
    expected: str = json.dumps(item.model_dump(), default=str, indent=2)
    assert result == expected


def test_json_output_multiple() -> None:
    """Ensure multiple models output as a JSON array."""
    item1 = Item(name="test1", value=42)
    item2 = Item(name="test2", value=99)
    result: str = OutputFormatter.format([item1, item2], output_format="json")
    expected: str = json.dumps([item1.model_dump(), item2.model_dump()], default=str, indent=2)
    assert result == expected


def test_table_output(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    For table output, the formatter prints the table to the console and returns an empty string.
    We'll monkeypatch the Console.print method to capture the output.
    """
    item = Item(name="test", value=42)
    captured: List[Any] = []

    def fake_print(self: Any, renderable: Any, *args: Any, **kwargs: Any) -> None:
        captured.append(renderable)

    monkeypatch.setattr("rich.console.Console.print", fake_print)
    result: str = OutputFormatter.format(item, output_format="table")
    # The formatter should return an empty string
    assert result == ""
    # And it should have attempted to print a Table
    assert any(isinstance(renderable, Table) for renderable in captured)


def test_jsonpath_with_root_single() -> None:
    """
    JSONPath root "$" should return a JSON object when input is a single model.
    """
    item = Item(name="test", value=42)
    result: str = OutputFormatter.format(item, output_format="jsonpath", jsonpath_expr="$")
    expected: str = json.dumps(item.model_dump(), default=str, indent=2)
    assert result == expected


def test_jsonpath_with_root_multiple() -> None:
    """
    JSONPath root "$" should return a JSON array when input is a list.
    """
    item1 = Item(name="test1", value=42)
    item2 = Item(name="test2", value=99)
    result: str = OutputFormatter.format(
        [item1, item2], output_format="jsonpath", jsonpath_expr="$"
    )
    expected: str = json.dumps([item1.model_dump(), item2.model_dump()], default=str, indent=2)
    assert result == expected


def test_jsonpath_single_value() -> None:
    """
    JSONPath extracting a single value (e.g., '$.name') should return a string, not an array.
    """
    item = Item(name="test", value=42)
    result: str = OutputFormatter.format(item, output_format="jsonpath", jsonpath_expr="$.name")
    expected: str = json.dumps("test", default=str, indent=2)
    assert result == expected


def test_jsonpath_multiple_values() -> None:
    """
    JSONPath extracting multiple values should return an array.
    """
    item1 = Item(name="test1", value=42)
    item2 = Item(name="test2", value=99)
    result: str = OutputFormatter.format(
        [item1, item2], output_format="jsonpath", jsonpath_expr="$.name"
    )
    expected: str = json.dumps(["test1", "test2"], default=str, indent=2)
    assert result == expected


def test_jsonpath_single_value_int() -> None:
    """
    JSONPath extracting a single integer value (e.g., '$.value') should return a number, not an array.
    """
    item = Item(name="test", value=42)
    result: str = OutputFormatter.format(item, output_format="jsonpath", jsonpath_expr="$.value")
    expected: str = json.dumps(42, default=str, indent=2)
    assert result == expected


def test_jsonpath_multiple_values_int() -> None:
    """
    JSONPath extracting multiple integer values should return an array.
    """
    item1 = Item(name="test1", value=42)
    item2 = Item(name="test2", value=99)
    result: str = OutputFormatter.format(
        [item1, item2], output_format="jsonpath", jsonpath_expr="$.value"
    )
    expected: str = json.dumps([42, 99], default=str, indent=2)
    assert result == expected


def test_unknown_format() -> None:
    """
    An unknown output format should raise a ClickException.
    """
    item = Item(name="test", value=42)
    with pytest.raises(click.ClickException) as exc_info:
        OutputFormatter.format(item, output_format="xml")
    assert "Unknown output format: xml" in str(exc_info.value)
