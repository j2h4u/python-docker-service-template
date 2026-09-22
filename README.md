# Python Docker Service Template

Template for Python 3.14 services that run in Docker and ship through hard
quality gates.

## Requirements

- Python 3.14
- `uv`
- `just`
- Docker

## After Creating A Repo From This Template

Agents should complete and update this checklist before the first real
implementation commit. Keep checked items checked in the generated repository
so later agents can see what was already adapted.

- [ ] Rename `python-docker-service-template`, `template_service`, and
  `template-service` to the product names.
- [ ] Update `release-please-config.json`, `pyproject.toml`, Docker image
  names, Compose service names, workflow names, and visible README text.
- [ ] Choose the new project's initial version, reset
  `.release-please-manifest.json`, align `pyproject.toml` and `uv.lock`, and
  replace or archive the template `CHANGELOG.md`.
- [ ] Search for leftover template names:
  `rg "python-docker-service-template|template_service|template-service|Python Docker Service Template"`.
- [ ] Decide whether the project ships in Docker.
- [ ] If it does not use Docker, remove `Dockerfile`, `docker-compose.yml`,
  `.dockerignore`, Docker Just recipes, Docker CI jobs, and runtime smoke
  requirements. Keep Python QA, dependency, security, and release gates.
- [ ] Delete or rewrite `docs/meta/`; it describes this template repository,
  not the generated project.
- [ ] Review `tach.toml` and import-linter contracts after the first real
  modules appear.
- [ ] Keep `just mutation-check` available, then decide when it becomes a
  required slow gate after real domain behavior and focused unit tests exist.
- [ ] Run `uv lock`, then `just verify`.
- [ ] Follow the GitHub security setup checklist in
  [Best Practices](docs/BEST_PRACTICES.md).
- [ ] Configure branch protection or a ruleset so `main` requires the aggregate
  `ci` check, uses squash merges, and uses the PR title as the squash subject.
- [ ] Confirm GitHub Actions may create pull requests, then approve the first
  release-please PR workflow run if GitHub asks for write-user approval.
- [ ] Keep `AGENTS.md` intact unless the gate policy changes deliberately.

## Gates

`just verify` is the default local contract: static checks, CRAP threshold,
unit tests, locked dependency vulnerability audit, Docker/Compose validation,
Docker build, and runtime smoke.

CI uses the same gate commands for code-affecting changes, split into separate
jobs for clearer failures: `just check`, `just crap-check`, `just unit`,
`just deps-audit`, `just docker-build`, and `just runtime-smoke`. CI adds the
PR-only release-contract check and skips heavyweight jobs for documentation-only
changes. `just mutation-check` stays a separate slow audit gate, not part of the
default local or CI contract.

The static gate includes Ruff, preview complexity/refactor checks, production
print checks, lockfile sync, basedpyright, import-linter, Tach module
boundaries, actionlint, deptry, suppression-budget checks, compile checks,
supply-chain pin checks, Vulture over source, scripts, and tests, and a
packaging smoke test that builds and installs the wheel. Pytest runs in strict
mode.

Run individual gates while iterating:

```bash
just check
just crap-check
just unit
just deps-audit
just mutation-check
just docker-check
just docker-build
just runtime-smoke
just release-check
```

`just coverage` is a non-blocking diagnostic report. Coverage is a CRAP input,
not a standalone quality floor.

`just mutation-check` is a separate slow gate powered by mutmut. It validates
that tests kill behavioral mutants, exports mutmut's CI statistics, and fails on
survived mutants, missing test coverage for mutants, suspicious results,
timeouts, interrupted runs, or segfaults.

This repository is a template, so its own mutation score is only a wiring smoke.
Generated projects should keep the recipe, remove template-specific exclusions,
and make it required once real domain behavior and focused unit tests exist. See
[Best Practices](docs/BEST_PRACTICES.md) for when to promote mutation testing
from an audit command to a required quality gate.

## Documentation

- [Best Practices](docs/BEST_PRACTICES.md): reusable QA, runtime, dependency,
  Docker, and GitHub security practices for repositories created from this
  template.
- [Template Roadmap](docs/meta/ROADMAP.md): maintainer roadmap for this
  template repository itself. Delete or rewrite `docs/meta/` in generated
  projects.

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
configuration. After creating a repository from this template, follow
`AGENTS.md` and `docs/BEST_PRACTICES.md` to enable repository security settings
that GitHub does not reliably copy from templates.

Full CI is event-driven: it runs for PRs and code-affecting pushes, not on a
daily schedule. Background security automation is intentionally rare: Dependabot
opens grouped weekly PRs, while CodeQL and OSV scheduled scans run monthly and
can also be started manually.

## Releases

Release automation is handled by release-please. PR titles must be releasable
Conventional Commit subjects because squash merges use that title as the
release input. Use `feat:` for minor releases, `fix:` for patch fixes, and `!`
for breaking major changes; maintenance work uses `chore:`, `refactor:`,
`test:`, `ci:`, `docs:`, `build:`, or `style:`.

Every non-Dependabot commit in a PR must have a Conventional Commit subject.
For multi-commit PRs, add a `BEGIN_COMMIT_OVERRIDE` / `END_COMMIT_OVERRIDE`
block to the PR body; the block is required because the squash commit has only
one title. Commit body bullets inside release input must be indented rather than
starting at column zero. Run `just release-check title="..." body=pr-body.md`
before pushing a PR that should feed the changelog. Release-please owns
`CHANGELOG.md`; review its generated release PR before merging it.

## License

PolyForm Noncommercial License 1.0.0.

Noncommercial use is permitted. Commercial use requires a separate commercial
license or prior written permission from Max Brashenko.
