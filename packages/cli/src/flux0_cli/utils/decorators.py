import functools
import json
from typing import Any, Callable, Optional, TypeVar, cast

import click
from flux0_client.models.apierror import APIError


def validate_jsonpath(f: Callable[..., Any]) -> Callable[..., Any]:
    """Click decorator to enforce JSONPath rules automatically."""

    @functools.wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        jsonpath_expr: Optional[str] = kwargs.get("jsonpath")
        output_format: str = kwargs.get("output", "table")

        # If --jsonpath is used, force output to jsonpath and reject table format
        if jsonpath_expr is not None:
            if output_format == "table":
                raise click.ClickException(
                    "Error: --jsonpath cannot be used with -o table. Use -o json instead."
                )
            kwargs["output"] = "jsonpath"
        return f(*args, **kwargs)

    return wrapper


F = TypeVar("F", bound=Callable[..., Any])


def get_options(group: click.Group, command_name: str) -> Callable[[F], F]:
    """Decorator to apply common options for 'get' commands dynamically."""

    def decorator(func: F) -> F:
        @group.command(command_name)
        @click.argument("id")
        @click.option(
            "--jsonpath",
            type=str,
            help="JSONPath expression (automatically sets output to jsonpath)",
        )
        @click.option(
            "-o",
            "--output",
            type=click.Choice(["json", "table", "jsonpath"]),
            default="table",
            help="Output format",
        )
        @click.pass_context
        @validate_jsonpath
        @functools.wraps(func)
        def wrapper(ctx: click.Context, id: str, output: str, jsonpath: Optional[str]) -> Any:
            return func(ctx, id, output, jsonpath)

        functools.update_wrapper(wrapper, func)  # Preserve function metadata
        return cast(F, wrapper)

    return decorator


def list_options(group: click.Group, command_name: str) -> Callable[[F], F]:
    """Decorator to apply common options for 'list' commands dynamically."""

    def decorator(func: F) -> F:
        decorated_func: Callable[..., Any] = func  # Explicitly cast to avoid mypy errors

        decorated_func = click.option(
            "--jsonpath",
            type=str,
            help="JSONPath expression (automatically sets output to jsonpath)",
        )(decorated_func)

        decorated_func = click.option(
            "-o",
            "--output",
            type=click.Choice(["json", "table", "jsonpath"]),
            default="table",
            help="Output format (automatically switches to jsonpath if --jsonpath is used)",
        )(decorated_func)

        decorated_func = validate_jsonpath(decorated_func)
        decorated_func = click.pass_context(decorated_func)

        # Register the command with the group
        group.command(name=command_name)(decorated_func)

        return cast(F, decorated_func)  # Cast back to F to satisfy type checks

    return decorator


def create_options(group: click.Group, command_name: str) -> Callable[[F], F]:
    """Decorator to apply common options for 'create' commands dynamically."""

    def decorator(func: F) -> F:
        @group.command(command_name)
        @click.option(
            "--jsonpath",
            type=str,
            help="JSONPath expression (automatically sets output to jsonpath)",
        )
        @click.option(
            "-o",
            "--output",
            type=click.Choice(["json", "table", "jsonpath"]),
            default="table",
            help="Output format",
        )
        @click.pass_context
        @validate_jsonpath
        @functools.wraps(func)
        def wrapper(ctx: click.Context, *args: Any, **kwargs: Any) -> Any:
            """Ensures correct argument passing without duplication."""
            return func(ctx, *args, **kwargs)

        functools.update_wrapper(wrapper, func)  # Preserve function metadata
        return cast(F, wrapper)  # Ensure correct return type for Mypy

    return decorator


def handle_exceptions(f: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to handle common exceptions in CLI commands."""

    @functools.wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return f(*args, **kwargs)
        except APIError as e:
            click.echo(f"❌ {json.loads(e.body).get('detail', 'Unknown error')}", err=True)
        except Exception as e:
            click.echo(f"⚠️ Unexpected error: {e}", err=True)
            return None  # Ensures the function always returns something

    return wrapper
