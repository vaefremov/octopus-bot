"""Telegram bot handler for Octopus Bot."""

import asyncio
import logging
from datetime import datetime

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from .config import BotConfig
from .server_ops import (
    get_cpu_load,
    get_disk_usage,
    run_script_once,
    run_script_streaming,
)

logger = logging.getLogger(__name__)


class OctopusBotHandler:
    """Handler for Telegram bot commands and interactions."""

    def __init__(self, config: BotConfig):
        """
        Initialize the bot handler.

        Args:
            config: Bot configuration
        """
        self.config = config
        self.app = Application.builder().token(config.telegram_token).build()
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Set up command handlers."""
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("status", self.status_command))
        self.app.add_handler(CommandHandler("run", self.run_command))
        self.app.add_handler(CommandHandler("stream", self.stream_command))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""
        user = update.effective_user
        await update.message.reply_text(
            f"Hello {user.first_name}! I'm the Octopus Bot. "
            "Use /help to see available commands."
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command."""
        help_text = (
            "/status - Get server status (CPU load, disk usage)\n"
            "/run <script_name> - Run a one-time script\n"
            "/stream <script_name> - Run a long-running script with streaming output\n"
            "/start - Start the bot\n"
            "/help - Show this help message"
        )
        await update.message.reply_text(help_text)

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /status command - report server status."""
        try:
            status_msg = "📊 **Server Status**\n\n"

            # CPU load
            try:
                cpu_load = get_cpu_load()
                status_msg += (
                    f"🖥️ **CPU Load**\n"
                    f"  1min: {cpu_load['1min']:.2f}\n"
                    f"  5min: {cpu_load['5min']:.2f}\n"
                    f"  15min: {cpu_load['15min']:.2f}\n\n"
                )
            except Exception as e:
                logger.error(f"Failed to get CPU load: {e}")
                status_msg += f"⚠️ Could not get CPU load: {e}\n\n"

            # Disk usage
            if self.config.monitored_devices:
                status_msg += "💾 **Disk Usage**\n"
                for device in self.config.monitored_devices:
                    try:
                        usage_percent, _ = get_disk_usage(device.path)
                        alert = "🔴" if usage_percent > device.alert_threshold else "🟢"
                        status_msg += (
                            f"  {alert} {device.name}: {usage_percent:.1f}%"
                        )
                        if usage_percent > device.alert_threshold:
                            status_msg += f" (⚠️ Alert threshold: {device.alert_threshold}%)"
                        status_msg += "\n"
                    except Exception as e:
                        logger.error(f"Failed to get disk usage for {device.name}: {e}")
                        status_msg += f"  ⚠️ {device.name}: Error - {e}\n"

            await update.message.reply_text(status_msg, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Error in status command: {e}")
            await update.message.reply_text(f"❌ Error getting status: {e}")

    async def run_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /run command - run a one-time script."""
        if not context.args:
            await update.message.reply_text(
                "Usage: /run <script_name>\n"
                f"Available scripts: {', '.join([s.name for s in self.config.one_time_scripts])}"
            )
            return

        script_name = context.args[0]
        script = next(
            (s for s in self.config.one_time_scripts if s.name == script_name),
            None,
        )

        if not script:
            await update.message.reply_text(
                f"❌ Script '{script_name}' not found.\n"
                f"Available scripts: {', '.join([s.name for s in self.config.one_time_scripts])}"
            )
            return

        try:
            await update.message.reply_text(
                f"⏳ Running script '{script_name}'..."
            )

            output = await run_script_once(script)

            # Split output into chunks if too long (Telegram limit is ~4096 chars)
            if len(output) > 4000:
                chunks = [output[i : i + 4000] for i in range(0, len(output), 4000)]
                for i, chunk in enumerate(chunks):
                    await update.message.reply_text(
                        f"📄 Output (part {i + 1}/{len(chunks)}):\n```\n{chunk}\n```",
                        parse_mode="Markdown",
                    )
            else:
                await update.message.reply_text(
                    f"✅ Script completed:\n```\n{output}\n```",
                    parse_mode="Markdown",
                )

        except Exception as e:
            logger.error(f"Error running script {script_name}: {e}")
            await update.message.reply_text(f"❌ Error running script: {e}")

    async def stream_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /stream command - run a long-running script with streaming output."""
        if not context.args:
            available = ', '.join([s.name for s in self.config.long_running_scripts]) if self.config.long_running_scripts else 'None configured'
            await update.message.reply_text(
                "Usage: /stream <script_name>\n"
                f"Available scripts: {available}"
            )
            return

        script_name = context.args[0]
        await self.run_streaming(update, script_name)

    async def run_streaming(
        self, update: Update, script_name: str
    ) -> None:
        """
        Run a long-running script with streaming output.

        Args:
            update: Telegram update
            script_name: Name of the script to run
        """
        script = next(
            (s for s in self.config.long_running_scripts if s.name == script_name),
            None,
        )

        if not script:
            await update.message.reply_text(
                f"❌ Long-running script '{script_name}' not found."
            )
            return

        try:
            await update.message.reply_text(
                f"▶️ Starting long-running script '{script_name}'..."
            )

            buffer = ""
            async for line in run_script_streaming(script):
                buffer += line + "\n"

                # Send buffered output in chunks
                if len(buffer) > 3000:
                    await update.message.reply_text(
                        f"📄 Output:\n```\n{buffer}\n```",
                        parse_mode="Markdown",
                    )
                    buffer = ""

            # Send remaining buffer
            if buffer:
                await update.message.reply_text(
                    f"📄 Output:\n```\n{buffer}\n```",
                    parse_mode="Markdown",
                )

            await update.message.reply_text(
                f"✅ Script '{script_name}' completed."
            )

        except Exception as e:
            logger.error(f"Error in streaming script {script_name}: {e}")
            await update.message.reply_text(f"❌ Error: {e}")

    async def start(self) -> None:
        """Start the bot and run polling indefinitely."""
        logger.info("Starting Octopus Bot...")
        # Initialize the application
        await self.app.initialize()
        await self.app.start()
        
        # Start polling for updates
        try:
            await self.app.updater.start_polling(
                allowed_updates=["message", "callback_query"]
            )
            # Keep polling running indefinitely
            while True:
                await asyncio.sleep(1)
        finally:
            # Cleanup on shutdown
            await self.app.updater.stop_polling()
            await self.app.stop()
            await self.app.shutdown()

    async def stop(self) -> None:
        """Stop the bot."""
        logger.info("Stopping Octopus Bot...")
        # Note: stop() is called automatically by run_polling on shutdown
        await self.app.stop()
