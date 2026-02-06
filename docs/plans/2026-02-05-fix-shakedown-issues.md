# Fix Shakedown Issues #7, #9, #10, #11 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix 4 issues found during shakedown v2 testing.

**Architecture:** Minimal targeted fixes - change OData field path for status filter, add Typer enum validation for rule action, improve filter error message, remove stale docs.

**Tech Stack:** Python, Typer, pytest

---

### Task 1: Fix `--status` filter (Issue #9)

**Files:**
- Modify: `src/verge_cli/commands/vm.py:51`
- Modify: `src/verge_cli/commands/network.py:82`
- Test: `tests/unit/test_vm_status.py` (add filter test)

**Fix:** Change `machine#status#status eq '{status}'` to `status eq '{status}'` in both files.

**Verification:** `vrg vm list --status running` and `vrg network list --status running`

---

### Task 2: Fix `--action` validation (Issue #7)

**Files:**
- Modify: `src/verge_cli/commands/network_rule.py:173-174`

**Fix:** Change `--action` from free-form `str` to validated choice. Valid values: accept, drop, reject, translate, route.

**Verification:** `vrg network rule create --action block` should show Typer validation error with valid choices.

---

### Task 3: Improve `--filter` error message (Issue #10)

**Files:**
- Modify: `src/verge_cli/commands/vm.py:32-35`
- Modify: `src/verge_cli/commands/network.py:60-63`

**Fix:** Update help text to clarify OData syntax: `"OData filter expression (e.g., \"name eq 'foo'\")"`.

---

### Task 4: Remove `--fields/-f` from global options (Issue #11)

**Files:**
- Modify: `src/verge_cli/cli.py:95-102` - remove fields option
- Modify: `src/verge_cli/cli.py:171` - remove ctx.obj["fields"] assignment

---
