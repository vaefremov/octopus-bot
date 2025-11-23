#!/bin/bash
# Example tail logs script (long-running)
# This script simulates tailing logs

echo "Starting log tail (simulated)..."
echo "Press Ctrl+C to stop"
echo ""

count=0
while [ $count -lt 20 ]; do
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    level=("INFO" "WARN" "ERROR" "DEBUG")
    random_level=${level[$RANDOM % ${#level[@]}]}
    
    echo "[$timestamp] [$random_level] Application event #$((count+1))"
    
    sleep 1
    ((count++))
done

echo "Log tail completed (simulated 20 messages)"
