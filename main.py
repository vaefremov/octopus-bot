"""Main entry point for Octopus Bot."""

import asyncio
import logging
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from octopus_bot.bot import OctopusBotHandler
from octopus_bot.config import load_config

# Timed rotating file handler will be configured below
from logging.handlers import TimedRotatingFileHandler

# Suppress verbose logs from external libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
log_dir = Path("logs")
log_dir.mkdir(parents=True, exist_ok=True)

log_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler = TimedRotatingFileHandler(log_dir / "octopus_bot.log", when="midnight", backupCount=7)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO)

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

# Module logger for this script
logger = logging.getLogger(__name__)


def main():
    """Main entry point."""
    bot = None
    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = load_config()

        # Initialize bot
        logger.info("Initializing bot...")
        bot = OctopusBotHandler(config)

        # Start bot
        logger.info("Bot started. Press Ctrl+C to stop.")
        asyncio.run(bot.start())

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
