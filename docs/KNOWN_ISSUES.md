# Known Issues

Issues to fix before MVP release.

## Fixed

### 1. `--query` fails on list commands

**Severity:** Medium
**Found:** 2026-02-04
**Fixed:** 2026-02-04

**Description:**
Using `--query` with list commands (e.g., `vrg vm list --query name`) caused an error:
```
Error: Unexpected error: 'str' object has no attribute 'get'
```

**Root Cause:**
In `output.py`, `extract_field()` returns a list of strings when extracting a field from a list of dicts. Then `format_table()` tries to call `.get()` on those strings.

**Fix Applied:**
In `output_result()`, detect when query result is a simple list of values (not dicts) and print as newline-separated values instead of trying to format as a table.

---

### 2. Numeric VM names interpreted as keys

**Severity:** Low
**Found:** 2026-02-04
**Fixed:** 2026-02-04

**Description:**
VMs with numeric names (e.g., "123") could not be referenced by name - the resolver treated them as keys.

```bash
vrg vm get 123  # Was looking for key=123, not name="123"
```

**Root Cause:**
In `utils.py`, `resolve_resource_id()` returned early if `identifier.isdigit()`.

**Fix Applied:**
Changed `resolve_resource_id()` to always search by name first. If no name match is found AND the identifier is numeric, it falls back to treating it as a key. This allows both numeric names and numeric keys to work correctly.

---

### 3. No update/edit command for VM devices

**Severity:** Low
**Found:** 2026-02-06
**Fixed:** 2026-02-10

**Description:**
`vrg vm device` supported `list`, `get`, `create`, and `delete` but had no `update` command. Device properties (name, enabled, settings) could not be modified after creation.

**Root Cause:**
The CLI command was never implemented, though the pyvergeos SDK supported `devices.update()` all along.

**Fix Applied:**
Added `vrg vm device update <VM> <DEVICE>` command with options: `--name`, `--description`, `--enabled/--no-enabled`, `--optional/--no-optional`, `--model`, `--version`.

---

### 4. `recipe create` missing `--version` option

**Severity:** Medium
**Found:** 2026-02-08
**Fixed:** 2026-02-10

**Description:**
`vrg recipe create` failed with an API validation error because the CLI did not expose a `--version` option:
```
Error: field 'vm_recipes.version' is required
```

**Root Cause:**
The `--version` option was present on the `update` command but was omitted from `create`.

**Fix Applied:**
Added required `--version` option to the `create` command in `recipe.py`.
