# Copyright (c) Microsoft. All rights reserved.

"""CLI surface tests -- no Docker required.

Verifies the installed binary responds correctly to flags,
missing arguments, and help text.
"""

import inspect

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


def test_mirror_help_shows_include_flags():
    """Verify mirror-from-github help includes all --include-* flags."""
    result = run_cli("mirror-from-github", "--help")
    assert result.returncode == 0
    assert "--include-issues" in result.stdout
    assert "--include-prs" in result.stdout
    assert "--include-labels" in result.stdout
    assert "--include-milestones" in result.stdout
    assert "--include-releases" in result.stdout
    assert "--include-wiki" in result.stdout


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


# ---------------------------------------------------------------------------
# create_environment signature tests (no Docker required)
# ---------------------------------------------------------------------------


def test_create_environment_has_health_check_host_param():
    """Verify health_check_host parameter exists and defaults to 'localhost'.

    This is a backward-compat guard: the parameter must be optional so all
    existing callers that omit it keep working without changes.
    """
    from amplifier_bundle_gitea.create import create_environment

    sig = inspect.signature(create_environment)
    assert "health_check_host" in sig.parameters, (
        "create_environment must accept health_check_host keyword argument"
    )
    param = sig.parameters["health_check_host"]
    assert param.default == "localhost", (
        f"health_check_host must default to 'localhost', got {param.default!r}"
    )


def test_create_environment_health_check_host_is_optional():
    """Confirm health_check_host has a default so existing callers need no changes."""
    from amplifier_bundle_gitea.create import create_environment

    sig = inspect.signature(create_environment)
    param = sig.parameters["health_check_host"]
    assert param.default is not inspect.Parameter.empty, (
        "health_check_host must be an optional parameter with a default value"
    )
