"""NAS management commands (parent group)."""

from __future__ import annotations

import typer

from verge_cli.commands import nas_service

app = typer.Typer(
    name="nas",
    help="Manage NAS services, volumes, and shares.",
    no_args_is_help=True,
)

app.add_typer(nas_service.app, name="service")
