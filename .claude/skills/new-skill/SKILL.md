---
name: new-skill
description: Creates a new Claude Code skill with proper structure and best practices. Triggered when creating custom skills, adding new commands, or extending Claude's capabilities.
argument-hint: "<skill-name> [description]"
allowed-tools: Read, Write, Glob, WebFetch
---

# Create New Skill

Create a new Claude Code skill with proper structure following the Agent Skills standard.

## Arguments

- `$ARGUMENTS`: Skill name and optional description
  - Example: `my-skill A skill that does something useful`
  - Example: `deploy` (description will be gathered interactively)

## Skill Structure

Every skill needs:
```
.claude/skills/<skill-name>/
└── SKILL.md           # Main instructions (required)
```

Optional supporting files:
```
.claude/skills/<skill-name>/
├── SKILL.md           # Main instructions
├── template.md        # Templates for Claude to fill
├── examples/          # Example outputs
└── scripts/           # Executable scripts
```

## Workflow

Copy this checklist and track progress:

```
Skill Creation:
- [ ] Step 1: Parse arguments
- [ ] Step 2: Fetch latest best practices
- [ ] Step 3: Determine skill type
- [ ] Step 4: Configure options
- [ ] Step 5: Generate SKILL.md
- [ ] Step 6: Create directory and file
- [ ] Step 7: Validate creation
- [ ] Step 8: Validate against best practices
```

### Step 1: Parse Arguments

Extract from `$ARGUMENTS`:
- **Skill name**: First word (lowercase, hyphens only)
- **Description**: Remaining text (if provided)

If no description provided, ask the user:
1. What does this skill do?
2. When should it be used?

### Step 2: Fetch Latest Best Practices

Fetch the official Anthropic documentation to ensure you have current guidance for all subsequent decisions:

1. **Fetch best practices guide:**
   - URL: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
   - Extract: Core quality checklist, naming conventions, anti-patterns

2. **Fetch Claude Code skills reference:**
   - URL: https://code.claude.com/docs/en/skills
   - Extract: Frontmatter requirements, invocation control patterns

3. **Note key requirements** from the docs to apply throughout:
   - Description format and voice
   - Naming conventions
   - Line count limits
   - Example structure

### Step 3: Determine Skill Type

Ask the user which type:

| Type | Auto-Invoke | Use Case |
|------|-------------|----------|
| **Standard** (default) | Yes | Most skills - can be invoked via `/command` or natural language |
| **Manual-only** | No | Dangerous operations where accidental invocation could cause harm |
| **Reference** | Claude-only | Background knowledge that shouldn't appear in `/` menu |

### Step 4: Configure Options

Based on skill type, determine:

**For Standard skills (recommended):**
- No `disable-model-invocation` needed (default allows both)
- Which tools does it need? (Read, Write, Bash, etc.)

**For Manual-only skills:**
- `disable-model-invocation: true` (only `/command` works, natural language won't trigger)
- Use sparingly - only for truly dangerous operations

**For Reference skills:**
- `user-invocable: false` (hidden from `/` menu, Claude can still use)
- Usually read-only tools

**For specialized execution:**
- `context: fork` for isolated subagent execution
- `agent: Explore` for read-only research
- `agent: Plan` for planning tasks

### Step 5: Generate SKILL.md

Create the skill file with this structure:

```markdown
---
name: <skill-name>
description: <Description in third-person>. Triggered when <trigger conditions>.
argument-hint: "<argument-format>"
allowed-tools: <tool-list>
---

# <Skill Title>

<One-line description of what this skill does>

## Arguments

- `$ARGUMENTS`: <description of expected input>

## Workflow

### Step 1: <Name>
<Instructions>

### Step 2: <Name>
<Instructions>

## Output Format

<Expected output structure or example>

## Examples

<Example invocations and results>
```

### Step 6: Create Directory and File

1. Create `.claude/skills/<skill-name>/` directory
2. Write the SKILL.md file

### Step 7: Validate Creation

Verify the skill was created correctly:

1. Confirm the file exists at `.claude/skills/<skill-name>/SKILL.md`
2. Read the file back to verify content was written
3. Check that frontmatter is valid (name, description present)
4. Report success to user with:
   - Skill location
   - How to invoke (`/<skill-name>`)
   - Suggestion to customize if needed

### Step 8: Validate Against Best Practices

Validate the generated skill against the guidance fetched in Step 2:

1. **Check against requirements:**
   - [ ] Description is specific with trigger conditions (not vague like "helps with X")
   - [ ] Description uses third-person voice ("Creates..." not "Create...")
   - [ ] SKILL.md body under 500 lines
   - [ ] `name` field: lowercase, numbers, hyphens only, max 64 chars
   - [ ] No reserved words in name ("anthropic", "claude")
   - [ ] Examples are concrete (input/output pairs preferred)
   - [ ] `disable-model-invocation` only used for dangerous operations
   - [ ] Consistent terminology throughout

2. **Report validation results:**
   - List items that pass
   - Flag items that need attention with specific suggestions
   - Recommend improvements based on the fetched official guidance

## Frontmatter Reference

| Field | Required | Description |
|-------|----------|-------------|
| `name` | No | Defaults to directory name (max 64 chars, lowercase/numbers/hyphens only, no "anthropic" or "claude") |
| `description` | Yes | When/why to use (max 1024 chars, third-person voice, include trigger conditions) |
| `argument-hint` | No | Shows expected arguments |
| `disable-model-invocation` | No | `true` = manual only |
| `user-invocable` | No | `false` = Claude-only |
| `allowed-tools` | No | Restrict available tools |
| `context` | No | `fork` = isolated subagent |
| `agent` | No | `Explore`, `Plan`, `general-purpose` |

## Best Practices

**Official documentation** (fetched live in Step 2):
- [Skill Authoring Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Claude Code Skills Reference](https://code.claude.com/docs/en/skills)

### Do:
- Keep SKILL.md under 500 lines - use reference files for details
- Write descriptions in third-person voice ("Creates..." not "Create...")
- Include trigger conditions in descriptions for auto-invocation
- Provide concrete examples with input/output pairs
- Use gerund naming: `processing-pdfs` not `pdf-processor`
- Reference supporting files instead of inlining everything

### Don't:
- Make descriptions too generic (triggers too often)
- Put 1000+ lines in SKILL.md
- Use `disable-model-invocation: true` unless truly necessary (blocks natural language invocation)
- Forget to specify allowed-tools for sensitive operations

## Common Tool Patterns

```yaml
# Read-only exploration
allowed-tools: Read, Grep, Glob

# Git operations
allowed-tools: Bash(git:*), Read, Grep

# GitHub CLI
allowed-tools: Bash(git:*), Bash(gh:*)

# Full bash access (use sparingly)
allowed-tools: Bash(*)

# File modification
allowed-tools: Read, Write, Edit, Grep, Glob
```

## Dynamic Context

Skills can inject dynamic content using `!`command``:

```markdown
## Current Branch
!`git branch --show-current`

## Recent Commits
!`git log --oneline -5`
```

Commands execute before Claude sees the skill content.

## Example Output

After running `/new-skill lint Check code for style issues`:

```
Created new skill: lint

Location: .claude/skills/lint/SKILL.md

Skill configuration:
- Type: Task (manual invocation only)
- Tools: Read, Grep, Glob, Bash(npm:*), Bash(pnpm:*)

You can now use /lint to invoke this skill.
Edit .claude/skills/lint/SKILL.md to customize the workflow.
```
