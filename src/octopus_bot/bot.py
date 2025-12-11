"""Telegram bot handler for Octopus Bot."""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Set

import schedule

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
        self.subscribers: Set[int] = set()
        self.first_subscriber: int | None = None
        self.subscribers_file = "subscribers.json"
        self._load_subscribers()
        self._setup_handlers()

    def _load_subscribers(self) -> None:
        """Load subscribers from file."""
        try:
            if os.path.exists(self.subscribers_file):
                with open(self.subscribers_file, "r") as f:
                    subscriber_ids = json.load(f)
                    self.subscribers = set(subscriber_ids)
                    logger.info(f"Loaded {len(self.subscribers)} subscribers")
        except Exception as e:
            logger.error(f"Failed to load subscribers: {e}")

    def _save_subscribers(self) -> None:
        """Save subscribers to file."""
        try:
            with open(self.subscribers_file, "w") as f:
                json.dump(list(self.subscribers), f)
        except Exception as e:
            logger.error(f"Failed to save subscribers: {e}")

    def _setup_handlers(self) -> None:
        """Set up command handlers."""
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("status", self.status_command))
        self.app.add_handler(CommandHandler("run", self.run_command))
        self.app.add_handler(CommandHandler("stream", self.stream_command))
        # New broadcast-related handlers
        self.app.add_handler(CommandHandler("subscribe", self.subscribe_command))
        self.app.add_handler(CommandHandler("unsubscribe", self.unsubscribe_command))
        self.app.add_handler(CommandHandler("broadcast", self.broadcast_command))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""
        user = update.effective_user
        await update.message.reply_text(
            f"Hello {user.first_name}! I'm the Octopus Bot. "
            "Use /help to see available commands.\n\n"
            "Use /subscribe to receive broadcast messages."
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command."""
        help_text = (
            "/status - Get server status (CPU load, disk usage)\n"
            "/run <script_name> - Run a one-time script\n"
            "/stream <script_name> - Run a long-running script with streaming output\n"
            "/subscribe - Subscribe to broadcast messages\n"
            "/unsubscribe - Unsubscribe from broadcast messages\n"
            "/start - Start the bot\n"
            "/help - Show this help message"
        )
        
        # Add admin commands for authorized users
        if self._is_admin_user(update.effective_user.id):
            help_text += "\n\n**Admin Commands:**\n"
            help_text += "/broadcast <message> - Send broadcast to all subscribers"
        
        await update.message.reply_text(help_text)

    async def subscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /subscribe command."""
        user_id = update.effective_user.id
        if user_id not in self.subscribers:
            self.subscribers.add(user_id)
            # Track the first subscriber
            if self.first_subscriber is None:
                self.first_subscriber = user_id
            self._save_subscribers()
            await update.message.reply_text("✅ You have been subscribed to broadcast messages!")
        else:
            await update.message.reply_text("ℹ️ You are already subscribed to broadcast messages.")

    async def unsubscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /unsubscribe command."""
        user_id = update.effective_user.id
        if user_id in self.subscribers:
            self.subscribers.remove(user_id)
            self._save_subscribers()
            await update.message.reply_text("✅ You have been unsubscribed from broadcast messages.")
        else:
            await update.message.reply_text("ℹ️ You are not currently subscribed to broadcast messages.")

    async def broadcast_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /broadcast command - send message to all subscribers."""
        # Check if user is admin
        if not self._is_admin_user(update.effective_user.id):
            await update.message.reply_text("❌ You don't have permission to send broadcast messages.")
            return

        # Check if message is provided
        if not context.args:
            await update.message.reply_text("Usage: /broadcast <message>")
            return

        message = "📢 **Broadcast Message**\n\n" + " ".join(context.args)
        
        # Send broadcast to all subscribers
        successful_sends = 0
        failed_sends = 0
        
        for user_id in self.subscribers.copy():  # Use copy to avoid modification during iteration
            try:
                await self.app.bot.send_message(chat_id=user_id, text=message, parse_mode="Markdown")
                successful_sends += 1
            except Exception as e:
                logger.error(f"Failed to send broadcast to user {user_id}: {e}")
                failed_sends += 1
                # Remove user if bot is blocked
                if "bot was blocked" in str(e).lower():
                    self.subscribers.discard(user_id)
                    self._save_subscribers()

        await update.message.reply_text(
            f"✅ Broadcast sent!\n"
            f"Successful: {successful_sends}\n"
            f"Failed: {failed_sends}"
        )

    def _is_admin_user(self, user_id: int) -> bool:
        """
        Check if user is admin.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if user is admin, False otherwise
        """
        # For now, we can use environment variable or config
        admin_users = os.getenv("ADMIN_USERS", "")
        if admin_users:
            try:
                admin_ids = [int(id.strip()) for id in admin_users.split(",")]
                return user_id in admin_ids
            except ValueError:
                pass
        # Default: first user to interact with bot is admin
        if self.first_subscriber is None:
            return True  # First user is admin
        # If there is a first subscriber, check if this user is the first one
        return user_id == self.first_subscriber

    async def broadcast_output(self, title: str, output: str) -> None:
        """
        Broadcast script output to all subscribers.

        Args:
            title: Title of the broadcast
            output: Output content
        """
        # Skip if output is empty
        if not output or not output.strip():
            logger.debug(f"Skipping broadcast for '{title}': output is empty")
            return

        # Split output into chunks if too long
        if len(output) > 4000:
            chunks = [output[i : i + 4000] for i in range(0, len(output), 4000)]
        else:
            chunks = [output]

        for user_id in self.subscribers.copy():
            try:
                # Send title
                await self.app.bot.send_message(
                    chat_id=user_id,
                    text=f"📢 **{title}**",
                    parse_mode="Markdown"
                )
                
                # Send output chunks
                for i, chunk in enumerate(chunks):
                    await self.app.bot.send_message(
                        chat_id=user_id,
                        text=f"```\n{chunk}\n```",
                        parse_mode="Markdown"
                    )
                    
            except Exception as e:
                logger.error(f"Failed to broadcast to user {user_id}: {e}")
                # Remove user if bot is blocked
                if "bot was blocked" in str(e).lower():
                    self.subscribers.discard(user_id)
                    self._save_subscribers()

    async def execute_periodic_script(self, script_name: str) -> None:
        """
        Execute a periodic script and broadcast its output.

        Args:
            script_name: Name of the script to execute
        """
        # Find the script in periodic scripts
        script = next(
            (s for s in self.config.periodic_scripts if s.name == script_name),
            None,
        )

        if not script:
            logger.warning(f"Periodic script '{script_name}' not found in config")
            return

        try:
            logger.info(f"Executing periodic script: {script_name}")
            
            # Execute the script (treat as one-time script)
            from .config import Script
            script_obj = Script(name=script.name, path=script.path, long_running=False)
            output = await run_script_once(script_obj)

            # Broadcast the output
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            title = f"Periodic Script: {script_name} ({timestamp})"
            await self.broadcast_output(title, output)

            logger.info(f"Periodic script '{script_name}' completed and broadcasted")

        except Exception as e:
            logger.error(f"Error executing periodic script '{script_name}': {e}")
            # Broadcast error to subscribers
            error_msg = f"Error executing periodic script '{script_name}': {e}"
            await self.broadcast_output(f"Error: {script_name}", error_msg)

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
        
        # Schedule periodic scripts
        self._schedule_periodic_scripts()
        
        # Start polling for updates
        try:
            # Start polling
            polling_task = asyncio.create_task(
                self.app.updater.start_polling(
                    allowed_updates=["message", "callback_query"]
                )
            )
            
            # Start scheduler task
            scheduler_task = asyncio.create_task(self._run_scheduler())
            
            # Keep both running indefinitely
            await asyncio.gather(polling_task, scheduler_task)
        finally:
            # Cleanup on shutdown
            await self.app.updater.stop_polling()
            await self.app.stop()
            await self.app.shutdown()

    def _schedule_periodic_scripts(self) -> None:
        """Schedule periodic scripts based on configuration."""
        for script in self.config.periodic_scripts:
            interval = script.interval
            schedule.every(interval).seconds.do(
                lambda script_name=script.name: asyncio.create_task(
                    self.execute_periodic_script(script_name)
                )
            )
            logger.info(f"Scheduled periodic script '{script.name}' every {interval} seconds")

    async def _run_scheduler(self) -> None:
        """Run the scheduler in the background."""
        while True:
            schedule.run_pending()
            await asyncio.sleep(1)  # Check every second if something needs to run

    async def stop(self) -> None:
        """Stop the bot."""
        logger.info("Stopping Octopus Bot...")
        # Note: stop() is called automatically by run_polling on shutdown
        await self.app.stop()
