#!/usr/bin/env bash

# report_journal.sh
# Reports new journal lines for one or more systemd units since the last run.
# Journal counterpart of report_task_log.sh, for tasks whose output goes to
# journald instead of a file (diserv production since 2026-11-21).
# Usage: ./report_journal.sh <unit> [<unit> ...]
#
# State is a journal cursor per task, kept in $REPORT_LOG_STATE_DIR, so a run
# reports exactly the entries after the previous one: no duplicated boundary
# line, no dependence on timestamps. The first run records the current position
# and prints nothing, so switching a task over does not replay its history.
# If the journal has been rotated or the machine rebooted, an old cursor fails
# to seek: a warning goes to stderr and the task restarts from now.

set -uo pipefail

readonly LOCK_FD=200
readonly SCRIPT_NAME=$(basename "$0")
readonly STATE_DIR="${REPORT_LOG_STATE_DIR:-/tmp/report_task_log_state}"
# The overlay scrollback is not in journalctl's default view of other tasks
readonly JOURNALCTL_OPTS=(-o short-iso --no-pager)

usage() {
    cat >&2 <<EOF
Usage: $SCRIPT_NAME <unit> [<unit> ...]

Reports journal lines for the given systemd units that are new since the last run.
Arguments may also be passed as one string: "$SCRIPT_NAME 'a b'".

Environment Variables:
  REPORT_LOG_STATE_DIR    Directory to store state files (default: /tmp/report_task_log_state)
EOF
    exit 1
}

[ $# -ge 1 ] || { echo "Error: Missing required argument: unit name" >&2; usage; }
[ -n "$1" ] || usage

# Accept both `a b` and `"a b"` from the bot's args string
read -r -a UNITS <<< "$*"
[ ${#UNITS[@]} -ge 1 ] || usage

for u in "${UNITS[@]}"; do
    if ! systemctl cat "$u" >/dev/null 2>&1; then
        echo "Error: no such unit: $u" >&2
        exit 1
    fi
done

mkdir -p "$STATE_DIR"
readonly STATE_NAME=$(printf 'journal_%s' "$*" | sed 's/[^a-zA-Z0-9._-]/_/g')
readonly STATE_FILE="$STATE_DIR/${STATE_NAME}.state"
readonly LOCK_FILE="$STATE_DIR/${STATE_NAME}.lock"

cleanup() {
    flock -u $LOCK_FD 2>/dev/null || true
    eval "exec $LOCK_FD>&-" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

eval "exec $LOCK_FD>\"$LOCK_FILE\""
if ! flock -n $LOCK_FD; then
    echo "Error: Another instance is already running for this task" >&2
    exit 1
fi

jargs=()
for u in "${UNITS[@]}"; do jargs+=(-u "$u"); done

# Cursor of the newest entry right now (empty when the units have no entries yet)
current_cursor() {
    journalctl "${jargs[@]}" -n 1 --show-cursor 2>/dev/null | sed -n 's/^-- cursor: //p' | tail -1
}

if [[ -f "$STATE_FILE" ]]; then
    CURSOR=$(cat "$STATE_FILE" 2>/dev/null || true)
else
    CURSOR=""
fi

if [[ -z "$CURSOR" ]]; then
    # First run (or a reset): start at the end, print nothing
    cur=$(current_cursor)
    if [ -n "$cur" ]; then
        echo "$cur" > "$STATE_FILE"
    else
        # Units exist (checked above) but show no entries: almost always a
        # process without the systemd-journal (or adm) group, e.g. one started
        # from a tmux server older than the group membership. journalctl then
        # shows only the user's own journal, silently.
        echo "Error: no journal entries visible for ${UNITS[*]} - is this process in the systemd-journal group? (groups: $(id -Gn))" >&2
        exit 1
    fi
    exit 0
fi

# Everything after the stored cursor. stderr stays out of the task output: it
# carries journalctl's own notes ("-- No entries --"), which must not reach the
# chat. A failed seek is a rotated journal or a reboot: say so once on stderr
# and restart from the current position.
ERR=$(mktemp)
if ! OUTPUT=$(journalctl "${jargs[@]}" --after-cursor "$CURSOR" --show-cursor "${JOURNALCTL_OPTS[@]}" 2>"$ERR"); then
    echo "Warning: cursor in $STATE_FILE no longer usable (journal rotated or host rebooted); restarting from now: $(tr '\n' ' ' < "$ERR")" >&2
    rm -f "$ERR"
    cur=$(current_cursor)
    [ -n "$cur" ] && echo "$cur" > "$STATE_FILE"
    exit 0
fi
rm -f "$ERR"

NEW_CURSOR=$(printf '%s\n' "$OUTPUT" | sed -n 's/^-- cursor: //p' | tail -1)

# Drop the cursor line; print the rest as the task output
printf '%s\n' "$OUTPUT" | grep -v '^-- cursor: ' | grep -v '^-- No entries --$' | grep -v '^$' || true

[ -n "$NEW_CURSOR" ] && echo "$NEW_CURSOR" > "$STATE_FILE"
exit 0
