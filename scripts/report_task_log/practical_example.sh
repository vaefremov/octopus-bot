#!/bin/bash

# practical_example.sh
# Demonstrates practical usage of report_task_log.sh

set -euo pipefail

LOG_FILE="/tmp/practical_example.log"
PID_FILE="/tmp/practical_example.pid"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Practical Example: Monitoring a Long-Running Task ===${NC}"
echo

# Clean up function
cleanup() {
    if [[ -f "$PID_FILE" ]]; then
        pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${YELLOW}Stopping long-running task (PID: $pid)${NC}"
            kill "$pid"
        fi
        rm -f "$PID_FILE"
    fi
}

trap cleanup EXIT

# Start the long-running task in background
echo -e "${BLUE}Step 1: Starting a long-running task in background${NC}"
echo "Command: ./simulated_long_task.sh > $LOG_FILE 2>&1 &"
./simulated_long_task.sh > "$LOG_FILE" 2>&1 &
TASK_PID=$!
echo "$TASK_PID" > "$PID_FILE"
echo "Task started with PID: $TASK_PID"
echo

# Wait a bit for some output
sleep 3

# First check - should get all existing output
echo -e "${BLUE}Step 2: First check - getting all output so far${NC}"
echo "Command: ./report_task_log.sh $LOG_FILE"
echo "Output:"
echo "---"
./report_task_log.sh "$LOG_FILE"
echo "---"
echo

# Immediate second check - should be empty
echo -e "${BLUE}Step 3: Immediate second check - should be empty${NC}"
echo "Command: ./report_task_log.sh $LOG_FILE"
output=$(./report_task_log.sh "$LOG_FILE")
if [[ -z "$output" ]]; then
    echo "(No new output - as expected)"
else
    echo "Output:"
    echo "$output"
fi
echo

# Wait for more output
echo -e "${YELLOW}Waiting 8 seconds for new output from the task...${NC}"
sleep 8

# Third check - should show only new lines
echo -e "${BLUE}Step 4: Third check - showing only new lines${NC}"
echo "Command: ./report_task_log.sh $LOG_FILE"
echo "Output:"
echo "---"
./report_task_log.sh "$LOG_FILE"
echo "---"
echo

# Demonstrate periodic checking
echo -e "${BLUE}Step 5: Demonstrating periodic checking (3 iterations)${NC}"
for i in {1..3}; do
    echo -e "${YELLOW}Check $i: (waiting 6 seconds between checks)${NC}"
    sleep 6
    echo "Command: ./report_task_log.sh $LOG_FILE"
    output=$(./report_task_log.sh "$LOG_FILE")
    if [[ -n "$output" ]]; then
        echo "New output:"
        echo "---"
        echo "$output"
        echo "---"
    else
        echo "(No new output this time)"
    fi
    echo
done

echo -e "${GREEN}=== Example Complete ===${NC}"
echo
echo "This demonstrates how report_task_log.sh can be used to:"
echo "  1. Monitor a long-running background task"
echo "  2. Fetch only new output since last check"
echo "  3. Run periodically without duplicating output"
echo
echo "Use Cases:"
echo "  - Telegram bots checking for updates"
echo "  - Cron jobs monitoring log files"
echo "  - Dashboard widgets showing recent activity"
echo "  - CI/CD pipelines tracking build progress"
