# Copyright (c) Microsoft. All rights reserved.

"""Gitea HTTP API operations for amplifier-gitea."""

import time
import uuid

import click
import httpx

from amplifier_bundle_gitea.constants import ADMIN_PASSWORD, ADMIN_USER


def wait_until_healthy(url: str, timeout: int = 60) -> None:
    """Poll Gitea's health endpoint until it responds 200.

    Args:
        url: Base Gitea URL, e.g. "http://localhost:10110".
        timeout: Max seconds to wait.

    Raises click.ClickException on timeout.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            resp = httpx.get(f"{url}/api/healthz", timeout=5)
            if resp.status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(2)
    raise click.ClickException(
        f"Gitea at {url} did not become healthy within {timeout}s"
    )


def check_healthy(url: str) -> bool:
    """Single-shot health check. Returns True if Gitea responds 200."""
    try:
        resp = httpx.get(f"{url}/api/healthz", timeout=5)
        return resp.status_code == 200
    except httpx.HTTPError:
        return False


def generate_token(url: str, token_name: str | None = None) -> str:
    """Create a new API token via Gitea's REST API.

    Uses basic auth with the admin credentials.
    Token name defaults to "amplifier-<uuid8>" to avoid collisions.
    Returns the plaintext token string.
    """
    if token_name is None:
        token_name = f"amplifier-{uuid.uuid4().hex[:8]}"
    resp = httpx.post(
        f"{url}/api/v1/users/{ADMIN_USER}/tokens",
        auth=(ADMIN_USER, ADMIN_PASSWORD),
        json={"name": token_name, "scopes": ["all"]},
        timeout=10,
    )
    if resp.status_code not in (200, 201):
        raise click.ClickException(
            f"Failed to generate token: {resp.status_code} {resp.text}"
        )
    data = resp.json()
    token_value = data.get("sha1", "")
    if not token_value:
        raise click.ClickException(f"Token response missing 'sha1' field: {data}")
    return token_value


def migrate_repo(
    gitea_url: str,
    token: str,
    clone_addr: str,
    repo_name: str,
    *,
    github_token: str = "",
    mirror: bool = False,
    issues: bool = True,
    pull_requests: bool = True,
    labels: bool = True,
) -> dict:
    """Migrate an external repository into Gitea via POST /api/v1/repos/migrate."""
    payload: dict = {
        "clone_addr": clone_addr,
        "repo_name": repo_name,
        "repo_owner": ADMIN_USER,
        "service": "github",
        "mirror": mirror,
        "issues": issues,
        "pull_requests": pull_requests,
        "labels": labels,
    }
    if github_token:
        payload["auth_token"] = github_token
    resp = httpx.post(
        f"{gitea_url}/api/v1/repos/migrate",
        headers={"Authorization": f"token {token}"},
        json=payload,
        timeout=120,
    )
    if resp.status_code not in (200, 201):
        raise click.ClickException(f"Migration failed: {resp.status_code} {resp.text}")
    return resp.json()


def get_tree_recursive(
    gitea_url: str, token: str, owner: str, repo: str, ref: str
) -> dict:
    """GET /api/v1/repos/{owner}/{repo}/git/trees/{ref}?recursive=true."""
    resp = httpx.get(
        f"{gitea_url}/api/v1/repos/{owner}/{repo}/git/trees/{ref}",
        params={"recursive": "true"},
        headers={"Authorization": f"token {token}"},
        timeout=30,
    )
    if not resp.is_success:
        raise click.ClickException(
            f"Failed to get tree for '{ref}': {resp.status_code} {resp.text}"
        )
    return resp.json()


def get_blob(gitea_url: str, token: str, owner: str, repo: str, sha: str) -> dict:
    """GET /api/v1/repos/{owner}/{repo}/git/blobs/{sha}."""
    resp = httpx.get(
        f"{gitea_url}/api/v1/repos/{owner}/{repo}/git/blobs/{sha}",
        headers={"Authorization": f"token {token}"},
        timeout=30,
    )
    if not resp.is_success:
        raise click.ClickException(
            f"Failed to get blob {sha}: {resp.status_code} {resp.text}"
        )
    return resp.json()
