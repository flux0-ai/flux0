import json
from typing import Optional, Sequence, Union

import click
from jsonpath_ng import parse  # type: ignore
from pydantic import BaseModel
from rich.console import Console
from rich.table import Table


class OutputFormatter:
    @staticmethod
    def format(
        data: Union[BaseModel, Sequence[BaseModel]],
        output_format: str = "table",
        jsonpath_expr: Optional[str] = None,
    ) -> str:
        """
        Format one or more Pydantic models using the specified output format.
        """
        models = [data] if isinstance(data, BaseModel) else data
        data_dicts = [model.model_dump() for model in models]

        if output_format == "json":
            return json.dumps(
                data_dicts[0] if isinstance(data, BaseModel) else data_dicts, default=str, indent=2
            )

        elif output_format == "table":
            if not data_dicts:
                return ""
            console = Console()
            table = Table(show_header=True, header_style="bold")
            headers = list(data_dicts[0].keys())
            for header in headers:
                table.add_column(header)
            for d in data_dicts:
                table.add_row(*(str(d.get(header, "")) for header in headers))
            console.print(table)
            return ""  # Prevent duplicate output

        elif output_format == "jsonpath":
            if jsonpath_expr is None:
                jsonpath_expr = "$"

            expr = parse(jsonpath_expr)
            matches = [match.value for d in data_dicts for match in expr.find(d)]

            # Always return JSON format
            if not matches:
                return json.dumps(None)  # Return null if no match
            elif len(matches) == 1:
                return json.dumps(matches[0], default=str, indent=2)  # Single value as JSON
            else:
                return json.dumps(
                    matches, default=str, indent=2
                )  # Always JSON array for multiple values

        else:
            raise click.ClickException(f"Unknown output format: {output_format}")
