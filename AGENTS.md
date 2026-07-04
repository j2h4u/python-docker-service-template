# Agent Rules

This project uses hard gates. Do not weaken, skip, or locally suppress them to
make a change pass.

- `just check` is the static gate: Ruff, preview complexity/refactor checks,
  production print guard, types, imports, workflow lint, dependency hygiene,
  compile, and dead-code checks must pass.
- Ruff complexity and unused-argument rules are blocking. Preview complexity
  rules that are not covered by Ruff prefixes are checked explicitly.
- `just crap-check` is a blocking CRAP threshold gate for every function.
- `just unit` must pass for behavior changes.
- `just docker-build` must pass because the service runs in Docker; it includes
  Dockerfile and Compose static validation before image build.
- Use `uv` only. Keep `uv.lock` current and use hardlink mode outside Docker.
- Keep stable QA and runtime practices in `BEST_PRACTICES.md`; keep this file
  compact.

Fix code until the gates pass. If a gate is wrong, change the gate deliberately
and explain why in the same change.

## After Using This Template

Follow the post-template GitHub security checklist in `BEST_PRACTICES.md`.
