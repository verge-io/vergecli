"""Tests for resource group commands."""

from __future__ import annotations

from unittest.mock import MagicMock

from typer.testing import CliRunner

from verge_cli.cli import app


def test_group_list(
    cli_runner: CliRunner, mock_client: MagicMock, mock_resource_group: MagicMock
) -> None:
    """Test listing resource groups."""
    mock_client.resource_groups.list.return_value = [mock_resource_group]

    result = cli_runner.invoke(app, ["resource-group", "list"])

    assert result.exit_code == 0
    assert "gpu-passthrough" in result.output
    assert "PCI" in result.output
    mock_client.resource_groups.list.assert_called_once()


def test_group_list_enabled(
    cli_runner: CliRunner, mock_client: MagicMock, mock_resource_group: MagicMock
) -> None:
    """Test listing enabled resource groups."""
    mock_client.resource_groups.list_enabled.return_value = [mock_resource_group]

    result = cli_runner.invoke(app, ["resource-group", "list", "--enabled"])

    assert result.exit_code == 0
    assert "gpu-passthrough" in result.output
    mock_client.resource_groups.list_enabled.assert_called_once()


def test_group_list_disabled(
    cli_runner: CliRunner, mock_client: MagicMock, mock_resource_group: MagicMock
) -> None:
    """Test listing disabled resource groups."""
    mock_resource_group.is_enabled = False
    mock_client.resource_groups.list_disabled.return_value = [mock_resource_group]

    result = cli_runner.invoke(app, ["resource-group", "list", "--disabled"])

    assert result.exit_code == 0
    assert "gpu-passthrough" in result.output
    mock_client.resource_groups.list_disabled.assert_called_once()


def test_group_list_by_type(
    cli_runner: CliRunner, mock_client: MagicMock, mock_resource_group: MagicMock
) -> None:
    """Test listing resource groups filtered by device type."""
    mock_client.resource_groups.list_by_type.return_value = [mock_resource_group]

    result = cli_runner.invoke(app, ["resource-group", "list", "--type", "pci"])

    assert result.exit_code == 0
    assert "gpu-passthrough" in result.output
    mock_client.resource_groups.list_by_type.assert_called_once_with(
        device_type="node_pci_devices", enabled=None
    )


def test_group_list_by_class(
    cli_runner: CliRunner, mock_client: MagicMock, mock_resource_group: MagicMock
) -> None:
    """Test listing resource groups filtered by device class."""
    mock_client.resource_groups.list_by_class.return_value = [mock_resource_group]

    result = cli_runner.invoke(app, ["resource-group", "list", "--class", "gpu"])

    assert result.exit_code == 0
    assert "gpu-passthrough" in result.output
    mock_client.resource_groups.list_by_class.assert_called_once_with(
        device_class="gpu", enabled=None
    )


def test_group_get_by_uuid(
    cli_runner: CliRunner, mock_client: MagicMock, mock_resource_group: MagicMock
) -> None:
    """Test getting a resource group by UUID."""
    mock_client.resource_groups.get.return_value = mock_resource_group

    result = cli_runner.invoke(
        app, ["resource-group", "get", "a1b2c3d4-e5f6-7890-abcd-ef1234567890"]
    )

    assert result.exit_code == 0
    assert "gpu-passthrough" in result.output
    # Called twice: once for resolve, once for get
    assert mock_client.resource_groups.get.call_count == 2


def test_group_get_by_name(
    cli_runner: CliRunner, mock_client: MagicMock, mock_resource_group: MagicMock
) -> None:
    """Test getting a resource group by name."""
    mock_client.resource_groups.get.return_value = mock_resource_group

    result = cli_runner.invoke(app, ["resource-group", "get", "gpu-passthrough"])

    assert result.exit_code == 0
    assert "gpu-passthrough" in result.output
    # First call to resolve (by name), second call to get (by UUID)
    mock_client.resource_groups.get.assert_any_call(name="gpu-passthrough")


def test_group_create_pci(
    cli_runner: CliRunner, mock_client: MagicMock, mock_resource_group: MagicMock
) -> None:
    """Test creating a PCI resource group."""
    mock_client.resource_groups.create_pci.return_value = mock_resource_group

    result = cli_runner.invoke(
        app,
        [
            "resource-group",
            "create",
            "--name",
            "my-gpu-group",
            "--type",
            "pci",
            "--description",
            "Test PCI group",
            "--device-class",
            "gpu",
        ],
    )

    assert result.exit_code == 0
    assert "gpu-passthrough" in result.output
    mock_client.resource_groups.create_pci.assert_called_once_with(
        name="my-gpu-group",
        description="Test PCI group",
        enabled=True,
        device_class="gpu",
    )


def test_group_create_usb(
    cli_runner: CliRunner, mock_client: MagicMock, mock_resource_group: MagicMock
) -> None:
    """Test creating a USB resource group."""
    mock_resource_group.device_type_display = "USB"
    mock_client.resource_groups.create_usb.return_value = mock_resource_group

    result = cli_runner.invoke(
        app,
        [
            "resource-group",
            "create",
            "--name",
            "usb-group",
            "--type",
            "usb",
            "--no-allow-guest-reset",
        ],
    )

    assert result.exit_code == 0
    mock_client.resource_groups.create_usb.assert_called_once_with(
        name="usb-group",
        description="",
        enabled=True,
        allow_guest_reset=False,
    )


def test_group_create_host_gpu(
    cli_runner: CliRunner, mock_client: MagicMock, mock_resource_group: MagicMock
) -> None:
    """Test creating a host GPU resource group."""
    mock_resource_group.device_type_display = "Host GPU"
    mock_client.resource_groups.create_host_gpu.return_value = mock_resource_group

    result = cli_runner.invoke(
        app,
        [
            "resource-group",
            "create",
            "--name",
            "host-gpu-group",
            "--type",
            "host-gpu",
        ],
    )

    assert result.exit_code == 0
    mock_client.resource_groups.create_host_gpu.assert_called_once_with(
        name="host-gpu-group",
        description="",
        enabled=True,
    )


def test_group_create_nvidia_vgpu(
    cli_runner: CliRunner, mock_client: MagicMock, mock_resource_group: MagicMock
) -> None:
    """Test creating an NVIDIA vGPU resource group."""
    mock_resource_group.device_type_display = "NVIDIA vGPU"
    mock_client.resource_groups.create_nvidia_vgpu.return_value = mock_resource_group

    result = cli_runner.invoke(
        app,
        [
            "resource-group",
            "create",
            "--name",
            "vgpu-group",
            "--type",
            "nvidia-vgpu",
            "--driver-file",
            "42",
            "--vgpu-profile",
            "10",
            "--make-guest-driver-iso",
        ],
    )

    assert result.exit_code == 0
    mock_client.resource_groups.create_nvidia_vgpu.assert_called_once_with(
        name="vgpu-group",
        driver_file=42,
        description="",
        enabled=True,
        nvidia_vgpu_profile=10,
        make_guest_driver_iso=True,
    )


def test_group_create_nvidia_vgpu_missing_driver(
    cli_runner: CliRunner, mock_client: MagicMock
) -> None:
    """Test creating vGPU group without required --driver-file fails."""
    result = cli_runner.invoke(
        app,
        [
            "resource-group",
            "create",
            "--name",
            "vgpu-group",
            "--type",
            "nvidia-vgpu",
        ],
    )

    assert result.exit_code == 2
    assert "--driver-file" in result.output


def test_group_create_sriov_nic(
    cli_runner: CliRunner, mock_client: MagicMock, mock_resource_group: MagicMock
) -> None:
    """Test creating an SR-IOV NIC resource group."""
    mock_resource_group.device_type_display = "SR-IOV NIC"
    mock_client.resource_groups.create_sriov_nic.return_value = mock_resource_group

    result = cli_runner.invoke(
        app,
        [
            "resource-group",
            "create",
            "--name",
            "sriov-group",
            "--type",
            "sriov-nic",
            "--vf-count",
            "8",
            "--native-vlan",
            "100",
        ],
    )

    assert result.exit_code == 0
    mock_client.resource_groups.create_sriov_nic.assert_called_once_with(
        name="sriov-group",
        description="",
        enabled=True,
        vf_count=8,
        native_vlan=100,
    )


def test_group_update(
    cli_runner: CliRunner, mock_client: MagicMock, mock_resource_group: MagicMock
) -> None:
    """Test updating a resource group."""
    mock_client.resource_groups.get.return_value = mock_resource_group
    mock_client.resource_groups.update.return_value = mock_resource_group

    result = cli_runner.invoke(
        app,
        [
            "resource-group",
            "update",
            "gpu-passthrough",
            "--description",
            "Updated description",
            "--no-enabled",
        ],
    )

    assert result.exit_code == 0
    mock_client.resource_groups.update.assert_called_once_with(
        "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        description="Updated description",
        enabled=False,
    )


def test_group_delete_confirm(
    cli_runner: CliRunner, mock_client: MagicMock, mock_resource_group: MagicMock
) -> None:
    """Test deleting a resource group with --yes."""
    mock_client.resource_groups.get.return_value = mock_resource_group

    result = cli_runner.invoke(app, ["resource-group", "delete", "gpu-passthrough", "--yes"])

    assert result.exit_code == 0
    mock_client.resource_groups.delete.assert_called_once_with(
        "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    )


def test_group_delete_no_confirm(
    cli_runner: CliRunner, mock_client: MagicMock, mock_resource_group: MagicMock
) -> None:
    """Test deleting a resource group without --yes aborts."""
    mock_client.resource_groups.get.return_value = mock_resource_group

    result = cli_runner.invoke(app, ["resource-group", "delete", "gpu-passthrough"], input="n\n")

    # Abort results in exit code 1 from typer
    assert result.exit_code == 1
    mock_client.resource_groups.delete.assert_not_called()


def test_group_not_found(cli_runner: CliRunner, mock_client: MagicMock) -> None:
    """Test resource group name resolution error."""
    from pyvergeos.exceptions import NotFoundError

    mock_client.resource_groups.get.side_effect = NotFoundError("Resource group not found")

    result = cli_runner.invoke(app, ["resource-group", "get", "nonexistent"])

    assert result.exit_code == 6
