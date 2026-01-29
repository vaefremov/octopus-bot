#!/bin/bash

# test_report_task_log.sh
# Demonstrates the usage of report_task_log.sh

set -euo pipefail

echo "=== Testing report_task_log.sh ==="
echo

# Clean up any previous test files
TEST_LOG="/tmp/test_long_task.log"
rm -f "$TEST_LOG"
rm -rf /tmp/report_task_log_state

echo "1. Creating a simulated long_task output..."
cat > "$TEST_LOG" <<'EOF'
[2025-01-29 10:00:00] Task started
[2025-01-29 10:00:01] Processing item 1
[2025-01-29 10:00:02] Processing item 2
[2025-01-29 10:00:03] Processing item 3
EOF

echo "   Log file created with 4 lines"
echo

echo "2. First run - should output all lines:"
echo "   $ ./report_task_log.sh $TEST_LOG"
echo "   ---"
./report_task_log.sh "$TEST_LOG"
echo "   ---"
echo

echo "3. Second run - should output nothing (no new lines):"
echo "   $ ./report_task_log.sh $TEST_LOG"
echo "   ---"
./report_task_log.sh "$TEST_LOG" || echo "(no output - expected)"
echo "   ---"
echo

echo "4. Simulating new output from long_task..."
cat >> "$TEST_LOG" <<'EOF'
[2025-01-29 10:05:00] Processing item 4
[2025-01-29 10:05:01] Processing item 5
EOF
echo "   Added 2 more lines"
echo

echo "5. Third run - should output only the 2 new lines:"
echo "   $ ./report_task_log.sh $TEST_LOG"
echo "   ---"
./report_task_log.sh "$TEST_LOG"
echo "   ---"
echo

echo "6. Simulating log rotation (file gets smaller)..."
cat > "$TEST_LOG" <<'EOF'
[2025-01-29 11:00:00] Log rotated - new session
[2025-01-29 11:00:01] Starting fresh
EOF
echo "   Log file replaced with smaller content"
echo

echo "7. Fourth run - should detect rotation and read from beginning:"
echo "   $ ./report_task_log.sh $TEST_LOG"
echo "   ---"
./report_task_log.sh "$TEST_LOG" 2>&1
echo "   ---"
echo

echo "8. Testing error handling - non-existent file:"
echo "   $ ./report_task_log.sh /tmp/nonexistent.log"
echo "   ---"
./report_task_log.sh /tmp/nonexistent.log 2>&1 || echo "   (error - expected)"
echo "   ---"
echo

echo "=== Test completed ==="
echo
echo "State files are stored in: /tmp/report_task_log_state/"
ls -la /tmp/report_task_log_state/ 2>/dev/null || true
