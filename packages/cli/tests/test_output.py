# Define a simple Pydantic model for testing.
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
    item = Item(name="test", value=42)
    result: str = OutputFormatter.format(item, output_format="json")
    expected: str = json.dumps([item.model_dump()], default=str, indent=2)
    assert result == expected


def test_json_output_multiple() -> None:
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


def test_jsonpath_with_root() -> None:
    """
    When using jsonpath with the root expression "$", the output should be the same as the json format.
    """
    item = Item(name="test", value=42)
    result: str = OutputFormatter.format(item, output_format="jsonpath", jsonpath_expr="$")
    expected: str = json.dumps([item.model_dump()], default=str, indent=2)
    assert result == expected


def test_jsonpath_non_root() -> None:
    """
    For a non-root jsonpath expression (e.g. $.name), only the matching values should be returned.
    """
    item = Item(name="test", value=42)
    result: str = OutputFormatter.format(item, output_format="jsonpath", jsonpath_expr="$.name")
    expected: str = json.dumps(["test"], default=str, indent=2)
    assert result == expected


def test_unknown_format() -> None:
    """
    An unknown output format should raise a ClickException.
    """
    item = Item(name="test", value=42)
    with pytest.raises(click.ClickException) as exc_info:
        OutputFormatter.format(item, output_format="xml")
    assert "Unknown output format: xml" in str(exc_info.value)
