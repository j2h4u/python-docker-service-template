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
5. Remove or rewrite `docs/meta/`; it describes this template repository, not
   the new project.

## Gates

`just verify` is the local contract: static checks, CRAP threshold, unit tests,
Docker/Compose validation, and Docker build.

The static gate includes Ruff, preview complexity/refactor checks, production
print checks, lockfile sync, basedpyright, import-linter, actionlint, deptry,
compile checks, Vulture over source, scripts, and tests, and a packaging smoke
test that builds and installs the wheel. Pytest runs in strict mode.

Run individual gates while iterating:

```bash
just check
just crap-check
just unit
just docker-check
just docker-build
```

## Best Practices

This repository also stores reusable QA and runtime practices. See
`docs/BEST_PRACTICES.md` for the canonical guidance on Python gates, Docker
build context, virtual environment handling, and post-template GitHub security
setup.

See `docs/README.md` for the documentation map. Template-maintainer planning
lives in `docs/meta/`, including `docs/meta/ROADMAP.md`. Those documents are
copied by GitHub templates, but they describe this repository itself and should
be removed or rewritten in repositories created from the template.

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

## License

PolyForm Noncommercial License 1.0.0.

Noncommercial use is permitted. Commercial use requires a separate commercial
license or prior written permission from Max Brashenko.
