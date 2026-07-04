# Best Practices

This repository is both a project template and a store of preferred QA,
runtime, and repository-operating practices. Keep durable rationale here. Keep
`AGENTS.md` short and operational.

This document is intended to be copied into repositories created from the
template. Maintainer-only plans for this template repository belong in
`docs/meta/`.

## Documentation Model

- `README.md` is the human-facing overview.
- `AGENTS.md` is the compact agent contract: hard gates, non-negotiable rules,
  and links to deeper runbooks.
- `docs/template/BEST_PRACTICES.md` is the canonical place for reusable
  engineering rationale and audit checklists.
- `docs/meta/` contains maintainer documentation for this template repository
  itself. It is copied by GitHub templates, but new projects should remove or
  rewrite it.

When a practice becomes stable enough to reuse across projects, document it here
by domain. If it needs exact commands for agents, include the commands here and
link to this document from `AGENTS.md`.

## Python QA Gates

Local and CI verification must share the same command surface. CI should call
`just` recipes instead of reimplementing local checks in workflow YAML.

- `just check` is the static gate: formatting, Ruff, preview
  complexity/refactor checks, production print guards, types, import contracts,
  GitHub Actions lint, dependency hygiene, compile checks, and dead-code checks.
- `just crap-check` is the hard CRAP threshold gate for every function.
- `just unit` is the behavior gate.
- `just docker-build` is the runtime packaging gate and includes Dockerfile and
  Compose validation before the image build.
- `just verify` is the full local gate before claiming completion.

Do not weaken, skip, or locally suppress gates to make a change pass. If a gate
is wrong, change the gate deliberately and explain why in the same change.

## Python Environment And Dependencies

Use `uv` only. Keep `uv.lock` current. Outside Docker, use hardlink mode so
virtual environments are fast and disk-efficient:

```bash
export UV_LINK_MODE=hardlink
uv sync --locked
```

If `.venv` was created before hardlink mode was enabled, recreate it instead of
trying to repair it in place:

```bash
rm -rf .venv
UV_LINK_MODE=hardlink uv sync --locked
```

When dependency constraints change, update the lockfile first, then sync:

```bash
uv lock
UV_LINK_MODE=hardlink uv sync --locked
```

Inside Docker, use copy mode for the project environment. Container layers and
host cache mounts do not need the same hardlink behavior as local development.

## Docker Build Context

Docker build context must be whitelist-based. Treat `.dockerignore` as the
container equivalent of a strict allowlist, not as a growing blacklist of local
artifacts.

Preferred pattern:

```dockerignore
*

!Dockerfile
!.dockerignore
!README.md
!pyproject.toml
!uv.lock
!src/
!src/**
```

Dockerfiles should also use explicit `COPY` instructions. Avoid broad copies
such as `COPY . .`; they make images larger, weaken reviewability, and increase
the chance of accidentally shipping local state.

If a new file is required in the image, update both the `.dockerignore`
allowlist and the relevant Dockerfile `COPY` line in the same change.

Runtime containers should stay small and boring:

- install only runtime dependencies in the final image;
- run as a non-root user;
- define a healthcheck for long-running services;
- keep default Compose resource limits conservative, such as a memory limit,
  unless the service needs otherwise.

## GitHub Template Security Setup

GitHub template creation copies repository files, including workflows and
`.github/dependabot.yml`, but repository security settings are not reliable
template outputs. After creating a new repository from this template, use `gh` to
enable and verify the security features that live in repository settings.

Run this from the new repository checkout:

```bash
REPO="$(gh repo view --json nameWithOwner --jq .nameWithOwner)"

gh api -X PUT "repos/$REPO/vulnerability-alerts" --silent
gh api -X PUT "repos/$REPO/automated-security-fixes" --silent

gh api -X PATCH "repos/$REPO" --input - <<'JSON'
{
  "security_and_analysis": {
    "secret_scanning": {"status": "enabled"},
    "secret_scanning_push_protection": {"status": "enabled"}
  }
}
JSON

gh api -X PATCH "repos/$REPO/code-scanning/default-setup" \
  -f state=not-configured \
  --silent || true

gh workflow run ci.yml --ref main
gh workflow run codeql.yml --ref main

gh api "repos/$REPO/dependabot/alerts?state=open&per_page=100" --jq length
gh api "repos/$REPO/code-scanning/alerts?state=open&per_page=100" --jq length
gh api "repos/$REPO/secret-scanning/alerts?state=open&per_page=100" --jq length
```

If GitHub exposes a separate malware-alerts toggle for the new repository, check
it manually in **Settings -> Code security and analysis**. Do not assume it was
copied from the template.

This template uses the copied CodeQL workflow. Do not also enable CodeQL default
setup, because GitHub rejects SARIF from advanced and default setup when both
are active.

## Future Agent Skill

If this repository grows into an agent skill, the skill should treat
`docs/template/BEST_PRACTICES.md` as its canonical source of project QA policy.
The skill can route by domain, but it should not duplicate the same policy in
multiple files.
