"""Task schedule trigger management commands for Verge CLI."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import TASK_TRIGGER_COLUMNS
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result, output_success
from verge_cli.utils import confirm_action, resolve_resource_id

app = typer.Typer(
    name="trigger",
    help="Manage task schedule triggers.",
    no_args_is_help=True,
)


def _trigger_to_dict(trigger: Any) -> dict[str, Any]:
    """Convert a TaskScheduleTrigger SDK object to a dictionary for output."""
    return {
        "$key": int(trigger.key),
        "task_key": trigger.task_key,
        "task_display": trigger.task_display,
        "schedule_key": trigger.schedule_key,
        "schedule_display": trigger.schedule_display,
        "schedule_enabled": trigger.is_schedule_enabled,
        "schedule_repeat": trigger.schedule_repeat_every or "",
    }


@app.command("list")
@handle_errors()
def trigger_list(
    ctx: typer.Context,
    task: Annotated[str, typer.Argument(help="Task ID or name.")],
) -> None:
    """List schedule triggers for a task."""
    vctx = get_context(ctx)
    task_key = resolve_resource_id(vctx.client.tasks, task, "Task")
    triggers = vctx.client.task_schedule_triggers.list(task=task_key)
    output_result(
        [_trigger_to_dict(t) for t in triggers],
        columns=TASK_TRIGGER_COLUMNS,
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("create")
@handle_errors()
def trigger_create(
    ctx: typer.Context,
    task: Annotated[str, typer.Argument(help="Task ID or name.")],
    schedule: Annotated[
        str,
        typer.Option("--schedule", help="Schedule ID or name to link."),
    ],
) -> None:
    """Create a trigger linking a task to a schedule."""
    vctx = get_context(ctx)
    task_key = resolve_resource_id(vctx.client.tasks, task, "Task")
    schedule_key = resolve_resource_id(vctx.client.task_schedules, schedule, "TaskSchedule")
    trigger = vctx.client.task_schedule_triggers.create(task=task_key, schedule=schedule_key)
    output_success(f"Trigger created (key={int(trigger.key)}) linking task to schedule.")


@app.command("delete")
@handle_errors()
def trigger_delete(
    ctx: typer.Context,
    trigger_id: Annotated[int, typer.Argument(help="Trigger ID (numeric key).")],
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation prompt."),
    ] = False,
) -> None:
    """Delete a schedule trigger."""
    vctx = get_context(ctx)
    if not confirm_action(f"Delete trigger {trigger_id}?", yes=yes):
        raise typer.Exit(0)
    vctx.client.task_schedule_triggers.delete(trigger_id)
    output_success(f"Trigger {trigger_id} deleted.")


@app.command("run")
@handle_errors()
def trigger_run(
    ctx: typer.Context,
    trigger_id: Annotated[int, typer.Argument(help="Trigger ID (numeric key).")],
) -> None:
    """Manually fire a schedule trigger."""
    vctx = get_context(ctx)
    vctx.client.task_schedule_triggers.trigger(trigger_id)
    output_success(f"Trigger {trigger_id} fired.")
