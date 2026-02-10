"""Update branch commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import ColumnDef
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result
from verge_cli.utils import resolve_resource_id

app = typer.Typer(
    name="branch",
    help="View update branches.",
    no_args_is_help=True,
)

BRANCH_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("description"),
    ColumnDef("created", wide_only=True),
]


def _branch_to_dict(branch: Any) -> dict[str, Any]:
    """Convert an UpdateBranch SDK object to a dict for output."""
    return {
        "$key": int(branch.key),
        "name": branch.name,
        "description": branch.get("description", ""),
        "created": branch.get("created", ""),
    }


@app.command("list")
@handle_errors()
def list_cmd(
    ctx: typer.Context,
    filter_expr: Annotated[
        str | None,
        typer.Option("--filter", help="OData filter expression."),
    ] = None,
) -> None:
    """List update branches."""
    vctx = get_context(ctx)
    kwargs: dict[str, Any] = {}
    if filter_expr is not None:
        kwargs["filter"] = filter_expr
    branches = vctx.client.update_branches.list(**kwargs)
    data = [_branch_to_dict(b) for b in branches]
    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=BRANCH_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def get_cmd(
    ctx: typer.Context,
    identifier: Annotated[str, typer.Argument(help="Branch key or name.")],
) -> None:
    """Get an update branch by key or name."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.update_branches, identifier, "Update branch")
    branch = vctx.client.update_branches.get(key=key)
    output_result(
        _branch_to_dict(branch),
        output_format=vctx.output_format,
        query=vctx.query,
        columns=BRANCH_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )
