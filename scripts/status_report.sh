#!/bin/bash
# Example health check script
# This script can be run as a one-time script via /run command

echo "=== System Health Check ==="
echo ""
echo "Timestamp: $(date)"
echo ""

echo "--- Uptime ---"
uptime
echo ""

echo "--- Memory Usage ---"
free -h
echo ""

echo "--- Disk Usage ---"
# Define filesystems to check
filesystems=(/ /tmp /hdd1 /hdd2 /hdd5 /ssd /var)

# Filter out filesystems that don't exist
existing_filesystems=()
for fs in "${filesystems[@]}"; do
    if [ -e "$fs" ]; then
        existing_filesystems+=("$fs")
    fi
done

# Check disk usage for existing filesystems
if [ ${#existing_filesystems[@]} -gt 0 ]; then
    df -h "${existing_filesystems[@]}"
else
    echo "No matching filesystems found"
fi
echo ""

echo "--- Load Average ---"
cat /proc/loadavg 2>/dev/null || echo "N/A (not available on this system)"
echo ""

echo "--- Running Processes Count ---"
ps aux | wc -l
echo ""

echo "Health check completed."
