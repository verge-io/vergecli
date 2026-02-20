"""Tests for system commands."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from verge_cli.cli import app

# ---------------------------------------------------------------------------
# Mock fixtures
# ---------------------------------------------------------------------------


def _mock_setting(key: str = "ui.theme", value: str = "dark", modified: bool = True) -> MagicMock:
    """Create a mock SystemSetting."""
    setting = MagicMock()
    setting.key = key

    def mock_get(k: str, default: Any = None) -> Any:
        data = {
            "key": key,
            "value": value,
            "default_value": "light",
            "description": "UI theme setting",
            "modified": modified,
        }
        return data.get(k, default)

    setting.get = mock_get
    return setting


def _mock_license() -> MagicMock:
    """Create a mock License."""
    lic = MagicMock()
    lic.key = 1
    lic.name = "VergeOS Enterprise"

    def mock_get(k: str, default: Any = None) -> Any:
        data: dict[str, Any] = {
            "name": "VergeOS Enterprise",
            "is_valid": True,
            "valid_from": "2026-01-01",
            "valid_until": "2027-01-01",
            "features": "all",
            "auto_renewal": True,
            "allow_branding": False,
            "note": "Production license",
        }
        return data.get(k, default)

    lic.get = mock_get
    return lic


# ---------------------------------------------------------------------------
# System info/version tests
# ---------------------------------------------------------------------------


def test_system_info(cli_runner, mock_client):
    """vrg system info should display system information."""
    result = cli_runner.invoke(app, ["system", "info"])
    assert result.exit_code == 0
    assert "Test Cloud" in result.output


def test_system_version(cli_runner, mock_client):
    """vrg system version should display version."""
    result = cli_runner.invoke(app, ["system", "version"])
    assert result.exit_code == 0
    assert "6.0.0" in result.output


# ---------------------------------------------------------------------------
# Settings tests
# ---------------------------------------------------------------------------


def test_settings_list(cli_runner, mock_client):
    """vrg system settings list should list settings."""
    mock_client.system.settings.list.return_value = [_mock_setting()]

    result = cli_runner.invoke(app, ["system", "settings", "list"])

    assert result.exit_code == 0
    assert "ui.theme" in result.output
    mock_client.system.settings.list.assert_called_once()


def test_settings_list_modified(cli_runner, mock_client):
    """vrg system settings list --modified should list only modified settings."""
    mock_client.system.settings.list_modified.return_value = [_mock_setting()]

    result = cli_runner.invoke(app, ["system", "settings", "list", "--modified"])

    assert result.exit_code == 0
    mock_client.system.settings.list_modified.assert_called_once()


def test_settings_get(cli_runner, mock_client):
    """vrg system settings get should get a setting."""
    mock_client.system.settings.get.return_value = _mock_setting()

    result = cli_runner.invoke(app, ["system", "settings", "get", "ui.theme"])

    assert result.exit_code == 0
    assert "dark" in result.output
    mock_client.system.settings.get.assert_called_once_with("ui.theme")


def test_settings_set(cli_runner, mock_client):
    """vrg system settings set should update a setting."""
    result = cli_runner.invoke(app, ["system", "settings", "set", "ui.theme", "light"])

    assert result.exit_code == 0
    assert "Set" in result.output
    mock_client.system.settings.update.assert_called_once_with("ui.theme", "light")


def test_settings_reset(cli_runner, mock_client):
    """vrg system settings reset should reset a setting."""
    result = cli_runner.invoke(app, ["system", "settings", "reset", "ui.theme"])

    assert result.exit_code == 0
    assert "Reset" in result.output
    mock_client.system.settings.reset.assert_called_once_with("ui.theme")


# ---------------------------------------------------------------------------
# License tests
# ---------------------------------------------------------------------------


def test_license_list(cli_runner, mock_client):
    """vrg system license list should list licenses."""
    mock_client.system.licenses.list.return_value = [_mock_license()]

    result = cli_runner.invoke(app, ["system", "license", "list"])

    assert result.exit_code == 0
    assert "VergeOS Enterprise" in result.output


def test_license_get_by_key(cli_runner, mock_client):
    """vrg system license get should accept numeric key."""
    mock_client.system.licenses.get.return_value = _mock_license()

    result = cli_runner.invoke(app, ["system", "license", "get", "1"])

    assert result.exit_code == 0
    assert "VergeOS Enterprise" in result.output
    mock_client.system.licenses.get.assert_called_once_with(1)


def test_license_get_by_name(cli_runner, mock_client):
    """vrg system license get should accept name."""
    mock_client.system.licenses.get.return_value = _mock_license()

    result = cli_runner.invoke(app, ["system", "license", "get", "VergeOS Enterprise"])

    assert result.exit_code == 0
    mock_client.system.licenses.get.assert_called_once_with(name="VergeOS Enterprise")


def test_license_add(cli_runner, mock_client):
    """vrg system license add should install a license."""
    mock_lic = _mock_license()
    mock_client.system.licenses.add.return_value = mock_lic

    result = cli_runner.invoke(
        app, ["system", "license", "add", "--license-text", "LICENSE-KEY-HERE"]
    )

    assert result.exit_code == 0
    assert "Added license" in result.output
    mock_client.system.licenses.add.assert_called_once_with("LICENSE-KEY-HERE")


def test_license_generate_payload(cli_runner, mock_client):
    """vrg system license generate-payload should output payload text."""
    mock_client.system.licenses.generate_payload.return_value = "AIRGAP-PAYLOAD-DATA"

    result = cli_runner.invoke(app, ["system", "license", "generate-payload"])

    assert result.exit_code == 0
    assert "AIRGAP-PAYLOAD-DATA" in result.output


# ---------------------------------------------------------------------------
# Inventory tests
# ---------------------------------------------------------------------------


def test_inventory(cli_runner, mock_client):
    """vrg system inventory should return inventory data."""
    mock_client.system.inventory.return_value = {"vms": 10, "nodes": 4}

    result = cli_runner.invoke(app, ["system", "inventory"])

    assert result.exit_code == 0
    mock_client.system.inventory.assert_called_once_with()


def test_inventory_filtered(cli_runner, mock_client):
    """vrg system inventory --vms --nodes should pass filter kwargs."""
    mock_client.system.inventory.return_value = {"vms": 10, "nodes": 4}

    result = cli_runner.invoke(app, ["system", "inventory", "--vms", "--nodes"])

    assert result.exit_code == 0
    mock_client.system.inventory.assert_called_once_with(include_vms=True, include_nodes=True)
