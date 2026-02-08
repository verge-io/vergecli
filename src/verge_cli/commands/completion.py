"""Shell completion script generation."""

from __future__ import annotations

import typer
from typer._completion_shared import Shells, get_completion_script

SHELL_NAMES = {s.value for s in Shells}

app = typer.Typer(help="Generate shell completion scripts.")


@app.command("show")
def show(
    shell: str = typer.Argument(help=f"Shell type ({', '.join(sorted(SHELL_NAMES))})."),
) -> None:
    """Print the completion script for a given shell.

    Redirect the output to the appropriate file for your shell:

        vrg completion show bash >> ~/.bashrc

        vrg completion show zsh > "${fpath[1]}/_vrg"

        vrg completion show fish > ~/.config/fish/completions/vrg.fish

        vrg completion show powershell >> $PROFILE
    """
    shell_lower = shell.lower()
    if shell_lower not in SHELL_NAMES:
        typer.echo(
            f"Error: Unknown shell '{shell}'. Supported: {', '.join(sorted(SHELL_NAMES))}",
            err=True,
        )
        raise typer.Exit(code=2)
    script = get_completion_script(prog_name="vrg", complete_var="_VRG_COMPLETE", shell=shell_lower)
    typer.echo(script, nl=False)
