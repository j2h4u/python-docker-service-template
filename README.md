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
- [ ] Run `uv lock`, then `just verify`.
- [ ] Follow the GitHub security setup checklist in
  [Best Practices](docs/BEST_PRACTICES.md).
- [ ] Keep `AGENTS.md` intact unless the gate policy changes deliberately.

## Gates

`just verify` is the local contract: static checks, CRAP threshold, unit tests,
locked dependency vulnerability audit, Docker/Compose validation, Docker build,
and runtime smoke.

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
just coverage
just unit
just deps-audit
just docker-check
just docker-build
just runtime-smoke
just release-check
```

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

## Releases

Release automation is handled by release-please. PR titles must be releasable
Conventional Commit subjects because squash merges use that title as the
release input. Use `feat:` for minor releases, `fix:` for patch fixes, and `!`
for breaking major changes; maintenance work uses `chore:`, `refactor:`,
`test:`, `ci:`, `docs:`, `build:`, or `style:`.

For multi-commit PRs, add a `BEGIN_COMMIT_OVERRIDE` / `END_COMMIT_OVERRIDE`
block to the PR body when the release notes need more than the squash title.
Run `just release-check` before pushing a PR that should feed the changelog.
Release-please owns `CHANGELOG.md`; review its generated release PR before
merging it.

## License

PolyForm Noncommercial License 1.0.0.

Noncommercial use is permitted. Commercial use requires a separate commercial
license or prior written permission from Max Brashenko.
