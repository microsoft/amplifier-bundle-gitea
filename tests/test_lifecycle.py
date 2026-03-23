# Copyright (c) Microsoft. All rights reserved.

"""Integration tests for lifecycle commands.

These tests require Docker and a working network connection (to pull the Gitea image).
Run with: uv run pytest tests/test_lifecycle.py --run-integration -v
"""

import socket

import pytest

from helpers import run_cli, run_cli_json


def _find_free_port() -> int:
    """Find a free TCP port. Used by standalone tests that can't share the module fixture."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def gitea_env(free_port):
    """Create a Gitea environment shared by all fixture-based tests in this module.

    The container is created once (on first use) and destroyed after the last
    fixture-based test finishes. This avoids paying the ~30s startup cost per test.
    """
    data, _ = run_cli_json("create", "--port", str(free_port), timeout=120)
    assert isinstance(data, dict), "Expected create to return a JSON object"
    yield data
    # Teardown: always destroy, even if tests failed
    run_cli("destroy", data["id"], timeout=30)


# ---------------------------------------------------------------------------
# Phase 1: create
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_create_returns_valid_json(gitea_env):
    """Verify the create command returns all required fields with correct values."""
    required_keys = {
        "id",
        "name",
        "port",
        "container_name",
        "gitea_url",
        "token",
        "admin_user",
        "admin_password",
        "status",
    }
    assert required_keys.issubset(gitea_env.keys()), (
        f"Missing keys: {required_keys - gitea_env.keys()}"
    )
    assert gitea_env["status"] == "running"
    assert gitea_env["admin_user"] == "admin"
    assert gitea_env["admin_password"] == "admin1234"
    assert isinstance(gitea_env["port"], int)
    assert gitea_env["gitea_url"].startswith("http://")
    assert gitea_env["container_name"].startswith("amplifier-gitea-")


@pytest.mark.integration
def test_create_token_works(gitea_env):
    """Verify the returned token actually authenticates against Gitea's API."""
    import httpx

    resp = httpx.get(
        f"{gitea_env['gitea_url']}/api/v1/user",
        headers={"Authorization": f"token {gitea_env['token']}"},
        timeout=10,
    )
    assert resp.status_code == 200, f"Token auth failed: {resp.status_code} {resp.text}"
    assert resp.json()["login"] == "admin"


# ---------------------------------------------------------------------------
# Phase 2: status, list, token, destroy
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_status_shows_running(gitea_env):
    """Verify status reports the container as running and Gitea as healthy."""
    data, _ = run_cli_json("status", gitea_env["id"])
    assert data["id"] == gitea_env["id"]
    assert data["container_running"] is True
    assert data["gitea_healthy"] is True
    assert isinstance(data["port"], int)


@pytest.mark.integration
def test_list_includes_environment(gitea_env):
    """Verify list returns an array containing the fixture's environment."""
    data, _ = run_cli_json("list")
    assert isinstance(data, list), f"Expected list, got {type(data)}"
    ids = [env["id"] for env in data]
    assert gitea_env["id"] in ids, f"Environment {gitea_env['id']} not in list: {ids}"
    matching = [env for env in data if env["id"] == gitea_env["id"]][0]
    assert matching["container_running"] is True


@pytest.mark.integration
def test_token_generates_new_working_token(gitea_env):
    """Verify the token command generates a new, distinct, working token."""
    import httpx

    data, _ = run_cli_json("token", gitea_env["id"])
    assert "token" in data
    assert data["admin_user"] == "admin"
    assert data["gitea_url"] == gitea_env["gitea_url"]

    # The new token must be different from the create token
    assert data["token"] != gitea_env["token"], (
        "New token should differ from create token"
    )

    # The new token must actually work
    resp = httpx.get(
        f"{data['gitea_url']}/api/v1/user",
        headers={"Authorization": f"token {data['token']}"},
        timeout=10,
    )
    assert resp.status_code == 200, (
        f"New token auth failed: {resp.status_code} {resp.text}"
    )
    assert resp.json()["login"] == "admin"


# ---------------------------------------------------------------------------
# Standalone tests (create their own environments, don't use gitea_env)
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_destroy_removes_container():
    """Standalone: create an environment, destroy it, verify it's gone."""
    port = _find_free_port()
    data, _ = run_cli_json("create", "--port", str(port), timeout=120)
    env_id = data["id"]

    # Destroy it
    destroy_data, _ = run_cli_json("destroy", env_id)
    assert destroy_data["id"] == env_id
    assert destroy_data["destroyed"] is True

    # Verify: status on the destroyed env should fail
    result = run_cli("status", env_id)
    assert result.returncode != 0, "status should fail for destroyed environment"


# ---------------------------------------------------------------------------
# Error case tests (no Docker containers needed)
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_destroy_nonexistent_id():
    """Destroy with a nonexistent ID should fail with a clear error."""
    result = run_cli("destroy", "nonexistent-id-12345")
    assert result.returncode != 0
    assert "nonexistent-id-12345" in result.stderr


@pytest.mark.integration
def test_status_nonexistent_id():
    """Status with a nonexistent ID should fail with a clear error."""
    result = run_cli("status", "nonexistent-id-12345")
    assert result.returncode != 0
    assert "nonexistent-id-12345" in result.stderr


@pytest.mark.integration
def test_token_nonexistent_id():
    """Token with a nonexistent ID should fail with a clear error."""
    result = run_cli("token", "nonexistent-id-12345")
    assert result.returncode != 0
    assert "nonexistent-id-12345" in result.stderr
