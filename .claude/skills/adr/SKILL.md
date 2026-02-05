---
name: adr
description: Creates, updates, or lists Architecture Decision Records in DECISIONS.md. Triggered when documenting architectural decisions, recording design choices, or reviewing project decision history.
argument-hint: "[new|update|list] [title-or-number]"
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Architecture Decision Records

Create, update, or list Architecture Decision Records (ADRs) in the project's DECISIONS.md file.

## Arguments

- `$ARGUMENTS`: Operation and optional identifier
  - `new <title>` - Create a new ADR with the given title
  - `update <number> <status>` - Update status of an existing ADR
  - `list` - List all existing ADRs with their statuses
  - Empty: Interactive mode (ask what to do)

## ADR Philosophy

ADRs are the **architectural memory** of your project:
- Document significant design decisions
- Capture the context and rationale behind choices
- Provide history for future developers and AI assistants
- Prevent relitigating past decisions without new context

## ADR Statuses

| Status | Meaning |
|--------|---------|
| **Proposed** | Under consideration, not yet decided |
| **Draft** | Work in progress, still being refined |
| **Accepted** | Decision made and in effect |
| **Rejected** | Considered but not adopted |
| **Deprecated** | Was accepted, no longer recommended |
| **Superseded** | Replaced by a newer ADR (reference the new one) |

## Workflow

Copy this checklist and track progress:

```
ADR Progress:
- [ ] Step 1: Determine operation
- [ ] Step 2: Execute operation
- [ ] Step 3: Verify changes
```

### Step 1: Determine Operation

Based on `$ARGUMENTS`, determine what the user wants:

| Input | Operation |
|-------|-----------|
| `new <title>` | Create new ADR |
| `update <number> <status>` | Update existing ADR status |
| `list` | Show all ADRs |
| Empty or unclear | Ask user what they want to do |

### Step 2: Execute Operation

#### For NEW ADRs:

1. Read existing DECISIONS.md (or note it doesn't exist)
2. Find the highest existing ADR number
3. Generate next ADR number (ADR-XXX)
4. Gather decision details:
   - **Context**: What is the issue or situation?
   - **Decision**: What was decided?
   - **Rationale**: Why was this decision made?
   - **Consequences**: What are the implications?
5. Set initial status (typically `Proposed` or `Accepted`)
6. Append new ADR to DECISIONS.md

#### For UPDATE operations:

1. Read DECISIONS.md
2. Find the specified ADR by number
3. Update the status line
4. If status is `Superseded`, ask which ADR supersedes it
5. Save changes

#### For LIST operations:

1. Read DECISIONS.md
2. Parse all ADR entries
3. Display summary table:
   ```
   | ADR | Title | Status | Date |
   |-----|-------|--------|------|
   ```

### Step 3: Verify Changes

- Confirm the operation completed
- Show the affected ADR(s)
- Suggest next steps if applicable

---

## ADR Template

When creating a new ADR, use this format:

```markdown
---

## ADR-XXX: <Title>

**Date:** <YYYY-MM-DD>

**Status:** <Proposed|Draft|Accepted|Rejected|Deprecated|Superseded>

**Context:** <What is the issue or situation that motivates this decision? What forces are at play? Include technical, business, and social context.>

**Decision:** <What is the decision that was made? State it clearly and concisely.>

**Rationale:**
- <Reason 1>
- <Reason 2>
- <Reason 3>

**Consequences:**
- <Consequence 1 - positive or negative>
- <Consequence 2>
- <Consequence 3>
```

### For Superseded ADRs

When an ADR is superseded, update the status line:

```markdown
**Status:** Superseded by ADR-XXX
```

---

## DECISIONS.md Structure

The file should have this overall structure:

```markdown
# Architecture Decision Records

This document captures key design decisions made during the development of <Project Name>.

---

## ADR-001: <First Decision>
...

---

## ADR-002: <Second Decision>
...
```

---

## Dynamic Context

### Existing ADRs
!`grep -E "^## ADR-[0-9]+" DECISIONS.md 2>/dev/null || echo "No DECISIONS.md found"`

### Current Date
!`date +%Y-%m-%d`

---

## Examples

### Create a new ADR

```
/adr new Use PostgreSQL for primary database
```

Output:
```
Created ADR-005: Use PostgreSQL for primary database

Status: Proposed
Location: DECISIONS.md

Next steps:
- Review with team
- Update status to Accepted when approved
```

### Update ADR status

```
/adr update 5 Accepted
```

Output:
```
Updated ADR-005: Use PostgreSQL for primary database

Status changed: Proposed → Accepted
```

### List all ADRs

```
/adr list
```

Output:
```
Architecture Decision Records (DECISIONS.md)

| ADR     | Title                              | Status    | Date       |
|---------|------------------------------------|-----------|------------|
| ADR-001 | Flat Package Structure             | Accepted  | 2025-01-02 |
| ADR-002 | FlexInt Type for ID Handling       | Accepted  | 2025-01-02 |
| ADR-003 | Functional Options Pattern         | Accepted  | 2025-01-02 |
| ADR-004 | Pointer Types for Optional Updates | Accepted  | 2025-01-02 |
| ADR-005 | Use PostgreSQL for primary database| Proposed  | 2025-01-15 |

Total: 5 ADRs (4 Accepted, 1 Proposed)
```

---

## Best Practices

### When to Create an ADR

Create an ADR when:
- Choosing between multiple viable approaches
- Making decisions that are hard to reverse
- Introducing new patterns or technologies
- Deviating from established conventions
- Making decisions others might question later

### When NOT to Create an ADR

Skip ADRs for:
- Trivial implementation details
- Decisions easily changed later
- Standard practices that need no justification
- Bug fixes or minor refactors

### Writing Good ADRs

**Do:**
- Be concise but complete
- Include the "why" not just the "what"
- List alternatives considered
- Be honest about trade-offs
- Date your decisions

**Don't:**
- Write novels - ADRs should be scannable
- Omit context - future readers need it
- Skip consequences - both positive and negative matter
- Forget to update status when decisions change

---

## Output

After any operation:

1. **Operation performed**: What was done
2. **ADR affected**: Number and title
3. **Current status**: The ADR's status
4. **File location**: Path to DECISIONS.md
5. **Next steps**: Suggestions if applicable
