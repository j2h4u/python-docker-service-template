# Agent Rules

This project uses hard gates. Do not weaken, skip, or locally suppress them to
make a change pass.

- `just check` is the static gate: Ruff, types, imports, workflow lint, compile,
  and dead-code checks must pass.
- Ruff complexity rules are blocking and use Ruff defaults.
- `just crap-check` is a blocking CRAP threshold gate for every function.
- `just unit` must pass for behavior changes.
- `just docker-build` must pass because the service runs in Docker.
- Use `uv` only. Keep `uv.lock` current and use hardlink mode outside Docker.

Fix code until the gates pass. If a gate is wrong, change the gate deliberately
and explain why in the same change.
