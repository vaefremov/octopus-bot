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

## Admin users and admin-only scripts

You can restrict certain scripts so that only administrators may invoke them interactively via `/run` or `/stream` by adding `admin_only: true` to the script entry in your YAML config (works for `one_time_scripts` and `long_running_scripts`).

Admin users are determined by either setting the `ADMIN_USERS` environment variable to a comma-separated list of Telegram user IDs, e.g.: `export ADMIN_USERS="123456789,987654321"`, or by the default behavior where the first user to interact with the bot becomes the administrator. Periodic scripts run by the scheduler will still broadcast their output to subscribers; `admin_only` only restricts interactive invocation.

Example:

```yaml
long_running_scripts:
	- name: deploy
		path: ./scripts/deploy.sh
		admin_only: true
```

