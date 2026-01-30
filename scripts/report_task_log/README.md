# report_task_log.sh

A bash script that monitors output from long-running tasks and reports only new lines since the last run.

## Features

- ✅ **Incremental Reading**: Only outputs new lines since last run
- ✅ **Position Tracking**: Maintains state between runs
- ✅ **Log Rotation Handling**: Detects and handles log file rotation
- ✅ **Concurrent Run Prevention**: Uses file locking to prevent conflicts
- ✅ **Error Handling**: Graceful handling of missing or rotated files
- ✅ **Automation Friendly**: Works in scripts, cron jobs, or Telegram bots

## Requirements

- Bash 3.2+ (compatible with macOS default bash and Linux)
- Standard Unix utilities: `stat`, `dd`, `flock`, `cat`
- `flock` command (usually available by default on Linux; on macOS, may need to install via Homebrew: `brew install flock`)

## Installation

```bash
# Make the script executable
chmod +x report_task_log.sh

# Optionally, move to a directory in your PATH
sudo mv report_task_log.sh /usr/local/bin/
```

## Usage

### Basic Usage

1. **Start your long-running task with output redirection:**

```bash
# Redirect both stdout and stderr to a log file
long_task > /tmp/long_task.log 2>&1 &

# Or just stdout
long_task > /tmp/long_task.log &
```

2. **Run the reporting script to fetch new output:**

```bash
./report_task_log.sh /tmp/long_task.log
```

3. **Run again later to get only new lines:**

```bash
./report_task_log.sh /tmp/long_task.log
```

### Command Line

```
Usage: report_task_log.sh <log_file_path>

Arguments:
  log_file_path    Path to the log file to monitor

Environment Variables:
  REPORT_LOG_STATE_DIR    Directory to store state files (default: /tmp/report_task_log_state)
```

### Examples

#### Example 1: Monitoring a Git Repository Watcher

```bash
# Start a git watch script that outputs on changes
git_watch.sh /path/to/repo > /tmp/git_watch.log 2>&1 &

# Check for new git events
./report_task_log.sh /tmp/git_watch.log
```

#### Example 2: Using with Telegram Bot

```python
import subprocess

def get_task_updates():
    """Fetch new lines from long_task log"""
    try:
        result = subprocess.run(
            ['./report_task_log.sh', '/tmp/long_task.log'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"

# In your bot handler
@bot.message_handler(commands=['status'])
def send_status(message):
    updates = get_task_updates()
    if updates:
        bot.reply_to(message, updates)
    else:
        bot.reply_to(message, "No new updates")
```

#### Example 3: Using in Cron Job

```bash
# Add to crontab to check every 5 minutes
# crontab -e
*/5 * * * * /path/to/report_task_log.sh /tmp/long_task.log | mail -s "Task Updates" user@example.com
```

#### Example 4: Monitoring tail -f Style Output

```bash
# Start a tail -f command
tail -f /var/log/syslog > /tmp/syslog_monitor.log 2>&1 &

# Periodically check for new lines
while true; do
    echo "=== New Updates ==="
    ./report_task_log.sh /tmp/syslog_monitor.log
    sleep 10
done
```

#### Example 5: Custom State Directory

```bash
# Use a custom directory for state files
export REPORT_LOG_STATE_DIR="$HOME/.report_task_log_state"
./report_task_log.sh /tmp/long_task.log
```

## How It Works

1. **State Tracking**: The script stores the last read byte position in a state file
2. **Incremental Reading**: On each run, it reads from the last position to the current end of file
3. **Lock File**: Prevents multiple instances from running simultaneously for the same log file
4. **Log Rotation Detection**: If the file size is smaller than the last position, it assumes rotation and starts from the beginning

### State Files Location

By default, state files are stored in `/tmp/report_task_log_state/`:

- `<sanitized_log_path>.state` - Contains the last read byte position
- `<sanitized_log_path>.lock` - Lock file for preventing concurrent access

## Edge Cases Handled

✅ **First run**: Outputs all existing content  
✅ **No new content**: Exits silently with no output (state file is still updated)  
✅ **Log rotation**: Detects when file is smaller and restarts from beginning  
✅ **Log rotation to empty file**: Properly updates state even when rotated file is empty (0 bytes)  
✅ **Missing file**: Returns error with helpful message  
✅ **Concurrent runs**: Second instance exits immediately with error  
✅ **Corrupted state**: Resets to position 0 and continues  

## Limitations

- Requires the long-running task to output to a file (not just stdout)
- Doesn't support real-time streaming (processes complete lines only)
- State is lost if state directory is cleaned (e.g., `/tmp` on reboot)

## Troubleshooting

### macOS: flock command not found

If you get "command not found: flock" on macOS, install it via Homebrew:
```bash
brew install flock
```

### macOS: Bash version check

The script is compatible with macOS's default bash 3.2. To check your bash version:
```bash
bash --version
```

### No output on first run

Make sure the log file exists and has content:
```bash
ls -lh /tmp/long_task.log
cat /tmp/long_task.log
```

### Permission denied errors

Ensure you have read permissions on the log file and write permissions on the state directory:
```bash
chmod 644 /tmp/long_task.log
chmod 755 /tmp/report_task_log_state
```

### Another instance is running

If you get this error but no other instance is running, the lock file may be stale:
```bash
rm /tmp/report_task_log_state/<sanitized_log_path>.lock
```

### State directory on reboot

To persist state across reboots, use a custom state directory:
```bash
export REPORT_LOG_STATE_DIR="$HOME/.report_task_log_state"
```

## Testing

Run the included test script:
```bash
./test_report_task_log.sh
```

This will demonstrate all features including incremental reading, log rotation handling, and error cases.

## License

MIT License - Feel free to use and modify as needed.
