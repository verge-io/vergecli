---
name: test
description: Generates tests for code following project conventions. Triggered when adding tests, writing tests, improving test coverage, or creating test cases.
argument-hint: "[file-or-function]"
allowed-tools: Read, Grep, Glob, Write, Bash(npm:*), Bash(pnpm:*), Bash(yarn:*), Bash(pytest:*), Bash(go:*)
---

# Test Generation

Generate comprehensive tests following project conventions and best practices.

## Arguments

- `$ARGUMENTS`: What to test (optional)
  - File path: `src/utils/parser.ts`
  - Function name: `parseConfig`
  - Empty: Test recent changes or prompt for target

## Workflow

Copy this checklist and track progress:

```
Test Generation Progress:
- [ ] Step 1: Detect test framework
- [ ] Step 2: Find existing test patterns
- [ ] Step 3: Analyze target code
- [ ] Step 4: Generate test cases
- [ ] Step 5: Write test file
- [ ] Step 6: Run and verify tests
```

### Step 1: Detect Test Framework

Check project configuration to determine the testing framework:

**JavaScript/TypeScript:**
```bash
# Check package.json for test framework
grep -E "(jest|vitest|mocha|ava)" package.json
```

| Indicator | Framework |
|-----------|-----------|
| `"jest"` in dependencies | Jest |
| `"vitest"` in dependencies | Vitest |
| `vitest.config` file | Vitest |
| `jest.config` file | Jest |
| `"mocha"` in dependencies | Mocha |

**Python:**
```bash
# Check for pytest or unittest
grep -E "(pytest|unittest)" pyproject.toml setup.py requirements*.txt
```

| Indicator | Framework |
|-----------|-----------|
| `pytest` in dependencies | pytest |
| No pytest, Python project | unittest |

**Go:**
- Always uses built-in `testing` package
- Look for existing `*_test.go` files for patterns

### Step 2: Find Existing Test Patterns

Search for existing tests to match conventions:

```bash
# Find test files
find . -name "*.test.ts" -o -name "*.spec.ts" -o -name "*_test.go" -o -name "test_*.py"
```

Analyze existing tests for:
- **File naming**: `*.test.ts` vs `*.spec.ts` vs `*_test.go`
- **Directory structure**: `__tests__/` vs colocated vs `tests/`
- **Import style**: How mocks/fixtures are imported
- **Assertion style**: expect vs assert vs testing.T

### Step 3: Analyze Target Code

Read the target file/function and identify:

1. **Function signatures**: Inputs and outputs
2. **Dependencies**: What needs mocking
3. **Edge cases**: Null, empty, boundary values
4. **Error conditions**: What can throw/fail
5. **Side effects**: DB, API, file operations

### Step 4: Generate Test Cases

Create tests covering:

#### Happy Path
- Normal expected inputs
- Typical use cases

#### Edge Cases
- Empty inputs (`""`, `[]`, `{}`, `null`, `undefined`)
- Boundary values (0, -1, MAX_INT)
- Special characters
- Unicode handling

#### Error Cases
- Invalid inputs
- Missing required fields
- Type mismatches
- Network/IO failures (if applicable)

#### Integration Points
- Mock external dependencies
- Verify correct API calls
- Check error propagation

### Step 5: Write Test File

Generate the test file following project conventions.

### Step 6: Run and Verify Tests

Run the tests to verify they pass:

```bash
# JavaScript/TypeScript
npm test -- --testPathPattern="<test-file>"
pnpm test -- --testPathPattern="<test-file>"

# Python
pytest <test-file> -v

# Go
go test -v -run <TestName>
```

- If tests fail, analyze the failure and fix the test or report the issue
- Confirm all new tests pass before completing
- Report test results summary to user

## Framework-Specific Templates

### Jest/Vitest (TypeScript)

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'; // or 'jest'
import { functionName } from './module';

describe('functionName', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('happy path', () => {
    it('should handle normal input', () => {
      const result = functionName(validInput);
      expect(result).toEqual(expectedOutput);
    });
  });

  describe('edge cases', () => {
    it('should handle empty input', () => {
      expect(functionName('')).toEqual(defaultValue);
    });

    it('should handle null input', () => {
      expect(() => functionName(null)).toThrow();
    });
  });

  describe('error handling', () => {
    it('should throw on invalid input', () => {
      expect(() => functionName(invalidInput)).toThrow(ExpectedError);
    });
  });
});
```

### pytest (Python)

```python
import pytest
from module import function_name

class TestFunctionName:
    """Tests for function_name."""

    def test_happy_path(self):
        """Should handle normal input."""
        result = function_name(valid_input)
        assert result == expected_output

    def test_empty_input(self):
        """Should handle empty input."""
        result = function_name("")
        assert result == default_value

    def test_none_input(self):
        """Should raise TypeError on None input."""
        with pytest.raises(TypeError):
            function_name(None)

    @pytest.mark.parametrize("input,expected", [
        ("case1", "result1"),
        ("case2", "result2"),
    ])
    def test_various_inputs(self, input, expected):
        """Should handle various inputs correctly."""
        assert function_name(input) == expected
```

### Go (testing)

```go
package mypackage

import (
    "testing"
)

func TestFunctionName(t *testing.T) {
    t.Run("happy path", func(t *testing.T) {
        result := FunctionName(validInput)
        if result != expectedOutput {
            t.Errorf("got %v, want %v", result, expectedOutput)
        }
    })

    t.Run("empty input", func(t *testing.T) {
        result := FunctionName("")
        if result != defaultValue {
            t.Errorf("got %v, want %v", result, defaultValue)
        }
    })

    t.Run("error case", func(t *testing.T) {
        _, err := FunctionName(invalidInput)
        if err == nil {
            t.Error("expected error, got nil")
        }
    })
}

// Table-driven tests
func TestFunctionNameTable(t *testing.T) {
    tests := []struct {
        name     string
        input    string
        expected string
    }{
        {"case1", "input1", "output1"},
        {"case2", "input2", "output2"},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            result := FunctionName(tt.input)
            if result != tt.expected {
                t.Errorf("got %v, want %v", result, tt.expected)
            }
        })
    }
}
```

## Test Quality Guidelines

### Good Tests:
- **Descriptive names**: `should_return_empty_array_when_input_is_null`
- **Single assertion focus**: One logical assertion per test
- **Independent**: No test depends on another
- **Fast**: Mock slow operations
- **Deterministic**: Same result every run

### Avoid:
- Testing implementation details
- Brittle snapshot overuse
- Excessive mocking (test real behavior when possible)
- Flaky async tests without proper waits

## Edge Case Checklist

| Category | Cases to Test |
|----------|---------------|
| **Strings** | Empty, whitespace, unicode, very long, special chars |
| **Numbers** | 0, -1, MAX_INT, MIN_INT, NaN, Infinity, decimals |
| **Arrays** | Empty, single item, many items, nested |
| **Objects** | Empty, missing keys, extra keys, null values |
| **Async** | Success, failure, timeout, cancellation |
| **Auth** | Unauthenticated, unauthorized, expired token |

## Output

After generating tests:

1. **Show test file location**
2. **Summarize coverage**:
   - Functions tested
   - Edge cases covered
   - Mocks required
3. **Suggest running**: `npm test`, `pytest`, or `go test`
