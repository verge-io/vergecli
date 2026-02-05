---
name: explain
description: Explains code with visual diagrams and analogies. Triggered when explaining how code works, teaching about a codebase, or answering "how does this work?" questions.
argument-hint: "[file-or-function]"
allowed-tools: Read, Grep, Glob
---

# Code Explanation

Explain code clearly using diagrams, analogies, and step-by-step walkthroughs.

## Arguments

- `$ARGUMENTS`: What to explain (optional)
  - File path: `src/auth/login.ts`
  - Function name: `parseConfig`
  - Concept: `authentication flow`
  - Empty: Explain based on context or ask what to explain

## Explanation Framework

Every explanation should include:

1. **An analogy** - Compare to something from everyday life
2. **A diagram** - Visual representation using ASCII art
3. **A walkthrough** - Step-by-step code execution
4. **A gotcha** - Common mistake or misconception

## Explanation Workflow

Copy this checklist and track progress:

```
Explanation Progress:
- [ ] Step 1: Understand the code
- [ ] Step 2: Create an analogy
- [ ] Step 3: Draw a diagram
- [ ] Step 4: Walk through the code
- [ ] Step 5: Highlight gotchas
```

### Step 1: Understand the Code

Read the target code and identify:
- **Purpose**: What problem does it solve?
- **Inputs**: What goes in?
- **Outputs**: What comes out?
- **Dependencies**: What does it rely on?
- **Side effects**: What does it change?

### Step 2: Create an Analogy

Connect the code to a real-world concept:

**Good analogies:**
| Code Concept | Analogy |
|--------------|---------|
| Cache | A sticky note on your desk |
| Queue | Line at a coffee shop |
| Stack | Pile of plates |
| Middleware | Security checkpoints at an airport |
| API | Restaurant menu and waiter |
| Database | Filing cabinet |
| Event loop | Juggling balls |
| Async/await | Ordering food and waiting for it |

**Example:**
> "This authentication flow is like entering a secure building. First you show your ID (login), then you get a visitor badge (token) that you wear while inside. The badge expires at the end of the day (token expiry), and security can check it anytime (middleware validation)."

### Step 3: Draw a Diagram

Use ASCII art to show:

**Data Flow:**
```
┌─────────┐    ┌─────────┐    ┌─────────┐
│  Input  │───▶│ Process │───▶│ Output  │
└─────────┘    └─────────┘    └─────────┘
```

**Component Relationships:**
```
┌─────────────────────────────────────┐
│              App                    │
│  ┌─────────┐       ┌─────────┐     │
│  │  Auth   │──────▶│   API   │     │
│  └─────────┘       └────┬────┘     │
│       │                 │          │
│       ▼                 ▼          │
│  ┌─────────┐       ┌─────────┐     │
│  │  Store  │◀──────│   DB    │     │
│  └─────────┘       └─────────┘     │
└─────────────────────────────────────┘
```

**Sequence Diagram:**
```
Client          Server          Database
  │                │                │
  │── login() ────▶│                │
  │                │── query() ────▶│
  │                │◀── user ───────│
  │◀── token ──────│                │
  │                │                │
```

**State Machine:**
```
         ┌──────────────┐
         │              │
         ▼              │
    ┌─────────┐    ┌────┴────┐
───▶│  Idle   │───▶│ Loading │
    └─────────┘    └────┬────┘
         ▲              │
         │              ▼
    ┌────┴────┐    ┌─────────┐
    │  Error  │◀───│ Success │
    └─────────┘    └─────────┘
```

**Tree Structure:**
```
src/
├── components/
│   ├── Button.tsx
│   └── Modal.tsx
├── hooks/
│   └── useAuth.ts
└── utils/
    └── helpers.ts
```

### Step 4: Walk Through the Code

Explain execution step-by-step:

```typescript
async function login(email, password) {
  // Step 1: Validate input
  // We check if email and password exist before hitting the server
  if (!email || !password) {
    throw new ValidationError('Email and password required');
  }

  // Step 2: Call the API
  // This is an async call - execution pauses here until server responds
  const response = await api.post('/auth/login', { email, password });

  // Step 3: Store the token
  // We save the token so future requests can be authenticated
  localStorage.setItem('token', response.token);

  // Step 4: Return user data
  // The caller receives the user object to update UI
  return response.user;
}
```

### Step 5: Highlight Gotchas

Point out common mistakes:

**Example gotchas:**
```markdown
## Common Gotchas

1. **Forgetting to await**: The `api.post` call returns a Promise.
   Without `await`, you'll be working with a Promise object, not the data.

2. **Token storage**: Using `localStorage` means the token persists
   after browser close. Use `sessionStorage` if you want it cleared.

3. **Error handling**: This function throws on validation error but
   doesn't catch API errors. Callers need to handle both cases.
```

## Explanation Templates

### For Functions:

```markdown
## `functionName(params)`

### What it does
<One sentence summary>

### Analogy
<Real-world comparison>

### How it works
<ASCII diagram>

### Step by step
1. <First step>
2. <Second step>
3. ...

### Watch out for
- <Gotcha 1>
- <Gotcha 2>

### Example usage
<Code example>
```

### For Modules/Classes:

```markdown
## ModuleName

### Purpose
<What problem it solves>

### Analogy
<Real-world comparison>

### Architecture
<ASCII diagram showing structure>

### Key methods
| Method | Purpose |
|--------|---------|
| `method1` | <description> |
| `method2` | <description> |

### Data flow
<Sequence or flow diagram>

### Common patterns
<How it's typically used>
```

### For Systems/Flows:

```markdown
## System Name

### Overview
<High-level description>

### Analogy
<Real-world comparison>

### Components
<Diagram showing all parts>

### Flow
<Step-by-step sequence diagram>

### Entry points
- <Entry point 1>: <when/why used>

### Common scenarios
1. <Scenario 1>: <flow description>
2. <Scenario 2>: <flow description>
```

## Complexity Levels

Adjust explanation depth based on audience:

**Beginner:** Heavy analogy use, simple diagrams, skip edge cases
**Intermediate:** Balance of analogy and technical detail
**Advanced:** Focus on implementation details, edge cases, performance

## Example Output

```markdown
## `useAuth` Hook

### What it does
Manages authentication state and provides login/logout functions.

### Analogy
Think of it like a keycard system at an office. The hook is your keycard
holder - it knows if you have a valid card (logged in), can get you a
new card (login), and can deactivate your card (logout).

### How it works
```
┌────────────────────────────────────────┐
│            useAuth Hook                │
│  ┌─────────┐    ┌─────────────────┐   │
│  │  State  │    │    Functions    │   │
│  │ • user  │    │ • login()      │   │
│  │ • token │    │ • logout()     │   │
│  │ • loading│   │ • refresh()    │   │
│  └────┬────┘    └───────┬─────────┘   │
│       │                 │             │
│       └────────┬────────┘             │
│                ▼                      │
│         Return Object                 │
│    { user, login, logout, ... }       │
└────────────────────────────────────────┘
```

### Step by step
1. On mount, check localStorage for existing token
2. If token exists, validate it with the server
3. If valid, set user state; if invalid, clear token
4. Expose login/logout functions that update state

### Watch out for
- **Race condition**: If component unmounts during login, state update fails
- **Token expiry**: Token might expire between validation and use
- **Memory leak**: Always cleanup listeners on unmount
```
