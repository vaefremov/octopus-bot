"""Integration test: verify that periodic scheduling triggers script execution and broadcasting."""

import asyncio
import os
import tempfile
from pathlib import Path

import schedule

from octopus_bot.config import load_config


def test_schedule_triggers_execute_and_broadcast(monkeypatch):
    """Schedule a periodic script and ensure it runs and broadcasts output.

    This test schedules a job, runs all scheduled jobs inside an asyncio event
    loop (so that `asyncio.create_task` works), and patches the bot's
    `run_script_once` and the handler's `broadcast_output` to observe calls.
    """

    config_content = """
long_running_scripts: []
one_time_scripts: []
monitored_devices: []
periodic_scripts:
  - name: test-job
    path: ./scripts/health_check.sh
    interval: 1
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "config.yaml"
        config_file.write_text(config_content)

        os.environ["TELEGRAM_TOKEN"] = "test_token"
        config = load_config(str(config_file))

        # Create handler
        from octopus_bot.bot import OctopusBotHandler
        from octopus_bot import bot as bot_module

        handler = OctopusBotHandler(config)

        # Patch the run_script_streaming used inside bot module
        async def fake_run_script_streaming(script):
            # async generator yielding one line
            yield "fake-output"

        monkeypatch.setattr(bot_module, "run_script_streaming", fake_run_script_streaming)

        broadcasts = []

        async def fake_broadcast_chunks(title, chunks, send_title=True):
            # collect joined chunks for assertion
            broadcasts.append((title, "\n".join(chunks)))

        # Patch the instance method
        monkeypatch.setattr(handler, "broadcast_chunks", fake_broadcast_chunks)

        # Ensure no leftover scheduled jobs
        schedule.clear()

        # Schedule jobs on the handler (schedules via schedule.every(...).seconds.do)
        handler._schedule_periodic_scripts()

        async def runner():
            # Run all scheduled jobs immediately inside the running event loop
            schedule.run_all(delay_seconds=0)

            # Give control back to the event loop to allow created tasks to run
            await asyncio.sleep(0.2)

        # Execute runner in event loop
        asyncio.run(runner())

        # Verify that broadcast was called
        assert len(broadcasts) >= 1
        title, output = broadcasts[0]
        assert "test-job" in title
        assert "fake-output" in output
