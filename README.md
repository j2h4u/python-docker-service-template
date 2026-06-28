# Python Docker Service Template

Template for Python 3.14 services that run in Docker and ship through hard
quality gates.

## After Creating A Repo From This Template

1. Rename `python-docker-service-template`, `template_service`, and
   `template-service` to the product names.
2. Run `uv lock`.
3. Run `just verify`.
4. Keep `AGENTS.md` intact unless the gate policy changes deliberately.

## Gates

`just verify` is the local contract: static checks, CRAP threshold, unit tests,
and Docker build.
