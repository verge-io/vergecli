"""VM import log commands."""

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
    help="View VM import logs.",
    no_args_is_help=True,
)

VM_IMPORT_LOG_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef("level"),
    ColumnDef("text", header="Message"),
    ColumnDef("timestamp", format_fn=format_epoch),
    ColumnDef("user", wide_only=True),
]


def _log_to_dict(log: Any) -> dict[str, Any]:
    """Convert a VmImportLog SDK object to a dict for output."""
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
    import_id: Annotated[
        str | None,
        typer.Option("--import", help="Filter by VM import name or key."),
    ] = None,
) -> None:
    """List VM import logs."""
    vctx = get_context(ctx)
    kwargs: dict[str, Any] = {}
    if import_id is not None:
        import_key = resolve_nas_resource(
            vctx.client.vm_imports,
            import_id,
            resource_type="VM import",
        )
        kwargs["vm_import"] = import_key
    logs = vctx.client.vm_import_logs.list(**kwargs)
    data = [_log_to_dict(entry) for entry in logs]
    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=VM_IMPORT_LOG_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def get_cmd(
    ctx: typer.Context,
    log: Annotated[str, typer.Argument(help="Log entry key.")],
) -> None:
    """Get a VM import log entry by key."""
    vctx = get_context(ctx)
    key = int(log)
    item = vctx.client.vm_import_logs.get(key=key)
    output_result(
        _log_to_dict(item),
        output_format=vctx.output_format,
        query=vctx.query,
        columns=VM_IMPORT_LOG_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )
