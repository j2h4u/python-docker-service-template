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
Docker/Compose validation, and Docker build.

The static gate includes Ruff, preview complexity/refactor checks, production
print checks, basedpyright, import-linter, actionlint, deptry, compile checks,
and Vulture over source, scripts, and tests. Pytest runs in strict mode.

Run individual gates while iterating:

```bash
just check
just crap-check
just unit
just docker-check
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

Agents should follow `AGENTS.md` for the exact `gh` checklist after creating a
repository from this template.

## License

PolyForm Noncommercial License 1.0.0.

Noncommercial use is permitted. Commercial use requires a separate commercial
license or prior written permission from Max Brashenko.
