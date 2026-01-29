#!/bin/bash

# simulated_long_task.sh
# Simulates a long-running task that outputs in bursts
# This mimics behavior like tail -f or git repository watchers

set -euo pipefail

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Long task started"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Monitoring for events..."
echo

counter=1

while true; do
    # Simulate burst of activity
    num_lines=$((RANDOM % 5 + 1))
    
    for ((i=1; i<=num_lines; i++)); do
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Event #$counter: Processing item $i of $num_lines"
        ((counter++))
    done
    
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Batch complete. Waiting for next event..."
    echo
    
    # Wait before next burst (5-15 seconds)
    sleep_time=$((RANDOM % 11 + 5))
    sleep $sleep_time
done
