"""Pytest configuration and fixtures."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


@pytest.fixture
def cli_runner() -> CliRunner:
    """Typer test runner for CLI testing."""
    return CliRunner()


@pytest.fixture
def mock_client(mocker: MockerFixture) -> MagicMock:
    """Mock the pyvergeos VergeClient for unit tests.

    This fixture patches get_client to return a mock client,
    preventing any actual API calls during tests.
    """
    mock = MagicMock()

    # Set up common properties
    mock.version = "6.0.0"
    mock.os_version = "1.0.0"
    mock.cloud_name = "Test Cloud"
    mock.host = "https://test.verge.io"

    # Mock system.statistics()
    mock_stats = MagicMock()
    mock_stats.vms_total = 10
    mock_stats.vms_online = 5
    mock_stats.tenants_total = 2
    mock_stats.tenants_online = 2
    mock_stats.networks_total = 3
    mock_stats.networks_online = 3
    mock_stats.nodes_total = 2
    mock_stats.nodes_online = 2
    mock_stats.alarms_total = 0
    mock.system.statistics.return_value = mock_stats

    mocker.patch("verge_cli.auth.get_client", return_value=mock)
    return mock


@pytest.fixture
def mock_vm() -> MagicMock:
    """Create a mock VM object."""
    vm = MagicMock()
    vm.key = 1
    vm.name = "test-vm"
    vm.status = "running"
    vm.is_running = True
    vm.is_snapshot = False
    vm.cluster_name = "Cluster1"
    vm.node_name = "Node1"

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "description": "Test VM",
            "cpu_cores": 2,
            "ram": 2048,
            "os_family": "linux",
            "created": "2024-01-01T00:00:00Z",
            "modified": "2024-01-02T00:00:00Z",
        }
        return data.get(key, default)

    vm.get = mock_get
    return vm


@pytest.fixture
def mock_network() -> MagicMock:
    """Create a mock Network object."""
    net = MagicMock()
    net.key = 1
    net.name = "test-network"

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "description": "Test Network",
            "type": "internal",
            "network": "10.0.0.0/24",
            "ipaddress": "10.0.0.1",
            "gateway": "10.0.0.1",
            "mtu": 1500,
            "status": "running",
            "running": True,
            "dhcp_enabled": True,
            "dhcp_start": "10.0.0.100",
            "dhcp_stop": "10.0.0.200",
            "dns": "10.0.0.1",
            "domain": "test.local",
        }
        return data.get(key, default)

    net.get = mock_get
    return net


@pytest.fixture
def mock_dns_view() -> MagicMock:
    """Create a mock DNS View object."""
    view = MagicMock()
    view.key = 10
    view.name = "internal"

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "$key": 10,
            "name": "internal",
            "recursion": True,
            "match_clients": "10.0.0.0/8;192.168.0.0/16;",
            "match_destinations": None,
            "max_cache_size": 33554432,
            "vnet": 1,
        }
        return data.get(key, default)

    view.get = mock_get
    return view


@pytest.fixture
def mock_drive() -> MagicMock:
    """Create a mock Drive object."""
    drive = MagicMock()
    drive.key = 10
    drive.name = "OS Disk"
    drive.size_gb = 50.0
    drive.used_gb = 12.5
    drive.interface_display = "VirtIO SCSI"
    drive.media_display = "Disk"
    drive.is_enabled = True
    drive.is_readonly = False

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "$key": 10,
            "name": "OS Disk",
            "description": "Operating System Disk",
            "interface": "virtio-scsi",
            "media": "disk",
            "disksize": 53687091200,
            "preferred_tier": 3,
            "enabled": True,
            "readonly": False,
            "machine": 38,
        }
        return data.get(key, default)

    drive.get = mock_get
    return drive


@pytest.fixture
def mock_nic() -> MagicMock:
    """Create a mock NIC object."""
    nic = MagicMock()
    nic.key = 20
    nic.name = "Primary Network"
    nic.interface_display = "VirtIO"
    nic.is_enabled = True
    nic.mac_address = "52:54:00:12:34:56"
    nic.ip_address = "10.0.0.100"
    nic.network_name = "DMZ Internal"
    nic.network_key = 3

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "$key": 20,
            "name": "Primary Network",
            "description": "LAN connection",
            "interface": "virtio",
            "enabled": True,
            "mac": "52:54:00:12:34:56",
            "ipaddress": "10.0.0.100",
            "vnet": 3,
            "vnet_name": "DMZ Internal",
            "machine": 38,
        }
        return data.get(key, default)

    nic.get = mock_get
    return nic


@pytest.fixture
def mock_device() -> MagicMock:
    """Create a mock Device object (TPM)."""
    device = MagicMock()
    device.key = 30
    device.name = "TPM"
    device.device_type = "TPM"
    device.device_type_raw = "tpm"
    device.is_enabled = True
    device.is_optional = False
    device.is_tpm = True
    device.is_gpu = False
    device.is_usb = False

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "$key": 30,
            "name": "TPM",
            "type": "tpm",
            "enabled": True,
            "optional": False,
            "settings_args": {"model": "crb", "version": "2"},
            "machine": 38,
        }
        return data.get(key, default)

    device.get = mock_get
    return device


@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Path:
    """Create a temporary config directory."""
    config_dir = tmp_path / ".vrg"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def sample_config_file(temp_config_dir: Path) -> Path:
    """Create a sample config file for testing."""
    config_file = temp_config_dir / "config.toml"
    config_file.write_text(
        """
[default]
host = "https://verge.example.com"
token = "test-token-12345"
verify_ssl = true
output = "table"
timeout = 30

[profile.dev]
host = "https://192.168.1.100"
username = "admin"
password = "secret"
verify_ssl = false
"""
    )
    return config_file
