"""Configuration loader for Octopus Bot."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class Script:
    """Configuration for a script."""

    name: str
    path: str
    long_running: bool = False


@dataclass
class PeriodicScript:
    """Configuration for a periodic script."""

    name: str
    path: str
    interval: int  # in seconds (e.g., 3600 for hourly)


@dataclass
class DeviceMonitor:
    """Configuration for device monitoring."""

    name: str
    path: str
    alert_threshold: float  # e.g., 80 for 80% disk usage


@dataclass
class BotConfig:
    """Bot configuration."""

    telegram_token: str
    long_running_scripts: list[Script]
    one_time_scripts: list[Script]
    monitored_devices: list[DeviceMonitor]
    periodic_scripts: list[PeriodicScript]


def load_config(config_path: str | None = None) -> BotConfig:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to the config file. If None, uses CONFIG_FILE env var
                    or defaults to config/config.yaml

    Returns:
        BotConfig: Parsed configuration

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is invalid
    """
    if config_path is None:
        config_path = os.getenv("CONFIG_FILE", "config/config.yaml")

    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_file) as f:
        data = yaml.safe_load(f)

    if not data:
        raise ValueError("Config file is empty")

    # Load Telegram token from environment variable
    telegram_token = os.getenv("TELEGRAM_TOKEN")
    if not telegram_token:
        raise ValueError("TELEGRAM_TOKEN environment variable not set")

    # Parse scripts
    long_running_scripts = []
    for script_data in data.get("long_running_scripts", []):
        long_running_scripts.append(
            Script(
                name=script_data["name"],
                path=script_data["path"],
                long_running=True,
            )
        )

    one_time_scripts = []
    for script_data in data.get("one_time_scripts", []):
        one_time_scripts.append(
            Script(
                name=script_data["name"],
                path=script_data["path"],
                long_running=False,
            )
        )

    # Parse device monitors
    monitored_devices = []
    for device_data in data.get("monitored_devices", []):
        monitored_devices.append(
            DeviceMonitor(
                name=device_data["name"],
                path=device_data["path"],
                alert_threshold=device_data.get("alert_threshold", 80),
            )
        )

    # Parse periodic scripts
    periodic_scripts = []
    for script_data in data.get("periodic_scripts", []):
        periodic_scripts.append(
            PeriodicScript(
                name=script_data["name"],
                path=script_data["path"],
                interval=script_data["interval"],
            )
        )

    return BotConfig(
        telegram_token=telegram_token,
        long_running_scripts=long_running_scripts,
        one_time_scripts=one_time_scripts,
        monitored_devices=monitored_devices,
        periodic_scripts=periodic_scripts,
    )
