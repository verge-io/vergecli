"""Recipe log management commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import ColumnDef, format_epoch
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result
from verge_cli.utils import resolve_nas_resource

app = typer.Typer(
    name="log",
    help="View recipe operation logs.",
    no_args_is_help=True,
)

RECIPE_LOG_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef("level"),
    ColumnDef("text", header="Message"),
    ColumnDef("timestamp", format_fn=format_epoch),
    ColumnDef("user", wide_only=True),
]


def _log_to_dict(log: Any) -> dict[str, Any]:
    """Convert a VmRecipeLog SDK object to a dict for output."""
    # Timestamp is in microseconds in the SDK — convert to seconds for format_epoch
    ts = log.get("timestamp")
    if isinstance(ts, (int, float)) and ts > 1e12:
        ts = ts / 1e6
    return {
        "$key": int(log.key),
        "level": log.get("level", ""),
        "text": log.get("text", ""),
        "timestamp": ts,
        "user": log.get("user", ""),
    }


@app.command("list")
@handle_errors()
def list_cmd(
    ctx: typer.Context,
    recipe: Annotated[
        str | None,
        typer.Option("--recipe", help="Filter by recipe name or key."),
    ] = None,
) -> None:
    """List recipe operation logs."""
    vctx = get_context(ctx)
    kwargs: dict[str, Any] = {}
    if recipe is not None:
        recipe_key = resolve_nas_resource(
            vctx.client.vm_recipes,
            recipe,
            resource_type="recipe",
        )
        kwargs["vm_recipe"] = recipe_key
    logs = vctx.client.vm_recipe_logs.list(**kwargs)
    data = [_log_to_dict(entry) for entry in logs]
    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=RECIPE_LOG_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def get_cmd(
    ctx: typer.Context,
    log: Annotated[str, typer.Argument(help="Log entry key.")],
) -> None:
    """Get a recipe log entry by key."""
    vctx = get_context(ctx)
    key = int(log)
    item = vctx.client.vm_recipe_logs.get(key=key)
    output_result(
        _log_to_dict(item),
        output_format=vctx.output_format,
        query=vctx.query,
        columns=RECIPE_LOG_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )
