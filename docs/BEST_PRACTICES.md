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
  Tach module boundaries, GitHub Actions lint, dependency hygiene, suppression
  budgets, compile checks, dead-code checks, lockfile sync, supply-chain pin
  checks, and packaging smoke.
- `just crap-check` is the hard CRAP threshold gate for every function.
- Coverage is measured as CRAP input, not as a standalone blocking floor.
- `just unit` is the behavior gate.
- `just deps-audit` is the locked dependency vulnerability gate.
- `just docker-build` is the runtime packaging gate and includes Dockerfile and
  Compose validation before the image build.
- `just runtime-smoke` is the container runtime gate: start the service, wait
  for health, and exercise a real installed command or protocol.
- `just verify` is the full local gate before claiming completion.

Do not weaken, skip, or locally suppress gates to make a change pass. If a gate
is wrong, change the gate deliberately and explain why in the same change.

Treat the radon-backed CRAP calculation as the authoritative complexity model.
Ruff complexity rules are still blocking because they are cheap and catch some
bad shapes early, but they are not the source of truth for formulas or quality
decisions. Ruff's complexity signal is narrower; it can miss complexity from
boolean expressions, comprehensions, conditional expressions, and other Python
constructs that radon counts. When discussing or tuning CRAP, use the
radon-based complexity value from `just crap-check` / `scripts/crap_gate.py`,
not Ruff's C901 score.

Prefer absolute gates over baseline ratchets in new repositories. Ratchets are
useful for paying down inherited debt, but they can also preserve debt while
spending CI time on bookkeeping. A new project should usually start with a
fixed rule, such as a per-function CRAP threshold, and add a ratchet only when
there is real legacy debt to manage. When this repository is used to bring a
brownfield project under control, CRAP ratchets are appropriate: freeze the
current debt, require new changes to improve or hold the line, then replace the
ratchet with absolute thresholds as the codebase gets clean.

Keep suppression budgets explicit and small. The default template budget is
zero for `noqa`, `type: ignore`, `pyright: ignore`, `pylint: disable`, and
file-level Ruff suppression because suppressions are policy exceptions, not
normal development tools. If a mature project needs exceptions, raise the
budget deliberately and explain the reason in the same change.

When the project has domain contracts, add one semantic invariant gate instead
of relying only on generic linters. Examples include OpenAPI contract checks,
schema validation, config validation, import-layer policy, or a small
repository-specific quality policy. Wire that gate into `just check` or
`just unit` so local and CI behavior stay identical.

Use import-linter and Tach together. Import-linter is best for named semantic
contracts such as "core must not import CLI" or "persistence must not know the
transport." Tach is stricter in a different dimension: it describes the whole
module dependency graph, can require every edge to be explicit, can forbid
cycles, can treat `TYPE_CHECKING` imports as real coupling, and with
`exact = true` fails when a declared dependency is no longer used. That makes
the architecture file both a gate and a living map, not a loose set of examples.

A fresh project should keep `tach.toml` small but real: define the current
layers, set `root_module = "forbid"`, keep `layers_explicit_depends_on = true`,
and declare actual module edges as soon as modules appear. In a mature project,
add `visibility`, `cannot_depend_on`, and `[[interfaces]]` rules for public
facades and reviewed ownership boundaries. Do not use deprecated edges as a
default; reserve them for named brownfield cleanup work with a removal plan.

Use pytest markers from the start:

- unmarked tests belong to the fast default unit lane;
- `integration` marks tests that cross process, service, container, or network
  boundaries;
- `slow` marks tests that are too slow for the default unit gate.

Slow and integration tests can move to separate workflows as the project grows,
but the markers should exist before the suite needs them.

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

Run a locked dependency vulnerability audit from local and CI gates:

```bash
just deps-audit
```

This audits the resolved lockfile instead of a hand-written requirements view.
Keep scheduled lockfile vulnerability scans, such as OSV-Scanner, as a second
signal for long-lived pinned dependencies. Scheduled scans can be detection-only
when fixes require deliberate coordination, while `just deps-audit` remains the
developer-facing gate.

If Vulture needs exceptions, prefer an explicit reviewed whitelist file over
lowering the confidence threshold globally. A whitelist makes false positives
auditable without weakening dead-code detection everywhere.

Workflow actions and container images must not use floating references. Full
action versions or SHAs are acceptable; floating refs such as `main`, `master`,
or major-only tags are not. Container images must use explicit non-floating tags
or digests, and local Compose images should use clear local tags.

CI should classify documentation-only changes explicitly instead of hiding them
behind workflow-level `paths-ignore`. A small change classifier keeps the final
aggregate job visible on every PR/push while skipping expensive code gates only
when the changed files are genuinely documentation or template-maintainer
metadata.

## Docker Build Context

Docker build context must be whitelist-based. Treat `.dockerignore` as the
container equivalent of a strict allowlist, not as a growing blacklist of local
artifacts.

Docker is a default layer in this template, not a requirement for every project
created from it. For non-Docker services, remove the Docker files, Just recipes,
and CI jobs in one deliberate template adaptation, while keeping the Python QA,
dependency, security, and release gates.

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
- avoid fixed `container_name` values in Compose files; they break isolated
  project names and make CI/runtime smoke checks collide with local services.

Docker image builds are not the same as runtime verification. Add a runtime
smoke gate that builds the image, starts the container in a CI-safe Compose
project, waits for health, and exercises one real interface. The first smoke can
be tiny, such as an installed CLI `health` command; replace it with a
domain-level protocol smoke when the service grows a real interface.

Python packages should also have a packaging smoke gate. Build the wheel,
install it into an isolated virtual environment, and run the installed
entrypoint. This catches missing package data, broken script entrypoints, and
wheel/install issues that source-tree tests can miss.

## Releases

Use release-please for changelog and GitHub Release automation. PR titles and
squash commit subjects must be releasable Conventional Commits because they are
the primary release input. Keep `release-please-config.json`,
`.release-please-manifest.json`, and `CHANGELOG.md` together; release-please
owns changelog headings, dates, comparison links, and release PR updates.

Validate release input before CI has to reject it:

```bash
just release-check
```

The release-note override is a `BEGIN_COMMIT_OVERRIDE` /
`END_COMMIT_OVERRIDE` block in the PR body. Use it when a broad or multi-commit
change would otherwise squash into one misleading changelog line. Entries in
the override block should be Conventional Commit messages separated by blank
lines.

Release automation is not the same as publishing a container. Keep release-please
as the default release layer for both Docker and non-Docker projects. Add GHCR
publishing, image scanning, SBOM generation, provenance attestations, and
runtime release contracts only for projects that actually ship containers.

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
