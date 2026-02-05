---
name: prd
description: Creates or updates a PRD.md file for a project or feature. Triggered when documenting requirements, creating a PRD, or planning a new feature before implementation.
argument-hint: "[feature-name]"
allowed-tools: Read, Write, Glob, Grep
---

# PRD Creation

Create or update a Product Requirements Document following PRD-first development principles.

## Arguments

- `$ARGUMENTS`: Feature or project name (optional)
  - Example: `user-authentication`
  - Example: `dark-mode`
  - Empty: Create/update main PRD.md

## PRD Philosophy

The PRD is your **North Star** - the single source of truth that:
- Defines what you're building
- Prevents scope creep
- Gives AI context for every conversation
- Ensures consistency across sessions

## Workflow

Copy this checklist and track progress:

```
PRD Creation Progress:
- [ ] Step 1: Gather requirements
- [ ] Step 2: Choose PRD level
- [ ] Step 3: Generate PRD
- [ ] Step 4: Verify quality checklist
```

### Step 1: Gather Requirements

**For new projects:**
- What problem are we solving?
- Who are the users?
- What are the core features?
- What's out of scope?

**For existing projects:**
- Read existing PRD.md if present
- Identify what's being added/changed
- Understand current architecture

### Step 2: Choose PRD Level

| Level | Use Case | Location |
|-------|----------|----------|
| Project PRD | Full application | `PRD.md` |
| Feature PRD | Single feature | `docs/prd/<feature>.md` |
| Epic PRD | Group of features | `docs/prd/<epic>.md` |

### Step 3: Generate PRD

Create the PRD following the template below.

---

## PRD Template

```markdown
# PRD: <Project/Feature Name>

## Overview

### Problem Statement
<What problem are we solving? Why does it matter?>

### Goals
- <Primary goal>
- <Secondary goal>
- <Success metric>

### Non-Goals (Out of Scope)
- <Explicitly excluded feature>
- <Future consideration>

---

## User Stories

### <User Type 1>
As a <user type>, I want to <action> so that <benefit>.

**Acceptance Criteria:**
- [ ] <Criterion 1>
- [ ] <Criterion 2>
- [ ] <Criterion 3>

### <User Type 2>
As a <user type>, I want to <action> so that <benefit>.

**Acceptance Criteria:**
- [ ] <Criterion 1>
- [ ] <Criterion 2>

---

## Technical Requirements

### Architecture
<High-level architecture description or diagram>

### Tech Stack
| Component | Technology | Rationale |
|-----------|------------|-----------|
| Frontend | <tech> | <why> |
| Backend | <tech> | <why> |
| Database | <tech> | <why> |
| Auth | <tech> | <why> |

### Data Model
<Key entities and relationships>

### API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/auth/login | User authentication |
| GET | /api/users/:id | Get user profile |

### Dependencies
- <External service 1>
- <Library/package>

---

## Design

### User Flow
<Describe the main user journey>

### UI Components
- <Component 1>: <purpose>
- <Component 2>: <purpose>

### Mockups
<Link to designs or ASCII wireframes>

---

## Implementation Phases

### Phase 1: <Name>
**Goal:** <What this phase accomplishes>
**Scope:**
- [ ] <Feature/task 1>
- [ ] <Feature/task 2>
- [ ] <Feature/task 3>

### Phase 2: <Name>
**Goal:** <What this phase accomplishes>
**Scope:**
- [ ] <Feature/task 1>
- [ ] <Feature/task 2>

### Phase 3: <Name>
**Goal:** <What this phase accomplishes>
**Scope:**
- [ ] <Feature/task 1>
- [ ] <Feature/task 2>

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| <Risk 1> | High/Med/Low | High/Med/Low | <Strategy> |
| <Risk 2> | High/Med/Low | High/Med/Low | <Strategy> |

---

## Open Questions

- [ ] <Question 1>
- [ ] <Question 2>

---

## Success Criteria

- [ ] <Measurable outcome 1>
- [ ] <Measurable outcome 2>
- [ ] <Performance benchmark>

---

## Appendix

### Glossary
| Term | Definition |
|------|------------|
| <Term> | <Definition> |

### References
- <Link to related doc>
- <External resource>
```

---

## PRD Quality Checklist

Before finalizing:

- [ ] Problem statement is clear
- [ ] Goals are measurable
- [ ] Non-goals explicitly stated
- [ ] User stories have acceptance criteria
- [ ] Technical requirements are specific
- [ ] Phases are actionable
- [ ] Risks identified with mitigations
- [ ] Open questions documented

## PRD Patterns

### Feature Flag Approach
For gradual rollout:
```markdown
### Feature Flags
| Flag | Description | Default |
|------|-------------|---------|
| `ENABLE_DARK_MODE` | Enable dark mode toggle | false |
```

### Migration Considerations
For changes to existing systems:
```markdown
### Migration Plan
1. Deploy with feature flag disabled
2. Migrate data in background
3. Enable for beta users
4. Monitor and fix issues
5. Full rollout
```

### A/B Testing
For experimental features:
```markdown
### Experiment
- **Hypothesis**: <what we expect>
- **Control**: <current behavior>
- **Treatment**: <new behavior>
- **Metric**: <what we measure>
- **Duration**: <how long>
```

## Output

After creating PRD:

1. **File location**: Path to PRD.md
2. **Summary**: Key points documented
3. **Next steps**: What to do with the PRD
4. **Gaps**: Any missing information to gather
