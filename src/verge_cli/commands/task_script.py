"""Task script management commands for Verge CLI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any

import typer

from verge_cli.columns import TASK_SCRIPT_COLUMNS
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result, output_success
from verge_cli.utils import confirm_action, resolve_resource_id

app = typer.Typer(
    name="script",
    help="Manage task scripts (GCS automation).",
    no_args_is_help=True,
)


def _script_to_dict(script: Any) -> dict[str, Any]:
    """Convert a TaskScript SDK object to a dictionary for output."""
    return {
        "$key": int(script.key),
        "name": script.name,
        "description": script.get("description", ""),
        "script": script.script_code or "",
        "task_count": script.task_count,
        "settings": script.settings,
    }


def _read_script_input(value: str) -> str:
    """Read script from file (@path) or return raw string."""
    if value.startswith("@"):
        path = Path(value[1:])
        if not path.exists():
            raise typer.BadParameter(f"Script file not found: {path}")
        return path.read_text()
    return value


@app.command("list")
@handle_errors()
def script_list(
    ctx: typer.Context,
    filter: Annotated[
        str | None,
        typer.Option("--filter", help="OData filter expression."),
    ] = None,
) -> None:
    """List task scripts."""
    vctx = get_context(ctx)
    kwargs: dict[str, Any] = {}
    if filter is not None:
        kwargs["filter"] = filter
    scripts = vctx.client.task_scripts.list(**kwargs)
    output_result(
        [_script_to_dict(s) for s in scripts],
        columns=TASK_SCRIPT_COLUMNS,
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def script_get(
    ctx: typer.Context,
    identifier: Annotated[str, typer.Argument(help="Script ID or name.")],
) -> None:
    """Get a task script by ID or name."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.task_scripts, identifier, "TaskScript")
    script = vctx.client.task_scripts.get(key)
    output_result(
        _script_to_dict(script),
        columns=TASK_SCRIPT_COLUMNS,
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("create")
@handle_errors()
def script_create(
    ctx: typer.Context,
    name: Annotated[str, typer.Option("--name", help="Script name.")],
    script: Annotated[
        str,
        typer.Option("--script", help="GCS script code or @file path."),
    ],
    description: Annotated[
        str | None,
        typer.Option("--description", help="Script description."),
    ] = None,
    settings_json: Annotated[
        str | None,
        typer.Option("--settings-json", help="Task settings as JSON string."),
    ] = None,
) -> None:
    """Create a task script."""
    vctx = get_context(ctx)
    script_code = _read_script_input(script)
    kwargs: dict[str, Any] = {
        "name": name,
        "script": script_code,
    }
    if description is not None:
        kwargs["description"] = description
    if settings_json is not None:
        kwargs["task_settings"] = json.loads(settings_json)
    result = vctx.client.task_scripts.create(**kwargs)
    output_success(f"Task script '{result.name}' created (key={int(result.key)}).")


@app.command("update")
@handle_errors()
def script_update(
    ctx: typer.Context,
    identifier: Annotated[str, typer.Argument(help="Script ID or name.")],
    name: Annotated[
        str | None,
        typer.Option("--name", help="New script name."),
    ] = None,
    description: Annotated[
        str | None,
        typer.Option("--description", help="New description."),
    ] = None,
    script: Annotated[
        str | None,
        typer.Option("--script", help="New GCS script code or @file path."),
    ] = None,
    settings_json: Annotated[
        str | None,
        typer.Option("--settings-json", help="Updated task settings as JSON string."),
    ] = None,
) -> None:
    """Update a task script."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.task_scripts, identifier, "TaskScript")
    kwargs: dict[str, Any] = {}
    if name is not None:
        kwargs["name"] = name
    if description is not None:
        kwargs["description"] = description
    if script is not None:
        kwargs["script"] = _read_script_input(script)
    if settings_json is not None:
        kwargs["task_settings"] = json.loads(settings_json)
    vctx.client.task_scripts.update(key, **kwargs)
    output_success(f"Task script '{identifier}' updated.")


@app.command("delete")
@handle_errors()
def script_delete(
    ctx: typer.Context,
    identifier: Annotated[str, typer.Argument(help="Script ID or name.")],
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation prompt."),
    ] = False,
) -> None:
    """Delete a task script."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.task_scripts, identifier, "TaskScript")
    if not confirm_action(f"Delete task script '{identifier}'?", yes=yes):
        raise typer.Exit(0)
    vctx.client.task_scripts.delete(key)
    output_success(f"Task script '{identifier}' deleted.")


@app.command("run")
@handle_errors()
def script_run(
    ctx: typer.Context,
    identifier: Annotated[str, typer.Argument(help="Script ID or name.")],
    params_json: Annotated[
        str | None,
        typer.Option("--params-json", help="Execution parameters as JSON string."),
    ] = None,
) -> None:
    """Run a task script."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.task_scripts, identifier, "TaskScript")
    params: dict[str, Any] = {}
    if params_json is not None:
        params = json.loads(params_json)
    vctx.client.task_scripts.run(key, **params)
    output_success(f"Task script '{identifier}' started.")
