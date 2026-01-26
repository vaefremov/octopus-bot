# AGENTS.md

This file provides guidelines and commands for agentic coding agents working in the Octopus Bot repository.

## Project Overview

Octopus Bot is a Python 3.12+ Telegram bot for managing server operations. It uses an async architecture with the following key components:

- **bot.py**: Main Telegram bot handler with command routing
- **server_ops.py**: Server operations (script execution, system monitoring)  
- **config.py**: Configuration loading and data structures
- **main.py**: Entry point with logging configuration

## Development Commands

### Testing
```bash
# Run all tests
source .venv/bin/activate && python -m pytest

# Run specific test file
source .venv/bin/activate && python -m pytest tests/test_bot.py

# Run single test with keyword matching
source .venv/bin/activate && python -m pytest -k "test_run_command"

# Run with coverage
source .venv/bin/activate && python -m coverage run -m pytest
source .venv/bin/activate && python -m coverage report
```

### Code Quality
```bash
# Type checking (uses pyright configuration in pyproject.toml)
# No explicit typecheck command - pyright runs automatically in editors

# Install dependencies
source .venv/bin/activate && pip install -e .
```

### Running the Bot
```bash
# Run with configuration from environment
source .venv/bin/activate && python main.py
```

## Code Style Guidelines

### Imports
- Standard library imports first, followed by third-party, then local imports
- Use `from .config import` for relative imports within the package
- Group imports with no blank lines between groups, one blank line between groups

### Type Hints
- Use Python 3.12+ union types: `str | int` instead of `Union[str, int]`
- Use `list[Type]` instead of `List[Type]`
- Use `dict[KeyType, ValueType]` instead of `Dict[KeyType, ValueType]`
- Always type function parameters and return values
- Use `-> None:` for functions that don't return values

### Dataclasses
- Use `@dataclass` for configuration objects and simple data containers
- Include type hints for all fields
- Use default values for optional fields
- Implement `__post_init__` for complex initialization (e.g., setting default list values)

### Async/Await
- All bot command handlers must be async and return `None`
- Use `asyncio.create_task()` for background tasks
- Use `async for` when iterating over async generators
- Handle subprocess with `asyncio.create_subprocess_exec()`

### Error Handling
- Log errors with appropriate level using the logger: `logger.error(f"Context: {error}")`
- Raise descriptive exceptions with context
- Handle FileNotFoundError for script validation
- Use try/except blocks around external operations (subprocess, file I/O, network calls)

### Logging
- Use module-level logger: `logger = logging.getLogger(__name__)`
- Log at appropriate levels:
  - `logger.debug()` for detailed debugging info
  - `logger.info()` for important state changes
  - `logger.warning()` for recoverable issues
  - `logger.error()` for errors with exceptions
- Include context in log messages (what operation, what data)

### String Handling
- Use f-strings for formatted strings
- Escape Markdown characters in user-facing content using the `escape_markdown()` function
- Handle encoding with `errors="replace"` when decoding subprocess output

### File Operations
- Use `pathlib.Path` for file path operations
- Handle file existence checks with `.exists()`
- Use context managers (`with open(...)`) for file I/O
- Store subscriber data in JSON format

### Configuration
- Environment variables for secrets: `TELEGRAM_TOKEN`, `ADMIN_USERS`, `CONFIG_FILE`
- YAML configuration for script definitions and settings
- Support both file-based and environment-based configuration
- Validate configuration at startup

### Testing Patterns
- Use `@pytest.fixture` for test setup
- Mock external dependencies with `unittest.mock`
- Use `pytest.mark.asyncio` for async test functions
- Test both success and error cases
- Use temporary files for file-based tests

### Naming Conventions
- **Functions**: `snake_case` with descriptive names
- **Classes**: `PascalCase` (e.g., `OctopusBotHandler`, `BotConfig`)
- **Constants**: `UPPER_SNAKE_CASE` (rarely used)
- **Private methods**: `_underscore_prefix` for internal methods
- **Variables**: `snake_case`, be descriptive

### Docstrings
- Use triple quotes with docstring format
- Include Args:, Returns:, and Raises: sections as appropriate
- Keep docstrings concise but informative
- Document public API methods thoroughly

### Git and Version Control
- Keep config/config.yaml out of version control (use config.example.yaml)
- Include example configurations in version control
- Log files (.coverage, *.log) should be gitignored

## Project Structure

```
src/octopus_bot/          # Main package
├── __init__.py
├── bot.py                # Telegram bot command handlers
├── config.py             # Configuration loading and dataclasses
└── server_ops.py         # System operations and script execution

tests/                     # Test suite
├── conftest.py           # Pytest configuration
├── test_*.py            # Unit and integration tests

config/                    # Configuration files
├── config.example.yaml   # Example configuration
└── config.yaml          # Actual config (not in git)

scripts/                   # Executable scripts referenced in config
├── *.sh                 # Shell scripts
└── *.py                 # Python scripts

logs/                      # Runtime logs (auto-created)
└── octopus_bot.log      # Main log file
```

## Key Implementation Details

- **Async Architecture**: All bot operations are non-blocking using asyncio
- **Subscriber Management**: Users stored in subscribers.json, supports broadcast messaging
- **Script Arguments**: Scripts can have command-line arguments defined in config
- **Admin Controls**: Admin-only scripts enforced via `_is_admin_user()` method
- **Periodic Tasks**: Uses `schedule` library with async wrapper
- **Config Reloading**: Hot configuration reload supported with file monitoring
- **Output Chunking**: Large script outputs split into Telegram-friendly chunks

## Common Patterns

### Command Handler Structure
```python
async def command_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /command command."""
    try:
        # Validate input
        if not context.args:
            await update.message.reply_text("Usage: /command <args>")
            return
            
        # Execute operation
        result = await some_operation()
        
        # Send response (chunked if needed)
        await update.message.reply_text(f"✅ Result: {result}")
        
    except Exception as e:
        logger.error(f"Error in command_name: {e}")
        await update.message.reply_text(f"❌ Error: {e}")
```

### Script Execution Pattern
```python
# Streaming execution (for long-running scripts)
async for line in run_script_streaming(script):
    buffer += line + "\n"
    if len(buffer) > self.chunk_size:
        await update.message.reply_text(f"```\n{buffer}\n```", parse_mode="Markdown")
        buffer = ""

# One-time execution
output = await run_script_once(script)
```

### Configuration Updates
- Changes to config/config.yaml are automatically detected and reloaded
- Broadcast notifications sent to subscribers on config reload success/failure
- Periodic script schedules are updated on config changes