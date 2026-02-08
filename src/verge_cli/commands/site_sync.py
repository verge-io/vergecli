"""Site sync management — registers outgoing and incoming sub-typers."""

from __future__ import annotations

import typer

from verge_cli.commands import site_sync_incoming, site_sync_outgoing

app = typer.Typer(
    name="sync",
    help="Manage site synchronization.",
    no_args_is_help=True,
)

app.add_typer(site_sync_outgoing.app, name="outgoing")
app.add_typer(site_sync_incoming.app, name="incoming")
