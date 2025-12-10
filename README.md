# Telegram bot to manage Octopus servers

This bot is used to support a number of tasks related to Octopus servers.

1. Run scripts specified in config file. For each script monitor the messages that
come from the server and send them to the user. These scripts are intended to run for
a long time.

2. Run specific scripts specified in config file. These scripts should be run once,
the output should be sent to the user.

3. Report the status of the server. Loads, free disk space on specific devices, as
provided by config file.

4. Notify user if some conditions are met (e.g. low disk space).

5. Broadcast messages to all subscribed users.

