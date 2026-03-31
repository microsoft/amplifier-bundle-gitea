# Amplifier Bundle Gitea

AI-driven development by default operates directly against real GitHub repositories, meaning every experimental commit, branch, and PR touches production infrastructure.
Outside of potentially creating noise or irreversible changes, this also means consumers can't freely experiment in isolation without worrying about cleanup or collateral damage.
`amplifier-bundle-gitea` provides on-demand, ephemeral Gitea instances so consumers can mirror real repos, work freely in isolation, and only promote results back to GitHub when ready.

Amplifier Gitea is designed to be spun up on demand and torn down when no longer needed.
Usable for any workflow that needs a local, disposable git server.
It supports most Git operations like commits and branches, features like Issues and PRs, 
and has additional abstractions for interfacing with GitHub.

![Architecture Dot File](docs/amplifier-gitea-architecture.svg)

A consumer creates a Gitea environment, mirrors repos from GitHub
into it, works against it, and optionally promotes results back to GitHub when done.

See [docs/api_reference.md](docs/api_reference.md) for the full API.


## Installation

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (package manager and runner)
- [Docker Engine](https://docs.docker.com/engine/install/) (container runtime)

### CLI

```bash
uv tool install git+https://github.com/microsoft/amplifier-bundle-gitea@main
```

### Amplifier Bundle

This repo is also an Amplifier bundle. The bundle provides a `gitea` skill and context awareness so the AI model knows how to use the `amplifier-gitea` CLI. The CLI must be installed separately (see above).

For interactive Amplifier sessions, install as an app bundle (recommended):
```bash
amplifier bundle add git+https://github.com/microsoft/amplifier-bundle-gitea@main --app
```

To compose into an existing bundle:
```bash
amplifier bundle add "git+https://github.com/microsoft/amplifier-bundle-gitea@main#subdirectory=behaviors/gitea.yaml"
```

Otherwise, consider using the CLI directly.

For development setup, see [docs/development.md](docs/development.md).


## Quick Start

`create` pulls a Gitea Docker image and starts a container configured with SQLite, offline mode, and sensible defaults — no external database required. 
A hardcoded admin account (`admin`/`admin1234`) is created automatically, and an API token is generated and returned in the output. 
The token is only available in plaintext at creation time. Docker must be running on the host.
Please submit feedback if you would like more configuration options made available.

```bash
# Create an environment which returns an id
amplifier-gitea create --port 10110

# Check its status
amplifier-gitea status <id>

# Tear it down
amplifier-gitea destroy <id>
```

Once an environment is running, you talk to Gitea directly. The API is largely GitHub-compatible:

```bash
export GITEA_URL="http://localhost:10110"
export GITEA_TOKEN="<token from create output>"

# Create a repo
curl -X POST "$GITEA_URL/api/v1/user/repos" \
  -H "Authorization: token $GITEA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-repo", "auto_init": true, "default_branch": "main"}'

# Clone, commit, push
git clone "http://admin:$GITEA_TOKEN@localhost:10110/admin/my-repo.git"
cd my-repo
echo "hello" > hello.txt
git add hello.txt && git commit -m "first commit" && git push origin main

# Create an issue
curl -X POST "$GITEA_URL/api/v1/repos/admin/my-repo/issues" \
  -H "Authorization: token $GITEA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Bug: login broken", "body": "Redirect fails after login."}'

# View Gitea at http://localhost:10110 (admin/admin1234) and see the repo, commit, and issue you just created!
```

### GitHub Sync

Mirror a GitHub repo into the environment, work in isolation, then promote your changes back as a PR:

```bash
# Mirror a repo from GitHub (copies git content, issues, PRs, labels)
amplifier-gitea mirror-from-github <id> \
  --github-repo https://github.com/org/repo \
  --github-token $(gh auth token)

# Promote a branch back to GitHub as a pull request
amplifier-gitea promote-to-github <id> \
  --repo admin/repo \
  --branch feature-xyz \
  --github-repo org/repo \
  --github-branch promote/feature-xyz \
  --title "Add feature XYZ" \
  --body "Description of changes"
```

All commands return JSON to stdout. See [docs/api_reference.md](docs/api_reference.md) for the full API.


## Development

See [docs/development.md](docs/development.md).

## Contributing

> [!NOTE]
> This project is not currently accepting external contributions, but we're actively working toward opening this up. We value community input and look forward to collaborating in the future. For now, feel free to fork and experiment!

Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit [Contributor License Agreements](https://cla.opensource.microsoft.com).

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft
trademarks or logos is subject to and must follow
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.
