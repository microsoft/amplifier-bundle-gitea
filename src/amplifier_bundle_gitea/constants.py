# Copyright (c) Microsoft. All rights reserved.

"""Shared constants for amplifier-gitea."""

ADMIN_USER = "admin"

LABEL_MANAGED_BY = "managed-by"
LABEL_MANAGED_BY_VALUE = "amplifier-gitea"
LABEL_ID = "amplifier-gitea.id"
LABEL_NAME = "amplifier-gitea.name"
LABEL_PORT = "amplifier-gitea.port"
LABEL_CREATED_AT = "amplifier-gitea.created-at"
LABEL_ADMIN_PASSWORD = "amplifier-gitea.admin-password"

CONTAINER_NAME_PREFIX = "amplifier-gitea-"
GITEA_INTERNAL_PORT = 3000
DEFAULT_IMAGE = "docker.gitea.com/gitea:latest"
DEFAULT_BIND_ADDRESS = "127.0.0.1"

GITEA_ENV_VARS: dict[str, str] = {
    "GITEA__security__INSTALL_LOCK": "true",
    "GITEA__database__DB_TYPE": "sqlite3",
    "GITEA__server__OFFLINE_MODE": "true",
    "GITEA__actions__ENABLED": "false",
    "GITEA__packages__ENABLED": "false",
    "GITEA__indexer__REPO_INDEXER_ENABLED": "false",
}
