"""E2E tests measuring the timing impact of each metadata type during mirror-from-github.

Uses microsoft/amplifier as the benchmark repo. Each test mirrors the repo with
a different combination of --include-* flags and records the wall-clock time.

Prerequisites:
    - Docker running
    - GitHub token (GH_TOKEN env or gh auth login)

Run:
    uv run pytest tests/test_e2e_mirror_metadata.py --run-e2e -v -s
"""

import time

import pytest

from helpers import run_cli, run_cli_json

MIRROR_REPO = "https://github.com/microsoft/amplifier"
MIRROR_REPO_NAME = "amplifier"


@pytest.fixture(scope="module")
def github_token():
    from amplifier_bundle_gitea.github_api import resolve_github_token

    token = resolve_github_token()
    if not token:
        pytest.skip("No GitHub token available")
    return token


def _create_env(free_port_gen):
    """Create a fresh Gitea environment and return its info dict."""
    port = free_port_gen()
    data, _ = run_cli_json("create", "--port", str(port), timeout=120)
    return data


def _destroy_env(env_id):
    run_cli("destroy", env_id, timeout=30)


def _mirror(env_id, github_token, extra_flags=None):
    """Run mirror-from-github and return (result_dict, elapsed_seconds)."""
    args = [
        "mirror-from-github",
        env_id,
        "--github-repo",
        MIRROR_REPO,
        "--github-token",
        github_token,
    ]
    if extra_flags:
        args.extend(extra_flags)

    start = time.monotonic()
    data, _ = run_cli_json(*args, timeout=600)
    elapsed = time.monotonic() - start
    return data, elapsed


@pytest.fixture(scope="module")
def _port_counter():
    """Yield a callable that returns fresh free ports."""
    import socket

    def _get():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            return s.getsockname()[1]

    return _get


# -- Tests: default behavior (git-only) --


@pytest.mark.e2e
def test_mirror_default(github_token, _port_counter):
    """Default mirror: full history, all branches, no metadata."""
    env = _create_env(_port_counter)
    try:
        data, elapsed = _mirror(env["id"], github_token)
        assert data["migrated"]["git"] is True
        assert data["migrated"]["issues"] is False
        assert data["migrated"]["pull_requests"] is False
        assert data["migrated"]["labels"] is False
        assert data["migrated"]["milestones"] is False
        assert data["migrated"]["releases"] is False
        assert data["migrated"]["wiki"] is False
        print(f"\n  default (git-only): {elapsed:.1f}s")
    finally:
        _destroy_env(env["id"])


# -- Tests: individual metadata types --


@pytest.mark.e2e
@pytest.mark.xfail(
    reason="Gitea bug: migrating issues alone causes 'comment references non existent IssueIndex' 500",
    strict=False,
)
def test_mirror_with_issues(github_token, _port_counter):
    """Mirror with --include-issues only."""
    env = _create_env(_port_counter)
    try:
        data, elapsed = _mirror(env["id"], github_token, ["--include-issues"])
        assert data["migrated"]["issues"] is True
        assert data["migrated"]["pull_requests"] is False
        print(f"\n  git+issues: {elapsed:.1f}s")
    finally:
        _destroy_env(env["id"])


@pytest.mark.e2e
@pytest.mark.xfail(
    reason="Gitea bug: migrating PRs alone causes 'comment references non existent IssueIndex' 500",
    strict=False,
)
def test_mirror_with_prs(github_token, _port_counter):
    """Mirror with --include-prs only."""
    env = _create_env(_port_counter)
    try:
        data, elapsed = _mirror(env["id"], github_token, ["--include-prs"])
        assert data["migrated"]["pull_requests"] is True
        assert data["migrated"]["issues"] is False
        print(f"\n  git+prs: {elapsed:.1f}s")
    finally:
        _destroy_env(env["id"])


@pytest.mark.e2e
def test_mirror_with_issues_and_prs(github_token, _port_counter):
    """Mirror with --include-issues --include-prs."""
    env = _create_env(_port_counter)
    try:
        data, elapsed = _mirror(
            env["id"], github_token, ["--include-issues", "--include-prs"]
        )
        assert data["migrated"]["issues"] is True
        assert data["migrated"]["pull_requests"] is True
        assert data["migrated"]["labels"] is False
        print(f"\n  git+issues+prs: {elapsed:.1f}s")
    finally:
        _destroy_env(env["id"])


@pytest.mark.e2e
def test_mirror_with_labels(github_token, _port_counter):
    """Mirror with --include-labels only."""
    env = _create_env(_port_counter)
    try:
        data, elapsed = _mirror(env["id"], github_token, ["--include-labels"])
        assert data["migrated"]["labels"] is True
        assert data["migrated"]["issues"] is False
        print(f"\n  git+labels: {elapsed:.1f}s")
    finally:
        _destroy_env(env["id"])


@pytest.mark.e2e
def test_mirror_with_milestones(github_token, _port_counter):
    """Mirror with --include-milestones only."""
    env = _create_env(_port_counter)
    try:
        data, elapsed = _mirror(env["id"], github_token, ["--include-milestones"])
        assert data["migrated"]["milestones"] is True
        assert data["migrated"]["issues"] is False
        print(f"\n  git+milestones: {elapsed:.1f}s")
    finally:
        _destroy_env(env["id"])


@pytest.mark.e2e
def test_mirror_with_releases(github_token, _port_counter):
    """Mirror with --include-releases only."""
    env = _create_env(_port_counter)
    try:
        data, elapsed = _mirror(env["id"], github_token, ["--include-releases"])
        assert data["migrated"]["releases"] is True
        assert data["migrated"]["issues"] is False
        print(f"\n  git+releases: {elapsed:.1f}s")
    finally:
        _destroy_env(env["id"])


@pytest.mark.e2e
def test_mirror_with_wiki(github_token, _port_counter):
    """Mirror with --include-wiki only."""
    env = _create_env(_port_counter)
    try:
        data, elapsed = _mirror(env["id"], github_token, ["--include-wiki"])
        assert data["migrated"]["wiki"] is True
        assert data["migrated"]["issues"] is False
        print(f"\n  git+wiki: {elapsed:.1f}s")
    finally:
        _destroy_env(env["id"])


@pytest.mark.e2e
def test_mirror_all_metadata(github_token, _port_counter):
    """Mirror with all --include-* flags (full migration)."""
    env = _create_env(_port_counter)
    try:
        data, elapsed = _mirror(
            env["id"],
            github_token,
            [
                "--include-issues",
                "--include-prs",
                "--include-labels",
                "--include-milestones",
                "--include-releases",
                "--include-wiki",
            ],
        )
        assert data["migrated"]["git"] is True
        assert data["migrated"]["issues"] is True
        assert data["migrated"]["pull_requests"] is True
        assert data["migrated"]["labels"] is True
        assert data["migrated"]["milestones"] is True
        assert data["migrated"]["releases"] is True
        assert data["migrated"]["wiki"] is True
        print(f"\n  all-metadata: {elapsed:.1f}s")
    finally:
        _destroy_env(env["id"])
