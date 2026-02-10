"""Update available package commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import ColumnDef, format_bool_yn
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result
from verge_cli.utils import resolve_resource_id

app = typer.Typer(
    name="available",
    help="View available update packages from sources.",
    no_args_is_help=True,
)

AVAILABLE_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("version"),
    ColumnDef(
        "downloaded",
        format_fn=format_bool_yn,
        style_map={"Y": "green", "-": "dim"},
    ),
    ColumnDef("optional", format_fn=format_bool_yn),
    ColumnDef("description", wide_only=True),
    ColumnDef("branch", wide_only=True),
    ColumnDef("source", wide_only=True),
]


def _available_to_dict(pkg: Any) -> dict[str, Any]:
    """Convert an UpdateSourcePackage SDK object to a dict for output."""
    return {
        "$key": int(pkg.key),
        "name": pkg.name,
        "version": pkg.get("version", ""),
        "downloaded": pkg.get("downloaded"),
        "optional": pkg.get("optional"),
        "description": pkg.get("description", ""),
        "branch": pkg.get("branch", ""),
        "source": pkg.get("source", ""),
    }


@app.command("list")
@handle_errors()
def list_cmd(
    ctx: typer.Context,
    source: Annotated[
        int | None,
        typer.Option("--source", help="Filter by source key."),
    ] = None,
    branch: Annotated[
        int | None,
        typer.Option("--branch", help="Filter by branch key."),
    ] = None,
    downloaded: Annotated[
        bool,
        typer.Option("--downloaded", help="Show only downloaded packages."),
    ] = False,
    pending: Annotated[
        bool,
        typer.Option("--pending", help="Show only pending (not downloaded) packages."),
    ] = False,
) -> None:
    """List available update packages from sources."""
    vctx = get_context(ctx)

    if downloaded and pending:
        raise typer.BadParameter("--downloaded and --pending are mutually exclusive.")

    if downloaded:
        packages = vctx.client.update_source_packages.list_downloaded()
    elif pending:
        packages = vctx.client.update_source_packages.list_pending()
    else:
        kwargs: dict[str, Any] = {}
        if source is not None:
            kwargs["source"] = source
        if branch is not None:
            kwargs["branch"] = branch
        packages = vctx.client.update_source_packages.list(**kwargs)

    data = [_available_to_dict(p) for p in packages]
    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=AVAILABLE_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def get_cmd(
    ctx: typer.Context,
    identifier: Annotated[str, typer.Argument(help="Package key or name.")],
) -> None:
    """Get an available update package by key or name."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.update_source_packages, identifier, "Available package")
    pkg = vctx.client.update_source_packages.get(key=key)
    output_result(
        _available_to_dict(pkg),
        output_format=vctx.output_format,
        query=vctx.query,
        columns=AVAILABLE_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )
