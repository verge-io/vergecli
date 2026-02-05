# CLAUDE.md Template

Use this template structure. Only include sections that have meaningful, project-specific content.

```markdown
# [Project Name]

> *Purpose: High-level summary of what the project is and who it serves.*

A [Language] library/application for [Target System/API], serving as the foundation for [Dependent Projects].

## Tech Stack

- **Language**: [Language & Version]
- **Package Manager**: [e.g., Go Modules, NPM, Pip]
- **Dependencies**: [Key dependencies or "Standard Lib only"]
- **Authentication**: [e.g., OAuth2, HTTP Basic, API Key]
- **Testing**: [Testing Framework]

## Project Structure

```text
[project-root]/
├── [core-logic-file]     # Main entry point or client definition
├── [config-file]         # Configuration handling
├── [error-file]          # Custom error definitions
├── [types-file]          # Shared type definitions
│
├── [module-a]/           # Service/Module A logic
├── [module-b]/           # Service/Module B logic
│
├── examples/             # Runnable code snippets
├── docs/                 # Architecture and design docs
│   ├── DECISIONS.md      # Architecture Decision Records
│   └── PRD.md            # Product Requirements
│
└── README.md             # User-facing documentation
```

## Commands

```bash
# Build
[build-command]

# Run tests
[test-command]
[test-single-command]

# Format and lint
[lint-command]

# Run examples (requires env vars)
[env-var-setup] [run-command]
```

## Reference Documentation

| Document | When to Read |
|----------|--------------|
| `docs/PRD.md` | Understanding requirements and feature scope |
| `docs/DECISIONS.md` | Understanding architectural history and design choices |
| `README.md` | Quick start guide and installation |
| `examples/` | Copy-pasteable code for common use cases |

## Architecture

### [Design Pattern Name]

All code lives in [Location]. This provides [Benefit] and follows patterns from [Reference].

### Component Design

The `[MainComponent]` manages instances of sub-services:

```[language]
client.Resource.Action(context)
```

### Key Files

- `[File A]` - Handles [Function A]
- `[File B]` - Handles [Function B]

## Code Conventions

### [Pattern Name]

Configuration uses [Pattern Description]:

```[language]
// Example code showing the pattern
```

### Error Handling

Use [Error Strategy]:

```[language]
// Example error check
```

### Naming Conventions

- `[CaseStyle]` for variables
- `[CaseStyle]` for exported types
- Filenames: `[naming-convention]`

## Adding a New Feature

### Step 0: Review Requirements

Check [Source of Truth] for coverage before writing code.

### Step 1: Create Types/Models

Create `[filename]` with definitions:

```[language]
// Example type definition
```

### Step 2: Create Logic/Service

Create `[filename]` with business logic:

```[language]
// Example function signature
```

### Step 3: Register/Export

Add to [Main Entry Point]:

```[language]
// Example registration code
```

### Step 4: Verify

Ensure:
- [Criterion A]
- [Criterion B]

## Testing Strategy

- **Location**: [e.g., Alongside code or in `tests/` folder]
- **Unit Tests**: Mock [External Dependencies]
- **Integration Tests**: Run against [Environment]
- **Coverage**: [Metric] coverage on critical paths
```
