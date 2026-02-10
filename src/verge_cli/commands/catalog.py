"""Catalog management commands (parent app)."""

from __future__ import annotations

import typer

from verge_cli.commands import catalog_repo

app = typer.Typer(
    name="catalog",
    help="Manage catalog repositories and catalogs.",
    no_args_is_help=True,
)

# Register sub-commands
app.add_typer(catalog_repo.app, name="repo")
