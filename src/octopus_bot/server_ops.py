"""Server operations module for executing scripts and gathering system info."""

import asyncio
import logging
import os
import subprocess
from pathlib import Path
from typing import AsyncGenerator

import psutil

from .config import Script

logger = logging.getLogger(__name__)


async def run_script_streaming(
    script: Script,
) -> AsyncGenerator[str, None]:
    """
    Run a long-running script and stream output line by line.

    Args:
        script: Script configuration

    Yields:
        Output lines from the script

    Raises:
        FileNotFoundError: If script path doesn't exist
        RuntimeError: If script execution fails
    """
    script_path = Path(script.path)
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script.path}")

    try:
        # Include script arguments if provided
        cmd = [str(script_path)] + script.args

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )

        while True:
            line = await process.stdout.readline()
            if not line:
                break

            yield line.decode("utf-8", errors="replace").rstrip()

        await process.wait()

        if process.returncode != 0:
            logger.warning(
                f"Script {script.name} exited with code {process.returncode} started as {cmd}"
            )

    except Exception as e:
        logger.error(f"Error running script {script.name}: {e}")
        raise RuntimeError(f"Failed to run script {script.name}") from e


async def run_script_once(script: Script) -> str:
    """
    Run a one-time script and return all output.

    Args:
        script: Script configuration

    Returns:
        Combined stdout and stderr output

    Raises:
        FileNotFoundError: If script path doesn't exist
        RuntimeError: If script execution fails
    """
    script_path = Path(script.path)
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script.path}")

    try:
        # Include script arguments if provided
        cmd = [str(script_path)] + script.args

        result = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )

        stdout, _ = await result.communicate()
        output = stdout.decode("utf-8", errors="replace")

        if result.returncode != 0:
            logger.warning(
                f"Script {script.name} exited with code {result.returncode} run as {cmd}"
            )

        return output

    except Exception as e:
        logger.error(f"Error running script {script.name}: {e}")
        raise RuntimeError(f"Failed to run script {script.name}") from e


def get_disk_usage(device_path: str) -> tuple[float, float]:
    """
    Get disk usage for a device.

    Args:
        device_path: Path to the device or mount point

    Returns:
        Tuple of (usage_percent, free_percent)

    Raises:
        RuntimeError: If unable to get disk usage
    """
    try:
        usage = psutil.disk_usage(device_path)
        return usage.percent, 100 - usage.percent
    except Exception as e:
        logger.error(f"Error getting disk usage for {device_path}: {e}")
        raise RuntimeError(f"Failed to get disk usage for {device_path}") from e


def get_cpu_load() -> dict[str, float]:
    """
    Get CPU load averages.

    Returns:
        Dictionary with 1min, 5min, 15min load averages
    """
    try:
        load = os.getloadavg()
        return {
            "1min": load[0],
            "5min": load[1],
            "15min": load[2],
        }
    except Exception as e:
        logger.error(f"Error getting CPU load: {e}")
        raise RuntimeError("Failed to get CPU load") from e
