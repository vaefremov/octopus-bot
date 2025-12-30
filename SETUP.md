# Setup and Installation Guide

## Prerequisites

- Python 3.12 or higher
- pip or similar package manager
- A Telegram bot token from BotFather

## Installation Steps

### 1. Clone the repository

```bash
git clone <repository-url>
cd octopus-bot
```

### 2. Create a virtual environment (optional but recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -e .
```

### 4. Set up configuration

Copy the example configuration file:

```bash
cp config/config.example.yaml config/config.yaml
```

Edit `config/config.yaml` to match your setup:

```yaml
# Long-running scripts that stream output to the user
long_running_scripts:
  - name: deploy
    path: ./scripts/deploy.sh
  - name: logs
    path: ./scripts/tail_logs.sh

# One-time scripts that run once and return output
one_time_scripts:
  - name: health-check
    path: ./scripts/health_check.sh
  - name: backup
    path: ./scripts/backup.sh

# Devices/paths to monitor for disk usage
monitored_devices:
  - name: root
    path: /
    alert_threshold: 85
  - name: home
    path: /home
    alert_threshold: 80
```

### 5. Set environment variables

```bash
export TELEGRAM_TOKEN="your_bot_token_here"
export CONFIG_FILE="config/config.yaml"  # Optional, defaults to config/config.yaml
# Optional: list admin users (comma-separated Telegram user IDs)
# These users may invoke scripts marked with `admin_only: true`
export ADMIN_USERS="123456789,987654321"
```

### 6. Run the bot

```bash
python main.py
```

## Configuration Guide

### Config File Structure

The configuration file is in YAML format with three main sections:

#### Long-Running Scripts

Scripts that are expected to run for an extended period. Output is streamed to the user in real-time.

```yaml
long_running_scripts:
  - name: deploy
    path: ./scripts/deploy.sh
```

#### One-Time Scripts

Scripts that execute once and return their complete output.

```yaml
one_time_scripts:
  - name: health-check
    path: ./scripts/health_check.sh
```

#### Monitored Devices

File systems or paths to monitor for disk usage.

```yaml
monitored_devices:
  - name: root
    path: /
    alert_threshold: 85  # Alert when usage exceeds 85%
```

## Available Commands

Once the bot is running, users can interact with it via these Telegram commands:

- `/start` - Start the bot and receive a greeting
- `/help` - Display available commands
- `/status` - Get server status (CPU load, disk usage)
- `/run <script_name>` - Execute a one-time script

Example:
```
/run health-check
```

## Creating Scripts

All scripts must be executable. Example script:

```bash
#!/bin/bash
# scripts/health_check.sh

echo "Checking system health..."
uptime
df -h
free -h
```

Make it executable:
```bash
chmod +x scripts/health_check.sh
```

## Security Considerations

1. **Telegram Token**: Store your bot token in an environment variable, never in code
2. **SSH Keys**: For remote server access, use SSH keys stored in `~/.ssh` with appropriate permissions:
   ```bash
   chmod 600 ~/.ssh/id_rsa
   chmod 700 ~/.ssh
   ```
3. **Script Permissions**: Only allow the bot to run trusted scripts with appropriate permissions
4. **User Access**: Restrict bot access by verifying user IDs in production
  - Use the `ADMIN_USERS` environment variable to list admin Telegram user IDs (comma-separated).
  - Mark sensitive scripts in the YAML config with `admin_only: true` to prevent interactive invocation by non-admins.

## Logging

The bot logs to both file and stdout:
- **File**: `octopus_bot.log` in the working directory
- **Stdout**: Console output for real-time monitoring

Log format: `timestamp - logger_name - level - message`

## Troubleshooting

### Bot not starting

1. Verify `TELEGRAM_TOKEN` is set correctly
2. Check that the config file exists and is valid YAML
3. Ensure all script paths in config exist and are executable
4. Check logs in `octopus_bot.log` for detailed error messages

### Scripts not executing

1. Verify script path is correct and absolute or relative from the working directory
2. Ensure scripts have execute permissions: `chmod +x script.sh`
3. Test the script manually from the command line
4. Check logs for specific error messages

### Disk usage not reported

1. Verify the path exists and is accessible
2. Ensure the user running the bot has permission to check disk usage
3. Check that `psutil` package is installed: `pip list | grep psutil`

## Performance Notes

- Long-running scripts output is buffered (3000 characters) before sending to Telegram
- Disk usage checks use `psutil` for efficiency
- CPU load uses system `getloadavg()` call
- Each command request is processed asynchronously

## Testing

Run the test suite:

```bash
pip install pytest pytest-asyncio
pytest tests/
```

Run tests with coverage:

```bash
pip install coverage
coverage run -m pytest tests/
coverage report
```

## Development

### Project Structure

```
octopus-bot/
├── src/octopus_bot/
│   ├── __init__.py          # Package initialization
│   ├── config.py            # Configuration loading and validation
│   ├── server_ops.py        # Server operations (scripts, system info)
│   └── bot.py              # Telegram bot handler
├── tests/
│   ├── conftest.py         # Pytest configuration
│   ├── test_config.py      # Config loading tests
│   └── test_server_ops.py  # Server operations tests
├── config/
│   └── config.example.yaml # Example configuration
├── main.py                 # Entry point
├── pyproject.toml          # Project metadata and dependencies
└── README.md              # Project overview
```

### Adding New Commands

Edit `src/octopus_bot/bot.py`:

1. Add a new method to `OctopusBotHandler` class
2. Register the handler in `_setup_handlers()`
3. Add tests in `tests/test_bot.py`

Example:

```python
async def custom_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /custom command."""
    await update.message.reply_text("Custom response")

# In _setup_handlers():
self.app.add_handler(CommandHandler("custom", self.custom_command))
```

## License

[Add your license here]

## Support

For issues and questions, please open an issue on the project repository.
