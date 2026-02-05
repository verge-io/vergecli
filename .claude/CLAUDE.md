# Verge Development Conventions

You are assisting Verge developers. Follow these principles and conventions.

## Core Principles

### Code Quality
- Write clear, readable code over clever code
- Use meaningful names that reveal intent
- Keep functions small and focused (single responsibility)
- Don't swallow errors silently - handle or propagate them
- Separate concerns - UI, business logic, and data access should be distinct

### Testing
- Write tests that document expected behavior
- Test edge cases and error conditions
- Prefer integration tests for critical paths
- Unit test complex logic in isolation

### Security
- Never commit secrets, keys, or credentials
- Validate all external input
- Use parameterized queries for databases
- Apply principle of least privilege

### Performance
- Measure before optimizing
- Avoid premature optimization
- Be mindful of N+1 query patterns
- Consider bundle size for frontend code

## Code Style Preferences

### General
- Use TypeScript for type safety when available
- Prefer `const` over `let`, avoid `var`
- Use async/await over raw promises
- Prefer early returns to reduce nesting

### Naming
- `camelCase` for variables and functions
- `PascalCase` for classes and components
- `SCREAMING_SNAKE_CASE` for constants
- Prefix booleans with `is`, `has`, `can`, `should`

### Imports
- Use path aliases (`@/`) when configured
- Group imports: external, internal, relative
- Avoid barrel files in large projects

## Git Conventions

### Commits
- Use conventional commit format with emoji (see `/commit`)
- Keep commits atomic - one logical change per commit
- Write commit messages in imperative mood

### Branches
- `main` - production-ready code
- `feature/<name>` - new features
- `fix/<name>` - bug fixes
- `refactor/<name>` - code improvements

### Pull Requests
- Include summary, changes list, and test plan
- Reference related issues
- Keep PRs focused and reviewable

## Project Structure Conventions

### Frontend (React/Next.js)
```
src/
├── components/     # Reusable UI components
├── pages/          # Route components
├── hooks/          # Custom React hooks
├── utils/          # Pure utility functions
├── services/       # API and external services
└── types/          # TypeScript types
```

### Backend (Node/API)
```
src/
├── routes/         # HTTP route handlers
├── services/       # Business logic
├── models/         # Data models/entities
├── middleware/     # Request middleware
├── utils/          # Utility functions
└── types/          # TypeScript types
```

## MCP Servers

The following MCP servers are available for use:

| Server | Purpose |
|--------|---------|
| **Marvin** | Internal Verge documentation and knowledge base. Use for company-specific docs, APIs, and processes. |
| **Context7** | Up-to-date library and framework documentation. Use when you need current docs for external dependencies. |
| **Sentry** | Production error tracking. Use for debugging production issues, viewing stack traces, and error context. |

## When You're Unsure

1. Look at existing code for patterns
2. Ask clarifying questions
3. Prefer consistency with the codebase
4. Document decisions in comments if non-obvious

## What NOT to Do

- Don't add dependencies without justification
- Don't refactor unrelated code in a feature PR
- Don't leave `console.log` statements
- Don't ignore TypeScript errors with `any`
- Don't skip tests for "simple" changes
