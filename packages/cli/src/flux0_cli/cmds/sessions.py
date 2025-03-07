from typing import Optional

import click
from flux0_cli.main import Flux0CLIContext
from flux0_cli.utils.decorators import (
    create_options,
    get_options,
    handle_exceptions,
)
from flux0_cli.utils.output import OutputFormatter
from flux0_client import Flux0Client


@click.group()
def sessions() -> None:
    """Manage sessions"""
    pass


@create_options(sessions, "create")
@handle_exceptions
@click.option("--agent-id", required=True, help="ID of the agent to intreact with")
@click.option("--title", required=False, help="Optional title of the session")
def create_agent(
    ctx: click.Context,
    agent_id: str,
    output: str,
    jsonpath: Optional[str],
    title: Optional[str],
) -> None:
    """Create a new agent"""
    cli_ctx: Flux0CLIContext = ctx.obj
    client: Flux0Client = cli_ctx.client

    session = client.sessions.create(agent_id=agent_id, title=title)

    result = OutputFormatter.format(session, output_format=output, jsonpath_expr=jsonpath)
    if result:
        click.echo(result)


@get_options(sessions, "get")
@handle_exceptions
def get_session(ctx: click.Context, id: str, output: str, jsonpath: Optional[str]) -> None:
    """Retrieve a session by ID"""
    cli_ctx: Flux0CLIContext = ctx.obj
    client: Flux0Client = cli_ctx.client
    session = client.sessions.retrieve(session_id=id)
    result = OutputFormatter.format(session, output_format=output, jsonpath_expr=jsonpath)
    if result:
        click.echo(result)
