---
name: fix-issue
description: Fixes a GitHub issue following project conventions with proper context gathering. Triggered when fixing an issue, resolving a bug, or implementing a feature from GitHub issues.
argument-hint: "<issue-number>"
allowed-tools: Read, Grep, Glob, Bash(git:*), Bash(gh:*), Edit, Write
---

# Fix GitHub Issue

Resolve a GitHub issue end-to-end with proper context, implementation, and PR creation.

## Arguments

- `$ARGUMENTS`: GitHub issue number
  - Example: `123`
  - Example: `#456`

## Workflow

Copy this checklist and track progress:

```
Fix Issue Progress:
- [ ] Step 1: Load issue context
- [ ] Step 2: Understand requirements
- [ ] Step 3: Explore codebase
- [ ] Step 4: Create feature branch
- [ ] Step 5: Implement the fix
- [ ] Step 6: Verify the fix
- [ ] Step 7: Commit changes
- [ ] Step 8: Create pull request
- [ ] Step 9: Link PR to issue
```

### Step 1: Load Issue Context

Fetch the issue details:
```bash
gh issue view $ARGUMENTS --comments
```

Extract from the issue:
- **Title**: What is being requested
- **Description**: Full context and requirements
- **Labels**: bug, feature, enhancement, etc.
- **Assignees**: Who's responsible
- **Comments**: Additional context, clarifications
- **Linked PRs**: Related work

### Step 2: Understand Requirements

Parse the issue to identify:

**For bugs:**
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details
- Stack traces/logs

**For features:**
- User story / use case
- Acceptance criteria
- Design constraints
- Related features

### Step 3: Explore Codebase

Find relevant code:
```bash
# Search for related files
grep -r "keyword from issue" --include="*.ts" --include="*.py"

# Find related tests
find . -name "*test*" | xargs grep "related function"
```

Identify:
- Files to modify
- Existing patterns to follow
- Tests that need updating
- Dependencies affected

### Step 4: Create Feature Branch

```bash
# Ensure main is up to date
git checkout main
git pull origin main

# Create branch following conventions
git checkout -b fix/<issue-number>-<short-description>
# or
git checkout -b feature/<issue-number>-<short-description>
```

Branch naming:
| Issue Type | Branch Prefix | Example |
|------------|---------------|---------|
| Bug | `fix/` | `fix/123-login-timeout` |
| Feature | `feature/` | `feature/456-dark-mode` |
| Refactor | `refactor/` | `refactor/789-auth-cleanup` |

### Step 5: Implement the Fix

**For bugs:**
1. Write a failing test that reproduces the bug
2. Implement the fix
3. Verify the test passes
4. Check for regressions

**For features:**
1. Review existing patterns
2. Implement following project conventions
3. Add tests for new functionality
4. Update documentation if needed

**Implementation guidelines:**
- Make minimal, focused changes
- Don't refactor unrelated code
- Follow existing code style
- Add comments for non-obvious logic

### Step 6: Verify the Fix

**Run tests:**
```bash
# JavaScript/TypeScript
npm test
pnpm test

# Python
pytest

# Go
go test ./...
```

**Run linting:**
```bash
npm run lint
pnpm lint
```

**Manual verification:**
- Test the specific scenario from the issue
- Check edge cases
- Verify no regressions

### Step 7: Commit Changes

Use the `/commit` skill or follow commit conventions:

```bash
# For bugs
git commit -m "fix: resolve <issue description> (#<issue-number>)"

# For features
git commit -m "feat: add <feature description> (#<issue-number>)"
```

Include issue reference in commit message for auto-linking.

### Step 8: Create Pull Request

Use the `/create-pr` skill or:

```bash
gh pr create --title "fix: <title> (#<issue-number>)" --body "$(cat <<'EOF'
## Summary
- Fixes #<issue-number>
- <Brief description of the fix>

## Changes
- <List of changes>

## Test Plan
- [ ] <Verification steps>
- [ ] Existing tests pass
- [ ] New tests added for the fix

## Notes
<Any additional context>
EOF
)"
```

### Step 9: Link PR to Issue

The PR should automatically link if you use:
- `Fixes #123` in the PR body (auto-closes on merge)
- `Closes #123` (same as Fixes)
- `Resolves #123` (same as Fixes)
- `Related to #123` (links without auto-close)

## Issue Resolution Checklist

Before marking complete:

- [ ] Issue requirements are fully addressed
- [ ] Code follows project conventions
- [ ] Tests added/updated
- [ ] No regressions introduced
- [ ] PR created and linked to issue
- [ ] Ready for review

## Common Patterns

### Referencing Issues in Code

```typescript
// TODO(#123): Remove this workaround after API v2 release
```

### Closing Multiple Issues

```markdown
## Summary
- Fixes #123
- Fixes #124
- Related to #100
```

### Partial Implementation

If the fix is partial:
```markdown
## Summary
- Partially addresses #123
- Completes the API changes, UI changes in separate PR

## Remaining Work
- [ ] Update frontend components
- [ ] Add integration tests
```

## Output

After completing:

1. **Issue link**: `#<number>` with title
2. **Branch**: Created branch name
3. **Changes**: Summary of modifications
4. **PR link**: URL to the created PR
5. **Status**: Ready for review / needs discussion
