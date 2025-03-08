import importlib
import importlib.resources as pkg_resources
import pkgutil
from typing import Any, Callable, TypeVar, Union, overload

import click
from flux0_client import Flux0Client

F = TypeVar("F", bound=Callable[..., Any])


class CLIGroup(click.Group):
    @overload
    def command(self, __func: Callable[..., Any]) -> click.Command: ...

    @overload
    def command(
        self, *args: Any, **kwargs: Any
    ) -> Callable[[Callable[..., Any]], click.Command]: ...

    def command(
        self, *args: Any, **kwargs: Any
    ) -> Union[click.Command, Callable[[Callable[..., Any]], click.Command]]:
        original_decorator = super().command(*args, **kwargs)

        def decorator(f: Callable[..., Any]) -> click.Command:
            # You can apply additional decorators or logging here if needed.
            result = original_decorator(f)
            assert isinstance(result, click.Command)
            return result

        if args and callable(args[0]):
            # If the first argument is a callable, treat it as the function to decorate.
            return decorator(args[0])
        else:
            # Otherwise, return the decorator function.
            return decorator


class Flux0CLIContext:
    """Typed context object for Click CLI."""

    def __init__(self) -> None:
        self.client: Flux0Client = Flux0Client()


# Main CLI group
@click.group(cls=CLIGroup)
@click.pass_context
def main(ctx: click.Context) -> None:
    """Flux0 CLI"""

    # Ensure ctx.obj is properly initialized
    if ctx.obj is None:
        ctx.obj = Flux0CLIContext()  # Use the typed context object


# Dynamically load commands from the "commands" package
def register_commands() -> None:
    # Use importlib.resources to safely access the package's contents
    with pkg_resources.path("flux0_cli.cmds", "__init__.py") as pkg_path:
        pkg_dir = pkg_path.parent

        for module_info in pkgutil.iter_modules([str(pkg_dir)]):
            module = importlib.import_module(f"flux0_cli.cmds.{module_info.name}")
            # Look for click groups defined in the module and add them
            for attr in dir(module):
                cmd = getattr(module, attr)
                if isinstance(cmd, click.Group):
                    main.add_command(cmd)


register_commands()

if __name__ == "__main__":
    main()
