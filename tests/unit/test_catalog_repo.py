"""Tests for catalog repository commands."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from verge_cli.cli import app

if TYPE_CHECKING:
    from typer.testing import CliRunner


class TestCatalogRepoList:
    """Tests for vrg catalog repo list."""

    def test_repo_list(
        self,
        cli_runner: CliRunner,
        mock_client: MagicMock,
        mock_catalog_repo: MagicMock,
    ) -> None:
        """List catalog repositories."""
        mock_client.catalog_repositories.list.return_value = [mock_catalog_repo]

        result = cli_runner.invoke(app, ["catalog", "repo", "list"])

        assert result.exit_code == 0
        assert "test-repo" in result.output
        mock_client.catalog_repositories.list.assert_called_once()

    def test_repo_list_by_type(
        self,
        cli_runner: CliRunner,
        mock_client: MagicMock,
        mock_catalog_repo: MagicMock,
    ) -> None:
        """List repositories filtered by type."""
        mock_client.catalog_repositories.list.return_value = [mock_catalog_repo]

        result = cli_runner.invoke(app, ["catalog", "repo", "list", "--type", "remote"])

        assert result.exit_code == 0
        mock_client.catalog_repositories.list.assert_called_once_with(type="remote")

    def test_repo_list_enabled(
        self,
        cli_runner: CliRunner,
        mock_client: MagicMock,
        mock_catalog_repo: MagicMock,
    ) -> None:
        """List repositories filtered by enabled state."""
        mock_client.catalog_repositories.list.return_value = [mock_catalog_repo]

        result = cli_runner.invoke(app, ["catalog", "repo", "list", "--enabled"])

        assert result.exit_code == 0
        mock_client.catalog_repositories.list.assert_called_once_with(enabled=True)


class TestCatalogRepoGet:
    """Tests for vrg catalog repo get."""

    def test_repo_get_by_key(
        self,
        cli_runner: CliRunner,
        mock_client: MagicMock,
        mock_catalog_repo: MagicMock,
    ) -> None:
        """Get repository by numeric key."""
        mock_client.catalog_repositories.get.return_value = mock_catalog_repo

        result = cli_runner.invoke(app, ["catalog", "repo", "get", "1"])

        assert result.exit_code == 0
        assert "test-repo" in result.output
        mock_client.catalog_repositories.get.assert_called_once_with(key=1)

    def test_repo_get_by_name(
        self,
        cli_runner: CliRunner,
        mock_client: MagicMock,
        mock_catalog_repo: MagicMock,
    ) -> None:
        """Get repository by name (resolve)."""
        mock_client.catalog_repositories.list.return_value = [mock_catalog_repo]
        mock_client.catalog_repositories.get.return_value = mock_catalog_repo

        result = cli_runner.invoke(app, ["catalog", "repo", "get", "test-repo"])

        assert result.exit_code == 0
        assert "test-repo" in result.output


class TestCatalogRepoCreate:
    """Tests for vrg catalog repo create."""

    def test_repo_create_local(
        self,
        cli_runner: CliRunner,
        mock_client: MagicMock,
        mock_catalog_repo: MagicMock,
    ) -> None:
        """Create a local repository."""
        mock_client.catalog_repositories.create.return_value = mock_catalog_repo

        result = cli_runner.invoke(
            app,
            ["catalog", "repo", "create", "--name", "test-repo"],
        )

        assert result.exit_code == 0
        mock_client.catalog_repositories.create.assert_called_once_with(
            name="test-repo",
            type="local",
            auto_refresh=True,
            max_tier="1",
            override_default_scope="none",
        )

    def test_repo_create_remote(
        self,
        cli_runner: CliRunner,
        mock_client: MagicMock,
        mock_catalog_repo: MagicMock,
    ) -> None:
        """Create a remote repository with URL/user/password."""
        mock_client.catalog_repositories.create.return_value = mock_catalog_repo

        result = cli_runner.invoke(
            app,
            [
                "catalog",
                "repo",
                "create",
                "--name",
                "remote-repo",
                "--type",
                "remote",
                "--url",
                "https://recipes.example.com/api",
                "--user",
                "api-user",
                "--password",
                "api-key",
            ],
        )

        assert result.exit_code == 0
        mock_client.catalog_repositories.create.assert_called_once_with(
            name="remote-repo",
            type="remote",
            auto_refresh=True,
            max_tier="1",
            override_default_scope="none",
            url="https://recipes.example.com/api",
            user="api-user",
            password="api-key",
        )


class TestCatalogRepoUpdate:
    """Tests for vrg catalog repo update."""

    def test_repo_update(
        self,
        cli_runner: CliRunner,
        mock_client: MagicMock,
        mock_catalog_repo: MagicMock,
    ) -> None:
        """Update repository description and URL."""
        mock_client.catalog_repositories.get.return_value = mock_catalog_repo
        mock_client.catalog_repositories.update.return_value = mock_catalog_repo

        result = cli_runner.invoke(
            app,
            [
                "catalog",
                "repo",
                "update",
                "1",
                "--description",
                "Updated description",
                "--url",
                "https://new-url.example.com",
            ],
        )

        assert result.exit_code == 0
        mock_client.catalog_repositories.update.assert_called_once_with(
            1,
            description="Updated description",
            url="https://new-url.example.com",
        )


class TestCatalogRepoDelete:
    """Tests for vrg catalog repo delete."""

    def test_repo_delete_confirm(
        self,
        cli_runner: CliRunner,
        mock_client: MagicMock,
        mock_catalog_repo: MagicMock,
    ) -> None:
        """Delete repository with --yes."""
        mock_client.catalog_repositories.get.return_value = mock_catalog_repo

        result = cli_runner.invoke(
            app,
            ["catalog", "repo", "delete", "1", "--yes"],
        )

        assert result.exit_code == 0
        mock_client.catalog_repositories.delete.assert_called_once_with(1)

    def test_repo_delete_no_confirm(
        self,
        cli_runner: CliRunner,
        mock_client: MagicMock,
        mock_catalog_repo: MagicMock,
    ) -> None:
        """Delete repository without --yes aborts."""
        mock_client.catalog_repositories.get.return_value = mock_catalog_repo

        result = cli_runner.invoke(
            app,
            ["catalog", "repo", "delete", "1"],
            input="n\n",
        )

        assert result.exit_code != 0
        mock_client.catalog_repositories.delete.assert_not_called()


class TestCatalogRepoRefresh:
    """Tests for vrg catalog repo refresh."""

    def test_repo_refresh(
        self,
        cli_runner: CliRunner,
        mock_client: MagicMock,
        mock_catalog_repo: MagicMock,
    ) -> None:
        """Trigger repository refresh."""
        mock_client.catalog_repositories.get.return_value = mock_catalog_repo
        mock_client.catalog_repositories.refresh.return_value = None

        result = cli_runner.invoke(app, ["catalog", "repo", "refresh", "1"])

        assert result.exit_code == 0
        assert "refresh initiated" in result.output.lower()
        mock_client.catalog_repositories.refresh.assert_called_once_with(1)


class TestCatalogRepoStatus:
    """Tests for vrg catalog repo status."""

    def test_repo_status(
        self,
        cli_runner: CliRunner,
        mock_client: MagicMock,
        mock_catalog_repo: MagicMock,
        mock_catalog_repo_status: MagicMock,
    ) -> None:
        """Show repository status."""
        mock_client.catalog_repositories.get.return_value = mock_catalog_repo
        mock_client.catalog_repositories.get_status.return_value = mock_catalog_repo_status

        result = cli_runner.invoke(app, ["catalog", "repo", "status", "1"])

        assert result.exit_code == 0
        assert "online" in result.output
        mock_client.catalog_repositories.get_status.assert_called_once_with(1)


class TestCatalogRepoErrors:
    """Tests for error handling."""

    def test_repo_not_found(
        self,
        cli_runner: CliRunner,
        mock_client: MagicMock,
    ) -> None:
        """Name resolution error (exit 6)."""
        mock_client.catalog_repositories.list.return_value = []

        result = cli_runner.invoke(app, ["catalog", "repo", "get", "nonexistent"])

        assert result.exit_code == 6
