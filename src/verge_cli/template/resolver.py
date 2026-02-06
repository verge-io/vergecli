"""Name-to-ID resolution using pyvergeos SDK managers."""

from __future__ import annotations

from typing import Any


def resolve_name(
    manager: Any,
    value: int | str | None,
    resource_type: str = "resource",
) -> int | None:
    """Resolve a name or ID to a resource key.

    Args:
        manager: pyvergeos resource manager (e.g., client.networks).
        value: Integer key, string name, or None.
        resource_type: Type name for error messages.

    Returns:
        Resource key (int) or None if value is None.

    Raises:
        ValueError: If name not found or multiple matches.
    """
    if value is None:
        return None

    # Int passthrough
    if isinstance(value, int):
        return value

    # Numeric string passthrough
    text = str(value).strip()
    if text.isdigit():
        return int(text)

    # Name lookup
    resources = manager.list()
    matches = [r for r in resources if getattr(r, "name", None) == text]

    if len(matches) == 1:
        return int(matches[0].key)

    if len(matches) > 1:
        keys = [str(m.key) for m in matches]
        msg = (
            f"Multiple {resource_type}s match '{text}': keys {', '.join(keys)}. "
            f"Use a numeric key to disambiguate."
        )
        raise ValueError(msg)

    msg = f"{resource_type} '{text}' not found."
    raise ValueError(msg)


def resolve_names(
    manager: Any,
    values: list[int | str],
    resource_type: str = "resource",
) -> list[int]:
    """Resolve a batch of names/IDs to resource keys.

    Calls manager.list() once and resolves all names from the cached result.

    Args:
        manager: pyvergeos resource manager.
        values: List of integer keys or string names.
        resource_type: Type name for error messages.

    Returns:
        List of resource keys (int).

    Raises:
        ValueError: If any name not found or has multiple matches.
    """
    if not values:
        return []

    # Separate ints from strings that need resolution
    needs_lookup = any(isinstance(v, str) and not str(v).strip().isdigit() for v in values)

    if not needs_lookup:
        return [int(v) if isinstance(v, str) else v for v in values]

    # Fetch all resources once
    resources = manager.list()
    name_to_keys: dict[str, list[int]] = {}
    for r in resources:
        name = getattr(r, "name", None)
        if name is not None:
            name_to_keys.setdefault(name, []).append(r.key)

    result: list[int] = []
    for v in values:
        if isinstance(v, int):
            result.append(v)
            continue

        text = str(v).strip()
        if text.isdigit():
            result.append(int(text))
            continue

        keys = name_to_keys.get(text, [])
        if len(keys) == 1:
            result.append(keys[0])
        elif len(keys) > 1:
            msg = (
                f"Multiple {resource_type}s match '{text}': keys {', '.join(str(k) for k in keys)}. "
                f"Use a numeric key to disambiguate."
            )
            raise ValueError(msg)
        else:
            msg = f"{resource_type} '{text}' not found."
            raise ValueError(msg)

    return result
