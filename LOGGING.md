# Logging Configuration

## Overview
The Octopus Bot uses Python's logging module to track bot operations, script execution, and errors. Verbose logs from external libraries are suppressed to keep console output clean.

## Current Configuration

### Log Levels
- **Application Logs** (octopus_bot): `INFO` - Shows bot startup, commands, and errors
- **httpx**: `WARNING` - Suppresses HTTP request details (e.g., polling messages)
- **telegram.ext**: `WARNING` - Suppresses Telegram library debug info
- **urllib3**: `WARNING` - Suppresses connection pool messages

### Output Destinations
1. **Console (stdout)** - Real-time logs during execution
2. **File** (`octopus_bot.log`) - Persistent log file in working directory

### Log Format
```
YYYY-MM-DD HH:MM:SS,mmm - logger_name - LEVEL - message
```

Example:
```
2025-12-10 14:06:55,699 - __main__ - INFO - Bot started. Press Ctrl+C to stop.
2025-12-10 14:06:55,699 - octopus_bot.bot - INFO - Starting Octopus Bot...
```

## Suppressed Logs

The following verbose logs from external libraries are now suppressed:

### httpx (HTTP Client)
**Before:**
```
2025-12-10 21:56:42,751 - httpx - INFO - HTTP Request: POST https://api.telegram.org/bot.../getUpdates "HTTP/1.1 200 OK"
```

**After:** Suppressed (only shows on WARNING or higher)

### telegram.ext
Suppresses debug information from the Telegram bot framework

### urllib3
Suppresses connection pool management messages

## What Still Gets Logged

✅ Bot initialization and startup
✅ Command received and executed
✅ Script execution start/completion
✅ Errors and exceptions
✅ Configuration loading issues
✅ Status command output
✅ Server operation results

## Viewing Logs

### Console Output
Logs are displayed in real-time while the bot is running:
```bash
python main.py
```

### Log File
View the complete log history:
```bash
tail -f octopus_bot.log
```

View last 50 lines:
```bash
tail -50 octopus_bot.log
```

Search for errors:
```bash
grep ERROR octopus_bot.log
```

## Customizing Log Levels

### To increase verbosity (see httpx logs again)
Edit `main.py` and change:
```python
logging.getLogger("httpx").setLevel(logging.INFO)  # Instead of WARNING
```

### To make logs even quieter
```python
logging.getLogger("octopus_bot").setLevel(logging.WARNING)  # Only warnings and errors
```

### To log only errors
```python
logging.basicConfig(level=logging.ERROR)
```

## Log File Rotation

For production deployment, consider rotating log files to prevent them from growing too large:

```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    "octopus_bot.log",
    maxBytes=10485760,  # 10MB
    backupCount=5       # Keep 5 backup files
)
```

## Sample Log Output

Here's what you'll see when the bot starts:

```
2025-12-10 14:06:55,658 - __main__ - INFO - Loading configuration...
2025-12-10 14:06:55,659 - __main__ - INFO - Initializing bot...
2025-12-10 14:06:55,699 - __main__ - INFO - Bot started. Press Ctrl+C to stop.
2025-12-10 14:06:55,699 - octopus_bot.bot - INFO - Starting Octopus Bot...
2025-12-10 14:06:56,000 - telegram.ext.Application - WARNING - Application started
2025-12-10 14:06:56,100 - telegram.ext.Application - WARNING - Updater started polling
```

When executing a command:
```
2025-12-10 14:07:15,234 - octopus_bot.bot - INFO - Starting script 'health-check'...
2025-12-10 14:07:16,456 - octopus_bot.bot - INFO - Script execution completed
```

On error:
```
2025-12-10 14:08:00,123 - octopus_bot.bot - ERROR - Error running script health-check: [error details]
```

## Environment Variables

Future enhancement - could support logging configuration via environment variables:
```bash
OCTOPUS_LOG_LEVEL=DEBUG python main.py
```

## Troubleshooting

### Too many logs?
Increase the suppression level:
```python
logging.getLogger("octopus_bot").setLevel(logging.WARNING)
```

### Not enough logs for debugging?
Decrease suppression:
```python
logging.getLogger("httpx").setLevel(logging.DEBUG)
logging.getLogger("telegram.ext").setLevel(logging.DEBUG)
```

### Need to disable file logging?
Remove the FileHandler from basicConfig:
```python
handlers=[logging.StreamHandler()]  # Only console
```

## Best Practices

1. **Check logs when bot doesn't respond** - Look for errors
2. **Monitor log file size** - Implement rotation in production
3. **Archive old logs** - Keep backups for auditing
4. **Use grep for searching** - `grep ERROR octopus_bot.log`
5. **Check timestamps** - Helps identify timing issues

## References

- Python logging: https://docs.python.org/3/library/logging.html
- httpx documentation: https://www.python-httpx.org/
- python-telegram-bot: https://python-telegram-bot.readthedocs.io/
