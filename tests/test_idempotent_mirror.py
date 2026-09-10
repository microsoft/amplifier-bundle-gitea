# Copyright (c) Microsoft. All rights reserved.

"""Unit tests for idempotent mirror-from-github behavior.

These tests do NOT require Docker — they monkeypatch httpx and the docker_ops
helpers so the migrate-409 path can be exercised in isolation.
"""

from __future__ import annotations

from typing import Any

import click
import httpx
import pytest

from amplifier_bundle_gitea import gitea_api, github_sync


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _FakeResponse:
    def __init__(self, status_code: int, payload: Any, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text or (payload if isinstance(payload, str) else "")

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300

    def json(self) -> Any:
        return self._payload


def _fake_repo_dict(name: str = "amplifier-foundation") -> dict:
    """Shape compatible with both Gitea's migrate response and GET /repos/<owner>/<name>."""
    return {
        "id": 1,
        "name": name,
        "full_name": f"admin/{name}",
        "owner": {"login": "admin"},
        "clone_url": f"http://localhost:10110/admin/{name}.git",
        "empty": False,
        "private": False,
    }


# ---------------------------------------------------------------------------
# gitea_api.migrate_repo: 409 semantics
# ---------------------------------------------------------------------------


def test_migrate_repo_raises_repo_exists_error_on_409(monkeypatch):
    """409 from Gitea's migrate API → RepoExistsError, not generic ClickException."""

    def _post(url, headers=None, json=None, timeout=None):
        return _FakeResponse(
            409,
            payload="",
            text='{"message":"The repository with the same name already exists."}',
        )

    monkeypatch.setattr(httpx, "post", _post)

    with pytest.raises(gitea_api.RepoExistsError) as exc:
        gitea_api.migrate_repo(
            "http://localhost:10110",
            "tok",
            clone_addr="https://github.com/microsoft/amplifier-foundation",
            repo_name="amplifier-foundation",
        )
    assert exc.value.repo_name == "amplifier-foundation"
    # RepoExistsError is a ClickException subclass so existing catch-all handlers still work.
    assert isinstance(exc.value, click.ClickException)


def test_migrate_repo_raises_generic_click_exception_on_other_failures(monkeypatch):
    """Non-409 failures still produce a generic ClickException — semantics preserved."""

    def _post(url, headers=None, json=None, timeout=None):
        return _FakeResponse(500, payload="", text="upstream blew up")

    monkeypatch.setattr(httpx, "post", _post)

    with pytest.raises(click.ClickException) as exc:
        gitea_api.migrate_repo(
            "http://localhost:10110",
            "tok",
            clone_addr="https://github.com/x/y",
            repo_name="y",
        )
    assert not isinstance(exc.value, gitea_api.RepoExistsError)
    assert "Migration failed: 500" in str(exc.value.message)


def test_migrate_repo_returns_payload_on_success(monkeypatch):
    """Happy-path behavior unchanged: returns the JSON body for 200/201 responses."""
    payload = _fake_repo_dict()

    def _post(url, headers=None, json=None, timeout=None):
        return _FakeResponse(201, payload=payload)

    monkeypatch.setattr(httpx, "post", _post)

    result = gitea_api.migrate_repo(
        "http://localhost:10110",
        "tok",
        clone_addr="https://github.com/microsoft/amplifier-foundation",
        repo_name="amplifier-foundation",
    )
    assert result == payload


# ---------------------------------------------------------------------------
# gitea_api.get_repo
# ---------------------------------------------------------------------------


def test_get_repo_returns_payload_on_200(monkeypatch):
    payload = _fake_repo_dict()

    def _get(url, headers=None, timeout=None):
        return _FakeResponse(200, payload=payload)

    monkeypatch.setattr(httpx, "get", _get)
    assert (
        gitea_api.get_repo(
            "http://localhost:10110", "tok", "admin", "amplifier-foundation"
        )
        == payload
    )


def test_get_repo_raises_on_404(monkeypatch):
    def _get(url, headers=None, timeout=None):
        return _FakeResponse(404, payload="", text="not found")

    monkeypatch.setattr(httpx, "get", _get)
    with pytest.raises(click.ClickException, match="not found"):
        gitea_api.get_repo("http://localhost:10110", "tok", "admin", "missing-repo")


# ---------------------------------------------------------------------------
# github_sync.mirror: skip_existing semantics
# ---------------------------------------------------------------------------


@pytest.fixture
def _mirror_env(monkeypatch):
    """Stub out docker_ops + gitea_api.generate_token so mirror() can run unit-style."""

    class _FakeContainer:
        attrs = {}

    def _get_docker_client():
        return object()

    def _find_container(client, env_id):
        return _FakeContainer()

    def _get_container_info(container):
        return {"port": 10110, "container_running": True}

    def _generate_token(url):
        return "fake-token"

    monkeypatch.setattr(github_sync.docker_ops, "get_docker_client", _get_docker_client)
    monkeypatch.setattr(github_sync.docker_ops, "find_container", _find_container)
    monkeypatch.setattr(
        github_sync.docker_ops, "get_container_info", _get_container_info
    )
    monkeypatch.setattr(github_sync.gitea_api, "generate_token", _generate_token)
    return monkeypatch


def test_mirror_skip_existing_returns_existing_repo_info(_mirror_env):
    """skip_existing=True + 409 → fetch existing, return shaped result with skipped=True."""

    def _migrate(*args, **kwargs):
        raise gitea_api.RepoExistsError(
            kwargs["repo_name"], "Repository already exists in Gitea"
        )

    def _get_repo(gitea_url, token, owner, repo_name):
        assert owner == "admin"
        return _fake_repo_dict(repo_name)

    _mirror_env.setattr(gitea_api, "migrate_repo", _migrate)
    _mirror_env.setattr(gitea_api, "get_repo", _get_repo)

    result = github_sync.mirror(
        "env-1",
        "https://github.com/microsoft/amplifier-foundation",
        github_token="",
        include_issues=False,
        include_prs=False,
        include_labels=False,
        include_milestones=False,
        include_releases=False,
        include_wiki=False,
        skip_existing=True,
    )

    assert result["skipped"] is True
    assert result["gitea_repo"] == "admin/amplifier-foundation"
    assert result["source"] == "https://github.com/microsoft/amplifier-foundation"
    # Nothing was actually migrated this call.
    assert all(v is False for v in result["migrated"].values())


def test_mirror_skip_existing_default_false_still_raises(_mirror_env):
    """Without skip_existing, 409 still surfaces as a fatal ClickException — backward compat."""

    def _migrate(*args, **kwargs):
        raise gitea_api.RepoExistsError(
            kwargs["repo_name"], "Repository already exists in Gitea"
        )

    _mirror_env.setattr(gitea_api, "migrate_repo", _migrate)

    with pytest.raises(gitea_api.RepoExistsError):
        github_sync.mirror(
            "env-1",
            "https://github.com/microsoft/amplifier-foundation",
            github_token="",
            include_issues=False,
            include_prs=False,
            include_labels=False,
            include_milestones=False,
            include_releases=False,
            include_wiki=False,
            # skip_existing defaults to False
        )


def test_mirror_happy_path_marks_skipped_false(_mirror_env):
    """Successful migrate() → skipped=False, migrated.git=True."""
    payload = _fake_repo_dict()

    def _migrate(*args, **kwargs):
        return payload

    _mirror_env.setattr(gitea_api, "migrate_repo", _migrate)

    result = github_sync.mirror(
        "env-1",
        "https://github.com/microsoft/amplifier-foundation",
        github_token="",
        include_issues=True,
        include_prs=False,
        include_labels=False,
        include_milestones=False,
        include_releases=False,
        include_wiki=False,
    )

    assert result["skipped"] is False
    assert result["migrated"]["git"] is True
    assert result["migrated"]["issues"] is True
    assert result["migrated"]["pull_requests"] is False
