"""GitHub HTTP API operations for amplifier-gitea."""

from __future__ import annotations

import os
import subprocess

import httpx


def resolve_github_token(explicit_token: str | None = None) -> str | None:
    """Resolve a GitHub token from three sources, in order:

    1. Explicit token parameter (from --github-token flag)
    2. GH_TOKEN environment variable
    3. ``gh auth token`` subprocess fallback

    Returns the token string, or None if all sources fail.

    Safety: The gh CLI token may have broad scopes. Callers MUST use it
    only for the specific API calls defined in the design. Never log,
    print, or expose the token.
    """
    if explicit_token:
        return explicit_token

    env_token = os.environ.get("GH_TOKEN")
    if env_token:
        return env_token

    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except FileNotFoundError:
        pass
    except subprocess.TimeoutExpired:
        pass

    return None


class GitHubClient:
    """Thin wrapper around httpx.Client for the GitHub REST API."""

    def __init__(self, token: str) -> None:
        self._client = httpx.Client(
            base_url="https://api.github.com",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=30,
        )

    @staticmethod
    def _raise_for_error(response: httpx.Response, message: str) -> None:
        if response.is_success:
            return
        detail = response.text[:500]
        raise httpx.HTTPStatusError(
            f"{message}: {response.status_code} {detail}",
            request=response.request,
            response=response,
        )

    # -- Branch operations --

    def get_branch(self, owner: str, repo: str, branch: str) -> dict:
        resp = self._client.get(f"/repos/{owner}/{repo}/branches/{branch}")
        self._raise_for_error(resp, f"Failed to get branch '{branch}'")
        return resp.json()

    def check_branch_exists(self, owner: str, repo: str, branch: str) -> bool:
        resp = self._client.get(f"/repos/{owner}/{repo}/branches/{branch}")
        if resp.status_code == 404:
            return False
        self._raise_for_error(resp, f"Failed to check branch '{branch}'")
        return True

    # -- Git Data API --

    def create_blob(
        self, owner: str, repo: str, content: str, encoding: str = "base64"
    ) -> dict:
        resp = self._client.post(
            f"/repos/{owner}/{repo}/git/blobs",
            json={"content": content, "encoding": encoding},
        )
        self._raise_for_error(resp, "Failed to create blob")
        return resp.json()

    def create_tree(
        self,
        owner: str,
        repo: str,
        base_tree: str,
        tree_items: list[dict],
    ) -> dict:
        resp = self._client.post(
            f"/repos/{owner}/{repo}/git/trees",
            json={"base_tree": base_tree, "tree": tree_items},
        )
        self._raise_for_error(resp, "Failed to create tree")
        return resp.json()

    def create_commit(
        self,
        owner: str,
        repo: str,
        message: str,
        tree_sha: str,
        parents: list[str],
    ) -> dict:
        resp = self._client.post(
            f"/repos/{owner}/{repo}/git/commits",
            json={"message": message, "tree": tree_sha, "parents": parents},
        )
        self._raise_for_error(resp, "Failed to create commit")
        return resp.json()

    def create_ref(self, owner: str, repo: str, ref: str, sha: str) -> dict:
        resp = self._client.post(
            f"/repos/{owner}/{repo}/git/refs",
            json={"ref": ref, "sha": sha},
        )
        self._raise_for_error(resp, "Failed to create ref")
        return resp.json()

    # -- Pull Requests API --

    def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        head: str,
        base: str,
    ) -> dict:
        resp = self._client.post(
            f"/repos/{owner}/{repo}/pulls",
            json={"title": title, "body": body, "head": head, "base": base},
        )
        self._raise_for_error(resp, "Failed to create pull request")
        return resp.json()

    # -- Cleanup (used by tests) --

    def delete_branch(self, owner: str, repo: str, branch: str) -> None:
        resp = self._client.delete(f"/repos/{owner}/{repo}/git/refs/heads/{branch}")
        if resp.status_code not in (204, 422):
            self._raise_for_error(resp, f"Failed to delete branch '{branch}'")

    def close_pull_request(self, owner: str, repo: str, pr_number: int) -> None:
        resp = self._client.patch(
            f"/repos/{owner}/{repo}/pulls/{pr_number}",
            json={"state": "closed"},
        )
        # Best-effort cleanup
        if not resp.is_success:
            pass
