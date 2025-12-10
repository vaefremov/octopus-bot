# Broadcast Messages Feature

The Octopus Bot now includes a broadcast messaging system that allows administrators to send messages to all subscribed users.

## How It Works

1. Users can subscribe to receive broadcast messages using the `/subscribe` command
2. Users can unsubscribe from broadcast messages using the `/unsubscribe` command
3. Administrators can send broadcast messages to all subscribers using the `/broadcast` command
4. Subscribers are stored persistently in a `subscribers.json` file

## Commands

### For All Users

- `/subscribe` - Subscribe to receive broadcast messages
- `/unsubscribe` - Unsubscribe from broadcast messages

### For Administrators

- `/broadcast <message>` - Send a message to all subscribed users

## Administration

### Setting Admin Users

To specify which users can send broadcast messages, set the `ADMIN_USERS` environment variable with a comma-separated list of Telegram user IDs:

```bash
export ADMIN_USERS="123456789,987654321"
```

If no `ADMIN_USERS` environment variable is set, the first user to interact with the bot will be considered the administrator.

### Managing Subscribers

Subscriber information is stored in a `subscribers.json` file in the bot's working directory. This file is automatically created and updated as users subscribe and unsubscribe.

## Example Usage

1. User subscribes to broadcasts:
   ```
   /subscribe
   ```
   Response: "✅ You have been subscribed to broadcast messages!"

2. Admin sends broadcast:
   ```
   /broadcast Hello everyone! This is a test broadcast message.
   ```
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