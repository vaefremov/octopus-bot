#!/bin/bash
# Script to compare database object ID with file-based ID
# Exits with status 0 and no output when everything is OK.
# Emits warning message to stdout when the difference is less than threshold.

set -euo pipefail

# Resolve default config path
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
DEFAULT_CONFIG="$SCRIPT_DIR/compare_ids.conf"

CONFIG="${COMPARE_IDS_CONFIG:-}"

# If no config provided, pick default
if [ -z "$CONFIG" ] && [ -f "$DEFAULT_CONFIG" ]; then
  CONFIG="$DEFAULT_CONFIG"
fi

if [ -n "${CONFIG:-}" ] && [ -f "$CONFIG" ]; then
  # shellcheck source=/dev/null
  source "$CONFIG"
fi

# Set sensible defaults if variables not provided by config
: ${THRESHOLD:=1000}

# Database connection parameters (using same pattern as other scripts)
export PGPASSWORD=${PGPASSWORD:-"password_should_be_secret"}
export PGUSER=${PGUSER:-postgres}
export PGHOST=${PGHOST:-localhost}
export PGDATABASE=${PGDATABASE:-octopus}

# Get next value from object_id_seq sequence
DB_ID_OUTPUT=""
DB_ID_QUERY_EXIT_CODE=0
DB_ID_OUTPUT=$(psql -t -A -c "SELECT nextval('object_id_seq');" 2>&1) || DB_ID_QUERY_EXIT_CODE=$?

if [ $DB_ID_QUERY_EXIT_CODE -ne 0 ]; then
  echo "Error: Failed to get next object ID from database: $DB_ID_OUTPUT" >&2
  exit 1
fi

DB_ID=$(echo "$DB_ID_OUTPUT" | tr -d '[:space:]')

# Get ID from file
FILE_ID_FILE="start_id.txt"
if [ -n "${START_ID_FILE:-}" ]; then
  FILE_ID_FILE="$START_ID_FILE"
fi

if [ ! -f "$FILE_ID_FILE" ]; then
  echo "Error: File $FILE_ID_FILE not found" >&2
  exit 1
fi

FILE_ID=$(cat "$FILE_ID_FILE" | tr -d '[:space:]')

# Validate that both values are numbers
if ! [[ "$DB_ID" =~ ^[0-9]+$ ]]; then
  echo "Error: Database ID '$DB_ID' is not a valid number" >&2
  exit 1
fi

if ! [[ "$FILE_ID" =~ ^[0-9]+$ ]]; then
  echo "Error: File ID '$FILE_ID' is not a valid number" >&2
  exit 1
fi

# Calculate difference
DIFF=$((FILE_ID - DB_ID))

# Compare with threshold
if [ "$DIFF" -lt "$THRESHOLD" ]; then
  echo "❌ Warning:"
  echo "Difference in ID between production database $PGDATABASE ($DB_ID) and test database ID ($FILE_ID from $FILE_ID_FILE) is $DIFF, which is less than threshold ($THRESHOLD)"
  echo
  exit 0
fi

# If difference is >= threshold, produce no output and exit successfully
exit 0