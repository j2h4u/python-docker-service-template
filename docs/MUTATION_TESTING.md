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

## Scope and survivors

Configure mutation targets narrowly. Start with production source paths and
exclude slow and integration tests from the mutmut selection command. If a
survivor exposes a meaningful behavior gap, address that gap rather than raising
a broad pardon budget. Mutmut
can filter invalid mutants with mypy or pyrefly, but not pyright; in this
template, rely on the normal basedpyright gate separately instead of hiding
mutants through a type-check filter.

Disable test-selection plugins inside mutation testing unless they are
explicitly mutation-aware. This template disables Tach for mutmut's pytest
invocation because Tach's ordinary affected-test optimization can hide the very
tests mutmut needs for mutant-to-test mapping.

For larger codebases, consider mutmut's stack-depth limiting only after the
first useful runs. A low `max_stack_depth` can make mutation testing faster and
more local, but in CLI-heavy or framework-heavy code it can also disconnect
valid tests from code they exercise.

## Baselines and timeouts

Do not treat this template repository's own mutation score as a meaningful
baseline. The template intentionally has almost no domain behavior; it only
proves that the tool is installed, configured, and callable through `just`. Its
packaging-version helper is excluded from mutation because it is template
boilerplate rather than domain behavior. After creating a real project, keep the
recipe, remove template-specific exclusions, narrow `source_paths` to production
modules, and enable the hard mutation gate by default with zero surviving
mutants allowed. A baseline or ratchet is not a template default; use one only
temporarily while migrating an existing project with accumulated mutation debt.
Make it explicit, forbid new survivors, and reduce it monotonically to zero.
Surviving mutants are usually prompts to add better assertions. Timeouts should
be investigated separately: they can mean the mutant created an infinite wait,
but they can also reveal that the selected test path is too broad or too slow
for a useful mutation gate.

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

## Cache and upgrades

The `mutants/` cache is not pruned when project files are deleted or renamed;
stale modules then poison test collection with imports of names that no longer
exist. Wipe `mutants/` after removing or renaming modules since the last run;
mutmut rebuilds its stats cheaply. Mutmut minor upgrades can also multiply the
number of generated mutants — a patch bump once tripled the count on a real
project. Compare result classes, not raw totals, across upgrades, and refresh
an explicit baseline through the dedicated recipe only after validating the
new run end to end.
