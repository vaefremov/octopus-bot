#!/usr/bin/env bash

# report_task_log.sh
# Reports new lines from a log file since the last run
# Usage: ./report_task_log.sh <log_file_path>

set -euo pipefail

# Use a fixed file descriptor for locking (compatible with bash 3.2+)
readonly LOCK_FD=200

# Configuration
readonly SCRIPT_NAME=$(basename "$0")
readonly STATE_DIR="${REPORT_LOG_STATE_DIR:-/tmp/report_task_log_state}"

# Colors for error messages (only if terminal)
if [[ -t 2 ]]; then
    readonly RED='\033[0;31m'
    readonly YELLOW='\033[1;33m'
    readonly NC='\033[0m' # No Color
else
    readonly RED=''
    readonly YELLOW=''
    readonly NC=''
fi

# Print error message to stderr
error() {
    echo -e "${RED}Error: $*${NC}" >&2
}

# Print warning message to stderr
warn() {
    echo -e "${YELLOW}Warning: $*${NC}" >&2
}

# Print usage information
usage() {
    cat >&2 <<EOF
Usage: $SCRIPT_NAME <log_file_path>

Reports new lines from a log file since the last run.

Arguments:
  log_file_path    Path to the log file to monitor

Environment Variables:
  REPORT_LOG_STATE_DIR    Directory to store state files (default: /tmp/report_task_log_state)

Examples:
  # Start your long-running task with output redirection
  long_task > /tmp/long_task.log 2>&1 &

  # Run the reporting script to get new output
  $SCRIPT_NAME /tmp/long_task.log

  # Run again later to get only new lines
  $SCRIPT_NAME /tmp/long_task.log
EOF
    exit 1
}

# Validate arguments
if [[ $# -ne 1 ]]; then
    error "Missing required argument: log_file_path"
    usage
fi

readonly LOG_FILE="$1"

# Create state directory if it doesn't exist
mkdir -p "$STATE_DIR"

# Generate state file path based on log file path (sanitize the name)
STATE_FILE_NAME=$(echo "$LOG_FILE" | sed 's/[^a-zA-Z0-9._-]/_/g')
readonly STATE_FILE="$STATE_DIR/${STATE_FILE_NAME}.state"
readonly LOCK_FILE="$STATE_DIR/${STATE_FILE_NAME}.lock"

# Function to clean up lock file on exit
cleanup() {
    # Release the lock if held
    flock -u $LOCK_FD 2>/dev/null || true
    # Close the file descriptor
    eval "exec $LOCK_FD>&-" 2>/dev/null || true
}

trap cleanup EXIT INT TERM

# Acquire exclusive lock to prevent concurrent runs
# Use eval for bash 3.2 compatibility (macOS default bash)
eval "exec $LOCK_FD>\"$LOCK_FILE\""
if ! flock -n $LOCK_FD; then
    error "Another instance is already running for this log file"
    exit 1
fi

# Check if log file exists
if [[ ! -f "$LOG_FILE" ]]; then
    error "Log file does not exist: $LOG_FILE"
    exit 1
fi

# Check if log file is readable
if [[ ! -r "$LOG_FILE" ]]; then
    error "Log file is not readable: $LOG_FILE"
    exit 1
fi

# Get current log file size (cross-platform)
if [[ "$(uname)" == "Darwin" ]]; then
    # macOS
    CURRENT_SIZE=$(stat -f %z "$LOG_FILE" 2>/dev/null)
else
    # Linux
    CURRENT_SIZE=$(stat -c %s "$LOG_FILE" 2>/dev/null)
fi

# Read last position from state file
LAST_POSITION=0
if [[ -f "$STATE_FILE" ]]; then
    LAST_POSITION=$(cat "$STATE_FILE" 2>/dev/null || echo "0")
    # Validate that it's a number
    if ! [[ "$LAST_POSITION" =~ ^[0-9]+$ ]]; then
        warn "Invalid state file content, resetting to 0"
        LAST_POSITION=0
    fi
fi

# Handle log rotation: if file is smaller than last position, it was likely rotated
if [[ $CURRENT_SIZE -lt $LAST_POSITION ]]; then
    warn "Log file appears to have been rotated (current size: $CURRENT_SIZE < last position: $LAST_POSITION)"
    warn "Starting from beginning of file"
    LAST_POSITION=0
fi

# Calculate bytes to read
BYTES_TO_READ=$((CURRENT_SIZE - LAST_POSITION))

# If there's nothing new, exit silently
if [[ $BYTES_TO_READ -eq 0 ]]; then
    exit 0
fi

# Read new content from log file
# Using tail with bytes to handle large files efficiently
if [[ $LAST_POSITION -eq 0 ]]; then
    # Read entire file
    cat "$LOG_FILE"
else
    # Read from last position to end
    # Using dd for precise byte-offset reading
    dd if="$LOG_FILE" bs=1 skip="$LAST_POSITION" count="$BYTES_TO_READ" 2>/dev/null
fi

# Update state file with new position
echo "$CURRENT_SIZE" > "$STATE_FILE"

exit 0
