# Architecture and API Documentation

## Overview

Octopus Bot is a Telegram bot for managing Octopus servers. It provides:

1. **Script Execution**: Run long-running or one-time scripts with output streaming
2. **Server Monitoring**: Monitor CPU load and disk usage
3. **Alert System**: Get notified when thresholds are exceeded
4. **Async Architecture**: Non-blocking operations using Python's asyncio

## Architecture

### Layered Design

```
┌─────────────────────────────────────┐
│   Telegram Bot Handler (bot.py)     │
│  Commands: /start, /help, /status,  │
│           /run, streaming            │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   Server Operations (server_ops.py) │
│  - Script execution (async)          │
│  - System info gathering             │
│  - Error handling & logging          │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  System Libraries & External APIs    │
│  - asyncio (async execution)         │
│  - psutil (system metrics)           │
│  - subprocess (script execution)     │
└─────────────────────────────────────┘
```

### Module Structure

#### `config.py`
Handles configuration loading and validation.

**Key Classes:**
- `Script`: Represents a runnable script
- `DeviceMonitor`: Device/path to monitor for disk usage
- `BotConfig`: Complete bot configuration

**Key Functions:**
- `load_config(config_path: str | None) -> BotConfig`: Load and parse YAML config

#### `server_ops.py`
Executes scripts and gathers system information.

**Key Functions:**
- `run_script_streaming(script: Script) -> AsyncGenerator[str, None]`: Run script with streaming output
- `run_script_once(script: Script) -> str`: Run script and return complete output
- `get_disk_usage(device_path: str) -> tuple[float, float]`: Get disk usage percentage
- `get_cpu_load() -> dict[str, float]`: Get CPU load averages

#### `bot.py`
Telegram bot command handlers and message routing.

**Key Classes:**
- `OctopusBotHandler`: Main bot handler class

**Key Methods:**
- `start_command()`: Handle /start command
- `help_command()`: Handle /help command
- `status_command()`: Handle /status command (reports CPU and disk)
- `run_command()`: Handle /run command (executes one-time scripts)
- `run_streaming()`: Execute and stream long-running script output
- `start()`: Start the bot and begin polling
- `stop()`: Stop the bot

## Data Flow

### Command: /status

```
User /status
    ↓
bot.py: status_command()
    ↓
server_ops.py: get_cpu_load()
    ↓ & get_disk_usage() [for each device]
    ↓
Telegram message sent to user
```

### Command: /run <script>

```
User /run health-check
    ↓
bot.py: run_command()
    ↓
server_ops.py: run_script_once()
    ↓
subprocess execution with asyncio
    ↓
Output collected and sent to user
(split into chunks if >4000 chars)
```

### Long-Running Script Streaming

```
bot.py: run_streaming()
    ↓
server_ops.py: run_script_streaming()
    ↓
AsyncGenerator yields lines in real-time
    ↓
bot.py buffers output (3000 chars)
    ↓
Telegram messages sent periodically
```

## Configuration Schema

The YAML configuration file must follow this structure:

```yaml
long_running_scripts:
  - name: <string>           # Unique identifier for the script
    path: <string>           # Path to the script (relative or absolute)

one_time_scripts:
  - name: <string>           # Unique identifier for the script
    path: <string>           # Path to the script (relative or absolute)

monitored_devices:
  - name: <string>           # Display name for the device
    path: <string>           # Mount point or path to check
    alert_threshold: <float> # Percentage (0-100), default 80
```

## Error Handling

### Script Execution Errors

- **FileNotFoundError**: Script path doesn't exist → Caught and logged
- **RuntimeError**: Execution failed → User receives error message via Telegram
- **Subprocess failure**: Non-zero exit code → Logged as warning, not treated as failure

### Disk Usage Errors

- **Invalid path**: User receives error message
- **Permission denied**: Caught and logged
- **System call failure**: RuntimeError raised with descriptive message

### Configuration Errors

- **Missing TELEGRAM_TOKEN**: ValueError on startup
- **Missing config file**: FileNotFoundError
- **Invalid YAML**: yaml.YAMLError (from pyyaml)
- **Empty config**: ValueError

## Async Architecture

### Event Loop

The bot uses Python's asyncio event loop for:
- Handling multiple Telegram updates concurrently
- Non-blocking subprocess execution
- Timeout management for long-running operations

### Async Functions

Key async operations:
- `run_script_streaming()`: Uses `asyncio.create_subprocess_exec()`
- `run_script_once()`: Uses `asyncio.create_subprocess_exec()`
- All Telegram command handlers: `async def` with `ContextTypes.DEFAULT_TYPE`
- Bot polling: `await self.app.updater.start_polling()`

## Security Considerations

### Environment Variables

- **TELEGRAM_TOKEN**: Never stored in code, always from environment
- **CONFIG_FILE**: Optional, defaults to `config/config.yaml`

### File System Access

- Scripts must be explicitly listed in config
- Script paths are validated before execution
- Only configured scripts can be executed

### Remote Access

- SSH keys should be in `~/.ssh` with proper permissions
- Scripts can authenticate to remote servers via SSH

### User Validation

- Current implementation processes all Telegram users
- Recommendation: Add user ID validation in production

## Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| Load config | <100ms | YAML parsing of small file |
| Get CPU load | <10ms | System call only |
| Get disk usage | <50ms | Per device, using psutil |
| Script execution | Variable | Depends on script duration |
| Telegram message | 100-500ms | Network dependent |

### Optimization Tips

1. **Batch disk checks**: Monitor only essential devices
2. **Script timeouts**: Consider adding execution timeouts
3. **Message buffering**: Current buffer is 3000 chars, adjustable
4. **Polling interval**: Telegram polling is configurable in Application builder

## Extension Points

### Adding New Commands

1. Create method in `OctopusBotHandler`
2. Register in `_setup_handlers()`
3. Implement using existing `server_ops` functions

### Adding New System Metrics

1. Add function to `server_ops.py`
2. Call from appropriate command handler in `bot.py`
3. Add tests in `tests/test_server_ops.py`

### Custom Script Types

Extend `Script` dataclass for additional properties:

```python
@dataclass
class Script:
    name: str
    path: str
    long_running: bool = False
    timeout: int | None = None  # Optional timeout
    retry_count: int = 0        # Optional retry logic
```

Then update config loader and script execution functions.

## Testing Strategy

### Unit Tests

- **test_config.py**: Configuration loading and validation
- **test_server_ops.py**: Script execution and system info gathering

Tests use:
- `tempfile.TemporaryDirectory()` for isolated environments
- Mock objects for external dependencies
- `pytest.mark.asyncio` for async test functions

### Integration Tests

Recommended:
1. Create a test Telegram bot (use BotFather)
2. Test full command flow end-to-end
3. Mock external script execution
4. Verify message formatting and chunking

### Running Tests

```bash
# All tests
pytest tests/

# Specific test file
pytest tests/test_config.py

# With coverage
coverage run -m pytest tests/
coverage report -m
```

## Logging

### Log Configuration

- **Level**: INFO by default
- **Format**: `timestamp - logger_name - level - message`
- **Handlers**: File (`octopus_bot.log`) and stdout

### Key Log Points

- Configuration loaded
- Bot started/stopped
- Each command received
- Script execution start/completion
- Errors with full traceback (level=ERROR)
- Warnings for non-fatal issues (level=WARNING)

## Future Enhancements

1. **Background Monitoring**: Periodic health checks and alerts without user request
2. **User Authentication**: Verify user IDs before processing commands
3. **Command Scheduling**: Run scripts on a schedule (APScheduler integration)
4. **Database Logging**: Store execution history
5. **Metrics Export**: Prometheus metrics for monitoring
6. **Web Dashboard**: HTTP interface for status and control
7. **Multi-bot Support**: Manage multiple Octopus servers from one bot
8. **Script Output History**: Archive and query previous execution logs

## Troubleshooting Guide

See SETUP.md for detailed troubleshooting information.
