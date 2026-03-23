"""Integration tests for GitHub sync commands.

Mirror tests (Docker only):
    uv run pytest tests/test_github_sync.py --run-integration -v -k mirror

Promote tests (Docker + real GitHub):
    uv run pytest tests/test_github_sync.py --run-integration --run-github \
        --github-test-repo org/test_repo -v
"""

import time

import httpx
import pytest

from helpers import run_cli, run_cli_json

MIRROR_SOURCE_REPO = "https://github.com/microsoft/amplifier-module-provider-openai"
MIRROR_REPO_NAME = "amplifier-module-provider-openai"


def _gitea_api(method, path, *, base_url, token, json_body=None, timeout=10):
    return httpx.request(
        method,
        f"{base_url}{path}",
        headers={"Authorization": f"token {token}"},
        json=json_body,
        timeout=timeout,
    )


@pytest.fixture(scope="module")
def github_token():
    from amplifier_bundle_gitea.github_api import resolve_github_token

    return resolve_github_token() or ""


@pytest.fixture(scope="module")
def gitea_env(free_port):
    data, _ = run_cli_json("create", "--port", str(free_port), timeout=120)
    assert isinstance(data, dict)
    yield data
    run_cli("destroy", data["id"], timeout=30)


# -- Mirror tests --


@pytest.mark.integration
def test_mirror_public_repo(gitea_env, github_token):
    args = ["mirror-from-github", gitea_env["id"], "--github-repo", MIRROR_SOURCE_REPO]
    if github_token:
        args.extend(["--github-token", github_token])
    data, _ = run_cli_json(*args, timeout=120)
    assert data["source"] == MIRROR_SOURCE_REPO
    assert data["gitea_repo"] == f"admin/{MIRROR_REPO_NAME}"
    assert data["migrated"]["git"] is True
    assert data["migrated"]["issues"] is True
    assert data["migrated"]["pull_requests"] is True
    assert data["migrated"]["labels"] is True

    resp = _gitea_api(
        "GET",
        f"/api/v1/repos/admin/{MIRROR_REPO_NAME}",
        base_url=gitea_env["gitea_url"],
        token=gitea_env["token"],
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == MIRROR_REPO_NAME


@pytest.mark.integration
def test_mirror_duplicate_fails(gitea_env, github_token):
    args = ["mirror-from-github", gitea_env["id"], "--github-repo", MIRROR_SOURCE_REPO]
    if github_token:
        args.extend(["--github-token", github_token])
    result = run_cli(*args, timeout=120)
    assert result.returncode != 0
    assert "Migration failed" in result.stderr or "already" in result.stderr.lower()


@pytest.mark.integration
def test_mirror_with_no_flags(gitea_env, github_token):
    args = [
        "mirror-from-github",
        gitea_env["id"],
        "--github-repo",
        MIRROR_SOURCE_REPO,
        "--no-issues",
        "--no-prs",
        "--no-labels",
    ]
    if github_token:
        args.extend(["--github-token", github_token])
    result = run_cli(*args, timeout=120)
    assert result.returncode != 0
    assert "Missing option" not in result.stderr


# -- Promote tests --


@pytest.mark.integration
@pytest.mark.github
def test_promote_round_trip(gitea_env, github_test_repo):
    """Full round-trip: mirror -> edit in Gitea -> promote -> verify PR -> cleanup."""
    from amplifier_bundle_gitea.github_api import GitHubClient, resolve_github_token

    token = resolve_github_token()
    assert token, "No GitHub token found. Set GH_TOKEN or run 'gh auth login'."

    gh_owner, gh_repo = github_test_repo.split("/", 1)
    gh = GitHubClient(token)
    ts = int(time.time())
    branch_name = f"amplifier-test-{ts}"
    github_branch_name = f"amplifier-promote-{ts}"
    pr_number = None

    try:
        # Step 1: Mirror the test repo into Gitea (ignore error if already mirrored)
        run_cli(
            "mirror-from-github",
            gitea_env["id"],
            "--github-repo",
            f"https://github.com/{github_test_repo}",
            "--github-token",
            token,
            "--no-issues",
            "--no-prs",
            "--no-labels",
            timeout=120,
        )

        gitea_url = gitea_env["gitea_url"]
        gitea_token = gitea_env["token"]
        local_repo_name = github_test_repo.split("/")[-1]

        # Step 2: Create a branch and add a file in Gitea
        resp = _gitea_api(
            "GET",
            f"/api/v1/repos/admin/{local_repo_name}",
            base_url=gitea_url,
            token=gitea_token,
        )
        assert resp.status_code == 200
        default_branch = resp.json()["default_branch"]

        resp = _gitea_api(
            "POST",
            f"/api/v1/repos/admin/{local_repo_name}/branches",
            base_url=gitea_url,
            token=gitea_token,
            json_body={
                "new_branch_name": branch_name,
                "old_branch_name": default_branch,
            },
        )
        assert resp.status_code == 201

        resp = _gitea_api(
            "POST",
            f"/api/v1/repos/admin/{local_repo_name}/contents/amplifier-test-{int(time.time())}.txt",
            base_url=gitea_url,
            token=gitea_token,
            json_body={
                "message": "test: add file for promote test",
                "content": "dGVzdCBmaWxlIGZyb20gYW1wbGlmaWVyLWdpdGVhIHByb21vdGUgdGVzdA==",
                "branch": branch_name,
            },
        )
        assert resp.status_code == 201

        # Step 3: Promote the branch to GitHub with a different branch name
        data, _ = run_cli_json(
            "promote-to-github",
            gitea_env["id"],
            "--repo",
            f"admin/{local_repo_name}",
            "--branch",
            branch_name,
            "--github-branch",
            github_branch_name,
            "--github-repo",
            github_test_repo,
            "--github-token",
            token,
            "--title",
            f"[amplifier-test] Promote test {github_branch_name}",
            "--body",
            "Automated test PR from amplifier-gitea. Will be cleaned up.",
            "--base",
            default_branch,
            timeout=120,
        )

        assert data["branch"] == github_branch_name
        assert data["base"] == default_branch
        assert data["pr_number"] > 0
        assert data["pr_url"].startswith("https://github.com/")
        pr_number = data["pr_number"]

        # Step 4: Verify PR exists on GitHub with the github branch name
        pr_info = gh._client.get(f"/repos/{gh_owner}/{gh_repo}/pulls/{pr_number}")
        assert pr_info.status_code == 200
        assert pr_info.json()["state"] == "open"
        assert pr_info.json()["head"]["ref"] == github_branch_name

        # Step 5: Verify duplicate github branch fails
        dup_result = run_cli(
            "promote-to-github",
            gitea_env["id"],
            "--repo",
            f"admin/{local_repo_name}",
            "--branch",
            branch_name,
            "--github-branch",
            github_branch_name,
            "--github-repo",
            github_test_repo,
            "--github-token",
            token,
            "--title",
            "Should fail",
            "--body",
            "Should fail",
            "--base",
            default_branch,
            timeout=60,
        )
        assert dup_result.returncode != 0
        assert "already exists" in dup_result.stderr

    finally:
        # Cleanup: delete github branch and close PR on GitHub
        try:
            gh.delete_branch(gh_owner, gh_repo, github_branch_name)
        except Exception:
            pass
        if pr_number is not None:
            try:
                gh.close_pull_request(gh_owner, gh_repo, pr_number)
            except Exception:
                pass
