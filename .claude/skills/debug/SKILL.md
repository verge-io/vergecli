---
name: debug
description: Debugs issues systematically with hypothesis testing and audit logging. Triggered when encountering a bug, error, unexpected behavior, or troubleshooting problems.
argument-hint: "<issue-description>"
allowed-tools: Read, Grep, Glob, Bash(*)
---

# Systematic Debugging

Debug issues using a structured hypothesis-driven approach with audit trail.

## Arguments

- `$ARGUMENTS`: Description of the issue
  - Example: `Login button not responding after form submission`
  - Example: `TypeError: Cannot read property 'map' of undefined in Dashboard`

## Debugging Workflow

Copy this checklist and track progress:

```
Debug Progress:
- [ ] Phase 1: Gather evidence
- [ ] Phase 2: Form hypotheses
- [ ] Phase 3: Test hypotheses
- [ ] Phase 4: Root cause analysis
- [ ] Phase 5: Implement fix
- [ ] Phase 6: Document (audit log)
```

### Phase 1: Gather Evidence

**1. Understand the symptom:**
- What is the expected behavior?
- What is the actual behavior?
- When did it start happening?
- Is it reproducible? How?

**2. Collect error information:**
```bash
# Check recent logs
tail -100 logs/app.log | grep -i error

# Check git history for recent changes
git log --oneline -10
git diff HEAD~5..HEAD --stat
```

**3. Identify the blast radius:**
- Which files/modules are involved?
- What are the dependencies?
- Who else might be affected?

### Phase 2: Form Hypotheses

Create ranked hypotheses based on evidence:

```markdown
## Hypotheses

| # | Hypothesis | Likelihood | Evidence |
|---|------------|------------|----------|
| 1 | <most likely cause> | High | <supporting evidence> |
| 2 | <second possibility> | Medium | <supporting evidence> |
| 3 | <less likely cause> | Low | <supporting evidence> |
```

**Common bug categories:**
- **Data issues**: Null/undefined, wrong type, missing field
- **State issues**: Race condition, stale state, incorrect order
- **Integration issues**: API contract change, version mismatch
- **Logic issues**: Off-by-one, wrong condition, missing case
- **Environment issues**: Config difference, missing dependency

### Phase 3: Test Hypotheses

For each hypothesis (starting with most likely):

**1. Design a test:**
- What would prove/disprove this hypothesis?
- What's the minimal reproduction?

**2. Execute the test:**
- Add logging/breakpoints if needed
- Run the specific scenario
- Observe the result

**3. Record the outcome:**
```markdown
### Hypothesis 1: <description>
**Test**: <what you did>
**Result**: Confirmed / Refuted
**Evidence**: <what you observed>
```

### Phase 4: Root Cause Analysis

Once the bug is found:

**1. Trace the root cause:**
- Why did this happen?
- Why wasn't it caught earlier?
- Are there similar issues elsewhere?

**2. Document the chain:**
```
Symptom: Login button unresponsive
  └─ Immediate cause: Click handler not attached
      └─ Root cause: useEffect missing dependency
          └─ Contributing factor: No lint rule for exhaustive-deps
```

### Phase 5: Implement Fix

**1. Write the fix:**
- Make the minimal change to fix the issue
- Don't refactor unrelated code

**2. Verify the fix:**
- Does it solve the original problem?
- Are there any regressions?
- Do existing tests still pass?

**3. Add a test:**
- Write a test that would have caught this bug
- Ensure it fails without the fix

### Phase 6: Document (Audit Log)

Create a debug log entry:

```markdown
## Debug Log: <Issue Title>

**Date**: <date>
**Duration**: <time spent>
**Severity**: Critical / High / Medium / Low

### Summary
<One paragraph description of the bug and fix>

### Symptom
<What was observed>

### Root Cause
<Why it happened>

### Fix
<What was changed>
**Files modified:**
- `path/to/file.ts:42` - <change description>

### Prevention
<How to prevent similar bugs>
- [ ] Add lint rule
- [ ] Add test coverage
- [ ] Update documentation

### Lessons Learned
<What we learned from this bug>
```

## Debug Techniques

### Binary Search (Git Bisect)

For regressions, use git bisect:
```bash
git bisect start
git bisect bad HEAD
git bisect good <known-good-commit>
# Test each commit until the culprit is found
```

### Divide and Conquer

1. Identify the data flow path
2. Add logging at midpoint
3. Determine which half has the bug
4. Repeat until isolated

### Rubber Duck Debugging

Explain the code line by line:
- What should this line do?
- What does it actually do?
- Are those the same?

### Diff Debugging

Compare working vs broken:
- Different environments?
- Different inputs?
- Different timing?

## Common Gotchas by Language

### JavaScript/TypeScript
- `undefined` vs `null` handling
- Async/await missing
- `this` binding lost
- Array mutation vs new array
- Object reference vs value

### Python
- Mutable default arguments
- Import cycle
- Indentation issues
- `is` vs `==`
- Generator exhaustion

### Go
- Nil pointer dereference
- Goroutine leak
- Channel deadlock
- Interface nil check
- Deferred function arguments

## Output

After debugging, provide:

1. **Bug summary**: One-line description
2. **Root cause**: Why it happened
3. **Fix location**: File and line
4. **Fix description**: What to change
5. **Test suggestion**: How to prevent regression
