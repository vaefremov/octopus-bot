# Broadcast and Periodic Scripts Guide

## Overview

The Octopus Bot now supports:
1. **User Subscriptions** - Users can subscribe to receive broadcast messages
2. **Admin Broadcasting** - Administrators can send messages to all subscribers
3. **Periodic Scripts** - Scripts that run automatically on a schedule and broadcast output to subscribers

## User Commands

### Subscribe to Broadcasts
Users can subscribe to receive periodic script output and broadcast messages:

```bash
/subscribe
```

Response:
```
✅ You have been subscribed to broadcast messages!
```

### Unsubscribe from Broadcasts
Users can unsubscribe to stop receiving messages:

```bash
/unsubscribe
```

Response:
```
✅ You have been unsubscribed from broadcast messages.
```

## Admin Commands

### Send Manual Broadcast
Administrators can send messages to all subscribers:

```bash
/broadcast Your message here
```

Response:
```
✅ Broadcast sent!
Successful: 5
Failed: 0
```

The bot will notify the admin of successful and failed sends. If the bot is blocked by a user, they are automatically removed from the subscriber list.

## Periodic Scripts

### Configuration

Define periodic scripts in `config/config.yaml`:

```yaml
periodic_scripts:
  - name: hourly-health
    path: ./scripts/health_check.sh
    interval: 3600  # Run every 3600 seconds (1 hour)
  - name: daily-backup
    path: ./scripts/backup.sh
    interval: 86400  # Run every 86400 seconds (1 day)
```

### Interval Specifications

Common intervals (in seconds):
- `60` - Every minute
- `300` - Every 5 minutes
- `600` - Every 10 minutes
- `1800` - Every 30 minutes
- `3600` - Every 1 hour
- `86400` - Every 1 day (24 hours)
- `604800` - Every 1 week

### How It Works

1. **Configuration** - Periodic scripts are defined in `config.yaml`
2. **Startup** - Bot schedules all periodic scripts when it starts
3. **Execution** - Scripts run automatically at specified intervals
4. **Broadcasting** - Output is sent to all subscribers
5. **Logging** - Execution is logged with timestamps

### Example Output

When a periodic script runs, subscribers receive:

```
📢 **Periodic Script: hourly-health (2025-12-11 14:30:45)**
```

Followed by the script output.

### Error Handling

If a periodic script fails, subscribers receive:

```
📢 **Error: hourly-health**

Error executing periodic script 'hourly-health': [error details]
```

## Subscribers Management

### Storage

Subscribers are stored in `subscribers.json` in the working directory:

```json
[123456789, 987654321, 555666777]
```

The file is created automatically when users subscribe.

### Admin Identification

Admin status is determined by:
1. **Environment Variable** (`ADMIN_USERS`) - Comma-separated user IDs
2. **First User** - The first user to interact with the bot
3. **Configuration** - Can be set programmatically

Set admin users via environment variable:

```bash
export ADMIN_USERS="123456789,987654321"
python main.py
```

## Examples

### Setup Periodic Health Checks

1. **Configure in `config/config.yaml`:**

```yaml
periodic_scripts:
  - name: health-check
    path: ./scripts/health_check.sh
    interval: 3600  # Every hour
```

2. **Users subscribe:**

```
/subscribe
```

3. **Automatic execution:**

Every hour, the bot:
- Executes `./scripts/health_check.sh`
- Broadcasts output to all subscribers
- Logs the execution

### Daily Backup Broadcast

```yaml
periodic_scripts:
  - name: daily-backup
    path: ./scripts/backup.sh
    interval: 86400  # Daily
```

Users subscribe once and receive backup status daily.

### Administrator Sends Custom Message

```bash
/broadcast Scheduled maintenance at 2:00 AM UTC
```

All subscribers receive the message immediately.

## Log Output

When periodic scripts are scheduled and executed:

```
2025-12-11 14:15:32 - octopus_bot.bot - INFO - Scheduled periodic script 'hourly-health' every 3600 seconds
2025-12-11 14:15:32 - octopus_bot.bot - INFO - Scheduled periodic script 'daily-backup' every 86400 seconds
...
2025-12-11 15:15:32 - octopus_bot.bot - INFO - Executing periodic script: hourly-health
2025-12-11 15:15:33 - octopus_bot.bot - INFO - Periodic script 'hourly-health' completed and broadcasted
```

## Best Practices

1. **Use Reasonable Intervals** - Don't run scripts too frequently (minimum 60 seconds recommended)
2. **Test Scripts** - Test scripts manually before adding to periodic execution
3. **Monitor Output** - Check that script output is useful
4. **Set Admin Users** - Use environment variables for security
5. **Manage Subscribers** - Monitor `subscribers.json` for inactive users

## Troubleshooting

### Periodic scripts not running?

1. Check logs: `tail -f octopus_bot.log`
2. Verify config syntax
3. Ensure script paths are correct
4. Check interval values (in seconds)

### Subscribers not receiving messages?

1. Verify users have subscribed: `/subscribe`
2. Check if bot is blocked: review logs
3. Verify admin permissions for manual broadcasts

### Script output not appearing?

1. Test script manually: `./scripts/health_check.sh`
2. Check script permissions: `chmod +x ./scripts/health_check.sh`
3. Review logs for execution errors
   Response: "✅ Broadcast sent! Successful: 5 Failed: 0"

3. User receives broadcast:
   ```
   📢 Broadcast Message

   Hello everyone! This is a test broadcast message.
   ```

4. User unsubscribes:
   ```
   /unsubscribe
   ```
   Response: "✅ You have been unsubscribed from broadcast messages."

## Technical Details

- Subscribers are stored in a JSON file for persistence across bot restarts
- The first user to interact with the bot becomes the administrator if no `ADMIN_USERS` is set
- Error handling is implemented for users who have blocked the bot
- Broadcast messages are sent with Markdown formatting support
- The system tracks successful and failed message deliveries