"""Unit tests for bot functionality."""

import asyncio
import json
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import User
from telegram.ext import Application, CommandHandler

from octopus_bot.bot import OctopusBotHandler
from octopus_bot.config import BotConfig, DeviceMonitor, Script


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    return BotConfig(
        telegram_token="test_token",
        long_running_scripts=[],
        one_time_scripts=[],
        monitored_devices=[],
    )


@pytest.fixture
def temp_subscribers_file():
    """Create a temporary subscribers file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        temp_file = f.name
    
    yield temp_file
    
    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)


def test_init_with_subscribers_file(mock_config):
    """Test bot initialization with subscribers file."""
    with patch("octopus_bot.bot.Application.builder") as mock_builder:
        mock_app = MagicMock()
        mock_builder.return_value.token.return_value.build.return_value = mock_app
        
        # Create bot with custom subscribers file
        bot = OctopusBotHandler(mock_config)
        
        # Test that subscribers is initialized as empty set
        assert isinstance(bot.subscribers, set)
        assert len(bot.subscribers) == 0


def test_load_subscribers_success(mock_config, temp_subscribers_file):
    """Test loading subscribers from file."""
    # Create a file with some subscriber IDs
    subscriber_ids = [123456789, 987654321]
    with open(temp_subscribers_file, "w") as f:
        json.dump(subscriber_ids, f)
    
    with patch("octopus_bot.bot.Application.builder") as mock_builder:
        mock_app = MagicMock()
        mock_builder.return_value.token.return_value.build.return_value = mock_app
        
        # Create bot with custom subscribers file
        bot = OctopusBotHandler(mock_config)
        bot.subscribers_file = temp_subscribers_file
        bot._load_subscribers()
        
        assert len(bot.subscribers) == 2
        assert 123456789 in bot.subscribers
        assert 987654321 in bot.subscribers


def test_load_subscribers_file_not_found(mock_config):
    """Test loading subscribers when file doesn't exist."""
    with patch("octopus_bot.bot.Application.builder") as mock_builder:
        mock_app = MagicMock()
        mock_builder.return_value.token.return_value.build.return_value = mock_app
        
        # Create bot with non-existent subscribers file
        bot = OctopusBotHandler(mock_config)
        bot.subscribers_file = "/nonexistent/file.json"
        bot._load_subscribers()
        
        # Should still have empty subscribers
        assert len(bot.subscribers) == 0


def test_save_subscribers_success(mock_config, temp_subscribers_file):
    """Test saving subscribers to file."""
    with patch("octopus_bot.bot.Application.builder") as mock_builder:
        mock_app = MagicMock()
        mock_builder.return_value.token.return_value.build.return_value = mock_app
        
        # Create bot with custom subscribers file
        bot = OctopusBotHandler(mock_config)
        bot.subscribers_file = temp_subscribers_file
        bot.subscribers = {123456789, 987654321}
        bot._save_subscribers()
        
        # Check that file was created with correct data
        with open(temp_subscribers_file, "r") as f:
            saved_ids = json.load(f)
        
        assert set(saved_ids) == bot.subscribers


def test_subscribe_command_new_user(mock_config):
    """Test subscribe command for new user."""
    with patch("octopus_bot.bot.Application.builder") as mock_builder:
        mock_app = MagicMock()
        mock_builder.return_value.token.return_value.build.return_value = mock_app
        
        bot = OctopusBotHandler(mock_config)
        bot._save_subscribers = MagicMock()  # Mock file saving
        
        # Create mock update and context
        mock_update = MagicMock()
        mock_update.effective_user.id = 123456789
        mock_update.message.reply_text = AsyncMock()
        
        mock_context = MagicMock()
        
        # Run subscribe command
        asyncio.run(bot.subscribe_command(mock_update, mock_context))
        
        # Check that user was added to subscribers
        assert 123456789 in bot.subscribers
        bot._save_subscribers.assert_called_once()
        mock_update.message.reply_text.assert_called_once_with(
            "✅ You have been subscribed to broadcast messages!"
        )


def test_subscribe_command_existing_user(mock_config):
    """Test subscribe command for existing user."""
    with patch("octopus_bot.bot.Application.builder") as mock_builder:
        mock_app = MagicMock()
        mock_builder.return_value.token.return_value.build.return_value = mock_app
        
        bot = OctopusBotHandler(mock_config)
        bot._save_subscribers = MagicMock()  # Mock file saving
        bot.subscribers = {123456789}  # User already subscribed
        
        # Create mock update and context
        mock_update = MagicMock()
        mock_update.effective_user.id = 123456789
        mock_update.message.reply_text = AsyncMock()
        
        mock_context = MagicMock()
        
        # Run subscribe command
        asyncio.run(bot.subscribe_command(mock_update, mock_context))
        
        # Check that user is still in subscribers (no change)
        assert len(bot.subscribers) == 1
        assert 123456789 in bot.subscribers
        bot._save_subscribers.assert_not_called()
        mock_update.message.reply_text.assert_called_once_with(
            "ℹ️ You are already subscribed to broadcast messages."
        )


def test_unsubscribe_command_existing_user(mock_config):
    """Test unsubscribe command for existing user."""
    with patch("octopus_bot.bot.Application.builder") as mock_builder:
        mock_app = MagicMock()
        mock_builder.return_value.token.return_value.build.return_value = mock_app
        
        bot = OctopusBotHandler(mock_config)
        bot._save_subscribers = MagicMock()  # Mock file saving
        bot.subscribers = {123456789}  # User subscribed
        
        # Create mock update and context
        mock_update = MagicMock()
        mock_update.effective_user.id = 123456789
        mock_update.message.reply_text = AsyncMock()
        
        mock_context = MagicMock()
        
        # Run unsubscribe command
        asyncio.run(bot.unsubscribe_command(mock_update, mock_context))
        
        # Check that user was removed from subscribers
        assert len(bot.subscribers) == 0
        bot._save_subscribers.assert_called_once()
        mock_update.message.reply_text.assert_called_once_with(
            "✅ You have been unsubscribed from broadcast messages."
        )


def test_unsubscribe_command_nonexistent_user(mock_config):
    """Test unsubscribe command for user not subscribed."""
    with patch("octopus_bot.bot.Application.builder") as mock_builder:
        mock_app = MagicMock()
        mock_builder.return_value.token.return_value.build.return_value = mock_app
        
        bot = OctopusBotHandler(mock_config)
        bot._save_subscribers = MagicMock()  # Mock file saving
        bot.subscribers = set()  # No subscribers
        
        # Create mock update and context
        mock_update = MagicMock()
        mock_update.effective_user.id = 123456789
        mock_update.message.reply_text = AsyncMock()
        
        mock_context = MagicMock()
        
        # Run unsubscribe command
        asyncio.run(bot.unsubscribe_command(mock_update, mock_context))
        
        # Check that subscribers is still empty
        assert len(bot.subscribers) == 0
        bot._save_subscribers.assert_not_called()
        mock_update.message.reply_text.assert_called_once_with(
            "ℹ️ You are not currently subscribed to broadcast messages."
        )


def test_is_admin_user_with_env_var(mock_config):
    """Test admin user check with environment variable."""
    with patch("octopus_bot.bot.Application.builder") as mock_builder, \
         patch.dict(os.environ, {"ADMIN_USERS": "123456789,987654321"}, clear=True):
        mock_app = MagicMock()
        mock_builder.return_value.token.return_value.build.return_value = mock_app
        
        bot = OctopusBotHandler(mock_config)
        
        # Test admin user
        assert bot._is_admin_user(123456789) is True
        assert bot._is_admin_user(987654321) is True
        
        # Test non-admin user
        assert bot._is_admin_user(111111111) is False


def test_is_admin_user_default_first_user(mock_config):
    """Test admin user check with default first user behavior."""
    with patch("octopus_bot.bot.Application.builder") as mock_builder, \
         patch.dict(os.environ, {}, clear=True):  # No ADMIN_USERS
        mock_app = MagicMock()
        mock_builder.return_value.token.return_value.build.return_value = mock_app
        
        bot = OctopusBotHandler(mock_config)
        
        # When no first subscriber, first user should be admin
        assert bot._is_admin_user(123456789) is True
        
        # Set first subscriber
        bot.first_subscriber = 123456789
        
        # First user should still be admin
        assert bot._is_admin_user(123456789) is True
        
        # Other users should not be admin
        assert bot._is_admin_user(987654321) is False