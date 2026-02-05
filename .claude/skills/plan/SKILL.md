---
name: plan
description: Creates a detailed implementation plan for a feature or task. Triggered when planning a feature, designing an approach, or thinking through implementation before coding.
argument-hint: "<feature-description>"
context: fork
agent: Plan
allowed-tools: Read, Grep, Glob, Bash(git:*), Bash(tree:*)
---

# Implementation Planning

Create a detailed implementation plan following the context reset pattern for optimal execution.

## Arguments

- `$ARGUMENTS`: Description of the feature or task to plan

## Why Planning Matters

Context window degradation leads to "lazy" coding and mistakes. By separating **planning** from **execution**:
- Planning session: Explore, research, design (can get messy)
- Execution session: Fresh context, clear instructions (focused)

## Planning Workflow

Copy this checklist and track progress:

```
Planning Progress:
- [ ] Phase 1: Research & Discovery
- [ ] Phase 2: Design
- [ ] Phase 3: Implementation Plan
- [ ] Save plan to .claude/plans/<feature-name>.md
- [ ] Verify plan is complete and actionable
```

### Phase 1: Research & Discovery

1. **Understand the codebase**:
   - Find related existing code
   - Identify patterns and conventions used
   - Locate tests for similar features
   - Note dependencies and constraints

2. **Clarify requirements**:
   - What exactly needs to be built?
   - What are the acceptance criteria?
   - What are the edge cases?
   - What are the non-functional requirements?

3. **Identify risks**:
   - What could go wrong?
   - What's the blast radius of changes?
   - Are there breaking changes?

### Phase 2: Design

1. **Architecture decisions**:
   - Where does this code belong?
   - What new files/modules are needed?
   - How does it integrate with existing code?

2. **Interface design**:
   - What are the inputs and outputs?
   - What's the API contract?
   - How will this be used?

3. **Data flow**:
   - How does data move through the system?
   - What transformations happen?
   - Where is state managed?

### Phase 3: Implementation Plan

Create a step-by-step plan with:
- **Ordered tasks**: What to do in what sequence
- **File changes**: Which files to create/modify
- **Dependencies**: What must be done before what
- **Test strategy**: How to verify each step

## Output Format

Save the plan to `.claude/plans/<feature-name>.md`:

```markdown
# Plan: <Feature Name>

## Overview
<2-3 sentence summary of what we're building>

## Requirements
- [ ] <Requirement 1>
- [ ] <Requirement 2>
- [ ] <Requirement 3>

## Research Findings

### Existing Patterns
<What patterns the codebase uses that we should follow>

### Related Code
- `path/to/file.ts` - <Why it's relevant>
- `path/to/other.ts` - <Why it's relevant>

### Dependencies
<External libraries or internal modules we'll use>

## Architecture

### New Files
- `src/feature/index.ts` - <Purpose>
- `src/feature/types.ts` - <Purpose>

### Modified Files
- `src/routes/index.ts` - <What changes>

### Data Flow
```
Input → Validation → Processing → Storage → Response
```

## Implementation Steps

### Step 1: <Name>
**Files**: `file1.ts`, `file2.ts`
**Description**: <What to do>
**Acceptance**: <How to verify it works>

### Step 2: <Name>
**Files**: `file3.ts`
**Description**: <What to do>
**Acceptance**: <How to verify it works>

### Step 3: Tests
**Files**: `__tests__/feature.test.ts`
**Description**: <Test coverage plan>

## Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| <Risk> | Low/Med/High | Low/Med/High | <How to handle> |

## Open Questions
- [ ] <Question that needs answering>

## Estimated Scope
- Files to create: X
- Files to modify: Y
- Tests to write: Z
```

## After Planning

Once the plan is complete:
1. **Save the plan** to `.claude/plans/<feature-name>.md`
2. **Start a fresh session** (context reset)
3. **Execute with**: "Implement the plan in `.claude/plans/<feature-name>.md`"

This ensures the execution session has maximum context for clean implementation.

## Tips for Good Plans

- **Be specific**: "Add validation" is bad. "Add email format validation using regex in `validateUser` function" is good.
- **Order matters**: Tasks should be in dependency order
- **Include acceptance criteria**: How do you know each step is done?
- **Note the non-obvious**: Document gotchas and edge cases
- **Keep it executable**: Someone should be able to follow the plan step by step
