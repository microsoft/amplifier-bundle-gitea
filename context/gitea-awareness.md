# Gitea Environments

You have access to `amplifier-gitea`, a CLI for on-demand ephemeral Gitea Docker environments. Use it for isolated git workflows, safe experimentation, and GitHub mirroring/promoting.

## When to Use

- User needs an isolated git environment (experiments, testing, demos)
- User wants to mirror a GitHub repo, work freely, then promote changes back as a PR
- User needs a disposable git server with issues, PRs, and API access

## Prerequisites

- Docker running on the host
- `amplifier-gitea` CLI installed (`uv tool install git+https://github.com/microsoft/amplifier-bundle-gitea@main`)

## Quick Command Reference

| Command | Purpose |
|---------|---------|
| `amplifier-gitea create --port <N>` | Spin up a Gitea container |
| `amplifier-gitea destroy <id>` | Tear down a container and its volumes |
| `amplifier-gitea status <id>` | Check if container and Gitea are healthy |
| `amplifier-gitea list` | List all managed environments |
| `amplifier-gitea token <id>` | Generate a new API token |
| `amplifier-gitea mirror-from-github <id> --github-repo <url>` | Snapshot a GitHub repo into Gitea |
| `amplifier-gitea promote-to-github <id> --repo <r> --branch <b> --github-repo <r> --title <t> --body <b>` | Push a Gitea branch to GitHub as a PR |

All commands output JSON to stdout.

## Full Reference

Load the `gitea` skill for complete CLI documentation, installation guide, workflows, and troubleshooting:

```
load_skill(skill_name="gitea")
```
