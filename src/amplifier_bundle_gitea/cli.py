# Copyright (c) Microsoft. All rights reserved.

"""amplifier-gitea CLI -- ephemeral Gitea instance management."""

import json

import click

from amplifier_bundle_gitea import docker_ops, gitea_api, github_sync
from amplifier_bundle_gitea.constants import ADMIN_USER
from amplifier_bundle_gitea.create import create_environment


@click.group()
@click.version_option(package_name="amplifier-bundle-gitea")
def main() -> None:
    """Manage ephemeral Gitea instances for isolated git workflows."""


# ---------------------------------------------------------------------------
# Lifecycle commands
# ---------------------------------------------------------------------------


@main.command()
@click.option(
    "--port",
    required=True,
    type=int,
    help="Host port to map to Gitea's internal HTTP port (3000).",
)
@click.option(
    "--name", default=None, help="Human-readable name. Defaults to gitea-<uuid8>."
)
@click.option(
    "--image", default="docker.gitea.com/gitea:latest", help="Container image."
)
@click.option("--network", default=None, help="Docker network to join.")
@click.option(
    "--network-alias",
    default=None,
    help="DNS alias on the joined network. Requires --network.",
)
@click.option(
    "--add-host",
    multiple=True,
    help="Add /etc/hosts entry. Format: host:ip. Repeatable.",
)
@click.option("--hostname", default=None, help="Set the container's hostname.")
def create(
    port: int,
    name: str | None,
    image: str,
    network: str | None,
    network_alias: str | None,
    add_host: tuple[str, ...],
    hostname: str | None,
) -> None:
    """Create a new Gitea environment."""
    result = create_environment(
        port=port,
        name=name,
        image=image,
        network=network,
        network_alias=network_alias,
        add_host=add_host,
        hostname=hostname,
    )
    click.echo(json.dumps(result, indent=2))


@main.command()
@click.argument("id")
def destroy(id: str) -> None:
    """Destroy an environment. Stops and removes the container and its volumes."""
    client = docker_ops.get_docker_client()
    docker_ops.remove_container(client, id)
    click.echo(json.dumps({"id": id, "destroyed": True}, indent=2))


@main.command()
@click.argument("id")
def status(id: str) -> None:
    """Check whether an environment's container is running and Gitea is responding."""
    client = docker_ops.get_docker_client()
    container = docker_ops.find_container(client, id)
    info = docker_ops.get_container_info(container)
    gitea_url = f"http://localhost:{info['port']}"
    healthy = gitea_api.check_healthy(gitea_url)
    result = {**info, "gitea_healthy": healthy}
    click.echo(json.dumps(result, indent=2))


@main.command("list")
def list_environments() -> None:
    """List all environments managed by this tool."""
    client = docker_ops.get_docker_client()
    containers = docker_ops.list_managed_containers(client)
    result = [docker_ops.get_container_info(c) for c in containers]
    click.echo(json.dumps(result, indent=2))


@main.command()
@click.argument("id")
def token(id: str) -> None:
    """Generate a new Gitea API token for an existing environment."""
    client = docker_ops.get_docker_client()
    container = docker_ops.find_container(client, id)
    info = docker_ops.get_container_info(container)
    gitea_url = f"http://localhost:{info['port']}"
    token_value = gitea_api.generate_token(gitea_url)
    result = {
        "id": id,
        "token": token_value,
        "gitea_url": gitea_url,
        "admin_user": ADMIN_USER,
    }
    click.echo(json.dumps(result, indent=2))


# ---------------------------------------------------------------------------
# GitHub sync commands
# ---------------------------------------------------------------------------


@main.command("mirror-from-github")
@click.argument("id")
@click.option("--github-repo", required=True, help="GitHub repository URL.")
@click.option("--github-token", default="", help="GitHub personal access token.")
@click.option("--include-issues", is_flag=True, default=False, help="Include issues.")
@click.option(
    "--include-prs", is_flag=True, default=False, help="Include pull requests."
)
@click.option("--include-labels", is_flag=True, default=False, help="Include labels.")
@click.option(
    "--include-milestones", is_flag=True, default=False, help="Include milestones."
)
@click.option(
    "--include-releases", is_flag=True, default=False, help="Include releases."
)
@click.option("--include-wiki", is_flag=True, default=False, help="Include wiki.")
def mirror_from_github(
    id: str,
    github_repo: str,
    github_token: str,
    include_issues: bool,
    include_prs: bool,
    include_labels: bool,
    include_milestones: bool,
    include_releases: bool,
    include_wiki: bool,
) -> None:
    """Mirror a GitHub repo into a Gitea environment.

    By default mirrors the full commit history and all branches.
    Use --include-* flags to opt in to metadata (issues, PRs, etc.).
    """
    result = github_sync.mirror(
        id,
        github_repo,
        github_token,
        include_issues,
        include_prs,
        include_labels,
        include_milestones,
        include_releases,
        include_wiki,
    )
    click.echo(json.dumps(result, indent=2))


@main.command("promote-to-github")
@click.argument("id")
@click.option("--repo", required=True, help="Gitea repo in owner/name format.")
@click.option("--branch", required=True, help="Branch in Gitea to promote.")
@click.option(
    "--github-repo", required=True, help="Target GitHub repo in owner/repo format."
)
@click.option(
    "--github-token",
    default=None,
    help="GitHub token. Falls back to GH_TOKEN env or gh CLI.",
)
@click.option(
    "--github-branch",
    default=None,
    help="Branch name to create on GitHub. Defaults to --branch.",
)
@click.option("--title", required=True, help="Pull request title.")
@click.option("--body", required=True, help="Pull request body.")
@click.option(
    "--base", default=None, help="Base branch for PR. Defaults to repo default."
)
def promote_to_github(
    id: str,
    repo: str,
    branch: str,
    github_repo: str,
    github_token: str | None,
    github_branch: str | None,
    title: str,
    body: str,
    base: str | None,
) -> None:
    """Push a branch from Gitea to GitHub and create a pull request."""
    result = github_sync.promote(
        id,
        repo,
        branch,
        github_repo,
        github_token,
        github_branch or branch,
        title,
        body,
        base,
    )
    click.echo(json.dumps(result, indent=2))
