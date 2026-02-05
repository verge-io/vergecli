---
name: initialize
description: Creates or improves a project CLAUDE.md file by analyzing the codebase structure, tech stack, and conventions. Triggered when initializing Claude Code for a new project, setting up AI context, or improving existing CLAUDE.md files.
argument-hint: "[--improve]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Initialize Project CLAUDE.md

Analyze a codebase and create a comprehensive CLAUDE.md file for future Claude Code sessions.

## Arguments

- `$ARGUMENTS`: Optional flags
  - `--improve` - Analyze and suggest improvements to existing CLAUDE.md
  - (no args) - Create new CLAUDE.md or improve existing one

## Workflow

Copy this checklist and track progress:

```
Initialize Progress:
- [ ] Step 1: Check for existing CLAUDE.md
- [ ] Step 2: Gather codebase context
- [ ] Step 3: Analyze tech stack
- [ ] Step 4: Extract commands
- [ ] Step 5: Identify architecture patterns
- [ ] Step 6: Document conventions
- [ ] Step 7: Generate CLAUDE.md
- [ ] Step 8: Verify output
```

### Step 1: Check for Existing CLAUDE.md

Look for existing `CLAUDE.md` in the project root.

**Important:** Do NOT modify `.claude/CLAUDE.md` - this is a centrally maintained file from the shared config.

If root `CLAUDE.md` exists, switch to improvement mode: analyze gaps and suggest additions rather than replacing.

### Step 2: Gather Codebase Context

**Required reads:**
- `README.md` - Project overview, setup instructions
- `package.json` / `go.mod` / `Cargo.toml` / `pyproject.toml` / `requirements.txt`

**Check for AI rules from other tools:**
- `.cursor/rules/` or `.cursorrules` - Cursor AI rules
- `.github/copilot-instructions.md` - GitHub Copilot rules

**Check for documentation:**
- `docs/PRD.md` - Product requirements
- `docs/DECISIONS.md` or `DECISIONS.md` - Architecture decisions
- `CONTRIBUTING.md` - Contribution guidelines

### Step 3: Analyze Tech Stack

Identify from package manifests:
- Language & Version
- Package Manager (npm/pnpm/yarn, go modules, pip/poetry, cargo)
- Framework (React, Next.js, FastAPI, Gin, etc.)
- Testing Framework
- Key Dependencies (database clients, auth libraries)

### Step 4: Extract Commands

Find commands from:
- `package.json` scripts
- `Makefile` targets
- `justfile` recipes
- CI/CD configs (`.github/workflows/`, `.gitlab-ci.yml`)
- README.md "Getting Started" sections

Focus on: build, test (all), test (single), lint/format, run/start

### Step 5: Identify Architecture Patterns

```bash
tree -L 3 -d --noreport 2>/dev/null || find . -type d -maxdepth 3 | head -50
```

Answer:
- Where does business logic live?
- How are API routes/handlers organized?
- Where are shared types defined?
- What pattern for dependency injection/configuration?

### Step 6: Document Conventions

Extract from:
- ESLint/Prettier/EditorConfig files
- Sample 2-3 representative files
- Sample test files
- Cursor/Copilot rules if present

Focus on **project-specific** conventions, not generic best practices.

### Step 7: Generate CLAUDE.md

See [TEMPLATE.md](TEMPLATE.md) for the exact structure to follow.

Only include sections that have meaningful, project-specific content.

### Step 8: Verify Output

1. **Check for redundancy**: Remove sections that duplicate README.md verbatim
2. **Check for generics**: Remove placeholder text or generic advice
3. **Check for value**: Each section must contain project-specific information
4. **Check length**: Comprehensive but not bloated

## Important Rules

**DO:**
- Extract actual commands from package.json/Makefile
- Include real file paths and patterns from the codebase
- Focus on "big picture" architecture requiring multiple files to understand
- Include important rules from Cursor/Copilot configs if present
- Summarize key README.md content relevant for development

**DO NOT:**
- Repeat yourself across sections
- Include obvious instructions ("Write tests", "Handle errors gracefully")
- List every file/component that's easily discoverable
- Include generic development practices
- Make up information not found in actual project files
- Add filler sections like "Tips for Development"

## Output Format

After completion, report:

```
Created CLAUDE.md for [Project Name]

Tech Stack: [Language] / [Framework] / [Key Tools]

Sections included:
- Tech Stack
- Project Structure
- Commands
- [Other sections with actual content]

Sources analyzed:
- README.md
- package.json
- [Other files read]

Next steps:
- Review the generated CLAUDE.md for accuracy
- Add any team-specific conventions not captured
- Consider adding a docs/PRD.md for requirements
```

## Improvement Mode

If existing CLAUDE.md found, analyze and suggest:

1. **Missing sections**: What valuable information is absent?
2. **Outdated info**: Do commands/paths still match the codebase?
3. **Generic content**: What could be made more specific?
4. **Redundancy**: What repeats other documentation unnecessarily?

Present suggestions as a diff or bulleted list of recommended changes.
