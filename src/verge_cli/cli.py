"""Main CLI application entry point."""

from __future__ import annotations

from typing import Annotated

import click
import typer

from verge_cli import __version__
from verge_cli.commands import cluster, configure, network, node, storage, system, tenant, vm
from verge_cli.config import get_effective_config

app = typer.Typer(
    name="vrg",
    help="Command-line interface for VergeOS.",
    no_args_is_help=True,
)

# Register sub-commands
app.add_typer(cluster.app, name="cluster")
app.add_typer(configure.app, name="configure")
app.add_typer(network.app, name="network")
app.add_typer(node.app, name="node")
app.add_typer(storage.app, name="storage")
app.add_typer(system.app, name="system")
app.add_typer(tenant.app, name="tenant")
app.add_typer(vm.app, name="vm")


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo(f"vrg version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    profile: Annotated[
        str | None,
        typer.Option(
            "--profile",
            "-p",
            help="Configuration profile to use.",
            envvar="VERGE_PROFILE",
        ),
    ] = None,
    host: Annotated[
        str | None,
        typer.Option(
            "--host",
            "-H",
            help="VergeOS host URL (overrides profile).",
            envvar="VERGE_HOST",
        ),
    ] = None,
    token: Annotated[
        str | None,
        typer.Option(
            "--token",
            help="Bearer token for authentication.",
            envvar="VERGE_TOKEN",
        ),
    ] = None,
    api_key: Annotated[
        str | None,
        typer.Option(
            "--api-key",
            help="API key for authentication.",
            envvar="VERGE_API_KEY",
        ),
    ] = None,
    username: Annotated[
        str | None,
        typer.Option(
            "--username",
            "-u",
            help="Username for basic authentication.",
            envvar="VERGE_USERNAME",
        ),
    ] = None,
    password: Annotated[
        str | None,
        typer.Option(
            "--password",
            help="Password for basic authentication.",
            envvar="VERGE_PASSWORD",
        ),
    ] = None,
    output: Annotated[
        str,
        typer.Option(
            "--output",
            "-o",
            help="Output format.",
            click_type=click.Choice(["table", "wide", "json", "csv"]),
        ),
    ] = "table",
    query: Annotated[
        str | None,
        typer.Option(
            "--query",
            help="Extract specific field using dot notation (e.g., 'status' or 'config.host').",
        ),
    ] = None,
    verbose: Annotated[
        int,
        typer.Option(
            "--verbose",
            "-v",
            count=True,
            help="Increase verbosity (-v, -vv, -vvv).",
        ),
    ] = 0,
    quiet: Annotated[
        bool,
        typer.Option(
            "--quiet",
            "-q",
            help="Suppress non-essential output.",
        ),
    ] = False,
    no_color: Annotated[
        bool,
        typer.Option(
            "--no-color",
            help="Disable colored output.",
            envvar="NO_COLOR",
        ),
    ] = False,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-V",
            help="Show version and exit.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = False,
) -> None:
    """Verge CLI - Command-line interface for VergeOS."""
    # Load configuration with environment overrides
    config = get_effective_config(profile)

    # Apply CLI overrides to config
    if host:
        config.host = host
    if token:
        config.token = token
    if api_key:
        config.api_key = api_key
    if username:
        config.username = username
    if password:
        config.password = password

    # Use output format from CLI or fall back to config
    effective_output = output if output != "table" else config.output

    # Store CLI overrides for lazy client creation
    ctx.ensure_object(dict)
    ctx.obj["config"] = config
    ctx.obj["output_format"] = effective_output
    ctx.obj["verbosity"] = verbose
    ctx.obj["quiet"] = quiet
    ctx.obj["query"] = query
    ctx.obj["no_color"] = no_color
    ctx.obj["_client"] = None  # Lazy-loaded client
