"""Error handling utilities for Verge CLI."""

from __future__ import annotations

import traceback
from functools import wraps
from typing import Any, Callable, ParamSpec, TypeVar

import typer
from pyvergeos.exceptions import (
    AuthenticationError,
    ConflictError,
    NotConnectedError,
    NotFoundError,
    ValidationError,
    VergeConnectionError,
    VergeError,
    VergeTimeoutError,
)
from rich.console import Console

P = ParamSpec("P")
T = TypeVar("T")


# Exit codes
class ExitCode:
    """CLI exit codes."""

    SUCCESS = 0
    GENERAL_ERROR = 1
    USAGE_ERROR = 2
    CONFIG_ERROR = 3
    AUTH_ERROR = 4
    FORBIDDEN_ERROR = 5
    NOT_FOUND_ERROR = 6
    CONFLICT_ERROR = 7
    VALIDATION_ERROR = 8
    TIMEOUT_ERROR = 9
    CONNECTION_ERROR = 10


class CliError(Exception):
    """Base exception for CLI errors with exit code."""

    exit_code: int = ExitCode.GENERAL_ERROR
    message: str = "An error occurred"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.__class__.message
        super().__init__(self.message)


class ConfigurationError(CliError):
    """Configuration-related error."""

    exit_code = ExitCode.CONFIG_ERROR
    message = "Configuration error"


class ResourceNotFoundError(CliError):
    """Resource not found error."""

    exit_code = ExitCode.NOT_FOUND_ERROR
    message = "Resource not found"


class MultipleMatchesError(CliError):
    """Multiple resources match the given identifier."""

    exit_code = ExitCode.CONFLICT_ERROR
    message = "Multiple resources match the given name"

    def __init__(self, resource_type: str, name: str, matches: list[dict[str, Any]]) -> None:
        self.resource_type = resource_type
        self.name = name
        self.matches = matches
        message = f"Multiple {resource_type}s match '{name}':\n"
        for match in matches:
            key = match.get("$key", match.get("key", "?"))
            match_name = match.get("name", "?")
            message += f"  - {match_name} (key: {key})\n"
        message += "Please specify by key or use a unique name."
        super().__init__(message)


class AuthError(CliError):
    """Authentication error."""

    exit_code = ExitCode.AUTH_ERROR
    message = "Authentication failed"


class ForbiddenError(CliError):
    """Authorization/permission error."""

    exit_code = ExitCode.FORBIDDEN_ERROR
    message = "Permission denied"


class ConflictCliError(CliError):
    """Conflict error (e.g., resource already exists)."""

    exit_code = ExitCode.CONFLICT_ERROR
    message = "Resource conflict"


class ValidationCliError(CliError):
    """Validation error."""

    exit_code = ExitCode.VALIDATION_ERROR
    message = "Validation error"


class TimeoutCliError(CliError):
    """Timeout error."""

    exit_code = ExitCode.TIMEOUT_ERROR
    message = "Operation timed out"


class ConnectionCliError(CliError):
    """Connection error."""

    exit_code = ExitCode.CONNECTION_ERROR
    message = "Connection failed"


def map_sdk_exception(exc: Exception) -> CliError:
    """Map a pyvergeos exception to a CLI error.

    Args:
        exc: pyvergeos exception.

    Returns:
        Corresponding CliError.
    """
    if isinstance(exc, AuthenticationError):
        return AuthError(str(exc))
    if isinstance(exc, NotFoundError):
        return ResourceNotFoundError(str(exc))
    if isinstance(exc, ConflictError):
        return ConflictCliError(str(exc))
    if isinstance(exc, ValidationError):
        return ValidationCliError(str(exc))
    if isinstance(exc, VergeTimeoutError):
        return TimeoutCliError(str(exc))
    if isinstance(exc, (VergeConnectionError, NotConnectedError)):
        return ConnectionCliError(str(exc))
    if isinstance(exc, VergeError):
        return CliError(str(exc))
    return CliError(str(exc))


def handle_errors(verbosity: int = 0) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator to handle errors and exit with appropriate codes.

    Args:
        verbosity: Verbosity level for error output.

    Returns:
        Decorated function.
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except typer.Exit:
                raise
            except CliError as e:
                _print_error(e.message, verbosity)
                raise typer.Exit(e.exit_code) from None
            except VergeError as e:
                cli_error = map_sdk_exception(e)
                _print_error(cli_error.message, verbosity, original=e)
                raise typer.Exit(cli_error.exit_code) from None
            except KeyboardInterrupt:
                _print_error("Operation cancelled by user", verbosity)
                raise typer.Exit(130) from None
            except Exception as e:
                _print_error(f"Unexpected error: {e}", verbosity, original=e)
                raise typer.Exit(ExitCode.GENERAL_ERROR) from None

        return wrapper

    return decorator


def _print_error(
    message: str,
    verbosity: int,
    original: Exception | None = None,
) -> None:
    """Print an error message with optional traceback.

    Args:
        message: Error message to display.
        verbosity: Verbosity level (0=minimal, 1+=show traceback).
        original: Original exception for traceback.
    """
    console = Console(stderr=True)
    console.print(f"[red]Error:[/red] {message}")

    if verbosity >= 1 and original:
        console.print("\n[dim]Traceback:[/dim]")
        console.print(traceback.format_exc())


def exit_with_error(message: str, exit_code: int = ExitCode.GENERAL_ERROR) -> None:
    """Print error and exit with code.

    Args:
        message: Error message.
        exit_code: Exit code.
    """
    console = Console(stderr=True)
    console.print(f"[red]Error:[/red] {message}")
    raise typer.Exit(exit_code)
