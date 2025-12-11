"""Unit tests for configuration loading."""

import os
import tempfile
from pathlib import Path

import pytest

from octopus_bot.config import BotConfig, DeviceMonitor, Script, load_config


def test_load_config_valid():
    """Test loading valid configuration."""
    config_content = """
long_running_scripts:
  - name: deploy
    path: /path/to/deploy.sh

one_time_scripts:
  - name: health-check
    path: /path/to/health_check.sh

monitored_devices:
  - name: root
    path: /
    alert_threshold: 85
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "config.yaml"
        config_file.write_text(config_content)

        os.environ["TELEGRAM_TOKEN"] = "test_token"
        config = load_config(str(config_file))

        assert config.telegram_token == "test_token"
        assert len(config.long_running_scripts) == 1
        assert config.long_running_scripts[0].name == "deploy"
        assert config.long_running_scripts[0].long_running is True

        assert len(config.one_time_scripts) == 1
        assert config.one_time_scripts[0].name == "health-check"
        assert config.one_time_scripts[0].long_running is False

        assert len(config.monitored_devices) == 1
        assert config.monitored_devices[0].name == "root"
        assert config.monitored_devices[0].alert_threshold == 85


def test_load_config_missing_token():
    """Test that loading config without TELEGRAM_TOKEN raises error."""
    config_content = """
long_running_scripts: []
one_time_scripts: []
monitored_devices: []
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "config.yaml"
        config_file.write_text(config_content)

        # Make sure TELEGRAM_TOKEN is not set
        os.environ.pop("TELEGRAM_TOKEN", None)

        with pytest.raises(ValueError, match="TELEGRAM_TOKEN"):
            load_config(str(config_file))


def test_load_config_file_not_found():
    """Test that loading non-existent config raises error."""
    os.environ["TELEGRAM_TOKEN"] = "test_token"

    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/config.yaml")


def test_load_config_empty_file():
    """Test that loading empty config raises error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "config.yaml"
        config_file.write_text("")

        os.environ["TELEGRAM_TOKEN"] = "test_token"

        with pytest.raises(ValueError, match="empty"):
            load_config(str(config_file))


def test_default_alert_threshold():
    """Test that default alert threshold is 80."""
    config_content = """
long_running_scripts: []
one_time_scripts: []
monitored_devices:
  - name: root
    path: /
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "config.yaml"
        config_file.write_text(config_content)

        os.environ["TELEGRAM_TOKEN"] = "test_token"
        config = load_config(str(config_file))

        assert config.monitored_devices[0].alert_threshold == 80


def test_load_config_with_periodic_scripts():
    """Test loading configuration with periodic scripts."""
    config_content = """
long_running_scripts: []
one_time_scripts: []
monitored_devices: []
periodic_scripts:
  - name: hourly-health
    path: ./scripts/health_check.sh
    interval: 3600
  - name: daily-backup
    path: ./scripts/backup.sh
    interval: 86400
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "config.yaml"
        config_file.write_text(config_content)

        os.environ["TELEGRAM_TOKEN"] = "test_token"
        config = load_config(str(config_file))

        assert len(config.periodic_scripts) == 2
        assert config.periodic_scripts[0].name == "hourly-health"
        assert config.periodic_scripts[0].interval == 3600
        assert config.periodic_scripts[1].name == "daily-backup"
        assert config.periodic_scripts[1].interval == 86400