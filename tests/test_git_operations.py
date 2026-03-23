# Copyright (c) Microsoft. All rights reserved.

"""Integration tests for Git Platform Operations.

These tests exercise the Gitea REST API and git-over-HTTP operations
documented in docs/api_reference.md § "Git Platform Operations":
  - Create a repository
  - Clone, commit, and push
  - Create an issue
  - Create a pull request

Run with: uv run pytest tests/test_git_operations.py --run-integration -v
"""

import subprocess

import pytest

from helpers import run_cli, run_cli_json


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _gitea_api(method, path, *, base_url, token, json_body=None, timeout=10):
    """Authenticated Gitea API request. Returns an httpx.Response."""
    import httpx

    return httpx.request(
        method,
        f"{base_url}{path}",
        headers={"Authorization": f"token {token}"},
        json=json_body,
        timeout=timeout,
    )


def _git(*args, cwd=None, timeout=30):
    """Run a git command and return the CompletedProcess."""
    return subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=timeout,
    )


def _create_repo(base_url, token, name, auto_init=True):
    """Create a repo via the Gitea API and return the response JSON."""
    resp = _gitea_api(
        "POST",
        "/api/v1/user/repos",
        base_url=base_url,
        token=token,
        json_body={
            "name": name,
            "description": f"Test repo: {name}",
            "private": False,
            "auto_init": auto_init,
            "default_branch": "main",
        },
    )
    assert resp.status_code == 201, (
        f"Repo creation failed ({resp.status_code}): {resp.text}"
    )
    return resp.json()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def gitea_env(free_port):
    """Shared Gitea environment for all tests in this module."""
    data, _ = run_cli_json("create", "--port", str(free_port), timeout=120)
    assert isinstance(data, dict)
    yield data
    run_cli("destroy", data["id"], timeout=30)


# ---------------------------------------------------------------------------
# Test: Create a repository
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_create_repo(gitea_env):
    """POST /api/v1/user/repos creates a repo and it is retrievable."""
    base_url = gitea_env["gitea_url"]
    token = gitea_env["token"]

    repo = _create_repo(base_url, token, "test-create-repo")

    assert repo["name"] == "test-create-repo"
    assert repo["default_branch"] == "main"
    assert repo["owner"]["login"] == "admin"

    # Verify via GET
    get_resp = _gitea_api(
        "GET",
        "/api/v1/repos/admin/test-create-repo",
        base_url=base_url,
        token=token,
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "test-create-repo"


# ---------------------------------------------------------------------------
# Test: Clone, commit, and push
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_clone_commit_push(gitea_env, tmp_path):
    """Clone a repo, commit a file, push, and verify via the API."""
    base_url = gitea_env["gitea_url"]
    token = gitea_env["token"]

    _create_repo(base_url, token, "test-push-repo")

    # Clone
    clone_url = (
        f"http://admin:{token}@localhost:{gitea_env['port']}/admin/test-push-repo.git"
    )
    clone_dir = tmp_path / "test-push-repo"
    result = _git("clone", clone_url, str(clone_dir))
    assert result.returncode == 0, f"git clone failed: {result.stderr}"

    # Write a file, add, commit, push
    readme = clone_dir / "hello.txt"
    readme.write_text("hello from e2e test\n")

    _git(
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@test.com",
        "add",
        "hello.txt",
        cwd=clone_dir,
    )
    commit = _git(
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@test.com",
        "commit",
        "-m",
        "add hello.txt",
        cwd=clone_dir,
    )
    assert commit.returncode == 0, f"git commit failed: {commit.stderr}"

    push = _git("push", "origin", "main", cwd=clone_dir)
    assert push.returncode == 0, f"git push failed: {push.stderr}"

    # Verify file exists via Gitea API
    contents_resp = _gitea_api(
        "GET",
        "/api/v1/repos/admin/test-push-repo/contents/hello.txt",
        base_url=base_url,
        token=token,
    )
    assert contents_resp.status_code == 200, (
        f"File not found after push: {contents_resp.status_code} {contents_resp.text}"
    )
    assert contents_resp.json()["name"] == "hello.txt"


# ---------------------------------------------------------------------------
# Test: Create an issue
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_create_issue(gitea_env):
    """POST /api/v1/repos/{owner}/{repo}/issues creates an issue."""
    base_url = gitea_env["gitea_url"]
    token = gitea_env["token"]

    _create_repo(base_url, token, "test-issue-repo")

    # Create issue
    issue_resp = _gitea_api(
        "POST",
        "/api/v1/repos/admin/test-issue-repo/issues",
        base_url=base_url,
        token=token,
        json_body={
            "title": "Bug: login redirect broken",
            "body": "Users are redirected to /undefined after login.",
        },
    )
    assert issue_resp.status_code == 201, (
        f"Issue creation failed ({issue_resp.status_code}): {issue_resp.text}"
    )
    issue = issue_resp.json()
    assert issue["title"] == "Bug: login redirect broken"
    assert issue["body"] == "Users are redirected to /undefined after login."
    assert issue["state"] == "open"

    # Verify via GET
    get_resp = _gitea_api(
        "GET",
        f"/api/v1/repos/admin/test-issue-repo/issues/{issue['number']}",
        base_url=base_url,
        token=token,
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["title"] == "Bug: login redirect broken"


# ---------------------------------------------------------------------------
# Test: Create a pull request
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_create_pull_request(gitea_env, tmp_path):
    """Create a branch, push it, open a PR via the API, and verify."""
    base_url = gitea_env["gitea_url"]
    token = gitea_env["token"]

    _create_repo(base_url, token, "test-pr-repo")

    # Clone and create a feature branch
    clone_url = (
        f"http://admin:{token}@localhost:{gitea_env['port']}/admin/test-pr-repo.git"
    )
    clone_dir = tmp_path / "test-pr-repo"
    result = _git("clone", clone_url, str(clone_dir))
    assert result.returncode == 0, f"git clone failed: {result.stderr}"

    _git("checkout", "-b", "feat/hello", cwd=clone_dir)

    feature_file = clone_dir / "feature.txt"
    feature_file.write_text("new feature\n")

    _git(
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@test.com",
        "add",
        "feature.txt",
        cwd=clone_dir,
    )
    commit = _git(
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@test.com",
        "commit",
        "-m",
        "add feature",
        cwd=clone_dir,
    )
    assert commit.returncode == 0, f"git commit failed: {commit.stderr}"

    push = _git("push", "origin", "feat/hello", cwd=clone_dir)
    assert push.returncode == 0, f"git push failed: {push.stderr}"

    # Create PR via API
    pr_resp = _gitea_api(
        "POST",
        "/api/v1/repos/admin/test-pr-repo/pulls",
        base_url=base_url,
        token=token,
        json_body={
            "title": "Add hello feature",
            "body": "This PR adds the hello feature.",
            "head": "feat/hello",
            "base": "main",
        },
    )
    assert pr_resp.status_code == 201, (
        f"PR creation failed ({pr_resp.status_code}): {pr_resp.text}"
    )
    pr = pr_resp.json()
    assert pr["title"] == "Add hello feature"
    assert pr["state"] == "open"
    assert pr["head"]["label"] == "feat/hello"
    assert pr["base"]["label"] == "main"

    # Verify via GET
    get_resp = _gitea_api(
        "GET",
        f"/api/v1/repos/admin/test-pr-repo/pulls/{pr['number']}",
        base_url=base_url,
        token=token,
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["title"] == "Add hello feature"
