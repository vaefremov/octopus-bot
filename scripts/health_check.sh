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
df -h
echo ""

echo "--- Load Average ---"
cat /proc/loadavg 2>/dev/null || echo "N/A (not available on this system)"
echo ""

echo "--- Running Processes Count ---"
ps aux | wc -l
echo ""

echo "Health check completed."
