"""Tests for auth-source commands."""

from __future__ import annotations

from verge_cli.cli import app


def test_auth_source_list(cli_runner, mock_client, mock_auth_source):
    """List auth sources, default output."""
    mock_client.auth_sources.list.return_value = [mock_auth_source]

    result = cli_runner.invoke(app, ["auth-source", "list"])

    assert result.exit_code == 0
    assert "azure-sso" in result.output
    mock_client.auth_sources.list.assert_called_once()


def test_auth_source_list_by_driver(cli_runner, mock_client, mock_auth_source):
    """--driver azure filters by driver."""
    mock_client.auth_sources.list.return_value = [mock_auth_source]

    result = cli_runner.invoke(app, ["auth-source", "list", "--driver", "azure"])

    assert result.exit_code == 0
    mock_client.auth_sources.list.assert_called_once_with(driver="azure")


def test_auth_source_get(cli_runner, mock_client, mock_auth_source):
    """Get auth source by name resolution."""
    mock_client.auth_sources.list.return_value = [mock_auth_source]
    mock_client.auth_sources.get.return_value = mock_auth_source

    result = cli_runner.invoke(app, ["auth-source", "get", "azure-sso"])

    assert result.exit_code == 0
    assert "azure-sso" in result.output


def test_auth_source_get_by_key(cli_runner, mock_client, mock_auth_source):
    """Get auth source by numeric key."""
    mock_client.auth_sources.list.return_value = []
    mock_client.auth_sources.get.return_value = mock_auth_source

    result = cli_runner.invoke(app, ["auth-source", "get", "40"])

    assert result.exit_code == 0
    assert "azure-sso" in result.output
    mock_client.auth_sources.get.assert_called_with(40, include_settings=False)


def test_auth_source_get_show_settings(cli_runner, mock_client, mock_auth_source):
    """--show-settings includes settings in output."""
    mock_client.auth_sources.list.return_value = []
    mock_client.auth_sources.get.return_value = mock_auth_source

    result = cli_runner.invoke(app, ["auth-source", "get", "40", "--show-settings"])

    assert result.exit_code == 0
    mock_client.auth_sources.get.assert_called_with(40, include_settings=True)


def test_auth_source_create_basic(cli_runner, mock_client, mock_auth_source):
    """Create with name + driver only."""
    mock_client.auth_sources.create.return_value = mock_auth_source

    result = cli_runner.invoke(
        app, ["auth-source", "create", "--name", "azure-sso", "--driver", "azure"]
    )

    assert result.exit_code == 0
    assert "Created auth source" in result.output
    mock_client.auth_sources.create.assert_called_once_with(
        name="azure-sso",
        driver="azure",
    )


def test_auth_source_create_azure(cli_runner, mock_client, mock_auth_source):
    """Create Azure source with client-id, tenant-id, scope."""
    mock_client.auth_sources.create.return_value = mock_auth_source

    result = cli_runner.invoke(
        app,
        [
            "auth-source",
            "create",
            "--name",
            "azure-sso",
            "--driver",
            "azure",
            "--client-id",
            "abc-123",
            "--client-secret",
            "secret-456",
            "--tenant-id",
            "tenant-789",
            "--scope",
            "openid profile email",
        ],
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.auth_sources.create.call_args[1]
    assert call_kwargs["name"] == "azure-sso"
    assert call_kwargs["driver"] == "azure"
    assert call_kwargs["settings"]["client_id"] == "abc-123"
    assert call_kwargs["settings"]["client_secret"] == "secret-456"
    assert call_kwargs["settings"]["tenant_id"] == "tenant-789"
    assert call_kwargs["settings"]["scope"] == "openid profile email"


def test_auth_source_create_with_json(cli_runner, mock_client, mock_auth_source):
    """--settings-json raw settings."""
    mock_client.auth_sources.create.return_value = mock_auth_source

    result = cli_runner.invoke(
        app,
        [
            "auth-source",
            "create",
            "--name",
            "custom",
            "--driver",
            "openid",
            "--settings-json",
            '{"custom_field": "value", "another": 42}',
        ],
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.auth_sources.create.call_args[1]
    assert call_kwargs["settings"]["custom_field"] == "value"
    assert call_kwargs["settings"]["another"] == 42


def test_auth_source_create_json_flag_merge(cli_runner, mock_client, mock_auth_source):
    """JSON + individual flags (flags override)."""
    mock_client.auth_sources.create.return_value = mock_auth_source

    result = cli_runner.invoke(
        app,
        [
            "auth-source",
            "create",
            "--name",
            "merged",
            "--driver",
            "azure",
            "--settings-json",
            '{"client_id": "old-id", "custom": "keep"}',
            "--client-id",
            "new-id",
        ],
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.auth_sources.create.call_args[1]
    # Flag should override JSON
    assert call_kwargs["settings"]["client_id"] == "new-id"
    # JSON-only field should be preserved
    assert call_kwargs["settings"]["custom"] == "keep"


def test_auth_source_create_login_menu(cli_runner, mock_client, mock_auth_source):
    """--show-on-login and button styling."""
    mock_client.auth_sources.create.return_value = mock_auth_source

    result = cli_runner.invoke(
        app,
        [
            "auth-source",
            "create",
            "--name",
            "google-sso",
            "--driver",
            "google",
            "--show-on-login",
            "--button-icon",
            "bi-google",
            "--button-bg-color",
            "#4285F4",
            "--button-text-color",
            "#ffffff",
        ],
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.auth_sources.create.call_args[1]
    assert call_kwargs["menu"] is True
    assert call_kwargs["button_fa_icon"] == "bi-google"
    assert call_kwargs["button_background_color"] == "#4285F4"
    assert call_kwargs["button_color"] == "#ffffff"


def test_auth_source_update(cli_runner, mock_client, mock_auth_source):
    """Update name and settings."""
    mock_client.auth_sources.list.return_value = [mock_auth_source]
    mock_client.auth_sources.update.return_value = mock_auth_source

    result = cli_runner.invoke(
        app,
        [
            "auth-source",
            "update",
            "azure-sso",
            "--name",
            "Azure AD SSO",
            "--scope",
            "openid profile email groups",
        ],
    )

    assert result.exit_code == 0
    assert "Updated auth source" in result.output
    call_args = mock_client.auth_sources.update.call_args
    assert call_args[0][0] == 40  # key
    assert call_args[1]["name"] == "Azure AD SSO"
    assert call_args[1]["settings"]["scope"] == "openid profile email groups"


def test_auth_source_delete(cli_runner, mock_client, mock_auth_source):
    """Delete with --yes."""
    mock_client.auth_sources.list.return_value = [mock_auth_source]
    mock_client.auth_sources.get.return_value = mock_auth_source

    result = cli_runner.invoke(app, ["auth-source", "delete", "azure-sso", "--yes"])

    assert result.exit_code == 0
    assert "Deleted auth source" in result.output
    mock_client.auth_sources.delete.assert_called_once_with(40)


def test_auth_source_delete_no_confirm(cli_runner, mock_client, mock_auth_source):
    """Delete without --yes aborts."""
    mock_client.auth_sources.list.return_value = [mock_auth_source]
    mock_client.auth_sources.get.return_value = mock_auth_source

    result = cli_runner.invoke(app, ["auth-source", "delete", "azure-sso"], input="n\n")

    assert result.exit_code == 0
    mock_client.auth_sources.delete.assert_not_called()


def test_auth_source_debug_on(cli_runner, mock_client, mock_auth_source):
    """Enable debug mode."""
    mock_client.auth_sources.list.return_value = [mock_auth_source]
    mock_client.auth_sources.get.return_value = mock_auth_source

    result = cli_runner.invoke(app, ["auth-source", "debug-on", "azure-sso"])

    assert result.exit_code == 0
    assert "Debug enabled" in result.output
    assert "auto-disables after 1 hour" in result.output
    mock_auth_source.enable_debug.assert_called_once()


def test_auth_source_debug_off(cli_runner, mock_client, mock_auth_source):
    """Disable debug mode."""
    mock_client.auth_sources.list.return_value = [mock_auth_source]
    mock_client.auth_sources.get.return_value = mock_auth_source

    result = cli_runner.invoke(app, ["auth-source", "debug-off", "azure-sso"])

    assert result.exit_code == 0
    assert "Debug disabled" in result.output
    mock_auth_source.disable_debug.assert_called_once()


def test_auth_source_not_found(cli_runner, mock_client):
    """Name resolution error (exit 6)."""
    mock_client.auth_sources.list.return_value = []

    result = cli_runner.invoke(app, ["auth-source", "get", "nonexistent"])

    assert result.exit_code == 6
