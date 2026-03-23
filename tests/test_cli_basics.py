# Copyright (c) Microsoft. All rights reserved.

"""CLI surface tests -- no Docker required.

Verifies the installed binary responds correctly to flags,
missing arguments, and help text.
"""

from helpers import run_cli


COMMANDS = [
    "create",
    "destroy",
    "list",
    "mirror-from-github",
    "promote-to-github",
    "status",
    "token",
]


def test_version():
    result = run_cli("--version")
    assert result.returncode == 0
    assert "0.1.0" in result.stdout


def test_help_lists_all_commands():
    result = run_cli("--help")
    assert result.returncode == 0
    for cmd in COMMANDS:
        assert cmd in result.stdout


def test_create_requires_port():
    result = run_cli("create")
    assert result.returncode != 0


def test_destroy_requires_id():
    result = run_cli("destroy")
    assert result.returncode != 0


def test_mirror_requires_flags():
    result = run_cli("mirror-from-github", "fake-id")
    assert result.returncode != 0


def test_promote_requires_flags():
    result = run_cli("promote-to-github", "fake-id")
    assert result.returncode != 0


def test_mirror_help_shows_no_flags():
    """Verify mirror-from-github help includes --no-issues, --no-prs, --no-labels."""
    result = run_cli("mirror-from-github", "--help")
    assert result.returncode == 0
    assert "--no-issues" in result.stdout
    assert "--no-prs" in result.stdout
    assert "--no-labels" in result.stdout


def test_mirror_github_token_is_optional():
    """--github-token is not required for mirror-from-github."""
    result = run_cli(
        "mirror-from-github", "fake-id", "--github-repo", "https://github.com/x/y"
    )
    assert "Missing option" not in result.stderr or "github-token" not in result.stderr


def test_promote_github_token_is_optional():
    """--github-token is not required for promote-to-github."""
    result = run_cli(
        "promote-to-github",
        "fake-id",
        "--repo",
        "admin/test",
        "--branch",
        "test-branch",
        "--github-repo",
        "org/repo",
        "--title",
        "Test",
        "--body",
        "Test body",
    )
    assert "Missing option" not in result.stderr or "github-token" not in result.stderr


def test_promote_help_shows_optional_flags():
    """promote-to-github help shows --github-token, --github-branch, and --base as optional."""
    result = run_cli("promote-to-github", "--help")
    assert result.returncode == 0
    assert "--github-token" in result.stdout
    assert "--github-branch" in result.stdout
    assert "--base" in result.stdout
