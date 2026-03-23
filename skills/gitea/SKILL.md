---
name: gitea
description: Use when managing ephemeral Gitea Docker environments, mirroring GitHub repos for isolated work, or promoting changes back to GitHub as PRs. Triggers on gitea, ephemeral git, isolated git environment, mirror repo, promote branch, disposable git server.
user-invocable: true
---

# Gitea Ephemeral Environments

`amplifier-gitea` is a CLI for on-demand, ephemeral Gitea Docker containers. All commands output JSON to stdout.

## Prerequisites Check

Before any gitea operation, verify the environment:

```bash
# 1. Is the CLI installed?
which amplifier-gitea

# 2. Is Docker available and running?
which docker && docker info > /dev/null 2>&1 && echo "Docker OK" || echo "Docker NOT running"
```

If `amplifier-gitea` is not found:
```bash
uv tool install git+https://github.com/microsoft/amplifier-bundle-gitea@main
```

If Docker is not running:
- **Linux**: `sudo systemctl start docker`
- **macOS**: `open -a Docker`
- **WSL**: Start Docker Desktop on Windows, ensure WSL integration is enabled

**If prerequisites are missing, report clearly and stop. Do not attempt workarounds.**

## Documentation

For overview, quick start, installation, and workflow examples:

```
read_file("@gitea:README.md")
```

For complete CLI reference with all flags, output schemas, and Gitea API examples:

```
read_file("@gitea:docs/api_reference.md")
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `command not found: amplifier-gitea` | `uv tool install git+https://github.com/microsoft/amplifier-bundle-gitea@main` |
| `Cannot connect to the Docker daemon` | Start Docker: `sudo systemctl start docker` (Linux) or open Docker Desktop (macOS/Windows) |
| `port is already allocated` | Choose a different `--port` value, or `amplifier-gitea list` to find existing environments |
| `mirror-from-github` fails on private repo | Pass `--github-token` or ensure `gh auth login` is done |
| Token lost after `create` | Run `amplifier-gitea token <id>` to generate a new one |
| `promote-to-github` 404 error | Verify `--github-repo` is in `owner/repo` format (not a full URL) |
