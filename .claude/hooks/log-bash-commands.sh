#!/bin/bash
# Hook: Log all Bash commands for audit trail
# Event: PreToolUse (Bash)
# Creates a "receipt" of all commands executed by Claude

LOG_DIR="${CLAUDE_PROJECT_DIR:-.}/.claude/logs"
LOG_FILE="$LOG_DIR/bash-commands-$(date +%Y-%m-%d).log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Read JSON input from stdin
INPUT=$(cat)

# Extract command and description using jq
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // "unknown"')
DESCRIPTION=$(echo "$INPUT" | jq -r '.tool_input.description // "No description"')
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Log the command
echo "[$TIMESTAMP] $DESCRIPTION" >> "$LOG_FILE"
echo "  Command: $COMMAND" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Exit 0 to allow the command to proceed
exit 0
