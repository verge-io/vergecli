"""Recipe section management commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import ColumnDef
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result, output_success
from verge_cli.utils import confirm_action, resolve_nas_resource, resolve_resource_id

app = typer.Typer(
    name="section",
    help="Manage recipe sections.",
    no_args_is_help=True,
)

RECIPE_SECTION_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("description"),
    ColumnDef("orderid", header="Order"),
]


def _section_to_dict(section: Any) -> dict[str, Any]:
    """Convert a RecipeSection SDK object to a dict for output."""
    return {
        "$key": int(section.key),
        "name": section.name,
        "description": section.get("description", ""),
        "orderid": section.get("orderid"),
    }


def _resolve_recipe(vctx: Any, identifier: str) -> str:
    """Resolve a recipe identifier to a hex key."""
    return resolve_nas_resource(
        vctx.client.vm_recipes,
        identifier,
        resource_type="recipe",
    )


@app.command("list")
@handle_errors()
def list_cmd(
    ctx: typer.Context,
    recipe: Annotated[str, typer.Argument(help="Recipe name or key.")],
) -> None:
    """List sections for a recipe."""
    vctx = get_context(ctx)
    recipe_key = _resolve_recipe(vctx, recipe)
    recipe_ref = f"vm_recipes/{recipe_key}"
    sections = vctx.client.recipe_sections.list(recipe_ref=recipe_ref)
    data = [_section_to_dict(s) for s in sections]
    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=RECIPE_SECTION_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def get_cmd(
    ctx: typer.Context,
    recipe: Annotated[str, typer.Argument(help="Recipe name or key.")],
    section: Annotated[str, typer.Argument(help="Section name or key.")],
) -> None:
    """Get a recipe section by name or key."""
    vctx = get_context(ctx)
    _resolve_recipe(vctx, recipe)  # Validate recipe exists
    section_key = resolve_resource_id(vctx.client.recipe_sections, section, "recipe section")
    item = vctx.client.recipe_sections.get(key=section_key)
    output_result(
        _section_to_dict(item),
        output_format=vctx.output_format,
        query=vctx.query,
        columns=RECIPE_SECTION_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("create")
@handle_errors()
def create_cmd(
    ctx: typer.Context,
    recipe: Annotated[str, typer.Argument(help="Recipe name or key.")],
    name: Annotated[str, typer.Option("--name", "-n", help="Section name.")],
    description: Annotated[
        str | None,
        typer.Option("--description", "-d", help="Section description."),
    ] = None,
) -> None:
    """Create a new recipe section."""
    vctx = get_context(ctx)
    recipe_key = _resolve_recipe(vctx, recipe)
    recipe_ref = f"vm_recipes/{recipe_key}"
    kwargs: dict[str, Any] = {}
    if description is not None:
        kwargs["description"] = description
    result = vctx.client.recipe_sections.create(
        name=name,
        recipe_ref=recipe_ref,
        **kwargs,
    )
    output_result(
        _section_to_dict(result),
        output_format=vctx.output_format,
        query=vctx.query,
        columns=RECIPE_SECTION_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )
    output_success(f"Section '{name}' created.")


@app.command("update")
@handle_errors()
def update_cmd(
    ctx: typer.Context,
    recipe: Annotated[str, typer.Argument(help="Recipe name or key.")],
    section: Annotated[str, typer.Argument(help="Section name or key.")],
    name: Annotated[
        str | None,
        typer.Option("--name", "-n", help="New section name."),
    ] = None,
    description: Annotated[
        str | None,
        typer.Option("--description", "-d", help="New description."),
    ] = None,
    order: Annotated[
        int | None,
        typer.Option("--order", help="Display order."),
    ] = None,
) -> None:
    """Update a recipe section."""
    vctx = get_context(ctx)
    _resolve_recipe(vctx, recipe)  # Validate recipe exists
    section_key = resolve_resource_id(vctx.client.recipe_sections, section, "recipe section")
    kwargs: dict[str, Any] = {}
    if name is not None:
        kwargs["name"] = name
    if description is not None:
        kwargs["description"] = description
    if order is not None:
        kwargs["orderid"] = order
    result = vctx.client.recipe_sections.update(section_key, **kwargs)
    output_result(
        _section_to_dict(result),
        output_format=vctx.output_format,
        query=vctx.query,
        columns=RECIPE_SECTION_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )
    output_success(f"Section '{section}' updated.")


@app.command("delete")
@handle_errors()
def delete_cmd(
    ctx: typer.Context,
    recipe: Annotated[str, typer.Argument(help="Recipe name or key.")],
    section: Annotated[str, typer.Argument(help="Section name or key.")],
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation."),
    ] = False,
) -> None:
    """Delete a recipe section (cascades to questions)."""
    vctx = get_context(ctx)
    _resolve_recipe(vctx, recipe)  # Validate recipe exists
    section_key = resolve_resource_id(vctx.client.recipe_sections, section, "recipe section")
    if not confirm_action(
        f"Delete section '{section}'? This will also delete all questions in this section.", yes=yes
    ):
        raise typer.Abort()
    vctx.client.recipe_sections.delete(section_key)
    output_success(f"Section '{section}' deleted.")
