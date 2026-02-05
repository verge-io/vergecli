---
name: create-pr
description: Creates a GitHub pull request with a well-structured summary and test plan. Triggered when opening a PR, creating a pull request, or submitting changes for review.
argument-hint: "[base-branch]"
allowed-tools: Bash(git:*), Bash(gh:*)
---

# Create Pull Request

Create a GitHub pull request with a comprehensive summary and test plan.

## Arguments

- `$ARGUMENTS`: Optional base branch (defaults to `main` or `master`)

## Workflow

Copy this checklist and track progress:

```
PR Creation Progress:
- [ ] Step 1: Gather context
- [ ] Step 2: Validate state
- [ ] Step 3: Analyze all commits
- [ ] Step 4: Generate PR content
- [ ] Step 5: Push and create PR
- [ ] Step 6: Verify PR creation
```

### Step 1: Gather Context

Run in parallel:
- `git status` - Check for uncommitted changes
- `git branch --show-current` - Get current branch name
- `git log main..HEAD --oneline` - See all commits to include
- `git diff main...HEAD` - See full diff against base branch

### Step 2: Validate State

- If uncommitted changes exist, ask user if they want to commit first
- If on main/master branch, stop and ask user to create a feature branch
- If no commits ahead of base, inform user there's nothing to PR

### Step 3: Analyze ALL Commits

- Review every commit in the branch, not just the latest
- Understand the full scope of changes
- Identify the type of change (feature, fix, refactor, etc.)

### Step 4: Generate PR Content

**Title**: Concise, descriptive title following pattern:
- `feat: <description>` for features
- `fix: <description>` for bug fixes
- `refactor: <description>` for refactoring
- `docs: <description>` for documentation

**Body structure**:
```markdown
## Summary
<2-4 bullet points explaining what changed and why>

## Changes
<List of specific changes organized by area>

## Test Plan
- [ ] <Specific test steps>
- [ ] <Edge cases to verify>
- [ ] <Regression checks>

## Notes
<Any additional context, breaking changes, or migration notes>
```

### Step 5: Push and Create PR

- Push branch with `-u` flag if not tracking remote
- Create PR using `gh pr create`

### Step 6: Verify PR Creation

- Confirm PR was created successfully
- Run `gh pr view --web` to open in browser (or show the PR URL)
- Report the PR number and URL to the user
- If creation failed, report the error and suggest fixes

## PR Quality Guidelines

### Summary Section
- Focus on **why**, not just what
- Mention the problem being solved
- Keep it scannable (bullet points)

### Test Plan Section
- Include specific steps to verify the change
- List edge cases that were considered
- Note any automated tests added
- Mention manual testing performed

### What NOT to Include
- Implementation details that are obvious from the diff
- Obvious statements ("updated the code")
- Time estimates

## Example Output

```markdown
## Summary
- Add rate limiting to the API to prevent abuse
- Implement token bucket algorithm with configurable limits
- Add monitoring metrics for rate limit hits

## Changes
**API Layer**
- Add `RateLimiter` middleware to all authenticated endpoints
- Configure 100 requests/minute default limit

**Infrastructure**
- Add Redis dependency for distributed rate limiting
- Update deployment config with Redis connection

**Monitoring**
- Add `api.rate_limit.exceeded` metric
- Create Grafana dashboard for rate limit monitoring

## Test Plan
- [ ] Verify rate limiting kicks in after 100 requests
- [ ] Confirm rate limit resets after 1 minute
- [ ] Test distributed limiting across multiple instances
- [ ] Verify existing tests still pass
- [ ] Load test to confirm performance impact is minimal

## Notes
- Breaking: Clients may need to handle 429 responses
- Redis is now a required dependency for API servers
```

## Commands Used

```bash
# Check remote tracking
git rev-parse --abbrev-ref --symbolic-full-name @{u}

# Push with tracking
git push -u origin <branch-name>

# Create PR
gh pr create --title "<title>" --body "<body>"
```
