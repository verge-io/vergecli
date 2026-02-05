---
name: refactor
description: Analyzes code for refactoring opportunities and implements improvements safely. Triggered when improving code quality, reducing complexity, or cleaning up technical debt.
argument-hint: "[file-or-directory]"
allowed-tools: Read, Grep, Glob, Edit, Write, Bash(npm:*), Bash(pnpm:*), Bash(pytest:*), Bash(go:*)
---

# Code Refactoring

Analyze and refactor code following best practices with safety checks.

## Arguments

- `$ARGUMENTS`: Target for refactoring (optional)
  - File path: `src/utils/parser.ts`
  - Directory: `src/components/`
  - Empty: Analyze recent changes or prompt for target

## Refactoring Workflow

Copy this checklist and track progress:

```
Refactoring Progress:
- [ ] Phase 1: Analysis (identify code smells)
- [ ] Phase 2: Validation (verify tests exist)
- [ ] Phase 3: Plan refactoring steps
- [ ] Phase 4: Execute refactoring
- [ ] Phase 5: Verify (tests pass, code works)
```

### Phase 1: Analysis (Writer)

**1. Read the target code:**
- Understand what the code does
- Identify the code's responsibilities
- Note dependencies and consumers

**2. Detect code smells:**

| Smell | Indicators | Severity |
|-------|------------|----------|
| Long function | >50 lines, many responsibilities | High |
| Deep nesting | >3 levels of indentation | High |
| Duplicate code | Similar blocks in multiple places | Medium |
| Large class | >300 lines, too many methods | Medium |
| Long parameter list | >4 parameters | Medium |
| Feature envy | Method uses other class's data heavily | Medium |
| Dead code | Unreachable or unused code | Low |
| Magic numbers | Unexplained literals | Low |

**3. Assess complexity:**
- Cyclomatic complexity
- Cognitive complexity
- Coupling and cohesion

### Phase 2: Validation (Critic)

Before refactoring, verify:

- [ ] Tests exist for this code
- [ ] All tests currently pass
- [ ] No breaking changes to public API
- [ ] Refactoring is worth the effort

**If no tests exist:** Write tests first before refactoring.

### Phase 3: Plan Refactoring

Create a refactoring plan with small, incremental steps:

```markdown
## Refactoring Plan: <target>

### Step 1: <Refactoring Name>
- **Pattern**: Extract Method / Rename / Move / etc.
- **Before**: <current state>
- **After**: <desired state>
- **Risk**: Low / Medium / High

### Step 2: ...
```

**Key principle:** Each step should leave code in a working state.

### Phase 4: Execute Refactoring

Apply refactoring patterns one at a time:

#### Extract Method
```typescript
// Before
function processOrder(order) {
  // 20 lines of validation
  // 30 lines of calculation
  // 15 lines of notification
}

// After
function processOrder(order) {
  validateOrder(order);
  const total = calculateTotal(order);
  notifyCustomer(order, total);
}
```

#### Rename for Clarity
```typescript
// Before
const d = new Date();
const x = users.filter(u => u.a);

// After
const currentDate = new Date();
const activeUsers = users.filter(user => user.isActive);
```

#### Simplify Conditionals
```typescript
// Before
if (user !== null && user !== undefined && user.isActive === true) {
  if (user.role === 'admin' || user.role === 'superadmin') {
    // ...
  }
}

// After
if (user?.isActive && isAdminRole(user.role)) {
  // ...
}
```

#### Replace Magic Numbers
```typescript
// Before
if (password.length < 8) { ... }
setTimeout(callback, 300000);

// After
const MIN_PASSWORD_LENGTH = 8;
const SESSION_TIMEOUT_MS = 5 * 60 * 1000; // 5 minutes

if (password.length < MIN_PASSWORD_LENGTH) { ... }
setTimeout(callback, SESSION_TIMEOUT_MS);
```

#### Remove Dead Code
```typescript
// Before
function oldFunction() { /* unused */ }
const LEGACY_FLAG = true; // always true
if (false) { /* never runs */ }

// After
// Simply delete the dead code
```

### Phase 5: Verify

After each refactoring step:

1. **Run tests:**
   ```bash
   npm test
   pnpm test
   pytest
   go test ./...
   ```

2. **Run linting:**
   ```bash
   npm run lint
   pnpm lint
   ```

3. **Manual review:**
   - Does the code still work?
   - Is it more readable?
   - Did we introduce any bugs?

**If tests fail:** Revert and try a smaller step.

## Common Refactoring Patterns

### Extract Interface/Type
Separate contract from implementation.

### Introduce Parameter Object
Group related parameters into a single object.

### Replace Conditional with Polymorphism
Use different classes instead of switch/if chains.

### Compose Method
Break down complex method into well-named steps.

### Move Method/Field
Relocate to more appropriate class/module.

### Introduce Null Object
Replace null checks with a default implementation.

## Refactoring Guidelines

### Do:
- Refactor in small, tested steps
- Keep the public API stable
- Run tests after each change
- Commit after each successful refactoring
- Document non-obvious changes

### Don't:
- Refactor and add features simultaneously
- Change behavior during refactoring
- Refactor without tests
- Make large changes in one step
- Refactor code you don't understand

## Complexity Thresholds

| Metric | Good | Acceptable | Needs Refactoring |
|--------|------|------------|-------------------|
| Function lines | <20 | <50 | >50 |
| Parameters | <3 | <5 | >5 |
| Nesting depth | <2 | <4 | >4 |
| Cyclomatic complexity | <5 | <10 | >10 |
| File lines | <200 | <400 | >400 |

## Output Format

After refactoring:

```markdown
## Refactoring Summary: <target>

### Changes Made
1. **Extracted `validateOrder` from `processOrder`**
   - Reduced function from 65 to 15 lines
   - Improved testability

2. **Renamed variables for clarity**
   - `d` → `currentDate`
   - `x` → `activeUsers`

3. **Removed dead code**
   - Deleted unused `legacyHandler` function
   - Removed commented-out code blocks

### Metrics
- Lines changed: +50 / -120
- Complexity: Reduced from 15 to 6
- Test coverage: Maintained at 85%

### Verification
- [x] All tests pass
- [x] Linting passes
- [x] Manual verification complete

### Follow-up Suggestions
- Consider extracting `calculateTotal` into a separate module
- Add tests for edge cases in `validateOrder`
```
