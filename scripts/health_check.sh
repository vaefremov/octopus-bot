#!/usr/bin/env bash
# Health check script for periodic run
# Exits with status 0 and no output when everything is OK.
# Emits human-readable report to stdout when any condition is met and exits with non-zero status.

set -euo pipefail

# Configurable checks (edit as needed)
# Filesystems and minimum free percent pairs: path min_free
filesystems=(/ 10 /tmp 5 /var 5)

# Processes and minimum counts pairs: name min_count
processes=(nginx 1 mysql 2)

# Swap usage threshold percent (report when swap usage > threshold)
swap_threshold=20

report=""

check_filesystems() {
  local i=0
  while [ $i -lt ${#filesystems[@]} ]; do
    path=${filesystems[$i]}
    min_free=${filesystems[$((i+1))]}

    # Get used percent (number without %)
    used_percent=$(df -P "$path" 2>/dev/null | awk 'NR==2 {gsub("%", "", $5); print $5}') || used_percent=""
    if [ -z "$used_percent" ]; then
      report+="Filesystem $path: ERROR reading df output\n"
    else
      free_percent=$((100 - used_percent))
      if [ "$free_percent" -lt "$min_free" ]; then
        report+="Filesystem $path low free space: ${free_percent}% free (threshold ${min_free}%)\n"
      fi
    fi

    i=$((i+2))
  done
}

check_processes() {
  local i=0
  while [ $i -lt ${#processes[@]} ]; do
    pname=${processes[$i]}
    need=${processes[$((i+1))]}
    # pgrep -c returns 0 if none, but may be non-zero exit; use || true
    count=$(pgrep -c -f "$pname" 2>/dev/null || true)
    count=${count:-0}
    if [ "$count" -lt "$need" ]; then
      report+="Process $pname count low: ${count} (need >= ${need})\n"
    fi
    i=$((i+2))
  done
}

check_swap() {
  if command -v free >/dev/null 2>&1; then
    # Linux
    swap_used=$(free -m | awk '/Swap:/ {print $3}')
    swap_total=$(free -m | awk '/Swap:/ {print $2}')
    if [ -n "$swap_total" ] && [ "$swap_total" -gt 0 ]; then
      swap_pct=$(( (swap_used * 100) / swap_total ))
      if [ "$swap_pct" -gt "$swap_threshold" ]; then
        report+="High swap usage: ${swap_pct}% used (threshold ${swap_threshold}%)\n"
      fi
    fi
  else
    # Fallback: try /proc/meminfo
    if [ -r /proc/meminfo ]; then
      swap_total_kb=$(awk '/SwapTotal:/ {print $2}' /proc/meminfo)
      swap_free_kb=$(awk '/SwapFree:/ {print $2}' /proc/meminfo)
      if [ -n "$swap_total_kb" ] && [ "$swap_total_kb" -gt 0 ]; then
        swap_used_kb=$((swap_total_kb - swap_free_kb))
        swap_pct=$(( (swap_used_kb * 100) / swap_total_kb ))
        if [ "$swap_pct" -gt "$swap_threshold" ]; then
          report+="High swap usage: ${swap_pct}% used (threshold ${swap_threshold}%)\n"
        fi
      fi
    fi
  fi
}

main() {
  check_filesystems
  check_processes
  check_swap

  if [ -n "$report" ]; then
    # Print the report and exit non-zero
    echo -e "$report"
    exit 2
  fi

  # If everything OK: exit 0 with no output
  exit 0
}

main "$@"
