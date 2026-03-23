# Copyright (c) Microsoft. All rights reserved.

"""Create operation for amplifier-gitea."""

import uuid
from datetime import datetime, timezone

import click
import docker.errors

from amplifier_bundle_gitea import docker_ops, gitea_api
from amplifier_bundle_gitea.constants import (
    ADMIN_PASSWORD,
    ADMIN_USER,
    CONTAINER_NAME_PREFIX,
    GITEA_ENV_VARS,
    GITEA_INTERNAL_PORT,
    LABEL_CREATED_AT,
    LABEL_ID,
    LABEL_MANAGED_BY,
    LABEL_MANAGED_BY_VALUE,
    LABEL_NAME,
    LABEL_PORT,
)


def create_environment(
    port: int,
    name: str | None,
    image: str,
    network: str | None,
    network_alias: str | None,
    add_host: tuple[str, ...],
    hostname: str | None,
) -> dict:
    """Create a new Gitea environment.

    Pulls the image, starts a container, waits for health,
    creates the admin user, generates an API token, and returns
    connection details.

    If any step after container creation fails, the container
    is removed to prevent orphans.
    """
    # 1. Generate ID
    env_id = f"gitea-{uuid.uuid4().hex[:8]}"
    if name is None:
        name = env_id

    # 2. Validate args
    if network_alias and not network:
        raise click.ClickException("--network-alias requires --network")

    # 3. Get Docker client
    client = docker_ops.get_docker_client()

    # 4. Pull image
    try:
        client.images.pull(image)
    except docker.errors.APIError as e:
        raise click.ClickException(f"Failed to pull image {image}: {e}") from e

    # 5. Start container
    container_name = f"{CONTAINER_NAME_PREFIX}{env_id}"
    labels = {
        LABEL_MANAGED_BY: LABEL_MANAGED_BY_VALUE,
        LABEL_ID: env_id,
        LABEL_NAME: name,
        LABEL_PORT: str(port),
        LABEL_CREATED_AT: datetime.now(timezone.utc).isoformat(),
    }
    environment = {
        **GITEA_ENV_VARS,
        "GITEA__server__ROOT_URL": f"http://localhost:{port}/",
        "GITEA__server__HTTP_PORT": str(GITEA_INTERNAL_PORT),
    }
    run_kwargs: dict = {
        "image": image,
        "detach": True,
        "name": container_name,
        "ports": {f"{GITEA_INTERNAL_PORT}/tcp": port},
        "labels": labels,
        "environment": environment,
    }
    if hostname:
        run_kwargs["hostname"] = hostname
    if add_host:
        run_kwargs["extra_hosts"] = list(add_host)

    container = None
    try:
        container = client.containers.run(**run_kwargs)

        # Connect to network (with optional alias)
        if network:
            net = client.networks.get(network)
            connect_kwargs: dict = {}
            if network_alias:
                connect_kwargs["aliases"] = [network_alias]
            net.connect(container, **connect_kwargs)

        # 6. Wait for healthy
        gitea_url = f"http://localhost:{port}"
        gitea_api.wait_until_healthy(gitea_url)

        # 7. Create admin user (must run as 'git' user, not root)
        container.exec_run(
            [
                "gitea",
                "admin",
                "user",
                "create",
                "--admin",
                "--username",
                ADMIN_USER,
                "--password",
                ADMIN_PASSWORD,
                "--email",
                "admin@localhost",
                "--must-change-password=false",
            ],
            user="git",
        )
        # Exit code 0 = created, non-zero = may already exist (OK)

        # 8. Generate token
        token = gitea_api.generate_token(gitea_url)

        # 9. Return result
        return {
            "id": env_id,
            "name": name,
            "port": port,
            "container_name": container_name,
            "gitea_url": gitea_url,
            "token": token,
            "admin_user": ADMIN_USER,
            "admin_password": ADMIN_PASSWORD,
            "status": "running",
        }
    except Exception:
        # Cleanup on failure to prevent orphan containers
        if container is not None:
            try:
                container.remove(force=True, v=True)
            except Exception:
                pass
        raise
