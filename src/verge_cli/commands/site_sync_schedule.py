"""Site sync schedule management commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import SITE_SYNC_SCHEDULE_COLUMNS
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result, output_success
from verge_cli.utils import confirm_action

app = typer.Typer(
    name="schedule",
    help="Manage site sync schedules.",
    no_args_is_help=True,
)


def _schedule_to_dict(schedule: Any) -> dict[str, Any]:
    """Convert a SiteSyncSchedule SDK object to a dict for output."""
    return {
        "$key": schedule.key,
        "sync_key": schedule.get("sync_key"),
        "sync_name": schedule.get("sync_name", ""),
        "profile_period_key": schedule.get("profile_period_key"),
        "profile_period_name": schedule.get("profile_period_name", ""),
        "retention": schedule.get("retention"),
        "priority": schedule.get("priority"),
        "do_not_expire": schedule.get("do_not_expire", False),
        "destination_prefix": schedule.get("destination_prefix", "remote"),
    }


@app.command("list")
@handle_errors()
def list_cmd(
    ctx: typer.Context,
    sync: Annotated[
        str | None,
        typer.Option("--sync", "-s", help="Filter by sync key"),
    ] = None,
) -> None:
    """List site sync schedules."""
    vctx = get_context(ctx)
    kwargs: dict[str, Any] = {}

    if sync is not None:
        if sync.isdigit():
            kwargs["sync_key"] = int(sync)
        else:
            kwargs["sync_name"] = sync

    schedules = vctx.client.site_sync_schedules.list(**kwargs)
    data = [_schedule_to_dict(s) for s in schedules]
    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=SITE_SYNC_SCHEDULE_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def get_cmd(
    ctx: typer.Context,
    schedule_id: Annotated[int, typer.Argument(help="Schedule key")],
) -> None:
    """Get details of a site sync schedule."""
    vctx = get_context(ctx)
    schedule = vctx.client.site_sync_schedules.get(schedule_id)
    output_result(
        _schedule_to_dict(schedule),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("create")
@handle_errors()
def create_cmd(
    ctx: typer.Context,
    sync_key: Annotated[int, typer.Option("--sync-key", help="Sync key to schedule")],
    profile_period_key: Annotated[
        int, typer.Option("--profile-period-key", help="Snapshot profile period key")
    ],
    retention: Annotated[int, typer.Option("--retention", help="Retention in seconds")],
    priority: Annotated[int | None, typer.Option("--priority", help="Schedule priority")] = None,
    do_not_expire: Annotated[
        bool, typer.Option("--do-not-expire", help="Never expire synced snapshots")
    ] = False,
    destination_prefix: Annotated[
        str, typer.Option("--destination-prefix", help="Destination prefix")
    ] = "remote",
) -> None:
    """Create a site sync schedule."""
    vctx = get_context(ctx)
    kwargs: dict[str, Any] = {
        "sync_key": sync_key,
        "profile_period_key": profile_period_key,
        "retention": retention,
        "do_not_expire": do_not_expire,
        "destination_prefix": destination_prefix,
    }
    if priority is not None:
        kwargs["priority"] = priority

    result = vctx.client.site_sync_schedules.create(**kwargs)
    output_success(f"Created site sync schedule (key: {result.key})", quiet=vctx.quiet)


@app.command("delete")
@handle_errors()
def delete_cmd(
    ctx: typer.Context,
    schedule_id: Annotated[int, typer.Argument(help="Schedule key")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation")] = False,
) -> None:
    """Delete a site sync schedule."""
    vctx = get_context(ctx)

    if not confirm_action(f"Delete site sync schedule {schedule_id}?", yes=yes):
        typer.echo("Cancelled.")
        raise typer.Exit(0)

    vctx.client.site_sync_schedules.delete(schedule_id)
    output_success(f"Deleted site sync schedule {schedule_id}", quiet=vctx.quiet)
