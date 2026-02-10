"""Alarm history commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import ColumnDef, format_epoch
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result

app = typer.Typer(
    name="history",
    help="Manage alarm history.",
    no_args_is_help=True,
)

ALARM_HISTORY_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef(
        "level",
        style_map={
            "critical": "red bold",
            "error": "red",
            "warning": "yellow",
            "message": "dim",
        },
    ),
    ColumnDef("alarm_type", header="Type"),
    ColumnDef("status"),
    ColumnDef("owner"),
    ColumnDef("raised_at", header="Raised", format_fn=format_epoch),
    ColumnDef("lowered_at", header="Lowered", format_fn=format_epoch),
    ColumnDef("archived_by", header="Archived By", wide_only=True),
    ColumnDef("alarm_id", header="Alarm ID", wide_only=True),
]


def _history_to_dict(entry: Any) -> dict[str, Any]:
    """Convert SDK AlarmHistory object to output dict."""
    return {
        "$key": int(entry.key),
        "level": entry.level,
        "alarm_type": entry.alarm_type,
        "alarm_id": entry.alarm_id,
        "status": entry.status,
        "owner": entry.owner,
        "archived_by": entry.archived_by,
        "raised_at": entry.raised_at.timestamp() if entry.raised_at else None,
        "lowered_at": entry.lowered_at.timestamp() if entry.lowered_at else None,
    }


@app.command("list")
@handle_errors()
def list_cmd(
    ctx: typer.Context,
    level: Annotated[
        str | None,
        typer.Option(
            "--level",
            "-l",
            help="Filter by alarm level.",
        ),
    ] = None,
    filter: Annotated[
        str | None,
        typer.Option(
            "--filter",
            help="OData filter expression.",
        ),
    ] = None,
    limit: Annotated[
        int | None,
        typer.Option(
            "--limit",
            help="Maximum number of results.",
        ),
    ] = None,
) -> None:
    """List alarm history (resolved/lowered alarms)."""
    vctx = get_context(ctx)
    entries = vctx.client.alarms.list_history(
        filter=filter,
        level=level,
        limit=limit,
    )
    output_result(
        [_history_to_dict(e) for e in entries],
        output_format=vctx.output_format,
        query=vctx.query,
        columns=ALARM_HISTORY_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command()
@handle_errors()
def get(
    ctx: typer.Context,
    key: Annotated[
        int,
        typer.Argument(help="Alarm history key (numeric ID)."),
    ],
) -> None:
    """Get alarm history entry by key."""
    vctx = get_context(ctx)
    entry = vctx.client.alarms.get_history(key)
    output_result(
        _history_to_dict(entry),
        output_format=vctx.output_format,
        query=vctx.query,
        columns=ALARM_HISTORY_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )
