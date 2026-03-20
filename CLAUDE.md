# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Octopus Bot is a Python 3.12+ Telegram bot for managing server operations. It enables running shell scripts remotely, monitoring server status, broadcasting output to subscribers, and scheduling periodic tasks.

## Development Commands

```bash
# Activate virtual environment first
source .venv/bin/activate

# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_bot.py

# Run single test by keyword
python -m pytest -k "test_run_command"

# Run with coverage
python -m coverage run -m pytest && python -m coverage report

# Run the bot
python main.py
```

## Architecture

Three core modules under `src/octopus_bot/`:

- **`bot.py`** — `OctopusBotHandler` class handles all Telegram command routing (`/run`, `/stream`, `/status`, `/subscribe`, `/broadcast`, etc.), subscriber management (JSON persistence), periodic script scheduling, and config hot-reload monitoring. The `start()` method runs three concurrent async tasks: Telegram polling, the `schedule` job runner, and the config file monitor.
- **`config.py`** — Dataclasses (`Script`, `PeriodicScript`, `DeviceMonitor`, `BotConfig`) and `load_config()` for parsing `config/config.yaml`.
- **`server_ops.py`** — `run_script_streaming()` (async generator yielding lines), `run_script_once()`, `get_cpu_load()`, `get_disk_usage()`.

**Script types in config:**
- `one_time_scripts`: run to completion, return full output
- `long_running_scripts`: streaming output via `/stream`; use `admin_only: true` to restrict
- `periodic_scripts`: auto-scheduled with `interval` (seconds) or `time` (HH:MM); output broadcast to all subscribers

**Admin model:** First user to interact becomes admin, or set via `ADMIN_USERS` env var. Admin-only scripts reject non-admins for `/run`/`/stream`, but periodic broadcasts go to all subscribers regardless.

**Output chunking:** Script output is buffered and split at `broadcast_chunk_size` (default 4000 chars) before sending — Telegram's message size limit.

**Config hot-reload:** `check_config_changes()` runs every 10s, detects mtime changes, re-parses YAML, reschedules periodic scripts, and broadcasts success/failure to subscribers.

## Code Style

- Python 3.12+ syntax: use `str | int` unions, `list[T]`/`dict[K, V]` generics
- All bot command handlers: `async def ... -> None`
- Module-level loggers: `logger = logging.getLogger(__name__)`
- Escape user-facing content with `escape_markdown()` for Telegram Markdown
- Use `pathlib.Path` for file operations
- Private methods prefixed with `_`

## Environment Variables

- `TELEGRAM_TOKEN` — required, from BotFather
- `CONFIG_FILE` — optional, defaults to `config/config.yaml`
- `ADMIN_USERS` — optional, comma-separated Telegram user IDs

`config/config.yaml` is not tracked in git (use `config/config.example.yaml` as template).
