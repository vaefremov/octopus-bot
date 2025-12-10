# Bot Testing Guide

## Current Status

Your Octopus Bot is **running and connected to Telegram**! ✅

### Bot Details
- **Token**: `8167025342:AAHPdmQxyXl0GkA...` (shown in logs)
- **Status**: Polling for messages
- **Configuration**: Using `config/config.yaml`

## How to Test the Bot

### 1. Find Your Bot on Telegram

1. Open Telegram
2. Search for your bot using the username you created with @BotFather
3. Click "Start" or send `/start`

### 2. Available Commands

Once you've found the bot, try these commands:

#### Basic Commands
- `/start` - Greet the bot
- `/help` - See available commands
- `/status` - Get server status (CPU load, disk usage)

#### Script Commands
- `/run health-check` - Run health check script
- `/run backup` - Run backup script

### 3. Expected Responses

#### `/start`
```
Hello [Your Name]! I'm the Octopus Bot. 
Use /help to see available commands.
```

#### `/help`
```
/status - Get server status (CPU load, disk usage)
/run <script_name> - Run a script (once)
/start - Start the bot
/help - Show this help message
```

#### `/status`
Shows:
- 🖥️ CPU load (1min, 5min, 15min)
- 💾 Disk usage for monitored devices with alerts

#### `/run health-check`
Shows:
- System uptime
- Memory usage
- Disk usage
- Load average
- Running process count

## Testing Long-Running Scripts

To test streaming scripts:

1. First, configure the bot to use long-running scripts in `config/config.yaml`
2. The bot will stream output as it executes

Example for testing:
```yaml
long_running_scripts:
  - name: deploy
    path: ./scripts/deploy.sh
  - name: logs
    path: ./scripts/tail_logs.sh
```

## Troubleshooting While Running

### Bot not responding to commands?

1. **Check the terminal logs** - Look for error messages
2. **Verify bot username** - Make sure you're messaging the correct bot
3. **Restart the bot** - Press Ctrl+C and restart with:
   ```bash
   TELEGRAM_TOKEN=<your_token> python main.py
   ```

### Scripts not executing?

1. **Check script paths** - Verify paths in `config/config.yaml`
2. **Check permissions** - Ensure scripts are executable: `chmod +x scripts/script.sh`
3. **Check logs** - Terminal output shows errors

### Message too long?

Long script output is automatically split into chunks. This is normal!

## Logs

Bot logs are written to:
- **File**: `octopus_bot.log` (in the working directory)
- **Stdout**: Console output (you see this in the terminal)

View logs while running:
```bash
# In another terminal
tail -f octopus_bot.log
```

## Configuration Changes

To change what the bot does:

1. **Edit** `config/config.yaml`
2. **Restart** the bot (Ctrl+C, then run again)
3. New configuration takes effect immediately

## Security Notes

⚠️ **For Development/Testing Only**

The current setup is fine for testing, but for production:

1. **Never expose your token** - Don't commit it to git
2. **Use environment variables** - Store token in `.env` file
3. **Add user authentication** - Verify user IDs
4. **Restrict script access** - Only allow trusted scripts
5. **Use SSH keys** - For remote server access

## Next Steps

### After Initial Testing

1. **Customize scripts** - Replace example scripts with your actual deployment scripts
2. **Update config** - Point to your real servers and scripts
3. **Add monitoring** - Configure disk thresholds for your environment
4. **Test in production** - Deploy to a production server

### Advanced Features to Add

1. **Background monitoring** - Automatic alerts without user request
2. **Command scheduling** - Run scripts on schedule
3. **User authentication** - Restrict who can control the bot
4. **Web dashboard** - HTTP interface for status
5. **Database logging** - Store execution history

## Support

For issues or questions:

1. Check `QUICKSTART.md` for setup help
2. See `SETUP.md` for troubleshooting
3. Read `ARCHITECTURE.md` for technical details
4. Check `TEST_REPORT.md` for test results

## Stopping the Bot

Press `Ctrl+C` in the terminal:

```
^C
2025-12-10 14:05:23,456 - __main__ - INFO - Received keyboard interrupt, shutting down...
```

The bot will gracefully shut down.

## Running in Background

For production deployment, run the bot in the background:

```bash
# Using nohup
nohup python main.py > octopus_bot.out 2>&1 &

# Using tmux
tmux new-session -d -s octopus "python main.py"

# Using systemd (recommended for production)
# See SETUP.md for systemd service configuration
```

---

Happy testing! 🎉
