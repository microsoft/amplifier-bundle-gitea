# Copyright (c) Microsoft. All rights reserved.

"""Security regression tests for Gitea environment creation."""

from types import SimpleNamespace
from typing import Any, cast

import click
import httpx
import pytest

from amplifier_bundle_gitea import docker_ops, gitea_api
from amplifier_bundle_gitea.constants import (
    LABEL_ADMIN_PASSWORD,
    LABEL_ID,
)
from amplifier_bundle_gitea.create import create_environment


class FakeContainer:
    def __init__(self, labels):
        self.labels = labels
        self.status = "running"
        self.exec_calls = []

    def exec_run(self, command, **kwargs):
        self.exec_calls.append((command, kwargs))


class FakeDockerClient:
    def __init__(self):
        self.run_kwargs: dict = {}
        self.container = FakeContainer({})
        self.images = SimpleNamespace(pull=lambda image: None)
        self.networks = SimpleNamespace(get=lambda network: None)
        self.containers = SimpleNamespace(run=self._run)

    def _run(self, **kwargs):
        self.run_kwargs = kwargs
        self.container = FakeContainer(kwargs["labels"])
        return self.container


def test_create_uses_random_password_and_loopback_binding(monkeypatch):
    client = FakeDockerClient()
    token_passwords = []

    monkeypatch.setattr(docker_ops, "get_docker_client", lambda: client)
    monkeypatch.setattr(gitea_api, "wait_until_healthy", lambda url: None)
    monkeypatch.setattr(
        gitea_api,
        "generate_token",
        lambda url, admin_password: token_passwords.append(admin_password)
        or "test-token",
    )

    result = create_environment(
        port=10110,
        name=None,
        image="gitea:test",
        network=None,
        network_alias=None,
        add_host=(),
        hostname=None,
    )

    password = result["admin_password"]
    assert password
    assert password != "admin1234"
    assert len(password) >= 32
    assert token_passwords == [password]
    assert client.run_kwargs["ports"] == {"3000/tcp": ("127.0.0.1", 10110)}
    assert client.run_kwargs["labels"][LABEL_ADMIN_PASSWORD] == password
    assert client.container.labels[LABEL_ID] == result["id"]
    assert password in client.container.exec_calls[0][0]


def test_create_honors_explicit_bind_address(monkeypatch):
    client = FakeDockerClient()

    monkeypatch.setattr(docker_ops, "get_docker_client", lambda: client)
    monkeypatch.setattr(gitea_api, "wait_until_healthy", lambda url: None)
    monkeypatch.setattr(
        gitea_api, "generate_token", lambda url, admin_password: "test-token"
    )

    create_environment(
        port=10110,
        name=None,
        image="gitea:test",
        network=None,
        network_alias=None,
        add_host=(),
        hostname=None,
        bind_address="0.0.0.0",
    )

    assert client.run_kwargs["ports"] == {"3000/tcp": ("0.0.0.0", 10110)}


def test_generate_token_uses_environment_password(monkeypatch):
    request = {}

    def fake_post(url, **kwargs):
        request.update(url=url, **kwargs)
        return httpx.Response(201, json={"sha1": "generated-token"})

    monkeypatch.setattr(httpx, "post", fake_post)

    token = gitea_api.generate_token(
        "http://localhost:10110", "unique-environment-password"
    )

    assert token == "generated-token"
    assert request["auth"] == ("admin", "unique-environment-password")


def test_missing_stored_password_requires_recreation():
    container = FakeContainer({LABEL_ID: "gitea-old"})

    with pytest.raises(
        click.ClickException, match="Destroy and recreate it with the current"
    ):
        docker_ops.get_admin_password(cast(Any, container))
