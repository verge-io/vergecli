"""Update package commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import ColumnDef, format_bool_yn
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result

app = typer.Typer(
    name="package",
    help="View installed update packages.",
    no_args_is_help=True,
)

PACKAGE_COLUMNS: list[ColumnDef] = [
    ColumnDef("name"),
    ColumnDef("version"),
    ColumnDef("type"),
    ColumnDef("optional", format_fn=format_bool_yn),
    ColumnDef("description", wide_only=True),
    ColumnDef("branch", wide_only=True),
    ColumnDef("modified", wide_only=True),
]


def _package_to_dict(pkg: Any) -> dict[str, Any]:
    """Convert an UpdatePackage SDK object to a dict for output."""
    return {
        "name": pkg.name,
        "version": pkg.get("version", ""),
        "type": pkg.get("type", ""),
        "optional": pkg.get("optional"),
        "description": pkg.get("description", ""),
        "branch": pkg.get("branch", ""),
        "modified": pkg.get("modified", ""),
    }


@app.command("list")
@handle_errors()
def list_cmd(
    ctx: typer.Context,
    filter_expr: Annotated[
        str | None,
        typer.Option("--filter", help="OData filter expression."),
    ] = None,
    branch: Annotated[
        int | None,
        typer.Option("--branch", help="Filter by branch key."),
    ] = None,
) -> None:
    """List installed update packages."""
    vctx = get_context(ctx)
    kwargs: dict[str, Any] = {}
    if filter_expr is not None:
        kwargs["filter"] = filter_expr
    if branch is not None:
        kwargs["branch"] = branch
    packages = vctx.client.update_packages.list(**kwargs)
    data = [_package_to_dict(p) for p in packages]
    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=PACKAGE_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def get_cmd(
    ctx: typer.Context,
    name: Annotated[str, typer.Argument(help="Package name.")],
) -> None:
    """Get an installed update package by name."""
    vctx = get_context(ctx)
    # Package keys are strings (name), not integers — pass directly
    pkg = vctx.client.update_packages.get(key=name)
    output_result(
        _package_to_dict(pkg),
        output_format=vctx.output_format,
        query=vctx.query,
        columns=PACKAGE_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )
