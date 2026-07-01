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

Fix code until the gates pass. If a gate is wrong, change the gate deliberately
and explain why in the same change.

## After Using This Template

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

gh api "repos/$REPO/dependabot/alerts?state=open&per_page=100" --jq length
gh api "repos/$REPO/code-scanning/alerts?state=open&per_page=100" --jq length
gh api "repos/$REPO/secret-scanning/alerts?state=open&per_page=100" --jq length
```

If GitHub exposes a separate malware-alerts toggle for the new repository, check
it manually in **Settings -> Code security and analysis**. Do not assume it was
copied from the template.
