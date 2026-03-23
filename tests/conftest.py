"""Shared fixtures and test configuration."""

import shutil
import socket
import subprocess

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests that require Docker",
    )
    parser.addoption(
        "--run-github",
        action="store_true",
        default=False,
        help="Run GitHub integration tests (requires --github-test-repo)",
    )
    parser.addoption(
        "--github-test-repo",
        default=None,
        help="GitHub repo for integration tests in owner/repo format",
    )


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-integration"):
        skip = pytest.mark.skip(reason="needs --run-integration")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip)

    run_github = config.getoption("--run-github")
    github_repo = config.getoption("--github-test-repo")
    if not (run_github and github_repo):
        skip = pytest.mark.skip(reason="needs --run-github and --github-test-repo")
        for item in items:
            if "github" in item.keywords:
                item.add_marker(skip)


@pytest.fixture(scope="session")
def github_test_repo(request):
    """Return the owner/repo string passed via --github-test-repo."""
    return request.config.getoption("--github-test-repo")


@pytest.fixture(scope="session", autouse=True)
def check_uv():
    if not shutil.which("uv"):
        pytest.fail("uv is required to run tests: https://docs.astral.sh/uv/")


@pytest.fixture(scope="module")
def free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@pytest.fixture(autouse=True, scope="session")
def cleanup_orphaned_containers():
    yield
    if not shutil.which("docker"):
        return
    result = subprocess.run(
        ["docker", "ps", "-aq", "--filter", "label=managed-by=amplifier-gitea"],
        capture_output=True,
        text=True,
    )
    for cid in result.stdout.strip().split():
        if cid:
            subprocess.run(["docker", "rm", "-f", cid], capture_output=True)
