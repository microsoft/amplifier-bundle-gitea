# Development

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (package manager and runner)
- [Docker Engine](https://docs.docker.com/engine/install/) (container runtime)

## Setup

```bash
git clone https://github.com/microsoft/amplifier-bundle-gitea.git
cd amplifier-bundle-gitea
uv sync
```

## Running the CLI locally

```bash
uv run amplifier-gitea --help
uv run amplifier-gitea create --port 10110
```

## Tests

> **Warning:** Integration tests (`--run-integration`) destroy **all**
> `amplifier-gitea` managed containers when the test session ends, not just
> the ones the tests created. Any environment you created with
> `amplifier-gitea create` will be removed. Run
> `amplifier-gitea list` beforehand and `amplifier-gitea destroy` anything
> you want cleanly shut down, or be aware that running environments will be
> force-removed.

Tests invoke `amplifier-gitea` as a subprocess via `uv run`, exactly as a
user would on their machine. No in-process test runners or mocks.

```bash
# CLI surface tests (no Docker required)
uv run pytest

# Full lifecycle tests (requires Docker running)
uv run pytest --run-integration
```

### GitHub Integration Tests

Some tests exercise the `promote-to-github` flow against a real GitHub repository. 
These require additional flags:

```bash
uv run pytest --run-integration --run-github --github-test-repo <org>/<repo_name> -v
```

**Requirements:**
- `--run-integration` — enables Docker-based tests
- `--run-github` — enables GitHub integration tests
- `--github-test-repo <owner/repo>` — the GitHub repo to test against

**Token resolution:** Tests use `resolve_github_token()` which checks:
1. `GH_TOKEN` environment variable
2. `gh auth token` CLI command

Make sure one of these is configured before running GitHub tests.

**Safety:** GitHub tests ONLY create a temporary branch and PR, then
clean up (delete branch, close PR) in a `finally` block. They do not
modify the default branch, create/delete repos, force push, or touch tags.


## Design Decisions

- **Consumer decides isolation.** The package creates isolated Gitea instances on demand. A consumer can create one shared instance or many dedicated ones.
- **Decoupled.** This is a standalone library usable by anything that needs a disposable local git server.
- **Consumer-initiated GitHub sync.** `mirror-from-github` and `promote-to-github` are explicit operations the consumer calls, not automatic background sync. The consumer controls when repos flow in and when results flow out.
- **Docker labels as source of truth.** Environments are discovered by querying Docker for labeled containers, not local filesystem state. No metadata to get out of sync.
- **Consumer controls networking.** The tool makes no networking assumptions. Consumers pass `--network`, `--network-alias`, `--add-host`, etc. as needed for their topology.
- **Opinionated Gitea defaults.** SQLite, offline mode, hardcoded admin account, disabled actions/packages/indexer. Optimized for ephemeral local use. Extractable into config later.
- **CLI-first, JSON output.** All commands return JSON to stdout for programmatic consumption.
- **Runs locally.** The CLI runs on the user's machine, not as a separate service. It talks to Docker for container lifecycle, to the Gitea API for repo operations, and to the GitHub API for PR creation. All over HTTP.
