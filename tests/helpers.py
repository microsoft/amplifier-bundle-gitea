# Copyright (c) Microsoft. All rights reserved.

"""Test helpers for subprocess-level CLI invocation."""

import json
import subprocess
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent


def run_cli(*args: str, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    """Run amplifier-gitea via uv, exactly as a user would.

    Uses ``uv run --project`` so the invocation works from any working
    directory without requiring PATH or venv activation.
    """
    return subprocess.run(
        [
            "uv",
            "run",
            "--no-sync",
            "--project",
            str(PROJECT_DIR),
            "amplifier-gitea",
            *args,
        ],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def run_cli_json(
    *args: str, **kwargs
) -> tuple[dict | list, subprocess.CompletedProcess[str]]:
    """Run a command and parse JSON from stdout."""
    result = run_cli(*args, **kwargs)
    assert result.returncode == 0, (
        f"Command failed (exit {result.returncode}):\n"
        f"  stdout: {result.stdout}\n"
        f"  stderr: {result.stderr}"
    )
    return json.loads(result.stdout), result
