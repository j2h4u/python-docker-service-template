# Python Docker Service Template

Knowledge as code for Python QA: executable quality gates with the reasoning
and adoption instructions alongside them. Use this repository to bootstrap a
new project or upgrade the QA chain in an existing project. The tiny service is
a wiring smoke for the template, not a product codebase. Docker is optional in
the resulting project.

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
  `.dockerignore`, Docker Just recipes, `tests/test_runtime_smoke.py`, Docker
  CI jobs, Docker from this README's requirements and agent instructions, and
  Docker-only dependencies in `verify` and the aggregate CI job's `needs`.
  Keep Python QA, dependency, security, and release gates, and retain or add
  the service-appropriate runtime smoke.
- [ ] Delete or rewrite `docs/meta/`; it describes this template repository,
  not the generated project.
- [ ] Review `tach.toml` and import-linter contracts after the first real
  modules appear.
- [ ] Adapt clone source roots and review inherited clone exceptions using
  [Code Clone Detection](docs/CODE_CLONES.md#adoption-and-review).
- [ ] Keep `just mutation-check` available, then decide when it becomes a
  required slow gate after real domain behavior and focused unit tests exist.
- [ ] If the project uses `uv`, run `uv lock`, then `just verify`. Preserve
  Poetry, PDM, or another existing package manager when adopting QA; do not
  migrate implicitly.
- [ ] Follow the GitHub security setup checklist in
  [Best Practices](docs/BEST_PRACTICES.md).
- [ ] Configure branch protection or a ruleset so `main` requires the aggregate
  `ci` check, uses squash merges, and uses the PR title as the squash subject.
- [ ] Confirm GitHub Actions may create pull requests, then approve the first
  release-please PR workflow run if GitHub asks for write-user approval.
- [ ] Keep `AGENTS.md` intact unless the gate policy changes deliberately.

## Upgrade An Existing Project

Agents should complete this checklist in the target repository and record what
was adopted. Preserve the project's product code, release history and deployment.
Follow the canonical [existing-project adoption procedure](docs/BEST_PRACTICES.md#adopting-into-an-existing-repository)
for scope mapping, configuration conflicts, inherited debt and acceptance checks.

- [ ] Compare the current gates with [Best Practices](docs/BEST_PRACTICES.md)
  and select the missing capabilities.
- [ ] Merge the relevant `pyproject.toml` settings and dev dependencies; adapt
  source paths, architecture contracts and entrypoints to the target project.
  Update the lockfile with the target's package manager; do not replace it with
  the template lockfile or migrate managers implicitly.
- [ ] Copy the required QA scripts and merge their Just recipes and CI calls.
  Keep local and CI commands aligned and preserve any stronger existing gates.
- [ ] Adopt reusable documentation and its links. Do not copy the example
  service, template release state, or `docs/meta/` into the target project.
- [ ] For clone checking, follow the dedicated
  [adoption procedure](docs/CODE_CLONES.md#adoption-and-review); review all
  initial findings and do not import another repository's exceptions blindly.
- [ ] Resolve inherited failures deliberately. Use brownfield ratchets only
  where justified by the [QA policy](docs/BEST_PRACTICES.md#python-qa-gates),
  rather than weakening new-code rules.
- [ ] Verify adopted gates locally and through the target project's CI, then
  check repository-level protection/security settings when those were changed.

## Gates

`just verify` is the full local contract: static checks, the CRAP threshold
(which runs the fast unit lane with coverage), offline integration tests,
locked dependency vulnerability audit, and runtime smoke. The runtime smoke
depends on Docker/Compose validation and performs the image build.

CI uses the same gate commands for code-affecting changes, split into separate
jobs for clearer failures: `just check`, `just crap-check`, `just integration`,
`just deps-audit`, and `just runtime-smoke`. CI adds the
PR-only release-contract check and skips heavyweight jobs for documentation-only
changes. `just mutation-check` stays a separate slow audit gate, not part of the
default local or CI contract.

The static gate includes one Ruff pass with explicit preview
complexity/refactor rules and per-file production-print exceptions, lockfile
sync, basedpyright, import-linter, Tach module boundaries, actionlint, deptry,
suppression-budget checks, compile checks, supply-chain pin checks, Vulture over
source, scripts, and tests, clone review enforcement over production and QA
scripts, and a packaging smoke test that builds and installs the wheel. Pytest
runs in strict mode. `preview-complexity-lint` and `print-lint` remain available
as standalone diagnostics; `check` already covers those rules in its main Ruff
pass.

Run the full contract with `just verify`. During iteration, run only the
relevant recipes; `just unit` and `just docker-build` remain available as
standalone commands but are already covered by the corresponding full-gate
paths. Other useful standalone checks include:

```bash
just check
just crap-check
just unit
just integration
just deps-audit
just clone-check
just clone-audit
just mutation-check
just docker-check
just docker-build
just runtime-smoke
just release-check
```

Do not run `just unit` as an additional full-gate step: `crap-check` already
runs the fast unit lane with coverage. Likewise, `runtime-smoke` already
depends on Docker/Compose validation and builds the image; use `docker-build`
only when that standalone build is the specific check needed.

`just coverage` is a non-blocking diagnostic report. Coverage is a CRAP input,
not a standalone quality floor.

`just mutation-check` is a separate slow gate powered by mutmut. It validates
that tests kill behavioral mutants, exports mutmut's CI statistics, and fails on
survived mutants, missing test coverage for mutants, suspicious results,
timeouts, interrupted runs, or segfaults.

This repository is a template, so its own mutation score is only a wiring smoke.
Generated projects may retain the recipe, remove template-specific exclusions,
and consider making it required once real domain behavior and focused tests
justify the added cost. See
[Best Practices](docs/BEST_PRACTICES.md) for when to promote mutation testing
from an audit command to a required quality gate.

## Documentation

- [Code Clone Detection](docs/CODE_CLONES.md): production gates, reviewed
  exceptions, adoption and manual embedding audits.
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
docker compose run --rm python-docker-service-template health
docker compose up -d --force-recreate --remove-orphans --wait
```

Compose names images per project; parallel runtime smokes use unique project
names and remove only their own containers, networks and images.
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

Release-please prepares version and changelog PRs. The release workflow publishes
merged release PRs with native `gh`, targeting their exact merge SHA only after
its latest `CI` push run on `main` succeeds. Manual dispatch uses the same check;
moving `main` cannot change the published commit. Pending or failed candidate CI
leaves publication blocked with an explicit warning. GitHub generates release
notes; release-please continues to own the project changelog.

PR titles must be releasable
Conventional Commit subjects because squash merges use that title as the
release input. Use `feat:` for minor releases, `fix:` for patch fixes, and `!`
for breaking major changes; maintenance work uses `chore:`, `refactor:`,
`test:`, `ci:`, `docs:`, `build:`, or `style:`.

Every non-Dependabot commit in a PR must have a Conventional Commit subject.
For multi-commit PRs, add a `BEGIN_COMMIT_OVERRIDE` / `END_COMMIT_OVERRIDE`
block to the PR body; the block is required because the squash commit has only
one title. Ordinary commit body bullets inside release input must be indented.
Bullets directly following a `BREAKING CHANGE:` note may remain unindented;
do not put a blank line between that note and its bullets.
Run `just release-check "feat(api): add endpoint" pr-body.md`
before pushing a PR that should feed the changelog. Release-please owns
[CHANGELOG.md](CHANGELOG.md); review its generated release PR before merging it.

## License

PolyForm Noncommercial License 1.0.0.

Noncommercial use is permitted. Commercial use requires a separate commercial
license or prior written permission from Max Brashenko.
