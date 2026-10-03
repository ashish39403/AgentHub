# AgentHub CI/CD Pipeline

This folder contains production-grade GitHub Actions templates for AgentHub.

They are intentionally stored under `cicd/` so they do not run automatically until you copy them into `.github/workflows/`.

## Workflows

- `github-actions/ci.yml`
  - backend dependency install
  - PostgreSQL test service on port `5433`
  - backend test suite
  - frontend typecheck/build
  - Docker image build validation

- `github-actions/docker-publish.yml`
  - builds the backend Docker image
  - pushes to GitHub Container Registry
  - intended for tags/releases/manual dispatch

- `github-actions/deploy-ssh-template.yml`
  - optional deployment template for a VPS
  - pulls the GHCR image and restarts Docker Compose remotely

- `docker-compose.production.yml`
  - server-side compose template that runs the published image
  - copy this to your server as `docker-compose.yml`

## Activate

Create the GitHub Actions folder and copy the templates:

```bash
mkdir -p .github/workflows
cp cicd/github-actions/*.yml .github/workflows/
```

On Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force .github/workflows
Copy-Item cicd/github-actions/*.yml .github/workflows/
```

## Required Repository Secrets

For CI only, no custom secrets are required.

For Docker publish:

- GitHub's built-in `GITHUB_TOKEN` is enough for GHCR if package permissions are enabled.

For SSH deploy template:

- `SSH_HOST`
- `SSH_USER`
- `SSH_PRIVATE_KEY`
- `DEPLOY_PATH`

Production runtime secrets should live on the server or deployment platform, not in GitHub workflow files.

## Server Setup For SSH Deploy

On the server:

```bash
mkdir -p /opt/agenthub
cd /opt/agenthub
```

Copy these files to the server:

- `cicd/docker-compose.production.yml` as `docker-compose.yml`
- `cicd/production-env.example` as `.env.production`

Then edit `.env.production` with real production values.

## Recommended Branch Flow

```text
feature branch
-> pull request
-> CI runs tests/build/docker validation
-> merge to main/master
-> tag release vX.Y.Z
-> docker-publish builds image
-> deploy workflow updates server
```

## Local Equivalent Checks

Run these before pushing:

```bash
uv run pytest
npm --prefix frontend run lint
npm --prefix frontend run build
docker build -t agenthub-backend:local .
docker compose config --quiet
```
