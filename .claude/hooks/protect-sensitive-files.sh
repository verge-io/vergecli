#!/bin/bash
# Hook: Protect sensitive files from being edited
# Event: PreToolUse (Edit, Write)
# Blocks modifications to .env files, lock files, and git internals

# Read JSON input from stdin
INPUT=$(cat)

# Extract file path
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.path // ""')

# Define protected patterns
PROTECTED_PATTERNS=(
    ".env"
    ".env.local"
    ".env.production"
    ".env.development"
    "package-lock.json"
    "pnpm-lock.yaml"
    "yarn.lock"
    "Cargo.lock"
    "poetry.lock"
    ".git/"
    "secrets"
    "credentials"
    ".pem"
    ".key"
)

# Check if file matches any protected pattern
for pattern in "${PROTECTED_PATTERNS[@]}"; do
    if [[ "$FILE_PATH" == *"$pattern"* ]]; then
        echo "BLOCKED: Cannot modify protected file: $FILE_PATH"
        echo "Protected patterns: ${PROTECTED_PATTERNS[*]}"
        exit 2  # Exit 2 blocks the action
    fi
done

# Allow the action
exit 0
