#!/usr/bin/env python
"""Test script to verify bot stays running."""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from octopus_bot.bot import OctopusBotHandler
from octopus_bot.config import load_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_bot():
    """Test bot startup and basic functionality."""
    try:
        logger.info("Loading configuration...")
        config = load_config()
        
        logger.info("Creating bot...")
        bot = OctopusBotHandler(config)
        
        logger.info("Bot initialized successfully")
        logger.info(f"Handlers configured: {len(bot.app.handlers)} groups")
        logger.info("Starting bot (will run for 10 seconds)...")
        
        # Create a task that runs for 10 seconds
        async def run_with_timeout():
            task = asyncio.create_task(bot.start())
            try:
                await asyncio.wait_for(task, timeout=10)
            except asyncio.TimeoutError:
                logger.info("Timeout reached, stopping bot")
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        await run_with_timeout()
        
        logger.info("✓ Bot ran successfully without errors")
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(test_bot())
