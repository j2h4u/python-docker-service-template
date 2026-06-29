# Python Docker Service Template

Template for Python 3.14 services that run in Docker and ship through hard
quality gates.

## Requirements

- Python 3.14
- `uv`
- `just`
- Docker

## After Creating A Repo From This Template

1. Rename `python-docker-service-template`, `template_service`, and
   `template-service` to the product names.
2. Run `uv lock`.
3. Run `just verify`.
4. Keep `AGENTS.md` intact unless the gate policy changes deliberately.

## Gates

`just verify` is the local contract: static checks, CRAP threshold, unit tests,
and Docker build.

Run individual gates while iterating:

```bash
just check
just crap-check
just unit
just docker-build
```

## Docker

Build and run the service locally:

```bash
just docker-build
docker run --rm python-docker-service-template:local health
docker compose up -d --force-recreate --remove-orphans --wait
```

The container runs as a non-root user, exposes `template-service` as the
entrypoint, and uses `template-service health` as its Docker healthcheck. The
Compose service defaults to a 1 GiB memory limit.

## GitHub Setup

The repository includes CI, CodeQL, dependency review, and Dependabot
configuration. After publishing a new repository, enable these GitHub security
features in the repository or organization settings. GitHub template creation
copies files such as workflows and `.github/dependabot.yml`, but repository
security settings are not reliable template outputs.

- Dependency graph
- Dependabot alerts
- Dependabot security updates
- Dependabot malware alerts, where GitHub exposes them for the repository
- Code scanning
- Secret scanning
- Secret scanning push protection

Agents should run this checklist after creating a repository from the template:

```bash
REPO="$(gh repo view --json nameWithOwner --jq .nameWithOwner)"

# Dependency graph / Dependabot alerts.
gh api -X PUT "repos/$REPO/vulnerability-alerts" --silent

# Dependabot security updates / automated security fixes.
gh api -X PUT "repos/$REPO/automated-security-fixes" --silent

# Secret scanning and push protection, where available for the repository.
gh api -X PATCH "repos/$REPO" --input - <<'JSON'
{
  "security_and_analysis": {
    "secret_scanning": {"status": "enabled"},
    "secret_scanning_push_protection": {"status": "enabled"}
  }
}
JSON

# This template uses the copied CodeQL workflow. Do not also enable CodeQL
# default setup, because GitHub rejects SARIF from advanced and default setup
# when both are active.
gh api -X PATCH "repos/$REPO/code-scanning/default-setup" \
  -f state=not-configured \
  --silent || true

# Run copied workflows once so code scanning and CI status are initialized.
gh workflow run ci.yml --ref main
gh workflow run codeql.yml --ref main

# Inspect remaining open alerts.
gh api "repos/$REPO/dependabot/alerts?state=open&per_page=100" --jq length
gh api "repos/$REPO/code-scanning/alerts?state=open&per_page=100" --jq length
gh api "repos/$REPO/secret-scanning/alerts?state=open&per_page=100" --jq length
```

If GitHub shows a separate malware-alerts toggle in the repository UI, verify it
manually under **Settings -> Code security and analysis**. The regular
Dependabot alerts API surfaces malware-classified alerts, but GitHub does not
expose a stable per-repository malware-alerts toggle through `gh` for every
account.

## License

PolyForm Noncommercial License 1.0.0.

Noncommercial use is permitted. Commercial use requires a separate commercial
license or prior written permission from Max Brashenko.
