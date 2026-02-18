"""VM export stats commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import ColumnDef
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result
from verge_cli.utils import resolve_resource_id

app = typer.Typer(
    name="stats",
    help="View VM export statistics.",
    no_args_is_help=True,
)

VM_EXPORT_STAT_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef("file_name", header="Export Name"),
    ColumnDef("virtual_machines", header="VMs"),
    ColumnDef("export_success", header="Success"),
    ColumnDef("errors"),
    ColumnDef("size_bytes", header="Size (bytes)", wide_only=True),
    ColumnDef("duration", wide_only=True),
    ColumnDef("timestamp", wide_only=True),
]


def _stat_to_dict(stat: Any) -> dict[str, Any]:
    """Convert a VolumeVmExportStat SDK object to a dict for output."""
    return {
        "$key": int(stat.key),
        "file_name": stat.get("file_name", ""),
        "virtual_machines": stat.get("virtual_machines", ""),
        "export_success": stat.get("export_success", ""),
        "errors": stat.get("errors", ""),
        "size_bytes": stat.get("size_bytes", ""),
        "duration": stat.get("duration", ""),
        "timestamp": stat.get("timestamp", ""),
        "volume_vm_exports": stat.get("volume_vm_exports", ""),
        "quiesced": stat.get("quiesced"),
    }


@app.command("list")
@handle_errors()
def list_cmd(
    ctx: typer.Context,
    export: Annotated[
        str | None,
        typer.Option("--export", help="Filter by VM export name or key."),
    ] = None,
) -> None:
    """List VM export statistics."""
    vctx = get_context(ctx)
    kwargs: dict[str, Any] = {}
    if export is not None:
        export_key = resolve_resource_id(
            vctx.client.volume_vm_exports,
            export,
            "VM export",
        )
        kwargs["volume_vm_exports"] = export_key
    stats = vctx.client.volume_vm_export_stats.list(**kwargs)
    data = [_stat_to_dict(s) for s in stats]
    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=VM_EXPORT_STAT_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def get_cmd(
    ctx: typer.Context,
    stat: Annotated[str, typer.Argument(help="Export stat key.")],
) -> None:
    """Get a VM export stat entry by key."""
    vctx = get_context(ctx)
    key = int(stat)
    item = vctx.client.volume_vm_export_stats.get(key=key)
    output_result(
        _stat_to_dict(item),
        output_format=vctx.output_format,
        query=vctx.query,
        columns=VM_EXPORT_STAT_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )
