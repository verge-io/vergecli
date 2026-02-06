"""CLI context management for Verge CLI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import typer

if TYPE_CHECKING:
    from pyvergeos import VergeClient

    from verge_cli.config import ProfileConfig


@dataclass
class VergeContext:
    """Shared context passed to all CLI commands via ctx.obj.

    This dataclass holds the authenticated client, configuration,
    and output settings for use across all sub-commands.
    """

    config: ProfileConfig
    client: VergeClient
    output_format: str
    verbosity: int
    quiet: bool
    query: str | None = None
    no_color: bool = False


def get_context(ctx: typer.Context) -> VergeContext:
    """Get or create the VergeContext with an authenticated client.

    This should be called by commands that need to access the VergeOS API.
    The client is created lazily on first access.

    Args:
        ctx: Typer context with configuration stored in ctx.obj.

    Returns:
        VergeContext with authenticated client.
    """
    from verge_cli.auth import get_client

    obj = ctx.obj

    # Create client if not already created
    if obj["_client"] is None:
        obj["_client"] = get_client(obj["config"])

    return VergeContext(
        config=obj["config"],
        client=obj["_client"],
        output_format=obj["output_format"],
        verbosity=obj["verbosity"],
        quiet=obj["quiet"],
        query=obj["query"],
        no_color=obj["no_color"],
    )
