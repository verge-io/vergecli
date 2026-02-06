"""Tests for vrg vm validate command."""

from verge_cli.cli import app


def test_validate_valid_template(cli_runner, tmp_path):
    """vrg vm validate should accept a valid template."""
    template = tmp_path / "test.vrg.yaml"
    template.write_text(
        "apiVersion: v4\nkind: VirtualMachine\nvm:\n  name: test-vm\n  os_family: linux\n"
    )

    result = cli_runner.invoke(app, ["vm", "validate", "-f", str(template)])
    assert result.exit_code == 0
    assert "valid" in result.output.lower()


def test_validate_invalid_template(cli_runner, tmp_path):
    """vrg vm validate should reject an invalid template."""
    template = tmp_path / "bad.vrg.yaml"
    template.write_text(
        'apiVersion: v4\nkind: VirtualMachine\nvm:\n  name: test-vm\n  os_family: "invalid"\n'
    )

    result = cli_runner.invoke(app, ["vm", "validate", "-f", str(template)])
    assert result.exit_code != 0


def test_validate_missing_file(cli_runner):
    """vrg vm validate should error on missing file."""
    result = cli_runner.invoke(app, ["vm", "validate", "-f", "/nonexistent.vrg.yaml"])
    assert result.exit_code != 0


def test_validate_with_variables(cli_runner, tmp_path):
    """vrg vm validate should resolve variables."""
    template = tmp_path / "test.vrg.yaml"
    template.write_text(
        "apiVersion: v4\n"
        "kind: VirtualMachine\n"
        "vars:\n"
        "  env: test\n"
        "vm:\n"
        '  name: "${env}-vm"\n'
        "  os_family: linux\n"
    )

    result = cli_runner.invoke(app, ["vm", "validate", "-f", str(template)])
    assert result.exit_code == 0
