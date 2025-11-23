"""Unit tests for server operations."""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

from octopus_bot.config import Script
from octopus_bot.server_ops import (
    get_disk_usage,
    run_script_once,
    run_script_streaming,
)


@pytest.mark.asyncio
async def test_run_script_streaming():
    """Test streaming script execution."""
    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = Path(tmpdir) / "test_script.sh"
        script_path.write_text("#!/bin/bash\necho 'line1'\necho 'line2'")
        script_path.chmod(0o755)

        script = Script(name="test", path=str(script_path), long_running=True)

        lines = []
        async for line in run_script_streaming(script):
            lines.append(line)

        assert len(lines) >= 2
        assert "line1" in lines[0]
        assert "line2" in lines[1]


@pytest.mark.asyncio
async def test_run_script_once():
    """Test one-time script execution."""
    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = Path(tmpdir) / "test_script.sh"
        script_path.write_text("#!/bin/bash\necho 'test output'")
        script_path.chmod(0o755)

        script = Script(name="test", path=str(script_path), long_running=False)

        output = await run_script_once(script)

        assert "test output" in output


@pytest.mark.asyncio
async def test_run_script_not_found():
    """Test that running non-existent script raises error."""
    script = Script(
        name="test",
        path="/nonexistent/script.sh",
        long_running=False,
    )

    with pytest.raises(FileNotFoundError):
        await run_script_once(script)


def test_get_disk_usage():
    """Test disk usage retrieval."""
    # Test with root directory which should always exist
    usage_percent, free_percent = get_disk_usage("/")

    assert 0 <= usage_percent <= 100
    assert 0 <= free_percent <= 100
    assert usage_percent + free_percent == 100


def test_get_disk_usage_invalid_path():
    """Test disk usage with invalid path."""
    with pytest.raises(RuntimeError):
        get_disk_usage("/nonexistent/path")
