"""Tests for webhook commands."""

from __future__ import annotations

from unittest.mock import MagicMock

from typer.testing import CliRunner

from verge_cli.cli import app


def test_webhook_list(
    cli_runner: CliRunner, mock_client: MagicMock, mock_webhook: MagicMock
) -> None:
    """Test listing webhooks."""
    mock_client.webhooks.list.return_value = [mock_webhook]

    result = cli_runner.invoke(app, ["webhook", "list"])

    assert result.exit_code == 0
    assert "my-webhook" in result.output
    assert "example.com" in result.output
    mock_client.webhooks.list.assert_called_once_with()


def test_webhook_list_with_auth_type(
    cli_runner: CliRunner, mock_client: MagicMock, mock_webhook: MagicMock
) -> None:
    """Test listing webhooks filtered by auth type."""
    mock_client.webhooks.list.return_value = [mock_webhook]

    result = cli_runner.invoke(app, ["webhook", "list", "--auth-type", "bearer"])

    assert result.exit_code == 0
    mock_client.webhooks.list.assert_called_once_with(auth_type="bearer")


def test_webhook_get_by_name(
    cli_runner: CliRunner, mock_client: MagicMock, mock_webhook: MagicMock
) -> None:
    """Test getting a webhook by name."""
    mock_client.webhooks.list.return_value = [mock_webhook]
    mock_client.webhooks.get.return_value = mock_webhook

    result = cli_runner.invoke(app, ["webhook", "get", "my-webhook"])

    assert result.exit_code == 0
    assert "my-webhook" in result.output


def test_webhook_get_by_key(
    cli_runner: CliRunner, mock_client: MagicMock, mock_webhook: MagicMock
) -> None:
    """Test getting a webhook by numeric key."""
    mock_client.webhooks.list.return_value = []
    mock_client.webhooks.get.return_value = mock_webhook

    result = cli_runner.invoke(app, ["webhook", "get", "10"])

    assert result.exit_code == 0
    assert "my-webhook" in result.output


def test_webhook_create(cli_runner: CliRunner, mock_client: MagicMock) -> None:
    """Test creating a webhook."""
    mock_result = MagicMock()
    mock_result.key = 11
    mock_client.webhooks.create.return_value = mock_result

    result = cli_runner.invoke(
        app,
        ["webhook", "create", "--name", "test-hook", "--url", "https://example.com/hook"],
    )

    assert result.exit_code == 0
    assert "created" in result.output.lower()
    mock_client.webhooks.create.assert_called_once_with(
        name="test-hook", url="https://example.com/hook"
    )


def test_webhook_create_with_all_options(cli_runner: CliRunner, mock_client: MagicMock) -> None:
    """Test creating a webhook with all options."""
    mock_result = MagicMock()
    mock_result.key = 12
    mock_client.webhooks.create.return_value = mock_result

    result = cli_runner.invoke(
        app,
        [
            "webhook",
            "create",
            "--name",
            "full-hook",
            "--url",
            "https://example.com/hook",
            "--auth-type",
            "bearer",
            "--auth-value",
            "my-token",
            "--header",
            "X-Custom:value1",
            "--header",
            "X-Other:value2",
            "--allow-insecure",
            "--timeout",
            "10",
            "--retries",
            "5",
        ],
    )

    assert result.exit_code == 0
    mock_client.webhooks.create.assert_called_once_with(
        name="full-hook",
        url="https://example.com/hook",
        auth_type="bearer",
        auth_value="my-token",
        headers={"X-Custom": "value1", "X-Other": "value2"},
        allow_insecure=True,
        timeout=10,
        retries=5,
    )


def test_webhook_update(
    cli_runner: CliRunner, mock_client: MagicMock, mock_webhook: MagicMock
) -> None:
    """Test updating a webhook."""
    mock_client.webhooks.list.return_value = [mock_webhook]
    mock_client.webhooks.update.return_value = None

    result = cli_runner.invoke(
        app,
        ["webhook", "update", "my-webhook", "--url", "https://new.example.com/hook"],
    )

    assert result.exit_code == 0
    assert "updated" in result.output.lower()


def test_webhook_delete(
    cli_runner: CliRunner, mock_client: MagicMock, mock_webhook: MagicMock
) -> None:
    """Test deleting a webhook with --yes."""
    mock_client.webhooks.list.return_value = [mock_webhook]
    mock_client.webhooks.delete.return_value = None

    result = cli_runner.invoke(app, ["webhook", "delete", "my-webhook", "--yes"])

    assert result.exit_code == 0
    assert "deleted" in result.output.lower()
    mock_client.webhooks.delete.assert_called_once_with(10)


def test_webhook_send(
    cli_runner: CliRunner, mock_client: MagicMock, mock_webhook: MagicMock
) -> None:
    """Test sending a message to a webhook."""
    mock_client.webhooks.list.return_value = [mock_webhook]
    mock_client.webhooks.send.return_value = None

    result = cli_runner.invoke(
        app,
        ["webhook", "send", "my-webhook", "--message", '{"test": true}'],
    )

    assert result.exit_code == 0
    assert "sent" in result.output.lower()
    mock_client.webhooks.send.assert_called_once_with(10, message='{"test": true}')


def test_webhook_history(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_webhook_history: MagicMock,
) -> None:
    """Test listing webhook delivery history."""
    mock_client.webhooks.history.return_value = [mock_webhook_history]

    result = cli_runner.invoke(app, ["webhook", "history"])

    assert result.exit_code == 0
    assert "Sent" in result.output
    mock_client.webhooks.history.assert_called_once_with()


def test_webhook_history_with_webhook_filter(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_webhook: MagicMock,
    mock_webhook_history: MagicMock,
) -> None:
    """Test webhook history filtered by webhook."""
    mock_client.webhooks.list.return_value = [mock_webhook]
    mock_client.webhooks.history.return_value = [mock_webhook_history]

    result = cli_runner.invoke(app, ["webhook", "history", "--webhook", "my-webhook"])

    assert result.exit_code == 0
    mock_client.webhooks.history.assert_called_once_with(webhook_key=10)


def test_webhook_history_pending(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_webhook_history: MagicMock,
) -> None:
    """Test webhook history with pending filter."""
    mock_client.webhooks.history.return_value = [mock_webhook_history]

    result = cli_runner.invoke(app, ["webhook", "history", "--pending"])

    assert result.exit_code == 0
    mock_client.webhooks.history.assert_called_once_with(pending=True)


def test_webhook_history_failed(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_webhook_history: MagicMock,
) -> None:
    """Test webhook history with failed filter."""
    mock_client.webhooks.history.return_value = [mock_webhook_history]

    result = cli_runner.invoke(app, ["webhook", "history", "--failed"])

    assert result.exit_code == 0
    mock_client.webhooks.history.assert_called_once_with(failed=True)
