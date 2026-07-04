# Template Repository Roadmap

This roadmap is for `j2h4u/python-docker-service-template` itself. GitHub
templates copy this file into new repositories, but it is maintainer metadata,
not a project-starting artifact. After creating a repository from this template,
delete `docs/meta/` or replace it with the new project's own planning docs. See
`docs/README.md` for the documentation map.

## Documentation Model

- Keep `README.md` as the short human-facing project overview.
- Keep `AGENTS.md` as the compact operational contract for agents.
- Keep reusable engineering guidance in `docs/BEST_PRACTICES.md`.
- Keep template-maintainer plans, decisions, and audits in `docs/meta/`.
- Add a short generated-template cleanup checklist if this distinction proves
  easy to miss in real projects.

## Agent Skill

- Design an agent skill that can consume this repository as a QA policy source.
- Route the skill by domain: Python gates, Docker context, GitHub security,
  dependency hygiene, and repository documentation.
- Make the skill audit-oriented: it should compare a target repository against
  the template's practices and report concrete gaps.
- Avoid duplicating policy text inside the skill. The skill should link back to
  `docs/BEST_PRACTICES.md` and other canonical docs.

## Template Consumer Experience

- Add a first-run checklist for repositories created from the template.
- Consider a rename script for replacing `python-docker-service-template`,
  `template_service`, and `template-service`.
- Document which files are meant to survive in generated projects and which
  files are template-maintainer metadata.
- Validate whether GitHub template creation has any useful hooks or limitations
  that affect cleanup guidance.

## QA Gates

- Keep local and CI gates aligned through `just` recipes.
- Review whether additional dependency and packaging checks belong in
  `just check`.
- Keep the CRAP threshold strict and documented.
- Keep the coverage floor strict enough to catch erosion without replacing
  per-function CRAP checks.
- Keep CRAP ratchets out of the default template unless there is inherited debt
  that cannot immediately meet an absolute threshold.
- Periodically audit Ruff preview rules and basedpyright settings for useful
  new checks.
- Keep examples small enough that the template remains understandable.
- Evaluate whether packaging smoke should move from static QA into a separate
  package job if it becomes too slow for normal iteration.
- Add stronger import-linter examples once the template has enough layers to
  demonstrate them without fake architecture.

## Docker And Runtime

- Keep Docker build context whitelist-based.
- Keep the final image minimal, non-root, and healthchecked.
- Revisit default Compose resource limits as the template gains real-world use.
- Replace the starter runtime smoke with a real protocol-level smoke once the
  template has a non-trivial service protocol.
- Add examples only when they clarify the practice without making the template
  look like an application framework.

## GitHub Repository Operations

- Keep the post-template security checklist current with GitHub's API surface.
- Recheck whether Dependabot, CodeQL, secret scanning, malware alerts, and
  security updates are copied or reset when creating repositories from the
  template.
- Verify that dependency submission keeps GitHub's Dependency Graph aligned
  with `uv.lock` in repositories created from the template.
- Decide whether OSV-Scanner, Trivy, or both should become default workflows or
  remain documented options for repositories with stricter vulnerability policy.
- Keep workflow-based CodeQL and default setup from conflicting.
- Periodically verify that the public template repo has no stale branches,
  open Dependabot PRs, failing workflows, or unexpected alerts.

## Licensing

- Keep the license model explicit: noncommercial open-source use is allowed,
  commercial use requires a separate license or written permission.
- Revisit license wording if the repository becomes a broadly reused policy
  source or an agent skill.
