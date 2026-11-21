# Mutation Testing

Methodology for the mutation-testing audit lane. The recipe, configuration, and
operational rules live here; [BEST Practices](BEST_PRACTICES.md) links to this
document from the QA-gates overview.

## Why and when

Use mutation testing to audit whether tests actually detect behavioral changes,
not just whether code was executed. The template uses `mutmut` as the default
tool because it is current on modern Python, works naturally with pytest, keeps
incremental state in `mutants/`, and can run with bounded parallelism through
`just mutation-check`. The recipe exports mutmut's CI/CD JSON statistics and
fails on survived mutants, mutants with no tests, suspicious results, timeouts,
interrupted runs, and segfaults. The default config re-runs mutants when
dependency or config files change so a gate does not pass on stale cached
results. Keep mutation testing in the slow lane: run it before releases, for
mature modules, after important test refactors, and during QA audits. Do not
wire it into `just check`; mutation testing is intentionally more expensive than
static analysis and CRAP.

## Goals

The hard mutation gate runs with **zero surviving mutants allowed** on business
logic. A baseline or ratchet is a temporary tool while migrating a project with
accumulated mutation debt — make it explicit, forbid new survivors, and reduce
it monotonically to zero. Do not keep a baseline as a permanent state.

Exclude from mutation entirely (display, logging, generated code) — then every
remaining mutant in business logic must be killed by a test. If a mutant seems
impossible to kill, the code is probably too complex: simplify it until the
mutant either becomes testable or disappears.

## Scope and survivors

Configure mutation targets narrowly. Start with production source paths and
exclude slow and integration tests from the mutmut selection command.

Exclude from mutation entirely (via `do_not_mutate` in `pyproject.toml`):
- Generated code (protobuf, migrations)
- Pure display/formatting modules (text rendering, CLI help)
- Packaging boilerplate

Do NOT exclude:
- Domain logic and business calculations
- Data mapping (proto→domain, domain→wire)
- Resolution, reconciliation, ranking algorithms

If a survivor exposes a meaningful behavior gap, address that gap rather than
raising a broad pardon budget. Mutmut can filter invalid mutants with mypy or
pyrefly, but not pyright; in this template, rely on the normal basedpyright
gate separately instead of hiding mutants through a type-check filter.

Disable test-selection plugins inside mutation testing unless they are
explicitly mutation-aware. This template disables Tach for mutmut's pytest
invocation because Tach's ordinary affected-test optimization can hide the very
tests mutmut needs for mutant-to-test mapping.

## Killing survivors efficiently

The naive approach — one assertion per surviving mutant — is wrong and
wasteful. Most mutants survive because existing tests use weak assertions,
not because tests are missing. Strengthen the assertions instead:

| Weak (mutants survive) | Strong (mutants killed) |
|---|---|
| `assert result is not None` | `assert result.field == exact_value` |
| `assert result > 0` | `assert result == 42.0` |
| `assert len(items) > 0` | `assert len(items) == 3 and items[0].name == "..."` |
| Check 2-3 key fields | Check ALL fields of the result object |
| Check status only | Check status + data + warnings + metadata |

One strengthened test that asserts every field of a result object kills
dozens of mutants at once. Audit which tests run against a mutated
function, identify what they DON'T assert, and add the missing
assertions.

When triaging survivors:
1. Group by function — one function's survivors share a root cause
2. Check what the covering tests assert vs what the function returns
3. Add assertions for every unchecked field
4. Re-run mutation testing on that function only to verify
5. Only then move to the next function cluster
6. Stop when remaining survivors are all justified as equivalent or
   not-worth-testing — do not write a test for every micro-edge case

## Baselines and the ratchet gate

A baseline records the current survivor count; the ratchet gate
(`just mutation-check`) fails if new survivors appear. This prevents
regressions while allowing gradual improvement.

Workflow for a new project:
1. Run `just mutation-check` — it will fail because no baseline exists
2. Triage survivors: fix critical gaps, justify the rest
3. Run `just mutation-baseline` to record the current state
4. From now on, `just mutation-check` passes only if survivor count
   does not increase
5. Over time, as you strengthen tests and suppress equivalents,
   refresh the baseline downward

The baseline is a tool, not a goal. Do not keep it at zero artificially
by excluding everything from mutation. Do not suppress mutants without
understanding why they survive. The point is to have confidence that
your critical logic is well-tested, not to achieve a number.

Timeouts should be investigated separately: they can mean the mutant
created an infinite wait, but they can also reveal that the selected
test path is too broad or too slow for a useful mutation gate.

## Running inside the mutants tree (mutmut >= 3.8.1)

Since mutmut 3.8.1 the runner executes pytest inside its own copied tree under
`mutants/`, with two operational consequences. First, tests that read
repository files relative to the project root resolve those paths inside the
copy: list every such file in `also_copy` (fixture configs, example settings),
or anchor fixtures only through directories that are copied anyway. Second,
tests that assert over the real repository shape — quality-gate self-tests,
clone reporting, supply-chain pins, release recipe checks — must be excluded
from the mutmut pytest invocation with `--ignore`: inside the instrumented
tree they see thousands of generated annotations and copied-only sources, so
they fail without proving anything about mutants. Excluding them loses no
mutation signal, because they test the repository tooling, not production
behavior.

## CPU priority

Mutation runs are long and CPU-bound. Run them at the lowest scheduler
priority (`nice -n 19`) and idle I/O class (`ionice -c 3`) so they take
free CPU and I/O bandwidth but immediately yield when production
workloads or interactive processes need the resources. The Justfile
recipes already apply both; keep them when adapting.

## Cache and upgrades

The `mutants/` cache is not pruned when project files are deleted or renamed;
stale modules then poison test collection with imports of names that no longer
exist. Wipe `mutants/` after removing or renaming modules since the last run;
mutmut rebuilds its stats cheaply. Mutmut minor upgrades can also multiply the
number of generated mutants — a patch bump once tripled the count on a real
project. Compare result classes, not raw totals, across upgrades, and refresh
the baseline through the dedicated recipe only after validating the new run
end to end.
