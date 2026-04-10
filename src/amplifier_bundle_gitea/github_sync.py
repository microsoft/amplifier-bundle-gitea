# Copyright (c) Microsoft. All rights reserved.

"""Orchestration logic for GitHub <-> Gitea sync operations."""

from __future__ import annotations

import click

from amplifier_bundle_gitea import docker_ops, gitea_api, github_api


def mirror(
    env_id: str,
    github_repo: str,
    github_token: str,
    include_issues: bool,
    include_prs: bool,
    include_labels: bool,
    include_milestones: bool,
    include_releases: bool,
    include_wiki: bool,
) -> dict:
    """Mirror a GitHub repo into a Gitea environment.

    Returns a result dict describing the migration outcome.
    Raises click.ClickException on errors.
    """
    client = docker_ops.get_docker_client()
    container = docker_ops.find_container(client, env_id)
    info = docker_ops.get_container_info(container)
    if not info["container_running"]:
        raise click.ClickException(f"Environment '{env_id}' is not running")
    gitea_url = f"http://localhost:{info['port']}"

    gitea_token = gitea_api.generate_token(gitea_url)
    repo_name = github_repo.rstrip("/").split("/")[-1]

    repo_info = gitea_api.migrate_repo(
        gitea_url,
        gitea_token,
        clone_addr=github_repo,
        repo_name=repo_name,
        github_token=github_token,
        mirror=False,
        issues=include_issues,
        pull_requests=include_prs,
        labels=include_labels,
        milestones=include_milestones,
        releases=include_releases,
        wiki=include_wiki,
    )

    return {
        "id": env_id,
        "gitea_repo": f"{repo_info['owner']['login']}/{repo_info['name']}",
        "gitea_clone_url": repo_info.get("clone_url", ""),
        "source": github_repo,
        "migrated": {
            "git": True,
            "issues": include_issues,
            "pull_requests": include_prs,
            "labels": include_labels,
            "milestones": include_milestones,
            "releases": include_releases,
            "wiki": include_wiki,
        },
    }


def promote(
    env_id: str,
    repo: str,
    branch: str,
    github_repo: str,
    github_token: str | None,
    github_branch: str,
    title: str,
    body: str,
    base: str | None,
) -> dict:
    """Push a branch from Gitea to GitHub and create a pull request.

    Returns a result dict describing the created PR.
    Raises click.ClickException on errors.
    """
    token = github_api.resolve_github_token(github_token)
    if not token:
        raise click.ClickException(
            "No GitHub token found. Set GH_TOKEN, pass --github-token, or run 'gh auth login'"
        )

    docker_client = docker_ops.get_docker_client()
    container = docker_ops.find_container(docker_client, env_id)
    info = docker_ops.get_container_info(container)
    if not info["container_running"]:
        raise click.ClickException(f"Environment '{env_id}' is not running")
    gitea_url = f"http://localhost:{info['port']}"

    gitea_token = gitea_api.generate_token(gitea_url)

    if "/" not in repo:
        raise click.ClickException(
            f"--repo must be in owner/name format, got: '{repo}'"
        )
    gitea_owner, gitea_repo = repo.split("/", 1)

    if "/" not in github_repo:
        raise click.ClickException(
            f"--github-repo must be in owner/repo format, got: '{github_repo}'"
        )
    gh_owner, gh_repo = github_repo.split("/", 1)

    gitea_tree = gitea_api.get_tree_recursive(
        gitea_url, gitea_token, gitea_owner, gitea_repo, branch
    )
    if not gitea_tree.get("tree"):
        raise click.ClickException(f"Branch '{branch}' not found in repo '{repo}'")

    gh = github_api.GitHubClient(token)

    if gh.check_branch_exists(gh_owner, gh_repo, github_branch):
        raise click.ClickException(
            f"Branch '{github_branch}' already exists on GitHub repository '{gh_owner}/{gh_repo}'"
        )

    if base is None:
        resp = gh._client.get(f"/repos/{gh_owner}/{gh_repo}")
        gh._raise_for_error(resp, "Failed to get GitHub repo info")
        base = str(resp.json()["default_branch"])

    base_branch = gh.get_branch(gh_owner, gh_repo, base)
    base_commit_sha = base_branch["commit"]["sha"]
    base_tree_sha = base_branch["commit"]["commit"]["tree"]["sha"]

    base_tree_resp = gh._client.get(
        f"/repos/{gh_owner}/{gh_repo}/git/trees/{base_tree_sha}",
        params={"recursive": "true"},
    )
    if base_tree_resp.status_code == 404:
        # Empty tree (e.g. repo with no files) — treat everything as new
        gh_base_entries = {}
    else:
        gh._raise_for_error(base_tree_resp, "Failed to get GitHub base tree")
        gh_base_entries = {
            entry["path"]: entry["sha"]
            for entry in base_tree_resp.json().get("tree", [])
            if entry["type"] == "blob"
        }

    tree_items: list[dict] = []
    for entry in gitea_tree["tree"]:
        if entry["type"] != "blob":
            continue
        path = entry["path"]
        gitea_sha = entry["sha"]
        if gh_base_entries.get(path) == gitea_sha:
            continue
        blob_data = gitea_api.get_blob(
            gitea_url, gitea_token, gitea_owner, gitea_repo, gitea_sha
        )
        gh_blob = gh.create_blob(gh_owner, gh_repo, blob_data["content"], "base64")
        tree_items.append(
            {"path": path, "mode": "100644", "type": "blob", "sha": gh_blob["sha"]}
        )

    gitea_paths = {
        entry["path"] for entry in gitea_tree["tree"] if entry["type"] == "blob"
    }
    for gh_path in gh_base_entries:
        if gh_path not in gitea_paths:
            tree_items.append(
                {"path": gh_path, "mode": "100644", "type": "blob", "sha": None}
            )

    new_tree = gh.create_tree(gh_owner, gh_repo, base_tree_sha, tree_items)
    new_commit = gh.create_commit(
        gh_owner, gh_repo, title, new_tree["sha"], [base_commit_sha]
    )
    gh.create_ref(gh_owner, gh_repo, f"refs/heads/{github_branch}", new_commit["sha"])
    pr = gh.create_pull_request(gh_owner, gh_repo, title, body, github_branch, base)

    return {
        "id": env_id,
        "pr_url": pr.get("html_url", ""),
        "pr_number": pr.get("number", 0),
        "branch": github_branch,
        "base": base,
    }
