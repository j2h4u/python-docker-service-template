# Agent Rules

This project uses hard gates. Do not weaken, skip, or locally suppress them to
make a change pass.

- Do not automatically add tests for configuration changes or every audit
  finding. Prefer native validators and focused audits; keep custom QA code and
  its existing checks proportional to actual risks.
- Run each required test selection, analysis and build once per verification.
- `just check` is the static gate: Ruff's main pass with security and explicit preview rules
  and per-file production-print exceptions, lock sync, types, imports, module
  boundaries, workflow lint, dependency hygiene, supply-chain pin checks,
  suppression budget, compile, dead-code checks, clone checking, and packaging
  smoke must pass.
- Clone findings must be fixed or explicitly reviewed under
  [Code Clone Detection](docs/CODE_CLONES.md). Never auto-accept findings to
  turn the gate green; semantic/API audit is manual and outside ordinary CI.
- Ruff complexity and unused-argument rules are blocking. Preview complexity
  rules that are not covered by Ruff prefixes are checked explicitly, but
  Ruff complexity is only an auxiliary lint signal.
- Production typing rejects Unknown types and bare generics; keep source roots
  aligned with the production execution environment when adopting the template.
- `just crap-check` enforces independent Radon CC <= 10 and CRAP <= 30 limits
  for every production function from one covered fast test run. Coverage is
  CRAP input, not a standalone floor; high coverage does not waive the CC limit.
- `just verify` is the full local gate: `check`, `crap-check` (including its
  fast unit lane with coverage), offline `integration`, `deps-audit`, and
  `runtime-smoke`. Do not redundantly run `unit` or `docker-build` as part of
  full verification.
- `just integration` uses offline tools and isolated fixtures, not external
  services.
- `just deps-audit` must pass before claiming release or template baseline
  readiness.
- `just runtime-smoke` must pass for Docker runtime changes.
- `just runtime-smoke` depends on Docker/Compose validation and performs the
  runtime image build; it is the Docker runtime gate.
- Use `uv` for this template. Keep `uv.lock` current and use hardlink mode
  outside Docker. When adopting QA into an existing project, preserve its
  package manager unless migration is explicitly in scope.
- Keep stable QA and runtime practices in `docs/BEST_PRACTICES.md`; keep this
  file compact.

Fix code until the gates pass. If a gate is wrong, change the gate deliberately
and explain why in the same change.

## After Using This Template

Follow the post-template GitHub security checklist in
`docs/BEST_PRACTICES.md`.

When upgrading an existing project's QA, follow the
[adoption procedure](docs/BEST_PRACTICES.md#adopting-into-an-existing-repository)
instead of copying bootstrap settings wholesale.
