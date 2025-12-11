# Periodic Scripts and Broadcasting Implementation Summary

## Overview

Added complete periodic script execution and broadcasting system to the Octopus Bot. Users can now subscribe to receive output from scripts that run automatically on a schedule, and administrators can broadcast messages to all subscribers.

## Features Implemented

### 1. Periodic Script Configuration
- Added `PeriodicScript` dataclass to `config.py`
- Added `periodic_scripts` list to `BotConfig`
- Updated configuration loader to parse periodic scripts from YAML

**Example configuration:**
```yaml
periodic_scripts:
  - name: hourly-health
    path: ./scripts/health_check.sh
    interval: 3600  # seconds
  - name: daily-backup
    path: ./scripts/backup.sh
    interval: 86400  # seconds
```

### 2. User Subscription System
- **Already Existed** in bot.py:
  - `/subscribe` - Users subscribe to broadcasts
  - `/unsubscribe` - Users unsubscribe
  - Persistent subscriber storage in `subscribers.json`

### 3. Admin Broadcasting
- **Already Existed** in bot.py:
  - `/broadcast <message>` - Send message to all subscribers
  - Admin identification (via ADMIN_USERS env var or first user)
  - Automatic removal of blocked users

### 4. Periodic Script Execution
**New methods in `bot.py`:**

- `broadcast_output(title, output)` - Send script output to all subscribers
  - Handles large outputs by chunking (4000 chars per message)
  - Graceful error handling for blocked users
  
- `execute_periodic_script(script_name)` - Execute a periodic script
  - Runs the script
  - Captures output
  - Broadcasts to subscribers
  - Logs execution with timestamp
  - Broadcasts errors if script fails

- `_schedule_periodic_scripts()` - Setup schedule for all configured scripts
  - Uses `schedule` library for simple interval-based scheduling
  - Schedules all scripts at bot startup

- `_run_scheduler()` - Background scheduler task
  - Runs asynchronously alongside polling
  - Checks every second if scripts need execution

### 5. Bot Lifecycle Integration
**Updated `start()` method:**
- Schedules periodic scripts at startup
- Runs polling and scheduler concurrently using `asyncio.gather()`
- Proper cleanup on shutdown

## Files Modified

### 1. `src/octopus_bot/config.py`
- Added `PeriodicScript` dataclass
- Added `periodic_scripts: list[PeriodicScript]` to `BotConfig`
- Updated `load_config()` to parse periodic scripts

### 2. `src/octopus_bot/bot.py`
- Added `import schedule` for scheduling
- Added `broadcast_output()` method - broadcast to subscribers
- Added `execute_periodic_script()` method - execute and broadcast
- Added `_schedule_periodic_scripts()` method - setup scheduling
- Added `_run_scheduler()` method - run scheduler loop
- Updated `start()` method - integrated scheduler
- Updated imports: `from .config import Script, PeriodicScript` in execute_periodic_script

### 3. `config/config.example.yaml`
- Added `periodic_scripts` section with examples

### 4. `tests/test_bot.py`
- Updated mock_config fixture to include `periodic_scripts=[]`

### 5. `tests/test_config.py`
- Added `test_load_config_with_periodic_scripts()` test
- Validates periodic script parsing

### 6. `BROADCAST.md`
- Completely rewritten with comprehensive documentation
- Covers subscriptions, broadcasting, and periodic scripts
- Includes examples and troubleshooting

## Design Decisions

### 1. Scheduler Choice
Used `schedule` library because:
- Simple interval-based scheduling (perfect for this use case)
- Lightweight, no external dependencies beyond existing ones
- Easy to understand and maintain
- Sufficient for current requirements

### 2. Async Integration
- Scheduler runs in a separate asyncio task
- Uses `asyncio.gather()` to run polling and scheduler concurrently
- Each script execution is async to avoid blocking the bot

### 3. Error Handling
- Script failures are logged and broadcasted to subscribers
- Blocked users are automatically removed from subscriber list
- Execution failures don't crash the bot

### 4. Output Broadcasting
- Output is chunked to respect Telegram's 4096 character limit
- Timestamp is included in broadcast title
- Clear formatting with markdown

## Testing

All tests pass (21/21):
```
tests/test_bot.py::test_* ✅ (10 tests)
tests/test_config.py::test_* ✅ (6 tests)
  - Including new test_load_config_with_periodic_scripts
tests/test_server_ops.py::test_* ✅ (5 tests)
```

## Usage Example

### Setup
1. **Configure periodic scripts in `config/config.yaml`:**
```yaml
periodic_scripts:
  - name: health-check
    path: ./scripts/health_check.sh
    interval: 3600  # Every hour
```

2. **Set admin users (optional):**
```bash
export ADMIN_USERS="123456789"
```

3. **Start bot:**
```bash
export TELEGRAM_TOKEN="your_token"
python main.py
```

### User Interaction
1. User subscribes: `/subscribe`
2. Every 3600 seconds, bot executes health_check.sh
3. Output is broadcast to all subscribers
4. Admin can send manual broadcasts: `/broadcast message`

## Logs
When running, you'll see:
```
2025-12-11 14:15:32 - octopus_bot.bot - INFO - Scheduled periodic script 'health-check' every 3600 seconds
...
2025-12-11 15:15:32 - octopus_bot.bot - INFO - Executing periodic script: health-check
2025-12-11 15:15:33 - octopus_bot.bot - INFO - Periodic script 'health-check' completed and broadcasted
```

## Future Enhancements
- Cron-style scheduling (0 0 * * * format)
- Script output filtering/formatting
- Per-user subscription preferences
- Web dashboard for script history
- Database storage instead of JSON

## Dependencies
- Added in pyproject.toml (already present): `schedule>=1.2.2`

## Backward Compatibility
- Fully backward compatible
- Optional feature (no periodic scripts if not configured)
- Existing /subscribe, /unsubscribe, /broadcast continue to work
