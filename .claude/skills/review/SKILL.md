---
name: review
description: Reviews code changes for bugs, security issues, and improvements using the writer-critic pattern. Triggered when requesting code review, checking changes, or reviewing a PR.
argument-hint: "[file|PR-number|staged]"
allowed-tools: Bash(git:*), Bash(gh:*), Read, Grep, Glob
---

# Code Review

Perform thorough code review using the writer-critic pattern for reliability.

## Arguments

- `$ARGUMENTS`: What to review:
  - `staged` or empty: Review staged changes
  - `PR-number` (e.g., `123`): Review a GitHub PR
  - `file-path`: Review a specific file
  - `branch-name`: Review all changes on a branch vs main

## Review Process (Writer-Critic Pattern)

Copy this checklist and track progress:

```
Review Progress:
- [ ] Step 1: Gather the code to review
- [ ] Step 2: Understand context
- [ ] Step 3: Generate initial findings (Writer phase)
- [ ] Step 4: Validate findings (Critic phase)
- [ ] Step 5: Format and deliver review
```

### Phase 1: Writer (Initial Analysis)

1. **Gather the code**:
   - For staged: `git diff --cached`
   - For PR: `gh pr diff <number>`
   - For file: Read the file directly
   - For branch: `git diff main...<branch>`

2. **Understand context**:
   - What is this code trying to accomplish?
   - What patterns does the codebase use?
   - Are there related tests?

3. **Generate initial findings** across these categories:
   - **Security**: Vulnerabilities, injection risks, auth issues
   - **Bugs**: Logic errors, edge cases, null handling
   - **Performance**: Inefficiencies, N+1 queries, memory leaks
   - **Maintainability**: Complexity, naming, documentation
   - **Testing**: Coverage gaps, missing edge cases

### Phase 2: Critic (Validation)

For each finding from Phase 1:
1. Is this actually a problem, or a false positive?
2. Is the severity assessment accurate?
3. Is the suggested fix correct?
4. Could this break something else?

Remove or adjust findings that don't hold up to scrutiny.

## Output Format

```markdown
## Review Summary

**Scope**: <what was reviewed>
**Risk Level**: 🟢 Low | 🟡 Medium | 🔴 High

## Critical Issues
<Issues that must be fixed before merge>

### [CRITICAL] <Title>
**File**: `path/to/file.ts:42`
**Issue**: <Clear description of the problem>
**Impact**: <What could go wrong>
**Fix**:
```suggestion
<corrected code>
```

## Recommendations
<Suggested improvements, not blocking>

### [SUGGESTION] <Title>
**File**: `path/to/file.ts:100`
**Current**: <What the code does now>
**Suggested**: <What it could do better>
**Rationale**: <Why this is better>

## Security Checklist
- [ ] No hardcoded secrets or credentials
- [ ] Input validation present where needed
- [ ] No SQL/command injection vulnerabilities
- [ ] Auth/authz checks in place
- [ ] Sensitive data not logged

## Questions
<Things that need clarification from the author>
```

## Review Categories

### Security Review
Look for:
- Hardcoded secrets, API keys, passwords
- SQL injection, command injection, XSS
- Missing authentication/authorization
- Insecure data handling
- Logging of sensitive data
- OWASP Top 10 vulnerabilities

### Bug Detection
Look for:
- Off-by-one errors
- Null/undefined handling
- Race conditions
- Incorrect error handling
- Type mismatches
- Logic inversions

### Performance Review
Look for:
- N+1 query patterns
- Missing indexes (for DB queries)
- Unnecessary re-renders
- Memory leaks
- Unbounded loops
- Large payload handling

### Maintainability Review
Look for:
- Overly complex functions (cognitive load)
- Poor naming
- Missing or outdated comments
- Code duplication
- Tight coupling
- Missing error messages

## Severity Levels

| Level | Meaning | Action |
|-------|---------|--------|
| 🔴 CRITICAL | Security vuln, data loss risk, crash | Must fix |
| 🟠 HIGH | Bug affecting users, performance issue | Should fix |
| 🟡 MEDIUM | Code smell, minor bug, maintainability | Consider fixing |
| 🟢 LOW | Style, minor improvement, nitpick | Optional |

## Example Review

```markdown
## Review Summary

**Scope**: PR #123 - Add user authentication
**Risk Level**: 🟡 Medium

## Critical Issues

### [CRITICAL] SQL Injection Vulnerability
**File**: `src/auth/login.ts:45`
**Issue**: User input directly concatenated into SQL query
**Impact**: Attackers could extract or modify database contents
**Fix**:
```typescript
// Before (vulnerable)
const query = `SELECT * FROM users WHERE email = '${email}'`;

// After (safe)
const query = 'SELECT * FROM users WHERE email = $1';
const result = await db.query(query, [email]);
```

## Recommendations

### [SUGGESTION] Add rate limiting
**File**: `src/auth/login.ts`
**Current**: No rate limiting on login attempts
**Suggested**: Add rate limiting to prevent brute force attacks
**Rationale**: Industry standard security practice
```
