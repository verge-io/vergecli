"""NAS management commands (parent group)."""

from __future__ import annotations

import typer

from verge_cli.commands import nas_service, nas_volume, nas_volume_snapshot

app = typer.Typer(
    name="nas",
    help="Manage NAS services, volumes, and shares.",
    no_args_is_help=True,
)

app.add_typer(nas_service.app, name="service")

# Volume commands with snapshot sub-typer
nas_volume.app.add_typer(nas_volume_snapshot.app, name="snapshot")
app.add_typer(nas_volume.app, name="volume")
