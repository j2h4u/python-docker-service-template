# Best Practices

This repository is both a project template and a store of preferred QA,
runtime, and repository-operating practices. Keep durable rationale here. Keep
`AGENTS.md` short and operational.

This document is intended to be copied into repositories created from the
template. Maintainer-only plans for this template repository belong in
`docs/meta/`; start with `docs/meta/ROADMAP.md` for template-repository
planning.

## Documentation Model

- `README.md` is the human-facing overview.
- `AGENTS.md` is the compact agent contract: hard gates, non-negotiable rules,
  and links to deeper runbooks.
- `docs/README.md` is the documentation map.
- `docs/BEST_PRACTICES.md` is the canonical place for reusable engineering
  rationale and audit checklists.
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
  GitHub Actions lint, dependency hygiene, compile checks, dead-code checks,
  lockfile sync, and packaging smoke.
- `just crap-check` is the hard CRAP threshold gate for every function.
- `just unit` is the behavior gate.
- `just docker-build` is the runtime packaging gate and includes Dockerfile and
  Compose validation before the image build.
- `just verify` is the full local gate before claiming completion.

Do not weaken, skip, or locally suppress gates to make a change pass. If a gate
is wrong, change the gate deliberately and explain why in the same change.

Prefer absolute gates over baseline ratchets in new repositories. Ratchets are
useful for paying down inherited debt, but they can also preserve debt while
spending CI time on bookkeeping. A new project should usually start with a
fixed rule, such as a per-function CRAP threshold, and add a ratchet only when
there is real legacy debt to manage.

When the project has domain contracts, add one semantic invariant gate instead
of relying only on generic linters. Examples include OpenAPI contract checks,
schema validation, config validation, import-layer policy, or a small
repository-specific quality policy. Wire that gate into `just check` or
`just unit` so local and CI behavior stay identical.

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

`uv.lock` must be checked explicitly:

```bash
uv lock --check
```

This catches stale lockfiles before Docker or CI fails later in the workflow.
On pull requests, remember that CI often checks the merged PR state; a
lockfile can be locally consistent on a branch and still stale after merging
with current `main`.

For GitHub repositories, submit `uv.lock` to the Dependency Graph with a
dedicated dependency-submission workflow. Dependency review catches PR deltas,
but dependency submission keeps GitHub's repository-level dependency graph
aligned with the lockfile.

Consider a scheduled lockfile vulnerability scan, such as OSV-Scanner, for
projects with long-lived pinned dependencies. Decide separately whether it is
blocking; detection-only scans can be useful when fixes require deliberate
coordination.

If Vulture needs exceptions, prefer an explicit reviewed whitelist file over
lowering the confidence threshold globally. A whitelist makes false positives
auditable without weakening dead-code detection everywhere.

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

Docker image builds are not the same as runtime verification. Once a service
has a meaningful protocol or health surface, add a runtime smoke gate that
builds the image, starts the container in a CI-safe Compose project, waits for
health, and exercises one real interface. Keep this separate from the minimal
template default until the service has real runtime behavior.

Python packages should also have a packaging smoke gate. Build the wheel,
install it into an isolated virtual environment, and run the installed
entrypoint. This catches missing package data, broken script entrypoints, and
wheel/install issues that source-tree tests can miss.

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
gh workflow run dependency-submission.yml --ref main

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
`docs/BEST_PRACTICES.md` as its canonical source of project QA policy. The
maintainer roadmap for that work lives in `docs/meta/ROADMAP.md`. The skill can
route by domain, but it should not duplicate the same policy in multiple files.
