---
name: doc
description: Generates documentation for code, APIs, or modules. Triggered when adding documentation, creating docs, or improving code documentation.
argument-hint: "[file-or-module]"
allowed-tools: Read, Grep, Glob, Write, Edit
---

# Documentation Generation

Generate comprehensive documentation following project conventions.

## Arguments

- `$ARGUMENTS`: What to document (optional)
  - File path: `src/utils/parser.ts`
  - Module: `auth`
  - API: `REST API`
  - Empty: Document based on context or prompt for target

## Documentation Types

| Type | Format | Location |
|------|--------|----------|
| Function docs | JSDoc/docstring | Inline |
| API docs | OpenAPI/Markdown | `docs/api/` |
| Module docs | Markdown | `docs/` or README |
| Usage examples | Markdown | README or `examples/` |

## Workflow

Copy this checklist and track progress:

```
Documentation Progress:
- [ ] Step 1: Analyze the code
- [ ] Step 2: Detect documentation style
- [ ] Step 3: Generate documentation
- [ ] Step 4: Verify quality checklist
```

### Step 1: Analyze the Code

Read the target and identify:
- Public API surface
- Function signatures
- Parameters and return types
- Side effects
- Dependencies
- Usage patterns

### Step 2: Detect Documentation Style

Check existing docs for conventions:

```bash
# Find existing documented files
grep -r "@param\|@returns\|:param\|Args:" --include="*.ts" --include="*.py" --include="*.go"
```

Match the existing style in the codebase.

### Step 3: Generate Documentation

Based on target type:

---

## Function Documentation

### TypeScript (JSDoc)

```typescript
/**
 * Parses a configuration file and returns validated settings.
 *
 * @description Reads the config file, validates against schema, and applies
 * defaults for missing values. Throws on invalid configuration.
 *
 * @param {string} filePath - Path to the configuration file
 * @param {ParseOptions} [options] - Optional parsing configuration
 * @param {boolean} [options.strict=false] - Enable strict validation mode
 * @param {object} [options.defaults] - Default values for missing fields
 *
 * @returns {Promise<Config>} Parsed and validated configuration object
 *
 * @throws {FileNotFoundError} If the config file doesn't exist
 * @throws {ValidationError} If the config fails schema validation
 *
 * @example
 * // Basic usage
 * const config = await parseConfig('./config.json');
 *
 * @example
 * // With options
 * const config = await parseConfig('./config.json', {
 *   strict: true,
 *   defaults: { port: 3000 }
 * });
 *
 * @see {@link validateConfig} for validation details
 * @since 1.0.0
 */
async function parseConfig(filePath: string, options?: ParseOptions): Promise<Config> {
```

### Python (Google Style Docstring)

```python
def parse_config(file_path: str, options: ParseOptions | None = None) -> Config:
    """Parse a configuration file and return validated settings.

    Reads the config file, validates against schema, and applies
    defaults for missing values.

    Args:
        file_path: Path to the configuration file.
        options: Optional parsing configuration.
            strict: Enable strict validation mode. Defaults to False.
            defaults: Default values for missing fields.

    Returns:
        Parsed and validated configuration object.

    Raises:
        FileNotFoundError: If the config file doesn't exist.
        ValidationError: If the config fails schema validation.

    Example:
        Basic usage::

            config = parse_config('./config.json')

        With options::

            config = parse_config('./config.json', ParseOptions(
                strict=True,
                defaults={'port': 3000}
            ))
    """
```

### Go (Godoc)

```go
// ParseConfig reads and validates a configuration file.
//
// It loads the file from the given path, validates it against the schema,
// and applies defaults for any missing values. Returns an error if the
// file doesn't exist or fails validation.
//
// Example usage:
//
//	config, err := ParseConfig("./config.json", nil)
//	if err != nil {
//	    log.Fatal(err)
//	}
//
//	// With options
//	config, err := ParseConfig("./config.json", &ParseOptions{
//	    Strict:   true,
//	    Defaults: map[string]any{"port": 3000},
//	})
func ParseConfig(filePath string, options *ParseOptions) (*Config, error) {
```

---

## API Documentation

### REST API (Markdown)

```markdown
## Endpoints

### POST /api/auth/login

Authenticate a user and return an access token.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | User's email address |
| password | string | Yes | User's password |

**Response:**

```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": "123",
    "email": "user@example.com",
    "name": "John Doe"
  },
  "expiresAt": "2024-01-15T12:00:00Z"
}
```

**Errors:**

| Status | Code | Description |
|--------|------|-------------|
| 400 | INVALID_INPUT | Missing email or password |
| 401 | INVALID_CREDENTIALS | Wrong email or password |
| 429 | RATE_LIMITED | Too many login attempts |

**Example:**

```bash
curl -X POST https://api.example.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "secret"}'
```
```

---

## Module Documentation

### README Format

```markdown
# Module Name

Brief description of what this module does.

## Installation

```bash
npm install module-name
```

## Quick Start

```typescript
import { MainFunction } from 'module-name';

const result = await MainFunction(input);
```

## API Reference

### `MainFunction(input, options?)`

Description of the function.

**Parameters:**
- `input` (string): Description
- `options` (object, optional): Configuration options
  - `option1` (boolean): Description. Default: `true`

**Returns:** `Promise<Result>`

**Example:**

```typescript
const result = await MainFunction('input', { option1: false });
```

## Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| option1 | boolean | true | Description |
| option2 | string | 'default' | Description |

## Error Handling

The module throws the following errors:

- `ValidationError`: When input is invalid
- `NetworkError`: When the request fails

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md)

## License

MIT
```

---

## Documentation Quality Checklist

- [ ] Every public function has documentation
- [ ] Parameters are described with types
- [ ] Return values are documented
- [ ] Errors/exceptions are listed
- [ ] Examples show common usage
- [ ] Edge cases are noted
- [ ] Links to related functions included

## Output

After generating docs:

1. **Summary**: What was documented
2. **Files modified**: List of changes
3. **Coverage**: Functions/APIs documented
4. **Suggestions**: Missing documentation areas
