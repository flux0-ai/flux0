from typing import Optional

import click
from flux0_cli.main import Flux0CLIContext
from flux0_cli.utils.decorators import (
    create_options,
    get_options,
    handle_exceptions,
    list_options,
    validate_jsonpath,
)
from flux0_cli.utils.output import OutputFormatter
from flux0_client import Flux0Client
from flux0_client.models.chunkeventstream import ChunkEventStream
from flux0_client.models.emittedeventstream import EmittedEventStream
from flux0_client.models.eventsourcedto import EventSourceDTO
from flux0_client.models.eventtypedto import EventTypeDTO


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


@sessions.command()
@click.pass_context
@click.option("--session-id", required=True, help="ID of the session to interact with")
@click.option("--content", required=True, help="Content of the event")
def create_event(ctx: click.Context, session_id: str, content: str) -> None:
    cli_ctx: Flux0CLIContext = ctx.obj
    client: Flux0Client = cli_ctx.client
    resp = client.sessions.create_event(
        session_id=session_id,
        type_=EventTypeDTO.MESSAGE,
        source=EventSourceDTO.USER,
        content=content,
    )
    for event in resp.generator:
        if isinstance(event, EmittedEventStream):
            print(f"{event.EVENT} : {event.data}")
        elif isinstance(event, ChunkEventStream):
            print(f"chunk event: {event.data.patches}")


@list_options(sessions, "list")
@validate_jsonpath
def list_sessions(ctx: click.Context, output: str, jsonpath: Optional[str]) -> None:
    """List all sessions"""
    cli_ctx: Flux0CLIContext = ctx.obj
    client: Flux0Client = cli_ctx.client
    response = client.sessions.list()

    result = OutputFormatter.format(response.data, output_format=output, jsonpath_expr=jsonpath)
    if result:
        click.echo(result)


@list_options(sessions, "list-events")
@click.option("--session-id", required=True, help="ID of the session to interact with")
@validate_jsonpath
def list_session_events(
    ctx: click.Context, session_id: str, output: str, jsonpath: Optional[str]
) -> None:
    """List session events"""
    cli_ctx: Flux0CLIContext = ctx.obj
    client: Flux0Client = cli_ctx.client
    response = client.sessions.list_events(session_id=session_id)

    result = OutputFormatter.format(response.data, output_format=output, jsonpath_expr=jsonpath)
    if result:
        click.echo(result)
