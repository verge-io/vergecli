"""YAML template loading with variable substitution and --set overrides."""

from __future__ import annotations

import os
import re

import yaml

# Match ${VAR} or ${VAR:-default}
_VAR_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-(.*?))?\}")


def substitute_variables(text: str, variables: dict[str, str]) -> str:
    """Substitute ${VAR} and ${VAR:-default} in text.

    Args:
        text: Raw text with variable references.
        variables: Variable name->value mapping.

    Returns:
        Text with variables substituted.

    Raises:
        ValueError: If a required variable (no default) is missing.
    """
    missing: list[str] = []

    def replacer(match: re.Match[str]) -> str:
        var_name = match.group(1)
        default = match.group(2)

        if var_name in variables:
            return variables[var_name]
        if default is not None:
            return default

        missing.append(var_name)
        return match.group(0)

    result = _VAR_PATTERN.sub(replacer, text)

    if missing:
        msg = f"Unresolved template variables: {', '.join(missing)}"
        raise ValueError(msg)

    return result


def apply_set_overrides(data: dict, overrides: list[str]) -> None:  # type: ignore[type-arg]
    """Apply --set dot-path overrides to parsed data (in-place).

    Args:
        data: Parsed template dict.
        overrides: List of 'dot.path=value' strings.

    Raises:
        ValueError: If override format is invalid.
    """
    for override in overrides:
        if "=" not in override:
            msg = f"Invalid --set format: '{override}'. Expected 'key.path=value'."
            raise ValueError(msg)

        path, value = override.split("=", 1)
        parts = path.split(".")

        # Navigate to parent, creating intermediate dicts as needed
        target = data
        for part in parts[:-1]:
            if part not in target or not isinstance(target[part], dict):
                target[part] = {}
            target = target[part]

        target[parts[-1]] = value


def _extract_vars_block(text: str) -> dict[str, str]:
    """Quick-parse YAML to extract just the vars: block.

    Args:
        text: Raw YAML text.

    Returns:
        Dict of variable definitions.
    """
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError:
        return {}

    if isinstance(data, dict) and "vars" in data:
        vars_block = data["vars"]
        if isinstance(vars_block, dict):
            return {k: str(v) for k, v in vars_block.items()}

    return {}


def load_template(
    path: str,
    set_overrides: list[str] | None = None,
    env_vars: dict[str, str] | None = None,
) -> dict:  # type: ignore[type-arg]
    """Load a .vrg.yaml template with variable substitution and overrides.

    Processing pipeline:
    1. Read raw YAML text
    2. Extract vars: block (pass 1)
    3. Merge with environment variables (env wins)
    4. Substitute ${VAR} references (pass 2)
    5. Full YAML parse (pass 3)
    6. Apply --set overrides
    7. Return parsed dict

    Args:
        path: Path to .vrg.yaml file.
        set_overrides: List of 'key.path=value' overrides.
        env_vars: Environment variable overrides (defaults to os.environ).

    Returns:
        Parsed and processed template dict.

    Raises:
        FileNotFoundError: If template file doesn't exist.
        ValueError: If variables can't be resolved.
        yaml.YAMLError: If YAML is malformed.
    """
    with open(path) as f:
        raw_text = f.read()

    # Pass 1: extract vars block
    template_vars = _extract_vars_block(raw_text)

    # Merge with env vars (env takes precedence)
    effective_env = env_vars if env_vars is not None else dict(os.environ)
    combined_vars = {**template_vars, **effective_env}

    # Pass 2: substitute variables
    substituted_text = substitute_variables(raw_text, combined_vars)

    # Pass 3: full YAML parse
    data = yaml.safe_load(substituted_text)

    if not isinstance(data, dict):
        msg = "Template must be a YAML mapping at the top level."
        raise ValueError(msg)

    # Remove vars block from output (consumed)
    data.pop("vars", None)

    # Apply --set overrides
    if set_overrides:
        apply_set_overrides(data, set_overrides)

    return data
