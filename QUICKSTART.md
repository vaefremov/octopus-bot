# Quick Start Guide

Get the Octopus Bot running in 5 minutes!

## 1. Get Your Telegram Bot Token

1. Open Telegram and find **@BotFather**
2. Send `/newbot` command
3. Follow the prompts to create your bot
4. Copy the token provided (looks like: `123456789:ABCDefGHIjKLmnoPQRstUVwxyz`)

## 2. Install and Setup

```bash
# Clone the repo
git clone <repository-url>
cd octopus-bot

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e .

# Install development dependencies (for testing)
pip install -e ".[dev]"
```

## 3. Configure

```bash
# Copy example config
cp config/config.example.yaml config/config.yaml

# Edit it to match your setup (optional for testing)
# The example config includes test scripts in ./scripts/
```

## 4. Set Environment Variable

```bash
# Set your bot token
export TELEGRAM_TOKEN="your_token_here"

# Optional: Set config file path (defaults to config/config.yaml)
export CONFIG_FILE="config/config.yaml"
```

## 5. Run the Bot

```bash
python main.py
```

You should see:
```
2024-11-23 10:30:00,123 - octopus_bot - INFO - Loading configuration...
2024-11-23 10:30:00,456 - octopus_bot - INFO - Initializing bot...
2024-11-23 10:30:00,789 - octopus_bot - INFO - Bot started. Press Ctrl+C to stop.
```

## 6. Test the Bot

Open Telegram and find your bot (search for its username).

### Try these commands:

1. `/start` - Get a greeting
2. `/help` - See available commands
3. `/status` - Check server status (CPU load, disk usage)
4. `/run health-check` - Run the example health check script
5. `/run backup` - Run the example backup script

## Example Config for Testing

The default `config/config.example.yaml` includes:

**Long-running scripts:**
- `deploy` - Simulates deployment process
- `logs` - Simulates log streaming

**One-time scripts:**
- `health-check` - Shows system health
- `backup` - Simulates backup process

**Monitored devices:**
- `root` (/) - Disk usage on root partition
- `home` (/home) - Disk usage on home partition

All use the example scripts in `./scripts/`

## Testing Everything Works

```bash
# Run the test suite
pytest tests/

# Run with coverage report
coverage run -m pytest tests/
coverage report
```

## Common Issues

### "ModuleNotFoundError: No module named 'octopus_bot'"

Make sure you installed with `-e` flag:
```bash
pip install -e .
```

### "TELEGRAM_TOKEN not set"

Set the environment variable:
```bash
export TELEGRAM_TOKEN="your_token_here"
```

### Bot doesn't respond to commands

1. Make sure bot is running: check terminal for "Bot started" message
2. Find your bot username in @BotFather conversation
3. Search for it in Telegram and send `/start`
4. Check logs in `octopus_bot.log`

### Scripts not executing

1. Verify scripts exist in `./scripts/` directory
2. Check they're executable: `ls -la scripts/`
3. Make sure config file points to correct paths
4. Test script manually: `./scripts/health_check.sh`

## What's Next?

- **Customize scripts**: Replace example scripts with your own
- **Add more commands**: See ARCHITECTURE.md for extension points
- **Deploy to production**: See SETUP.md for security considerations
- **Monitor your servers**: Add your own system checks and alerts

## Project Structure

```
octopus-bot/
├── main.py                  ← Run this to start the bot
├── config/
│   ├── config.example.yaml  ← Configuration template
│   └── config.yaml          ← Your configuration (create from example)
├── scripts/                 ← Example scripts
│   ├── health_check.sh
│   ├── backup.sh
│   ├── deploy.sh
│   └── tail_logs.sh
├── src/octopus_bot/        ← Source code
│   ├── config.py           ← Config loading
│   ├── server_ops.py       ← Script execution & system info
│   └── bot.py              ← Telegram bot handler
├── tests/                   ← Test suite
└── SETUP.md                ← Full setup guide
```

## Full Documentation

- **SETUP.md** - Detailed setup and configuration
- **ARCHITECTURE.md** - Architecture, API reference, and extension guide
- **README.md** - Project overview

Good luck! 🚀
