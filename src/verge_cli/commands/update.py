"""Update management commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import ColumnDef, format_bool_yn
from verge_cli.commands import update_source
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result, output_success

app = typer.Typer(
    name="update",
    help="Manage system updates.",
    no_args_is_help=True,
)

# Register sub-commands
app.add_typer(update_source.app, name="source")

SETTINGS_COLUMNS: list[ColumnDef] = [
    ColumnDef("source", header="Source"),
    ColumnDef("branch", header="Branch"),
    ColumnDef("auto_refresh", header="Auto Refresh", format_fn=format_bool_yn),
    ColumnDef("auto_update", header="Auto Update", format_fn=format_bool_yn),
    ColumnDef("auto_reboot", header="Auto Reboot", format_fn=format_bool_yn),
    ColumnDef("update_time", header="Update Time"),
    ColumnDef(
        "installed",
        header="Installed",
        format_fn=format_bool_yn,
        style_map={"Y": "green", "-": "dim"},
    ),
    ColumnDef(
        "reboot_required",
        header="Reboot Req",
        format_fn=format_bool_yn,
        style_map={"Y": "yellow", "-": "dim"},
    ),
    ColumnDef(
        "applying_updates",
        header="Applying",
        format_fn=format_bool_yn,
        wide_only=True,
    ),
    ColumnDef(
        "warm_reboot",
        header="Warm Reboot",
        format_fn=format_bool_yn,
        wide_only=True,
    ),
    ColumnDef(
        "multi_cluster_update",
        header="Multi-Cluster",
        format_fn=format_bool_yn,
        wide_only=True,
    ),
    ColumnDef(
        "snapshot_on_update",
        header="Snapshot",
        format_fn=format_bool_yn,
        wide_only=True,
    ),
    ColumnDef("max_vsan_usage", header="Max vSAN%", wide_only=True),
]


def _settings_to_dict(settings: Any) -> dict[str, Any]:
    """Convert UpdateSettings SDK object to dict for output."""
    return {
        "source": settings.get("source", ""),
        "branch": settings.get("branch", ""),
        "auto_refresh": settings.get("auto_refresh"),
        "auto_update": settings.get("auto_update"),
        "auto_reboot": settings.get("auto_reboot"),
        "update_time": settings.get("update_time", ""),
        "max_vsan_usage": settings.get("max_vsan_usage", ""),
        "warm_reboot": settings.get("warm_reboot"),
        "multi_cluster_update": settings.get("multi_cluster_update"),
        "snapshot_on_update": settings.get("snapshot_cloud_on_update"),
        "installed": settings.get("installed"),
        "reboot_required": settings.get("reboot_required"),
        "applying_updates": settings.get("applying_updates"),
    }


@app.command("settings")
@handle_errors()
def settings_cmd(ctx: typer.Context) -> None:
    """Display current update settings."""
    vctx = get_context(ctx)
    settings = vctx.client.update_settings.get()
    output_result(
        _settings_to_dict(settings),
        output_format=vctx.output_format,
        query=vctx.query,
        columns=SETTINGS_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("configure")
@handle_errors()
def configure_cmd(
    ctx: typer.Context,
    source: Annotated[
        int | None,
        typer.Option("--source", help="Active update source key."),
    ] = None,
    branch: Annotated[
        int | None,
        typer.Option("--branch", help="Selected branch key."),
    ] = None,
    auto_refresh: Annotated[
        bool | None,
        typer.Option("--auto-refresh/--no-auto-refresh", help="Auto-refresh updates."),
    ] = None,
    auto_update: Annotated[
        bool | None,
        typer.Option("--auto-update/--no-auto-update", help="Auto-install updates."),
    ] = None,
    auto_reboot: Annotated[
        bool | None,
        typer.Option("--auto-reboot/--no-auto-reboot", help="Auto-reboot after updates."),
    ] = None,
    update_time: Annotated[
        str | None,
        typer.Option("--update-time", help="Scheduled update time (HH:MM)."),
    ] = None,
    max_vsan_usage: Annotated[
        int | None,
        typer.Option("--max-vsan-usage", help="Max vSAN usage percentage."),
    ] = None,
    warm_reboot: Annotated[
        bool | None,
        typer.Option("--warm-reboot/--no-warm-reboot", help="Use kexec for faster reboots."),
    ] = None,
    multi_cluster_update: Annotated[
        bool | None,
        typer.Option(
            "--multi-cluster-update/--no-multi-cluster-update",
            help="Allow multi-cluster updates.",
        ),
    ] = None,
    snapshot_on_update: Annotated[
        bool | None,
        typer.Option(
            "--snapshot-on-update/--no-snapshot-on-update",
            help="Snapshot before updates.",
        ),
    ] = None,
    snapshot_expire: Annotated[
        int | None,
        typer.Option("--snapshot-expire", help="Snapshot expire seconds."),
    ] = None,
    anonymize_stats: Annotated[
        bool | None,
        typer.Option(
            "--anonymize-stats/--no-anonymize-stats",
            help="Anonymize statistics.",
        ),
    ] = None,
) -> None:
    """Configure update settings."""
    vctx = get_context(ctx)
    kwargs: dict[str, Any] = {}
    if source is not None:
        kwargs["source"] = source
    if branch is not None:
        kwargs["branch"] = branch
    if auto_refresh is not None:
        kwargs["auto_refresh"] = auto_refresh
    if auto_update is not None:
        kwargs["auto_update"] = auto_update
    if auto_reboot is not None:
        kwargs["auto_reboot"] = auto_reboot
    if update_time is not None:
        kwargs["update_time"] = update_time
    if max_vsan_usage is not None:
        kwargs["max_vsan_usage"] = max_vsan_usage
    if warm_reboot is not None:
        kwargs["warm_reboot"] = warm_reboot
    if multi_cluster_update is not None:
        kwargs["multi_cluster_update"] = multi_cluster_update
    if snapshot_on_update is not None:
        kwargs["snapshot_cloud_on_update"] = snapshot_on_update
    if snapshot_expire is not None:
        kwargs["snapshot_cloud_expire_seconds"] = snapshot_expire
    if anonymize_stats is not None:
        kwargs["anonymize_statistics"] = anonymize_stats
    result = vctx.client.update_settings.update(**kwargs)
    output_result(
        _settings_to_dict(result),
        output_format=vctx.output_format,
        query=vctx.query,
        columns=SETTINGS_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )
    output_success("Update settings configured.", quiet=vctx.quiet)


@app.command("check")
@handle_errors()
def check_cmd(ctx: typer.Context) -> None:
    """Check for available updates."""
    vctx = get_context(ctx)
    result = vctx.client.update_settings.check()
    if result:
        output_result(
            result,
            output_format=vctx.output_format,
            query=vctx.query,
            quiet=vctx.quiet,
            no_color=vctx.no_color,
        )
    output_success("Update check initiated.", quiet=vctx.quiet)


@app.command("download")
@handle_errors()
def download_cmd(ctx: typer.Context) -> None:
    """Download available updates."""
    vctx = get_context(ctx)
    result = vctx.client.update_settings.download()
    if result:
        output_result(
            result,
            output_format=vctx.output_format,
            query=vctx.query,
            quiet=vctx.quiet,
            no_color=vctx.no_color,
        )
    output_success("Update download initiated.", quiet=vctx.quiet)


@app.command("install")
@handle_errors()
def install_cmd(
    ctx: typer.Context,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation prompt."),
    ] = False,
) -> None:
    """Install downloaded updates."""
    from verge_cli.utils import confirm_action

    vctx = get_context(ctx)
    if not confirm_action("Install updates? This may require a reboot.", yes=yes):
        raise typer.Abort()
    result = vctx.client.update_settings.install()
    if result:
        output_result(
            result,
            output_format=vctx.output_format,
            query=vctx.query,
            quiet=vctx.quiet,
            no_color=vctx.no_color,
        )
    output_success("Update install initiated.", quiet=vctx.quiet)


@app.command("apply")
@handle_errors()
def apply_cmd(
    ctx: typer.Context,
    force: Annotated[
        bool,
        typer.Option("--force", help="Force update even if already up to date."),
    ] = False,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation prompt."),
    ] = False,
) -> None:
    """Check, download, and install updates in one step."""
    from verge_cli.utils import confirm_action

    vctx = get_context(ctx)
    if not confirm_action(
        "Apply updates? This will check, download, install, and may reboot nodes.",
        yes=yes,
    ):
        raise typer.Abort()
    result = vctx.client.update_settings.update_all(force=force)
    if result:
        output_result(
            result,
            output_format=vctx.output_format,
            query=vctx.query,
            quiet=vctx.quiet,
            no_color=vctx.no_color,
        )
    output_success("Update apply initiated.", quiet=vctx.quiet)
