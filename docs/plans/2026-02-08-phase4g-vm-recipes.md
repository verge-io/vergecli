# Phase 4g: VM Recipes Implementation Plan

**Date:** 2026-02-08
**Status:** Draft
**Scope:** `vrg recipe` commands for VM recipe management with sections, questions, instances, and logs
**Depends on:** None (independent of NAS plans)
**Task Checklist:** Bottom of file — `tail -20` to check status

---

## Overview

Add VM recipe management for template-based VM provisioning from catalogs. Recipes define configurable VM templates with sections (grouping) and questions (configuration parameters). Users can deploy VMs from recipes by answering questions. The SDK exposes recipes via:

- `client.vm_recipes` (VmRecipeManager) — recipe CRUD + deploy
- `client.recipe_sections` (RecipeSectionManager) — section CRUD
- `client.recipe_questions` (RecipeQuestionManager) — question CRUD
- `client.vm_recipe_instances` (VmRecipeInstanceManager) — deployed instances
- `client.vm_recipe_logs` (VmRecipeLogManager) — operation logs

Recipes and instances use **integer keys**. Questions and sections also use integer keys. The `recipe_ref` parameter uses the format `"vm_recipes/{key}"`.

## Commands

### Recipes
```
vrg recipe list [--catalog CATALOG] [--downloaded]
vrg recipe get <RECIPE>
vrg recipe create --name NAME --catalog CATALOG [--description DESC] [--base-vm VM] [--base-snapshot SNAP] [--notes NOTES] [--custom-script-before SCRIPT] [--custom-script-after SCRIPT] [--enabled | --no-enabled]
vrg recipe update <RECIPE> [--name NAME] [--description DESC] [--base-vm VM] [--base-snapshot SNAP] [--notes NOTES] [--custom-script-before SCRIPT] [--custom-script-after SCRIPT] [--enabled | --no-enabled]
vrg recipe delete <RECIPE> [--yes]
vrg recipe deploy <RECIPE> --name NAME [--set KEY=VALUE]... [--auto-update]
```

### Sections
```
vrg recipe section list <RECIPE>
vrg recipe section get <RECIPE> <SECTION>
vrg recipe section create <RECIPE> --name NAME [--description DESC]
vrg recipe section update <RECIPE> <SECTION> [--name NAME] [--description DESC] [--order ORDER]
vrg recipe section delete <RECIPE> <SECTION> [--yes]
```

### Questions
```
vrg recipe question list <RECIPE> [--section SECTION]
vrg recipe question get <RECIPE> <QUESTION>
vrg recipe question create <RECIPE> --name NAME --section SECTION --type TYPE [--display DISPLAY] [--hint HINT] [--help HELP] [--note NOTE] [--default DEFAULT] [--required] [--readonly] [--min MIN] [--max MAX] [--regex REGEX] [--list-options OPTIONS]
vrg recipe question update <RECIPE> <QUESTION> [--display DISPLAY] [--hint HINT] [--help HELP] [--note NOTE] [--default DEFAULT] [--required | --no-required] [--readonly | --no-readonly] [--min MIN] [--max MAX] [--order ORDER]
vrg recipe question delete <RECIPE> <QUESTION> [--yes]
```

### Instances
```
vrg recipe instance list [--recipe RECIPE]
vrg recipe instance get <INSTANCE>
vrg recipe instance delete <INSTANCE> [--yes]
```

### Logs
```
vrg recipe log list [--recipe RECIPE]
vrg recipe log get <LOG>
```

### Command Details

#### Recipe `list`
- Options:
  - `--catalog` (str, optional) — filter by catalog name
  - `--downloaded` (flag, optional) — only show downloaded recipes
- SDK: `client.vm_recipes.list(catalog=catalog, downloaded=downloaded)`

#### Recipe `get`
- Positional: `RECIPE` (name or key)
- SDK: `client.vm_recipes.get(key=key)` or `get(name=name)`
- Uses existing `resolve_resource_id()` (integer keys)

#### Recipe `create`
- Required: `--name`, `--catalog`
- Options:
  - `--name / -n` (str, required)
  - `--catalog` (str, required) — catalog name or key
  - `--description / -d` (str, optional)
  - `--base-vm` (str, optional) — base VM name or key
  - `--base-snapshot` (str, optional) — base snapshot name or key
  - `--notes` (str, optional) — recipe notes/documentation
  - `--custom-script-before` (str, optional) — script to run before deployment
  - `--custom-script-after` (str, optional) — script to run after deployment
  - `--enabled / --no-enabled` (bool, default True)
- SDK: `client.vm_recipes.create(name=..., catalog=..., ...)`

#### Recipe `update`
- Positional: `RECIPE`
- Same options as create minus --catalog
- SDK: `client.vm_recipes.update(key, ...)`

#### Recipe `delete`
- Positional: `RECIPE`
- Options: `--yes / -y`
- SDK: `client.vm_recipes.delete(key)`

#### Recipe `deploy`
- Positional: `RECIPE` (name or key)
- Options:
  - `--name / -n` (str, required) — name for the deployed VM
  - `--set` (list of KEY=VALUE, optional, multiple) — answers to recipe questions (e.g., `--set YB_CPU_CORES=2 --set YB_RAM=4096`)
  - `--auto-update` (flag, default False) — auto-update when recipe is updated
- SDK: `client.vm_recipes.deploy(key, name=name, answers=answers_dict, auto_update=auto_update)`
- The `--set` values are parsed into a dict: `{"KEY": "VALUE", ...}`
- Returns the created VmRecipeInstance

#### Section `list`
- Positional: `RECIPE`
- SDK: `client.recipe_sections.list(recipe_ref=f"vm_recipes/{recipe_key}")`

#### Section `get`
- Positional: `RECIPE`, `SECTION` (name or key)
- SDK: `client.recipe_sections.get(key=key)` or `get(name=name)`

#### Section `create`
- Positional: `RECIPE`
- Required: `--name`
- Options:
  - `--name / -n` (str, required) — section name
  - `--description / -d` (str, optional)
- SDK: `client.recipe_sections.create(name=..., recipe_ref=f"vm_recipes/{recipe_key}", description=...)`

#### Section `update`
- Positional: `RECIPE`, `SECTION`
- Options: `--name`, `--description`, `--order` (int, optional — display order)
- SDK: `client.recipe_sections.update(key, name=..., description=..., orderid=...)`

#### Section `delete`
- Positional: `RECIPE`, `SECTION`
- Options: `--yes / -y`
- SDK: `client.recipe_sections.delete(key)` — cascades to questions in section

#### Question `list`
- Positional: `RECIPE`
- Options: `--section` (str, optional) — filter by section name or key
- SDK: `client.recipe_questions.list(recipe_ref=f"vm_recipes/{recipe_key}", section=section_key, enabled=True)`

#### Question `get`
- Positional: `RECIPE`, `QUESTION` (name or key)
- SDK: `client.recipe_questions.get(key=key)` or `get(name=name)`

#### Question `create`
- Positional: `RECIPE`
- Required: `--name`, `--section`, `--type`
- Options:
  - `--name / -n` (str, required) — variable name (convention: YB_*, SELECT_*, or custom)
  - `--section` (str, required) — section name or key
  - `--type` (str, required) — question type: string, bool, num, password, list, text_area, hidden, ram, disk_size, cluster, network, row_selection
  - `--display` (str, optional) — UI label
  - `--hint` (str, optional) — placeholder text
  - `--help` (str, optional) — tooltip text
  - `--note` (str, optional) — below-field text
  - `--default` (str, optional) — default value
  - `--required` (flag, default False)
  - `--readonly` (flag, default False)
  - `--min` (int, optional) — minimum for numeric types
  - `--max` (int, optional) — maximum for numeric types
  - `--regex` (str, optional) — validation pattern
  - `--list-options` (str, optional) — comma-separated key=value pairs for list type (e.g., "small=Small,medium=Medium,large=Large")
- SDK: `client.recipe_questions.create(name=..., recipe_ref=f"vm_recipes/{recipe_key}", section=section_key, question_type=type, ...)`

#### Question `update`
- Positional: `RECIPE`, `QUESTION`
- Options: `--display`, `--hint`, `--help`, `--note`, `--default`, `--required / --no-required`, `--readonly / --no-readonly`, `--min`, `--max`, `--order` (int)
- SDK: `client.recipe_questions.update(key, ...)`

#### Question `delete`
- Positional: `RECIPE`, `QUESTION`
- Options: `--yes / -y`
- SDK: `client.recipe_questions.delete(key)`

#### Instance `list`
- Options: `--recipe` (str, optional) — filter by recipe name or key
- SDK: `client.vm_recipe_instances.list(recipe=recipe_key)`

#### Instance `get`
- Positional: `INSTANCE` (name or key)
- SDK: `client.vm_recipe_instances.get(key=key)` or `get(name=name)`

#### Instance `delete`
- Positional: `INSTANCE`
- Options: `--yes / -y` — removes instance tracking only, not the VM
- SDK: `client.vm_recipe_instances.delete(key)`

#### Log `list`
- Options: `--recipe` (str, optional) — filter by recipe
- SDK: `client.vm_recipe_logs.list(recipe=recipe_key)`

#### Log `get`
- Positional: `LOG` (key)
- SDK: `client.vm_recipe_logs.get(key=key)`

## Files

### New Files

1. **`src/verge_cli/commands/recipe.py`**
   - Helpers: `_recipe_to_dict()`, `_parse_set_args()` (parse KEY=VALUE pairs into dict)
   - Commands: list, get, create, update, delete, deploy

2. **`src/verge_cli/commands/recipe_section.py`**
   - Helpers: `_section_to_dict()`, `_resolve_recipe()` (resolve recipe positional arg to key)
   - Commands: list, get, create, update, delete

3. **`src/verge_cli/commands/recipe_question.py`**
   - Helpers: `_question_to_dict()`, `_parse_list_options()` (parse "key=val,key=val" into dict)
   - Commands: list, get, create, update, delete

4. **`src/verge_cli/commands/recipe_instance.py`**
   - Helpers: `_instance_to_dict()`
   - Commands: list, get, delete

5. **`src/verge_cli/commands/recipe_log.py`**
   - Helpers: `_log_to_dict()`
   - Commands: list, get

6. **`tests/unit/test_recipe.py`** — recipe tests
7. **`tests/unit/test_recipe_section.py`** — section tests
8. **`tests/unit/test_recipe_question.py`** — question tests
9. **`tests/unit/test_recipe_instance.py`** — instance tests
10. **`tests/unit/test_recipe_log.py`** — log tests

### Modified Files

11. **`src/verge_cli/cli.py`**
    - Add: `from verge_cli.commands import recipe`
    - Add: `app.add_typer(recipe.app, name="recipe")`

12. **`tests/conftest.py`**
    - Add fixtures: `mock_recipe`, `mock_recipe_section`, `mock_recipe_question`, `mock_recipe_instance`, `mock_recipe_log`

## Column Definitions

```python
# In recipe.py
RECIPE_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("description", wide_only=True),
    ColumnDef("enabled", format_fn=format_bool_yn, style_map={"Yes": "green", "No": "red"}),
    ColumnDef("notes", wide_only=True),
]

# In recipe_section.py
RECIPE_SECTION_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("description"),
    ColumnDef("orderid", header="Order"),
]

# In recipe_question.py
RECIPE_QUESTION_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("display", header="Label"),
    ColumnDef("type"),
    ColumnDef("required", format_fn=format_bool_yn),
    ColumnDef("default", wide_only=True),
    ColumnDef("hint", wide_only=True),
]

# In recipe_instance.py
RECIPE_INSTANCE_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("recipe_name", header="Recipe"),
    ColumnDef("auto_update", header="Auto Update", format_fn=format_bool_yn, wide_only=True),
]

# In recipe_log.py
RECIPE_LOG_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef("action"),
    ColumnDef("status"),
    ColumnDef("created", format_fn=format_epoch),
    ColumnDef("message", wide_only=True),
]
```

## Data Mapping

```python
def _recipe_to_dict(recipe: Any) -> dict[str, Any]:
    return {
        "$key": recipe.key,
        "name": recipe.name,
        "description": recipe.get("description", ""),
        "enabled": recipe.get("enabled"),
        "notes": recipe.get("notes", ""),
    }

def _section_to_dict(section: Any) -> dict[str, Any]:
    return {
        "$key": section.key,
        "name": section.name,
        "description": section.get("description", ""),
        "orderid": section.get("orderid"),
    }

def _question_to_dict(question: Any) -> dict[str, Any]:
    return {
        "$key": question.key,
        "name": question.name,
        "display": question.get("display", ""),
        "type": question.get("type"),
        "required": question.get("required"),
        "default": question.get("default", ""),
        "hint": question.get("hint", ""),
    }

def _instance_to_dict(inst: Any) -> dict[str, Any]:
    return {
        "$key": inst.key,
        "name": inst.name,
        "recipe_name": inst.get("recipe_name", ""),
        "auto_update": inst.get("auto_update"),
    }

def _log_to_dict(log: Any) -> dict[str, Any]:
    return {
        "$key": log.key,
        "action": log.get("action", ""),
        "status": log.get("status", ""),
        "created": log.get("created"),
        "message": log.get("message", ""),
    }
```

## Test Plan

| # | Test | Validates |
|---|------|-----------|
| 1 | `test_recipe_list` | Lists all recipes |
| 2 | `test_recipe_list_downloaded` | Filter by --downloaded |
| 3 | `test_recipe_get` | Get by name |
| 4 | `test_recipe_create` | Create with required args |
| 5 | `test_recipe_update` | Update description and notes |
| 6 | `test_recipe_delete` | Delete with --yes |
| 7 | `test_recipe_deploy` | Deploy with --name and --set KEY=VALUE |
| 8 | `test_recipe_deploy_with_auto_update` | Deploy with --auto-update |
| 9 | `test_section_list` | List sections for a recipe |
| 10 | `test_section_get` | Get section by name |
| 11 | `test_section_create` | Create section with name and description |
| 12 | `test_section_update` | Update section order |
| 13 | `test_section_delete` | Delete section (cascades to questions) |
| 14 | `test_question_list` | List questions for a recipe |
| 15 | `test_question_list_by_section` | Filter by --section |
| 16 | `test_question_get` | Get question by name |
| 17 | `test_question_create` | Create with name, section, type |
| 18 | `test_question_create_with_list_options` | Create list-type with --list-options |
| 19 | `test_question_update` | Update display and default |
| 20 | `test_question_delete` | Delete question |
| 21 | `test_instance_list` | List deployed instances |
| 22 | `test_instance_get` | Get instance details |
| 23 | `test_instance_delete` | Delete instance tracking |
| 24 | `test_log_list` | List recipe logs |
| 25 | `test_log_get` | Get log details |
| 26 | `test_recipe_not_found` | Recipe resolution error (exit 6) |
| 27 | `test_parse_set_args` | Parse KEY=VALUE pairs into dict |

## Task Checklist

- [ ] Create `src/verge_cli/commands/recipe.py` with recipe commands + deploy
- [ ] Create `src/verge_cli/commands/recipe_section.py` with section commands
- [ ] Create `src/verge_cli/commands/recipe_question.py` with question commands
- [ ] Create `src/verge_cli/commands/recipe_instance.py` with instance commands
- [ ] Create `src/verge_cli/commands/recipe_log.py` with log commands
- [ ] Register `recipe` typer in `cli.py` with section/question/instance/log sub-typers
- [ ] Add fixtures to `conftest.py`
- [ ] Create all 5 test files
- [ ] Run `uv run ruff check` and `uv run mypy src/verge_cli`
- [ ] Run `uv run pytest tests/unit/test_recipe*.py -v`

## Notes

- Recipes use **integer keys** — use existing `resolve_resource_id()`
- The `recipe_ref` parameter uses format `"vm_recipes/{key}"` — construct this in the CLI
- `--set KEY=VALUE` parsing: split on first `=` to handle values containing `=`
- `--list-options` parsing: split on commas, then each item on `=` to build `{value: display}` dict
- Section delete cascades to all questions in that section
- Instance delete only removes tracking — the deployed VM is NOT deleted
- Common recipe question variable names: YB_CPU_CORES, YB_RAM, YB_HOSTNAME, YB_IP_ADDR_TYPE, YB_USER, YB_PASSWORD
- Question types include specialized UI types (ram, disk_size, cluster, network, row_selection) that map to specific input widgets in the VergeOS UI
- This plan covers both VM recipes and their sub-resources. Tenant recipes (`client.tenant_recipes`) are structurally identical but out of scope for Phase 4.
