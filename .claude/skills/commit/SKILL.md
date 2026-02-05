---
name: commit
description: Creates well-formatted git commits with conventional commit messages and emoji. Triggered when committing changes, creating a commit, or saving work to version control.
argument-hint: "[--no-verify]"
allowed-tools: Bash(git:*), Bash(pnpm:*), Bash(npm:*), Read, Grep
---

# Commit Workflow

Create well-formatted commits with conventional commit messages and emoji.

## Arguments

- `--no-verify`: Skip running pre-commit checks (lint, build, generate:docs)

## Workflow

Copy this checklist and track progress:

```
Commit Progress:
- [ ] Step 1: Pre-commit checks (or skip with --no-verify)
- [ ] Step 2: Check staged files
- [ ] Step 3: Analyze changes
- [ ] Step 4: Split if needed
- [ ] Step 5: Create commit message
- [ ] Step 6: Verify commit
```

### Step 1: Pre-commit Checks

Skip if `--no-verify` in `$ARGUMENTS`. Otherwise:
- Run `pnpm lint` to ensure code quality
- Run `pnpm build` to verify the build succeeds
- Run `pnpm generate:docs` to update documentation (if script exists)
- If checks fail, ask user whether to proceed or fix issues first

### Step 2: Check Staged Files

- Run `git status` to see what's staged
- If nothing staged, run `git add .` to stage all changes

### Step 3: Analyze Changes

- Run `git diff --cached` to understand the changes
- Determine if multiple distinct logical changes are present

### Step 4: Split if Needed

If multiple distinct changes detected (different concerns, different types, different file patterns), suggest splitting into multiple commits and help stage files separately.

### Step 5: Create Commit

Use emoji conventional commit format: `<emoji> <type>: <description>`

Run `git commit -m "<message>"` to create the commit.

### Step 6: Verify Commit

- Run `git log -1` to confirm commit was created
- Show the commit hash and message to the user
- If commit failed, report the error and suggest fixes

## Commit Types & Emoji

| Type | Emoji | Description |
|------|-------|-------------|
| feat | ✨ | New feature |
| fix | 🐛 | Bug fix |
| docs | 📝 | Documentation |
| style | 💄 | Formatting/style |
| refactor | ♻️ | Code refactoring |
| perf | ⚡️ | Performance |
| test | ✅ | Tests |
| chore | 🔧 | Tooling, config |
| ci | 🚀 | CI/CD |
| revert | ⏪️ | Reverting changes |

### Specialized Emoji

| Context | Emoji | Type |
|---------|-------|------|
| Security fix | 🔒️ | fix |
| Critical hotfix | 🚑️ | fix |
| Linter warnings | 🚨 | fix |
| Typos | ✏️ | fix |
| Remove code/files | 🔥 | fix |
| CI build | 💚 | fix |
| Breaking changes | 💥 | feat |
| Types | 🏷️ | feat |
| Accessibility | ♿️ | feat |
| Validation | 🦺 | feat |
| Analytics | 📈 | feat |
| Logs | 🔊 | feat |
| Business logic | 👔 | feat |
| UX improvements | 🚸 | feat |
| Responsive design | 📱 | feat |
| Internationalization | 🌐 | feat |
| Architecture | 🏗️ | refactor |
| Dead code removal | ⚰️ | refactor |
| Move/rename | 🚚 | refactor |
| Code comments | 💡 | docs |
| Dependencies add | ➕ | chore |
| Dependencies remove | ➖ | chore |
| gitignore | 🙈 | chore |
| Database | 🗃️ | db |
| WIP | 🚧 | wip |

## Commit Message Guidelines

- **Present tense, imperative mood**: "add feature" not "added feature"
- **Concise first line**: Under 72 characters
- **Atomic commits**: Each commit serves a single purpose

## Examples

Good commit messages:
- ✨ feat: add user authentication system
- 🐛 fix: resolve memory leak in rendering process
- 📝 docs: update API documentation with new endpoints
- ♻️ refactor: simplify error handling logic in parser
- 🔒️ fix: strengthen authentication password requirements
- 🏗️ refactor: restructure module architecture for scalability

Example split commits:
1. ✨ feat: add new solc version type definitions
2. 📝 docs: update documentation for new solc versions
3. 🔧 chore: update package.json dependencies
4. ✅ test: add unit tests for new solc version features
