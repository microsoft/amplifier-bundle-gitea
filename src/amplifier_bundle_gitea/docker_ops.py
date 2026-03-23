# Copyright (c) Microsoft. All rights reserved.

"""Docker container operations for amplifier-gitea."""

import click
import docker
import docker.errors
from docker.models.containers import Container

from amplifier_bundle_gitea.constants import (
    LABEL_CREATED_AT,
    LABEL_ID,
    LABEL_MANAGED_BY,
    LABEL_MANAGED_BY_VALUE,
    LABEL_NAME,
    LABEL_PORT,
)


def get_docker_client() -> docker.DockerClient:
    """Create a Docker client from the environment.

    Raises click.ClickException if Docker is not available.
    """
    try:
        return docker.from_env()
    except docker.errors.DockerException as e:
        raise click.ClickException(
            f"Cannot connect to Docker. Is Docker running? ({e})"
        ) from e


def find_container(client: docker.DockerClient, env_id: str) -> Container:
    """Find a managed container by environment ID.

    Raises click.ClickException if not found.
    """
    containers = client.containers.list(
        all=True,
        filters={"label": f"{LABEL_ID}={env_id}"},
    )
    if not containers:
        raise click.ClickException(f"Environment not found: {env_id}")
    return containers[0]


def list_managed_containers(client: docker.DockerClient) -> list[Container]:
    """List all containers managed by amplifier-gitea."""
    return client.containers.list(
        all=True,
        filters={"label": f"{LABEL_MANAGED_BY}={LABEL_MANAGED_BY_VALUE}"},
    )


def get_container_info(container: Container) -> dict:
    """Extract standard info from a container's labels and status."""
    labels = container.labels
    return {
        "id": labels.get(LABEL_ID, ""),
        "name": labels.get(LABEL_NAME, ""),
        "port": int(labels.get(LABEL_PORT, "0")),
        "created_at": labels.get(LABEL_CREATED_AT, ""),
        "container_running": container.status == "running",
    }


def remove_container(client: docker.DockerClient, env_id: str) -> None:
    """Find and force-remove a container by environment ID."""
    container = find_container(client, env_id)
    try:
        container.remove(force=True, v=True)
    except docker.errors.APIError as e:
        raise click.ClickException(
            f"Failed to remove container for environment {env_id}: {e}"
        ) from e
