"""Main entry point for Octopus Bot."""

import asyncio
import logging
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from octopus_bot.bot import OctopusBotHandler
from octopus_bot.config import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("octopus_bot.log"),
        logging.StreamHandler(),
    ],
)

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
