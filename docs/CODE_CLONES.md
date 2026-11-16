# Code Clone Detection

See [README](../README.md) for active commands and
[Best Practices](BEST_PRACTICES.md) for the existing QA contract.

## Quality Contract

Every production file in the configured scope must be processed without parse
or skipping errors. Every finding emitted by either detector must be fixed or
match a current, explicitly reviewed exception. Agents assess meaning; scripts
and CI validate recorded decisions. No LLM runs inside CI.

This does not guarantee discovery of every possible clone. Similar syntax can
implement different responsibilities, and detectors have false negatives.
Do not create an inappropriate shared abstraction just to silence a finding.

Ordinary enforcement scans all maintained Python under `src/` and `scripts/`,
including unchanged files. Tests belong to a manual audit with different
expectations about fixture/assertion repetition. Generated source requires an
explicit reviewed scope decision.

## Selected Tools And Commands

Pin `pyscn==1.33.0` and `jscpd==5.4.1` as locked development tools. Both are
native binaries distributed through Python packages. Ordinary execution needs
no Node runtime, embedding model, API key or inference service. Verify supported
platforms before declaring integration ready.

The two detectors provide complementary structural analyses. PySCN static
data-flow Type-4 analysis is distinct from embedding inference.

`just clone-check` runs inside `just check`, which CI already invokes. Install
dependencies before checking; the gate runs installed locked tools. No
additional CI job is needed. `scripts/clone_tools.py` holds pinned effective
settings; `.clone-acceptances.json` records that policy and reviewed exceptions.

PySCN should retain types 1-4 and data-flow analysis, pin grouping/sensitivity,
disable LSH explicitly with `lsh_enabled = "false"`, and validate JSON schema 2.
For jscpd retain combined token normalization, near-miss and AST detection:
ignore identifier/literal differences, gaps up to 2 lines, similarity 0.8.
AST-only filtering loses a tested third-copy case caught by the combined pass.

Keep machine-readable configuration and exceptions outside `docs/` and
Markdown, since CI treats documentation-only changes as eligible for heavy-job
skipping. Gate policy changes must trigger their own validation.

## Adoption And Review

For a new project, adapt `SOURCE_ROOTS` in `scripts/check_clones.py` if the
production layout differs, then migrate the acceptance contract. Keep tests
outside enforcement. Review copied template exceptions: retain them only if
the exact reviewed code and rationale still apply.

For an existing project, copy `scripts/clone_tools.py`, `scripts/check_clones.py`
and optionally `scripts/clone_audit.py`; merge their locked dev dependencies,
Just recipes and documentation links. Preserve the target layout and stronger
existing checks. Start its acceptance file with its own contract and an empty
`accepted` list, not the template's accepted pairs. Do not copy the example
service, package version, release history or maintainer roadmap. See both
[adoption checklists](../README.md).

Keep clone scope in the shared `SOURCE_ROOTS` policy rather than adding a
separate audit scope knob. Use detector-native configuration and report
validation where available, and audit reviewed acceptance changes explicitly.
Retain existing justified contract checks, but do not reproduce detector
behavior in one-off tests for every finding.

At first adoption, scan the full production scope and review every emitted
finding. Do not bulk-accept existing debt.

Inspect both implementations, callers and relevant tests. Consolidate genuinely
shared invariants or algorithms when callers' behavior remains intact. Preserve
independent contracts or lifecycle boundaries with a concrete explanation.
"Already existed" is not sufficient justification.

After a fix, rerun checking. For intentional duplication, propose the specific
exception and reason in the PR. Agent review evaluates that reason; the script
checks its presence and binding. As with other QA configuration, an agent able
to edit policy remains inside the repository review trust boundary.

Run `just clone-check` and inspect `.clone-reports/review.json`. It contains
current findings, display locations, the current contract and candidate records
with blank reasons. Copy only individually reviewed candidates into the
acceptance file's `accepted` list and supply their reasons. The command never
writes acceptances. Missing/mismatching policy remains an error even when no
clones are found. Do not paste the whole report as a blanket baseline.

## Reviewed Exceptions

Use one small adapter with tool-specific parsers and one reviewed-record file.
Avoid separate native baselines and reason sidecars that can drift apart.

Bind records to detector, identity-schema version, effective detector settings,
configured source roots/exclusions, both fragment contents, reviewed
multiplicity and nonempty reason. The implementation uses a small common
raw-source identity: SHA-256 of detector and sorted endpoint hashes, computed
from validated inclusive full-line UTF-8 source spans. This avoids mapping
opaque native baseline keys back to reported locations. PySCN sequential IDs
and normalized hashes are never used as acceptance keys.

Require exact equality of current and accepted multisets. New findings or
higher multiplicity fail as unreviewed; removed findings or lower multiplicity
fail as stale permissions. Editing either copy requires renewed review,
including names/literals normalized away during matching. A new reported copy
requires review; no claim is made that the tools discover every new copy.

No wildcard, whole-file permission, unlimited count or automatic refresh.
Reject supported inline clone-ignore markers in enforced source, including
unmatched markers and native jscpd markers embedded in strings. Directory
symlinks are rejected instead of silently skipping their contents.
Exceptions accept pairs rather than removing source from
either detector. Prevent implicit configuration/ignore files from silently
narrowing the reviewed scope.

Paths/lines are display hints. Content identity should survive moves and
preceding-line edits. It consequently cannot distinguish relocation from
deletion followed by identical reinsertion elsewhere. Accept this equivalence
limit rather than building Git-history provenance tracking.

Bind scope definitions, not the changing file inventory or entire lockfile.
Unrelated additions/dependency changes should not revoke all acceptances.
Tool, scope, sensitivity, grouping and identity changes need deliberate
migration and review; CI never regenerates permissions.

## Analysis Failures And Capacity

Validate fresh complete report files before applying acceptances. Reject tool
errors, timeouts, invalid schema/version, malformed or contradictory mandatory
fields, invalid endpoint references/spans, parse diagnostics and skipped input.
Missing arrays must not become empty success results. A process exit code or
`clone.success` flag alone is insufficient.

Validate source accounting against an independent inventory using the pinned
tool's proven semantics. Distinguish missing roots, explicitly empty scope,
tiny valid files and parse failures. Zero fragments alone is neither an error
nor evidence of successful analysis. Empty scope needs an empty acceptance set.

The runner stages an explicit snapshot without repository ignore/config files,
validates every selected file with Python AST parsing, and checks PySCN's file
counts. jscpd excludes files below its token/line thresholds by design, so its
native source count can be smaller. Tiny valid files are not falsely treated
as failed analysis. Files over the pinned 1 MiB limit fail explicitly.

PySCN internally retains at most 10,000 matching pairs. This is not a maximum
project size: thousands of distinct functions can produce few matches.
The capacity concerns matching pairs, not a universal function-count ceiling.

Reject a report containing 10,000 or more pairs before matching acceptances.
No accepted multiplicity or reason can waive observable truncation/saturation.
This guard is partial protection: internal trimming precedes other filtering,
so a smaller final report does not certify an uncapped search. Hidden pairs
remain a documented detector false negative. Track an upstream overflow signal
as follow-up, not a prerequisite for enforcing the reported-finding contract.

## Manual Extended Audit

`just clone-audit` is separate, offline by default, with explicit
embedding/API opt-in. Use it at onboarding, before major reviews and after
substantial restructuring. Include tests when appropriate and distinguish
production, test and mixed findings.

This extended audit is optional, not a default adoption requirement. Copy its
embedding/API path only when the target has a concrete use for it.

Embeddings can reveal additional related implementations, but similarity does
not prove behavioral equivalence. jscpd semantic mode is experimental. Reuse
its implementation; do not build another vector database or inference engine.

Choose provider/model and outbound source scope explicitly. Credentials stay
in the environment. Bound total runtime and supported request/retry budgets;
verify controls actually honored by the pinned binary. Normal gates never
invoke this mode. Do not promise unsupported provider quotas.

```bash
just clone-check
just clone-audit --include-tests
just clone-audit --semantic --endpoint https://provider.example/v1/embeddings --model MODEL --timeout 180
```

Semantic execution requires `JSCPD_SEMANTIC_API_KEY` in the environment and sends
selected Python fragments to the explicitly supplied provider. It never falls
back to local inference. The total deadline kills the process group; native
retries apply within it. The pinned binary has no request-count quota.

The ignored `.clone-audit/audit.json` records state, scope, effective limits,
errors and a per-run directory with native reports. HTTP is allowed only on
loopback for local provider-stub testing; external endpoints require HTTPS.

Use an ignored local cache bound to endpoint/provider, model identity,
preprocessing and source content. Never cache failures as empty findings or
claim reproducibility for an unpinned model alias.

Retain useful partial findings, but distinguish complete, incomplete and failed
runs. Record configuration, analyzed/skipped scope and API errors. Timeout,
quota exhaustion and partial API failure are not clean audits. Manual results
never automatically alter production acceptances.

## Verification During Adoption And Upgrades

Run existing checks for the shared contract when changing its behavior, then
run the target project's full production scan and review every emitted finding
under final settings. Do not create exhaustive malformed-report fixtures or a
regression test for each finding; rely on native validators where available
and audit the actual scan and acceptance changes. Passing checks for the
template's tiny service does not establish correctness of the target's scope
or exceptions.

## Sources

- [PySCN documentation](https://docs.codescan.dev/pyscn/).
- [Versioned clone service](https://github.com/ludo-technologies/pyscn/blob/v1.33.0/service/clone_service.go).
- [Versioned detector](https://github.com/ludo-technologies/pyscn/blob/v1.33.0/internal/analyzer/clone_detector.go).
- [jscpd baseline](https://jscpd.dev/guides/baseline) and
  [JSON reports](https://jscpd.dev/reference/reporters/json).
- [jscpd semantic audit](https://jscpd.dev/guides/semantic-clones).
- [PMD CPD suppression comments](https://pmd.github.io/pmd/pmd_userdocs_cpd.html).

Live documentation can describe newer behavior than pinned binaries. Verify
the installed versions and any existing contract checks during upgrades.
