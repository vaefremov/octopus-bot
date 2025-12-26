#!/usr/bin/env bash
# Health check script for periodic run
# Exits with status 0 and no output when everything is OK.
# Emits human-readable report to stdout when any condition is met and exits with non-zero status.

set -euo pipefail

# Usage: health_check.sh [-c /path/to/config]
# The config file is a shell fragment that can override the following variables:
# - filesystems: array of pairs (path min_free_percent)
# - processes: array of pairs (name min_count)
# - swap_threshold: integer percent threshold
# Example config (shell syntax):
# filesystems=(/ 10 /tmp 5 /var 5)
# processes=(nginx 1 mysql 2)
# swap_threshold=20

# Resolve default config path: accept -c, then env HEALTH_CHECK_CONFIG, then ./health_check.conf, then /etc/octopus/health_check.conf
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
DEFAULT_CONFIG1="$SCRIPT_DIR/health_check.conf"
DEFAULT_CONFIG2="/etc/octopus/health_check.conf"

CONFIG="${HEALTH_CHECK_CONFIG:-}" # allow env override

while getopts ":c:" opt; do
  case $opt in
    c)
      CONFIG="$OPTARG"
      ;;
    \?)
      echo "Usage: $0 [-c config_file]" >&2
      exit 2
      ;;
  esac
done

# If no config provided, pick defaults
if [ -z "$CONFIG" ]; then
  if [ -f "$DEFAULT_CONFIG1" ]; then
    CONFIG="$DEFAULT_CONFIG1"
  elif [ -f "$DEFAULT_CONFIG2" ]; then
    CONFIG="$DEFAULT_CONFIG2"
  fi
fi

if [ -n "${CONFIG:-}" ] && [ -f "$CONFIG" ]; then
  # shellcheck source=/dev/null
  source "$CONFIG"
fi

# Set sensible defaults if variables not provided by config
if ! declare -p filesystems >/dev/null 2>&1; then
  filesystems=(/ 10 /tmp 5 /var 5)
fi

if ! declare -p processes >/dev/null 2>&1; then
  processes=(nginx 1 mysql 2)
fi

: ${swap_threshold:=20}

report=""

# If a deploy lockfile exists and the PID inside is alive, exit quietly with status 0
# Lock path can be set via env `DEPLOY_LOCK` or `deploy_lock` variable in config.
deploy_lock_from_env=${DEPLOY_LOCK:-}
deploy_lock_from_config=${deploy_lock:-}

check_deploy_lock() {
  local lockpath
  if [ -n "$deploy_lock_from_env" ]; then
    lockpath="$deploy_lock_from_env"
  elif [ -n "$deploy_lock_from_config" ]; then
    lockpath="$deploy_lock_from_config"
  else
    lockpath="/tmp/octopus_deploy.lock"
    # also check script-local default
    if [ -f "$SCRIPT_DIR/.deploy.lock" ]; then
      lockpath="$SCRIPT_DIR/.deploy.lock"
    fi
  fi

  if [ ! -f "$lockpath" ]; then
    return 1
  fi

  pid=$(cat "$lockpath" 2>/dev/null || true)
  if [ -z "$pid" ]; then
    # empty or unreadable lockfile
    return 1
  fi

  # Check if PID is alive
  if kill -0 "$pid" 2>/dev/null; then
    return 0
  fi

  # Stale lockfile (pid not running)
  return 1
}

# If a live deploy lock is present, exit silently
if check_deploy_lock; then
  exit 0
fi

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
