"""Tests for update management commands."""

from __future__ import annotations

from unittest.mock import MagicMock

from typer.testing import CliRunner

from verge_cli.cli import app


def test_update_settings(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_update_settings: MagicMock,
) -> None:
    """Test showing current update settings."""
    mock_client.update_settings.get.return_value = mock_update_settings

    result = cli_runner.invoke(app, ["update", "settings"])

    assert result.exit_code == 0
    assert "02:00" in result.output
    mock_client.update_settings.get.assert_called_once()


def test_update_settings_json(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_update_settings: MagicMock,
) -> None:
    """Test showing settings in JSON format."""
    mock_client.update_settings.get.return_value = mock_update_settings

    result = cli_runner.invoke(app, ["--output", "json", "update", "settings"])

    assert result.exit_code == 0
    assert "auto_refresh" in result.output


def test_update_configure(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_update_settings: MagicMock,
) -> None:
    """Test configuring update settings with auto_refresh and update_time."""
    mock_client.update_settings.update.return_value = mock_update_settings

    result = cli_runner.invoke(
        app,
        ["update", "configure", "--auto-refresh", "--update-time", "03:00"],
    )

    assert result.exit_code == 0
    mock_client.update_settings.update.assert_called_once_with(
        auto_refresh=True,
        update_time="03:00",
    )


def test_update_configure_booleans(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_update_settings: MagicMock,
) -> None:
    """Test configuring boolean toggles."""
    mock_client.update_settings.update.return_value = mock_update_settings

    result = cli_runner.invoke(
        app,
        ["update", "configure", "--auto-update", "--no-auto-reboot"],
    )

    assert result.exit_code == 0
    mock_client.update_settings.update.assert_called_once_with(
        auto_update=True,
        auto_reboot=False,
    )


def test_update_check(
    cli_runner: CliRunner,
    mock_client: MagicMock,
) -> None:
    """Test check for updates."""
    mock_client.update_settings.check.return_value = {"status": "ok"}

    result = cli_runner.invoke(app, ["update", "check"])

    assert result.exit_code == 0
    mock_client.update_settings.check.assert_called_once()


def test_update_download(
    cli_runner: CliRunner,
    mock_client: MagicMock,
) -> None:
    """Test download updates."""
    mock_client.update_settings.download.return_value = {"status": "ok"}

    result = cli_runner.invoke(app, ["update", "download"])

    assert result.exit_code == 0
    mock_client.update_settings.download.assert_called_once()


def test_update_install_confirm(
    cli_runner: CliRunner,
    mock_client: MagicMock,
) -> None:
    """Test install with --yes confirmation."""
    mock_client.update_settings.install.return_value = {"status": "ok"}

    result = cli_runner.invoke(app, ["update", "install", "--yes"])

    assert result.exit_code == 0
    mock_client.update_settings.install.assert_called_once()


def test_update_install_no_confirm(
    cli_runner: CliRunner,
    mock_client: MagicMock,
) -> None:
    """Test install without --yes aborts."""
    result = cli_runner.invoke(app, ["update", "install"], input="n\n")

    assert result.exit_code != 0
    mock_client.update_settings.install.assert_not_called()


def test_update_apply_confirm(
    cli_runner: CliRunner,
    mock_client: MagicMock,
) -> None:
    """Test apply with --yes confirmation."""
    mock_client.update_settings.update_all.return_value = {"status": "ok"}

    result = cli_runner.invoke(app, ["update", "apply", "--yes"])

    assert result.exit_code == 0
    mock_client.update_settings.update_all.assert_called_once_with(force=False)


def test_update_apply_force(
    cli_runner: CliRunner,
    mock_client: MagicMock,
) -> None:
    """Test apply with --force --yes."""
    mock_client.update_settings.update_all.return_value = {"status": "ok"}

    result = cli_runner.invoke(app, ["update", "apply", "--force", "--yes"])

    assert result.exit_code == 0
    mock_client.update_settings.update_all.assert_called_once_with(force=True)
