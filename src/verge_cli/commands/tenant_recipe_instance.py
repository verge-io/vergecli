"""Tenant recipe instance management commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import ColumnDef
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result, output_success
from verge_cli.utils import confirm_action, resolve_nas_resource, resolve_resource_id

app = typer.Typer(
    name="instance",
    help="Manage tenant recipe instances (deployed tenants).",
    no_args_is_help=True,
)

TENANT_RECIPE_INSTANCE_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("recipe_name", header="Recipe"),
]


def _instance_to_dict(inst: Any) -> dict[str, Any]:
    """Convert a TenantRecipeInstance SDK object to a dict for output."""
    return {
        "$key": int(inst.key),
        "name": inst.name,
        "recipe_name": inst.get("recipe_name", ""),
    }


@app.command("list")
@handle_errors()
def list_cmd(
    ctx: typer.Context,
    recipe: Annotated[
        str | None,
        typer.Option("--recipe", help="Filter by tenant recipe name or key."),
    ] = None,
) -> None:
    """List tenant recipe instances."""
    vctx = get_context(ctx)
    kwargs: dict[str, Any] = {}
    if recipe is not None:
        recipe_key = resolve_nas_resource(
            vctx.client.tenant_recipes,
            recipe,
            resource_type="tenant recipe",
        )
        kwargs["recipe"] = recipe_key
    instances = vctx.client.tenant_recipe_instances.list(**kwargs)
    data = [_instance_to_dict(i) for i in instances]
    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=TENANT_RECIPE_INSTANCE_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def get_cmd(
    ctx: typer.Context,
    instance: Annotated[str, typer.Argument(help="Instance name or key.")],
) -> None:
    """Get a tenant recipe instance by name or key."""
    vctx = get_context(ctx)
    key = resolve_resource_id(
        vctx.client.tenant_recipe_instances, instance, "tenant recipe instance"
    )
    item = vctx.client.tenant_recipe_instances.get(key=key)
    output_result(
        _instance_to_dict(item),
        output_format=vctx.output_format,
        query=vctx.query,
        columns=TENANT_RECIPE_INSTANCE_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("delete")
@handle_errors()
def delete_cmd(
    ctx: typer.Context,
    instance: Annotated[str, typer.Argument(help="Instance name or key.")],
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation."),
    ] = False,
) -> None:
    """Delete a tenant recipe instance (removes tracking only)."""
    vctx = get_context(ctx)
    key = resolve_resource_id(
        vctx.client.tenant_recipe_instances, instance, "tenant recipe instance"
    )
    if not confirm_action(
        f"Delete instance '{instance}'? This removes tracking only.",
        yes=yes,
    ):
        raise typer.Abort()
    vctx.client.tenant_recipe_instances.delete(key)
    output_success(f"Instance '{instance}' deleted.")
