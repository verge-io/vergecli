"""Tests for API key commands."""

from __future__ import annotations

from verge_cli.cli import app


def test_api_key_list(cli_runner, mock_client, mock_api_key):
    """List API keys."""
    mock_client.api_keys.list.return_value = [mock_api_key]

    result = cli_runner.invoke(app, ["api-key", "list"])

    assert result.exit_code == 0
    assert "automation" in result.output
    mock_client.api_keys.list.assert_called_once()


def test_api_key_list_by_user(cli_runner, mock_client, mock_api_key):
    """--user filter passes to SDK."""
    mock_client.api_keys.list.return_value = [mock_api_key]

    result = cli_runner.invoke(app, ["api-key", "list", "--user", "admin"])

    assert result.exit_code == 0
    mock_client.api_keys.list.assert_called_once_with(user="admin")


def test_api_key_list_by_user_key(cli_runner, mock_client, mock_api_key):
    """--user with numeric key passes as int."""
    mock_client.api_keys.list.return_value = [mock_api_key]

    result = cli_runner.invoke(app, ["api-key", "list", "--user", "10"])

    assert result.exit_code == 0
    mock_client.api_keys.list.assert_called_once_with(user=10)


def test_api_key_get_by_key(cli_runner, mock_client, mock_api_key):
    """Get by numeric key."""
    mock_client.api_keys.get.return_value = mock_api_key

    result = cli_runner.invoke(app, ["api-key", "get", "60"])

    assert result.exit_code == 0
    assert "automation" in result.output
    mock_client.api_keys.get.assert_called_once_with(60)


def test_api_key_get_by_name(cli_runner, mock_client, mock_api_key):
    """Get by name with --user."""
    mock_client.api_keys.get.return_value = mock_api_key

    result = cli_runner.invoke(app, ["api-key", "get", "automation", "--user", "admin"])

    assert result.exit_code == 0
    assert "automation" in result.output
    mock_client.api_keys.get.assert_called_once_with(name="automation", user="admin")


def test_api_key_get_by_name_no_user(cli_runner, mock_client):
    """Get by name without --user should error."""
    result = cli_runner.invoke(app, ["api-key", "get", "automation"])

    assert result.exit_code == 2
    assert "--user is required" in result.output


def test_api_key_create(cli_runner, mock_client, mock_api_key_created):
    """Basic create, verify secret in output."""
    mock_client.api_keys.create.return_value = mock_api_key_created

    result = cli_runner.invoke(
        app,
        ["api-key", "create", "--user", "admin", "--name", "new-key"],
    )

    assert result.exit_code == 0
    assert "Created API key" in result.output
    assert "vrg_sk_abc123def456ghi789" in result.output
    assert "Store this secret" in result.output
    mock_client.api_keys.create.assert_called_once_with(
        user="admin",
        name="new-key",
    )


def test_api_key_create_with_options(cli_runner, mock_client, mock_api_key_created):
    """All optional flags."""
    mock_client.api_keys.create.return_value = mock_api_key_created

    result = cli_runner.invoke(
        app,
        [
            "api-key",
            "create",
            "--user",
            "admin",
            "--name",
            "new-key",
            "--description",
            "CI/CD key",
            "--expires-in",
            "90d",
        ],
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.api_keys.create.call_args[1]
    assert call_kwargs["description"] == "CI/CD key"
    assert call_kwargs["expires_in"] == "90d"


def test_api_key_create_ip_lists(cli_runner, mock_client, mock_api_key_created):
    """--ip-allow and --ip-deny parsing."""
    mock_client.api_keys.create.return_value = mock_api_key_created

    result = cli_runner.invoke(
        app,
        [
            "api-key",
            "create",
            "--user",
            "admin",
            "--name",
            "new-key",
            "--ip-allow",
            "10.0.0.0/8,192.168.1.100",
            "--ip-deny",
            "172.16.0.0/12",
        ],
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.api_keys.create.call_args[1]
    assert call_kwargs["ip_allow_list"] == ["10.0.0.0/8", "192.168.1.100"]
    assert call_kwargs["ip_deny_list"] == ["172.16.0.0/12"]


def test_api_key_delete(cli_runner, mock_client):
    """Delete with --yes."""
    result = cli_runner.invoke(app, ["api-key", "delete", "60", "--yes"])

    assert result.exit_code == 0
    assert "Deleted API key" in result.output
    mock_client.api_keys.delete.assert_called_once_with(60)


def test_api_key_delete_no_confirm(cli_runner, mock_client):
    """Delete without --yes aborts."""
    result = cli_runner.invoke(app, ["api-key", "delete", "60"], input="n\n")

    assert result.exit_code == 0
    mock_client.api_keys.delete.assert_not_called()
