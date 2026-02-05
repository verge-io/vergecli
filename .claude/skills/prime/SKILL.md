---
name: prime
description: Primes the session with project context, PRD, and codebase structure. Triggered at the start of a coding session or when context seems lost.
argument-hint: "[--full]"
allowed-tools: Read, Glob, Bash(tree:*), Bash(git:*)
---

# Session Priming

Establish project context for an effective coding session.

## Dynamic Context

### Project Structure
!`tree -L 2 -I 'node_modules|.git|dist|build|coverage|__pycache__|.next|.cache' 2>/dev/null || find . -maxdepth 2 -type d | head -50`

### Git Status
!`git branch --show-current 2>/dev/null && git log --oneline -5 2>/dev/null`

### Package Info
!`cat package.json 2>/dev/null | head -30 || cat Cargo.toml 2>/dev/null | head -30 || cat pyproject.toml 2>/dev/null | head -30 || cat go.mod 2>/dev/null | head -10 || echo "No package manifest found"`

## Priming Workflow

Copy this checklist and track progress:

```
Priming Progress:
- [ ] Step 1: Load core documents
- [ ] Step 2: Understand tech stack
- [ ] Step 3: Identify conventions
- [ ] Step 4: Check current state
- [ ] Step 5: Provide session summary
```

### Step 1: Load Core Documents

Check for and read these files if they exist:
1. `CLAUDE.md` - Root project AI instructions
2. `.claude/CLAUDE.md` - Additional AI conventions and guidelines
3. `PRD.md` or `docs/PRD.md` - Product requirements
4. `DECISIONS.md` or `docs/DECISIONS.md` - Architecture decision records
5. `README.md` - Project overview
6. `.claude/plans/*.md` - Active implementation plans

### Step 2: Understand Tech Stack

Based on package manifest, identify:
- **Language/Runtime**: Node.js, Python, Rust, Go, etc.
- **Framework**: React, Next.js, FastAPI, etc.
- **Key Dependencies**: Database, auth, testing frameworks
- **Build Tools**: Bundler, test runner, linter

### Step 3: Identify Conventions

Look for and note:
- **Code Style**: ESLint/Prettier config, `.editorconfig`
- **Testing Pattern**: Test file locations, naming conventions
- **Project Structure**: Where different types of code live

### Step 4: Check Current State

- **Git branch**: What are we working on?
- **Recent commits**: What was recently changed?
- **Uncommitted changes**: Is there work in progress?

## Output Summary

After priming, provide a brief summary:

```markdown
## Session Context

**Project**: <name>
**Stack**: <language/framework>
**Branch**: <current branch>
**Status**: <clean/dirty with uncommitted changes>

### Key Files Loaded
- <CLAUDE.md status>
- <.claude/CLAUDE.md status>
- <PRD.md status>
- <DECISIONS.md status>
- <Active plans>

### Project Structure
<Brief overview of main directories>

### Ready to Work On
<Based on PRD, plans, or recent commits, what's the current focus?>

### Conventions Noted
- <Testing pattern>
- <Import style>
- <Any project-specific rules>
```

## When to Use /prime

- **Session start**: Always prime at the beginning
- **Context drift**: When responses seem to forget project details
- **After breaks**: Returning after time away
- **New features**: Before starting something new

## Quick Prime vs Full Prime

### Quick Prime (default)
Loads structure and key docs, provides summary.

### Full Prime (`/prime --full`)
Additionally reads:
- Test examples
- API route structure
- Database schema (if available)
- CI/CD configuration

Use full prime when working on complex features that touch many parts of the codebase.
