# API Reference

CLI: `amplifier-gitea`

All commands return JSON to stdout.


## Lifecycle

### `create`

Create a new Gitea environment. Starts a container running Gitea, creates
an admin user, generates an API token, and returns connection details.

Environments are tracked via Docker container labels. The container is the source of truth.

```
amplifier-gitea create \
  --port 10110 \
  [--name my-env] \
  [--image docker.gitea.com/gitea:latest] \
  [--network my-network] \
  [--network-alias gitea] \
  [--add-host host.docker.internal:host-gateway] \
  [--hostname gitea-server]
```

`--port` (required)
  Host port to map to Gitea's internal HTTP port (3000).

`--name` (optional)
  Human-readable name. Defaults to `gitea-<uuid8>`.

`--image` (optional)
  Container image. Defaults to `docker.gitea.com/gitea:latest`.

`--network` (optional)
  Docker network to join.

`--network-alias` (optional)
  DNS alias on the joined network. Requires `--network`.

`--add-host` (optional, repeatable)
  Add an entry to the container's /etc/hosts. Format: `host:ip`.

`--hostname` (optional)
  Set the container's hostname.

Returns:

```json
{
  "id": "gitea-a1b2c3d4",
  "name": "gitea-a1b2c3d4",
  "port": 10110,
  "container_name": "amplifier-gitea-gitea-a1b2c3d4",
  "gitea_url": "http://localhost:10110",
  "token": "sha1_abc123...",
  "admin_user": "admin",
  "admin_password": "admin1234",
  "status": "running"
}
```

Steps performed:
1. Pull image if not cached.
2. Start container with Docker labels for discovery:
   - `managed-by=amplifier-gitea`
   - `amplifier-gitea.id=<id>`
   - `amplifier-gitea.name=<name>`
   - `amplifier-gitea.port=<port>`
   - `amplifier-gitea.created-at=<ISO8601>`
3. Wait for Gitea to pass health check (`GET /api/healthz`).
4. Create admin user via `gitea admin user create` inside the container.
5. Generate API token via `POST /api/v1/users/admin/tokens` with basic auth (same mechanism as the `token` command).
6. Return connection details including the token.

Note: The token value is only available at creation time. Gitea does not
store tokens in plain text. Use the `token` command to generate a new one
if needed.


### `destroy`

Destroy an environment. Stops and removes the container and its volumes.
No confirmation prompt.

```
amplifier-gitea destroy <id>
```

`<id>` (required)
  Environment ID.

Returns:

```json
{
  "id": "gitea-a1b2c3d4",
  "destroyed": true
}
```


### `status`

Check whether an environment's container is running and Gitea is responding.

```
amplifier-gitea status <id>
```

`<id>` (required)
  Environment ID.

Returns:

```json
{
  "id": "gitea-a1b2c3d4",
  "name": "gitea-a1b2c3d4",
  "port": 10110,
  "created_at": "2026-03-18T14:15:00Z",
  "container_running": true,
  "gitea_healthy": true
}
```

`container_running` is determined by `docker inspect`.
`gitea_healthy` is determined by `GET /api/healthz` on the mapped port.
`created_at` is extracted from the container label `amplifier-gitea.created-at`.


### `list`

List all environments managed by this tool. Queries Docker for containers
with the `managed-by=amplifier-gitea` label.

```
amplifier-gitea list
```

Returns:

```json
[
  {
    "id": "gitea-a1b2c3d4",
    "name": "gitea-a1b2c3d4",
    "port": 10110,
    "container_running": true,
    "created_at": "2026-03-18T14:15:00Z"
  }
]
```


### `token`

Generate a new Gitea API token for an existing environment. This creates
a new token each time -- Gitea does not store token values in plain text,
so previously created tokens cannot be retrieved.

```
amplifier-gitea token <id>
```

`<id>` (required)
  Environment ID.

Returns:

```json
{
  "id": "gitea-a1b2c3d4",
  "token": "sha1_def456...",
  "gitea_url": "http://localhost:10110",
  "admin_user": "admin"
}
```

Uses `POST /api/v1/users/admin/tokens` with basic auth against the
hardcoded admin credentials.


## Git Platform Operations

After `create` gives you a URL and token, you talk to Gitea directly. Gitea's API is largely GitHub-compatible.
Below are some common examples.

Full API docs: `http://<gitea_url>/swagger`

### Create a repository

```bash
curl -X POST "http://localhost:10110/api/v1/user/repos" \
  -H "Authorization: token $GITEA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-repo",
    "description": "Created via API",
    "private": false,
    "auto_init": true,
    "default_branch": "main"
  }'
```

To create under an organization instead, use
`/api/v1/orgs/{org}/repos` with the same body.

### Push to a repository

Standard git over HTTP. Use the API token as the password:

```bash
git clone http://admin:$GITEA_TOKEN@localhost:10110/admin/my-repo.git
cd my-repo
# make changes
git add .
git commit -m "some work"
git push origin main
```

### Create an issue

```bash
curl -X POST "http://localhost:10110/api/v1/repos/admin/my-repo/issues" \
  -H "Authorization: token $GITEA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Bug: login redirect broken",
    "body": "Users are redirected to /undefined after login."
  }'
```

## GitHub Sync

### `mirror-from-github`

One-time migration of a GitHub repo into a Gitea environment. 
Copies git content, issues, PRs, and labels. Does not set up ongoing sync -- this is a snapshot.

Internally calls Gitea's `POST /api/v1/repos/migrate`.

```
amplifier-gitea mirror-from-github <id> \
  --github-repo https://github.com/org/repo \
  [--github-token $GH_TOKEN] \
  [--no-issues] \
  [--no-prs] \
  [--no-labels]
```

`<id>` (required)
  Environment ID.

`--github-repo` (required)
  GitHub repository URL.

`--github-token` (optional)
  GitHub personal access token. Needed for private repos and to avoid
  rate limits. Public repos can be mirrored without a token. Consumers
  signed into the GitHub CLI can use `--github-token $(gh auth token)`.

`--no-issues` (optional)
  Skip migrating issues from the source repository.

`--no-prs` (optional)
  Skip migrating pull requests from the source repository.

`--no-labels` (optional)
  Skip migrating labels from the source repository.

Returns:

```json
{
  "id": "gitea-a1b2c3d4",
  "gitea_repo": "admin/repo",
  "gitea_clone_url": "http://localhost:10110/admin/repo.git",
  "source": "https://github.com/org/repo",
  "migrated": {
    "git": true,
    "issues": true,
    "pull_requests": true,
    "labels": true
  }
}
```


### `promote-to-github`

Push a branch from a Gitea repo to GitHub and create a pull request.

Does not force-push or modify the GitHub default branch. 
Only the specified branch is pushed, and a PR is opened against the base branch.

```
amplifier-gitea promote-to-github <id> \
  --repo admin/my-repo \
  --branch feature-xyz \
  --github-repo org/repo \
  [--github-token $GH_TOKEN] \
  [--github-branch promote-feature-xyz] \
  --title "Add feature XYZ" \
  --body "Description of changes" \
  [--base main]
```

`<id>` (required)
  Environment ID.

`--repo` (required)
  Gitea repo in `owner/name` format.

`--branch` (required)
  Branch in the Gitea repo to promote.

`--github-repo` (required)
  Target GitHub repository in `owner/repo` format.

`--github-token` (optional)
  GitHub personal access token with repo scope. If not provided, the
  token is resolved automatically: first from the `GH_TOKEN` environment
  variable, then from `gh auth token` CLI command. Consumers signed into
  the GitHub CLI do not need to pass this flag explicitly.

`--github-branch` (optional)
  Branch name to create on GitHub. Defaults to `--branch`. Use this when
  the GitHub branch should have a different name than the Gitea source branch.

`--title` (required)
  Pull request title.

`--body` (required)
  Pull request body.

`--base` (optional)
  Base branch for the PR. Defaults to the repo's default branch.

Returns:

```json
{
  "id": "gitea-a1b2c3d4",
  "pr_url": "https://github.com/org/repo/pull/42",
  "pr_number": 42,
  "branch": "feature-xyz",
  "base": "main"
}
```

Steps performed (HTTP-only, no git clone):
1. Fetch the full tree of the Gitea branch via Gitea's API.
2. Fetch the base branch tree from GitHub's API.
3. Diff the two trees to find changed and deleted files.
4. For each changed file, read the blob from Gitea and create a corresponding blob on GitHub.
5. Create a new tree on GitHub with the changed/deleted entries.
6. Create a commit on GitHub pointing to the new tree.
7. Create a ref (branch) on GitHub pointing to the new commit.
8. Open a pull request from the new branch against the base branch.
9. Return the PR URL and number.
