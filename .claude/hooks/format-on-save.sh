#!/bin/bash
# Hook: Auto-format files after editing
# Event: PostToolUse (Edit, Write)
# Runs appropriate formatter based on file type

# Read JSON input from stdin
INPUT=$(cat)

# Extract file path
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.path // ""')

# Skip if no file path
if [[ -z "$FILE_PATH" || "$FILE_PATH" == "null" ]]; then
    exit 0
fi

# Get file extension
EXT="${FILE_PATH##*.}"

# Project directory
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"

# Format based on file type
case "$EXT" in
    ts|tsx|js|jsx|json|css|scss|md|mdx|html|yaml|yml)
        # Check if prettier is available
        if command -v npx &> /dev/null && [[ -f "$PROJECT_DIR/node_modules/.bin/prettier" || -f "$PROJECT_DIR/package.json" ]]; then
            npx prettier --write "$FILE_PATH" 2>/dev/null || true
        fi
        ;;
    py)
        # Python formatting with black or ruff
        if command -v ruff &> /dev/null; then
            ruff format "$FILE_PATH" 2>/dev/null || true
        elif command -v black &> /dev/null; then
            black "$FILE_PATH" 2>/dev/null || true
        fi
        ;;
    rs)
        # Rust formatting
        if command -v rustfmt &> /dev/null; then
            rustfmt "$FILE_PATH" 2>/dev/null || true
        fi
        ;;
    go)
        # Go formatting
        if command -v gofmt &> /dev/null; then
            gofmt -w "$FILE_PATH" 2>/dev/null || true
        fi
        ;;
esac

# Always exit 0 - formatting failures shouldn't block edits
exit 0
