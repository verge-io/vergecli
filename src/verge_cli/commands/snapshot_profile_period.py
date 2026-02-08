"""Snapshot profile period sub-resource commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import SNAPSHOT_PROFILE_PERIOD_COLUMNS
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result, output_success
from verge_cli.utils import confirm_action, resolve_resource_id

app = typer.Typer(
    name="period",
    help="Manage snapshot profile periods.",
    no_args_is_help=True,
)


def _get_profile(ctx: typer.Context, profile_identifier: str) -> tuple[Any, int]:
    """Resolve profile and return (vctx, profile_key)."""
    vctx = get_context(ctx)
    profile_key = resolve_resource_id(
        vctx.client.snapshot_profiles, profile_identifier, "Snapshot profile"
    )
    return vctx, profile_key


def _resolve_period(period_mgr: Any, identifier: str) -> int:
    """Resolve a period name or key to an integer key."""
    if identifier.isdigit():
        return int(identifier)
    periods = period_mgr.list()
    matches = [p for p in periods if p.name == identifier]
    if len(matches) == 1:
        return int(matches[0].key)
    if len(matches) > 1:
        typer.echo(
            f"Error: Multiple periods match '{identifier}'. Use a numeric key.",
            err=True,
        )
        raise typer.Exit(7)
    typer.echo(f"Error: Period '{identifier}' not found.", err=True)
    raise typer.Exit(6)


def _period_to_dict(period: Any) -> dict[str, Any]:
    """Convert a SnapshotProfilePeriod object to a dict for output."""
    return {
        "$key": period.key,
        "name": period.name,
        "frequency": period.get("frequency"),
        "retention": period.get("retention"),
        "min_snapshots": period.get("min_snapshots"),
        "max_tier": period.get("max_tier"),
        "minute": period.get("minute"),
        "hour": period.get("hour"),
        "day_of_week": period.get("day_of_week", "any"),
        "quiesce": period.get("quiesce", False),
        "immutable": period.get("immutable", False),
        "skip_missed": period.get("skip_missed", False),
    }


@app.command("list")
@handle_errors()
def period_list(
    ctx: typer.Context,
    profile: Annotated[str, typer.Argument(help="Profile name or key")],
) -> None:
    """List periods for a snapshot profile."""
    vctx, profile_key = _get_profile(ctx, profile)
    periods = vctx.client.snapshot_profiles.periods(profile_key).list()
    data = [_period_to_dict(p) for p in periods]
    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=SNAPSHOT_PROFILE_PERIOD_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def period_get(
    ctx: typer.Context,
    profile: Annotated[str, typer.Argument(help="Profile name or key")],
    period: Annotated[str, typer.Argument(help="Period name or key")],
) -> None:
    """Get details of a snapshot profile period."""
    vctx, profile_key = _get_profile(ctx, profile)
    period_mgr = vctx.client.snapshot_profiles.periods(profile_key)
    period_key = _resolve_period(period_mgr, period)
    period_obj = period_mgr.get(period_key)
    output_result(
        _period_to_dict(period_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("create")
@handle_errors()
def period_create(
    ctx: typer.Context,
    profile: Annotated[str, typer.Argument(help="Profile name or key")],
    name: Annotated[str, typer.Option("--name", "-n", help="Period name")],
    frequency: Annotated[
        str,
        typer.Option(
            "--frequency",
            "-f",
            help="Frequency: hourly, daily, weekly, monthly, yearly",
        ),
    ],
    retention: Annotated[
        int,
        typer.Option("--retention", help="Retention in seconds (0 = never expires)"),
    ],
    minute: Annotated[int, typer.Option("--minute", help="Minute of the hour (0-59)")] = 0,
    hour: Annotated[int, typer.Option("--hour", help="Hour of the day (0-23)")] = 0,
    day_of_week: Annotated[
        str,
        typer.Option("--day-of-week", help="Day of week (e.g., mon, tue, any)"),
    ] = "any",
    day_of_month: Annotated[
        int, typer.Option("--day-of-month", help="Day of the month (0-31, 0=any)")
    ] = 0,
    quiesce: Annotated[
        bool,
        typer.Option("--quiesce", help="Quiesce filesystem before snapshot"),
    ] = False,
    immutable: Annotated[
        bool,
        typer.Option("--immutable", help="Make snapshots immutable"),
    ] = False,
    min_snapshots: Annotated[
        int,
        typer.Option("--min-snapshots", help="Minimum snapshots to keep"),
    ] = 1,
    max_tier: Annotated[
        int,
        typer.Option("--max-tier", help="Maximum storage tier"),
    ] = 1,
    skip_missed: Annotated[
        bool,
        typer.Option("--skip-missed", help="Skip missed snapshot windows"),
    ] = False,
) -> None:
    """Create a period in a snapshot profile."""
    vctx, profile_key = _get_profile(ctx, profile)
    period_mgr = vctx.client.snapshot_profiles.periods(profile_key)

    result = period_mgr.create(
        name=name,
        frequency=frequency,
        retention=retention,
        minute=minute,
        hour=hour,
        day_of_week=day_of_week,
        day_of_month=day_of_month,
        quiesce=quiesce,
        immutable=immutable,
        min_snapshots=min_snapshots,
        max_tier=max_tier,
        skip_missed=skip_missed,
    )

    period_name = result.name if result else name
    period_key = result.key if result else "?"
    output_success(
        f"Created period '{period_name}' (key: {period_key})",
        quiet=vctx.quiet,
    )


@app.command("update")
@handle_errors()
def period_update(
    ctx: typer.Context,
    profile: Annotated[str, typer.Argument(help="Profile name or key")],
    period: Annotated[str, typer.Argument(help="Period name or key")],
    name: Annotated[str | None, typer.Option("--name", "-n", help="New period name")] = None,
    frequency: Annotated[
        str | None,
        typer.Option("--frequency", "-f", help="New frequency"),
    ] = None,
    retention: Annotated[
        int | None,
        typer.Option("--retention", help="Retention in seconds"),
    ] = None,
    minute: Annotated[
        int | None, typer.Option("--minute", help="Minute of the hour (0-59)")
    ] = None,
    hour: Annotated[int | None, typer.Option("--hour", help="Hour of the day (0-23)")] = None,
    day_of_week: Annotated[
        str | None,
        typer.Option("--day-of-week", help="Day of week"),
    ] = None,
    day_of_month: Annotated[
        int | None,
        typer.Option("--day-of-month", help="Day of the month (0-31)"),
    ] = None,
    quiesce: Annotated[
        bool | None,
        typer.Option("--quiesce/--no-quiesce", help="Quiesce filesystem"),
    ] = None,
    immutable: Annotated[
        bool | None,
        typer.Option("--immutable/--no-immutable", help="Make snapshots immutable"),
    ] = None,
    min_snapshots: Annotated[
        int | None,
        typer.Option("--min-snapshots", help="Minimum snapshots to keep"),
    ] = None,
    max_tier: Annotated[
        int | None,
        typer.Option("--max-tier", help="Maximum storage tier"),
    ] = None,
    skip_missed: Annotated[
        bool | None,
        typer.Option("--skip-missed/--no-skip-missed", help="Skip missed windows"),
    ] = None,
) -> None:
    """Update a snapshot profile period."""
    vctx, profile_key = _get_profile(ctx, profile)
    period_mgr = vctx.client.snapshot_profiles.periods(profile_key)
    period_key = _resolve_period(period_mgr, period)

    kwargs: dict[str, Any] = {}
    if name is not None:
        kwargs["name"] = name
    if frequency is not None:
        kwargs["frequency"] = frequency
    if retention is not None:
        kwargs["retention"] = retention
    if minute is not None:
        kwargs["minute"] = minute
    if hour is not None:
        kwargs["hour"] = hour
    if day_of_week is not None:
        kwargs["day_of_week"] = day_of_week
    if day_of_month is not None:
        kwargs["day_of_month"] = day_of_month
    if quiesce is not None:
        kwargs["quiesce"] = quiesce
    if immutable is not None:
        kwargs["immutable"] = immutable
    if min_snapshots is not None:
        kwargs["min_snapshots"] = min_snapshots
    if max_tier is not None:
        kwargs["max_tier"] = max_tier
    if skip_missed is not None:
        kwargs["skip_missed"] = skip_missed

    if not kwargs:
        typer.echo("No updates specified.", err=True)
        raise typer.Exit(2)

    period_mgr.update(period_key, **kwargs)
    output_success(f"Updated period '{period}'", quiet=vctx.quiet)


@app.command("delete")
@handle_errors()
def period_delete(
    ctx: typer.Context,
    profile: Annotated[str, typer.Argument(help="Profile name or key")],
    period: Annotated[str, typer.Argument(help="Period name or key")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation")] = False,
) -> None:
    """Delete a snapshot profile period."""
    vctx, profile_key = _get_profile(ctx, profile)
    period_mgr = vctx.client.snapshot_profiles.periods(profile_key)
    period_key = _resolve_period(period_mgr, period)

    if not confirm_action(f"Delete period '{period}'?", yes=yes):
        typer.echo("Cancelled.")
        raise typer.Exit(0)

    period_mgr.delete(period_key)
    output_success(f"Deleted period '{period}'", quiet=vctx.quiet)
