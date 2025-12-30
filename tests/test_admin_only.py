"""Tests for admin-only script enforcement in bot commands."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from octopus_bot.bot import OctopusBotHandler
from octopus_bot.config import BotConfig, Script


def make_mock_app_builder():
    mock_builder = MagicMock()
    mock_app = MagicMock()
    mock_builder.return_value.token.return_value.build.return_value = mock_app
    return mock_builder, mock_app


def test_run_command_denies_non_admin():
    mock_builder, mock_app = make_mock_app_builder()
    with patch("octopus_bot.bot.Application.builder", mock_builder):
        cfg = BotConfig(
            telegram_token="t",
            long_running_scripts=[],
            one_time_scripts=[Script(name="secure", path="./scripts/secure.sh", admin_only=True)],
            monitored_devices=[],
            periodic_scripts=[],
        )
        bot = OctopusBotHandler(cfg)
        # Set a different first_subscriber so the test user is NOT admin
        bot.first_subscriber = 999999999

        mock_update = MagicMock()
        mock_update.effective_user.id = 111111111
        mock_update.message.reply_text = AsyncMock()

        mock_ctx = MagicMock()
        mock_ctx.args = ["secure"]

        asyncio.run(bot.run_command(mock_update, mock_ctx))

        mock_update.message.reply_text.assert_called()
        # Ensure permission denied message is returned
        called_with = mock_update.message.reply_text.call_args[0][0]
        assert "don't have permission" in called_with or "You don't have permission" in called_with


def test_run_command_allows_admin():
    mock_builder, mock_app = make_mock_app_builder()
    with patch("octopus_bot.bot.Application.builder", mock_builder), \
         patch("octopus_bot.bot.run_script_once", new=AsyncMock(return_value="ok")):
        cfg = BotConfig(
            telegram_token="t",
            long_running_scripts=[],
            one_time_scripts=[Script(name="secure", path="./scripts/secure.sh", admin_only=True)],
            monitored_devices=[],
            periodic_scripts=[],
        )
        bot = OctopusBotHandler(cfg)
        # Make the test user the first subscriber (admin)
        bot.first_subscriber = 111111111

        mock_update = MagicMock()
        mock_update.effective_user.id = 111111111
        mock_update.message.reply_text = AsyncMock()

        mock_ctx = MagicMock()
        mock_ctx.args = ["secure"]

        asyncio.run(bot.run_command(mock_update, mock_ctx))

        # Should have at least one reply about running/completed
        assert mock_update.message.reply_text.call_count >= 1


def test_stream_command_denies_non_admin():
    mock_builder, mock_app = make_mock_app_builder()
    with patch("octopus_bot.bot.Application.builder", mock_builder):
        cfg = BotConfig(
            telegram_token="t",
            long_running_scripts=[Script(name="secure_stream", path="./scripts/secure.sh", admin_only=True)],
            one_time_scripts=[],
            monitored_devices=[],
            periodic_scripts=[],
        )
        bot = OctopusBotHandler(cfg)
        bot.first_subscriber = 999999999

        mock_update = MagicMock()
        mock_update.effective_user.id = 111111111
        mock_update.message.reply_text = AsyncMock()

        mock_ctx = MagicMock()
        mock_ctx.args = ["secure_stream"]

        asyncio.run(bot.stream_command(mock_update, mock_ctx))

        mock_update.message.reply_text.assert_called()
        called_with = mock_update.message.reply_text.call_args[0][0]
        assert "don't have permission" in called_with or "You don't have permission" in called_with


def test_stream_command_allows_admin():
    mock_builder, mock_app = make_mock_app_builder()

    async def fake_stream(script):
        yield "line1"
        yield "line2"

    with patch("octopus_bot.bot.Application.builder", mock_builder), \
         patch("octopus_bot.bot.run_script_streaming", new=fake_stream):
        cfg = BotConfig(
            telegram_token="t",
            long_running_scripts=[Script(name="secure_stream", path="./scripts/secure.sh", admin_only=True)],
            one_time_scripts=[],
            monitored_devices=[],
            periodic_scripts=[],
        )
        bot = OctopusBotHandler(cfg)
        bot.first_subscriber = 111111111

        mock_update = MagicMock()
        mock_update.effective_user.id = 111111111
        mock_update.message.reply_text = AsyncMock()

        mock_ctx = MagicMock()
        mock_ctx.args = ["secure_stream"]

        asyncio.run(bot.stream_command(mock_update, mock_ctx))

        # Expect multiple replies for streaming
        assert mock_update.message.reply_text.call_count >= 2
