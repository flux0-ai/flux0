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


@click.group()
def agents() -> None:
    """Manage agents"""
    pass


@get_options(agents, "get")
@handle_exceptions
def get_agent(ctx: click.Context, id: str, output: str, jsonpath: Optional[str]) -> None:
    """Retrieve an agent by ID"""
    cli_ctx: Flux0CLIContext = ctx.obj
    client: Flux0Client = cli_ctx.client
    agent = client.agents.retrieve(agent_id=id)
    result = OutputFormatter.format(agent, output_format=output, jsonpath_expr=jsonpath)
    if result:
        click.echo(result)


@list_options(agents, "list")
@validate_jsonpath
def list_agents(ctx: click.Context, output: str, jsonpath: Optional[str]) -> None:
    """Retrieve agents"""
    cli_ctx: Flux0CLIContext = ctx.obj
    client: Flux0Client = cli_ctx.client
    response = client.agents.list()

    result = OutputFormatter.format(response.data, output_format=output, jsonpath_expr=jsonpath)
    if result:
        click.echo(result)


@create_options(agents, "create")
@click.option("--name", required=True, help="Name of the agent")
@click.option("--type", "agent_type", required=True, help="Type of the agent")
@click.option(
    "--description",
    type=str,
    required=False,
    help="Optional description of the agent",
)
def create_agent(
    ctx: click.Context,
    name: str,
    agent_type: str,
    output: str,
    jsonpath: Optional[str],
    description: Optional[str] = None,  # Added description field with default None
) -> None:
    """Create a new agent"""
    cli_ctx: Flux0CLIContext = ctx.obj
    client: Flux0Client = cli_ctx.client

    # Pass the description if provided
    agent = client.agents.create(name=name, type_=agent_type, description=description)

    result = OutputFormatter.format(agent, output_format=output, jsonpath_expr=jsonpath)
    if result:
        click.echo(result)
