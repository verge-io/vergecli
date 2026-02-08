"""Tests for the completion command."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from verge_cli.cli import app


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


class TestCompletionShow:
    """Tests for `vrg completion show <shell>`."""

    @pytest.mark.parametrize("shell", ["bash", "zsh", "fish", "powershell", "pwsh"])
    def test_generates_script(self, runner: CliRunner, shell: str) -> None:
        result = runner.invoke(app, ["completion", "show", shell])
        assert result.exit_code == 0
        assert len(result.output) > 0

    def test_bash_script_content(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["completion", "show", "bash"])
        assert result.exit_code == 0
        assert "_VRG_COMPLETE" in result.output
        assert "COMPREPLY" in result.output

    def test_zsh_script_content(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["completion", "show", "zsh"])
        assert result.exit_code == 0
        assert "_VRG_COMPLETE" in result.output
        assert "compdef" in result.output

    def test_fish_script_content(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["completion", "show", "fish"])
        assert result.exit_code == 0
        assert "_VRG_COMPLETE" in result.output
        assert "complete --command vrg" in result.output

    def test_powershell_script_content(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["completion", "show", "powershell"])
        assert result.exit_code == 0
        assert "_VRG_COMPLETE" in result.output
        assert "Register-ArgumentCompleter" in result.output

    def test_case_insensitive(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["completion", "show", "BASH"])
        assert result.exit_code == 0
        assert "_VRG_COMPLETE" in result.output

    def test_invalid_shell(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["completion", "show", "ksh"])
        assert result.exit_code != 0
        assert "Unknown shell" in result.output

    def test_no_shell_argument(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["completion", "show"])
        assert result.exit_code != 0
