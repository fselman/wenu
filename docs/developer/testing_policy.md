# Testing policy and module independence

**Current policy:** 2026-10-18. Select tests from the actual change and its
contracts/consumers. A complete production run is a release/composition gate,
not a prerequisite for every production edit. This supersedes the blanket
full-suite rule used through PR #244. No numerical or visual oracle is removed.

## Choosing a gate

1. Review the full diff: implementation, tests/fixtures, resources, configuration,
   dependencies, build and collection. Identify changed behavior, its owner,
   public contract and immediate consumers, including dynamic/delegated callers.
2. Select the owner and affected seams. Record the named gate, added tests and
   excluded owners with reasons in the PR. Compatible internal changes reuse
   lower-level science evidence; composition needs its own seam/failure checks.
3. Expand when a changed contract reaches another owner. A change to time/frame
   meaning, SDK state/admission, resource schemas, shared dependencies, build,
   collection or new consumers needs an explicit affected-consumer matrix.
   Missing ownership requires investigation before accepting a narrow gate;
   it is not permission to silently omit coverage. A full run is justified when
   impact spans the product or cannot be bounded after review.
4. Run the selected gate once after final edits. Fix failures and rerun the
   closest gate; broaden only for newly demonstrated impact. Do not rerun the
   same tests merely after an identical-tree merge.

Broad `wenu.__init__` imports still impose collection dependencies. That prevents
claiming independent installation; it does not mean a request cleanup edit
requires executing satellite orbit/illumination or catalogue wheel tests.
Package extraction must separately prove absence of unrelated dependencies.

Root pytest remains scoped to `tests`; the isolated kernel keeps its own
[manifest](../../packages/wenu_kernel/test_selection_v1.json). Run that core
only for SDK changes or affected SDK contracts. New K3 routing needs real
consumer/compatibility evidence; adding a production SDK dependency itself
requires build/import and consumer impact review.

## Executable legacy selections

[tools/test_gates_v1.json](../../tools/test_gates_v1.json) records the reviewed
base, exact existing test selectors, protected boundaries and exclusion reasons.
[tools/run_test_gate.py](../../tools/run_test_gate.py) prints a plan by default;
`--collect` collects and `--run` executes the same selection once using the
current Python. Whole-owner selections retain every parametrization. Unknown
gates, missing tests, invalid paths and cyclic extensions fail; there is no
fallback to zero tests or the full suite. Ambient plugin autoload and
`PYTEST_ADDOPTS` are disabled for these reproducible gates. No arbitrary pytest
filters are accepted by the runner.

| Gate | Change scope | Selected evidence |
|---|---|---|
| `documentation` | Guides, inventory, executable documentation contracts | Current documentation, user-guide and fixed-sky documentation owners |
| `request-lifecycle` | Ownership/rollback and optional journal hooks preserving standalone behavior | Build/close/failure/retry; resource binding; standalone grids/horizon/tracks/disks; drawing and CLI; observer-time and fixed-sky callers |
| `request-configuration` | Above plus configuration/component/cadence behavior using unchanged science services | Extends lifecycle with Moon/Venus/Mercury disk/sequence and reference-policy owners |

The names are reviewed scopes, not automatic changed-file classifications.
A numerical, renderer, atlas, shared-schema or new-routing change cannot be
approved just because its file also appears in one of these gates. Review and
extend the selection and retain independent owner oracles as necessary.
The new selections await normal Mac collection/execution; no timing target or
independent product installation is claimed. Their supporting tooling is
independently tested with the standard library:

```bash
python -I -S -m unittest discover -s tools/tests -v
python tools/run_test_gate.py documentation --run
python tools/run_test_gate.py request-configuration --run
```

For routine lifecycle work, choose `request-lifecycle` instead of
`request-configuration`; do not run both, since the latter includes the former.
Run documentation when it changes. The current tooling/manifest milestone uses
the broader gate once to validate all newly published selectors, without a full
production run. Future unchanged manifests do not require revalidating every
gate. `--collect` is available for diagnosis, not an extra mandatory pass before
`--run`.

## Request consumers and retained evidence

The accepted baseline is PR #244, tested head `595ff557`, merged as `d36b1786`
with the same tree: 104 focused Mac tests and 3,415 production tests passed.
That receipt covers unchanged owners; it is not a claim that future changed
code passed all 3,415 tests. The inventory retains exact revisions and times.

| Actual route | Implication for selection |
|---|---|
| `generate_chart_request` → `build_chart_request` → `_prepare_with_sphere` | Journal/rollback owner tests plus real observer-time exports and report clipping |
| Ordinary CLI → `draw_chart_view_request` → helpers → export | Separate route without the journal; preserve standalone helper semantics and direct drawing/CLI seams |
| Observer-time sequence → ordinary generator | Keep real two-frame export and resume, beyond mocked delegation |
| Fixed-sky reference/reuse → ordinary generator; complete-render baseline → observer-time pipeline | Keep both delegation/observer-lifetime routes and baseline planning; these delegation tests mock the generator, so they do not establish new full fixed-scene numerical equivalence |
| Atlas CLI → `wenu_chart atlas-sheet` → native `AtlasSheetChartRequest` branch | Preserves exact sheet geometry/paper and observer-free native sky; branches before ordinary journal/configuration. Keep public dispatch guard; full saved/spawned-page comparisons belong to atlas/snapshot/export changes or release composition |

Unchanged satellite crossing/acceleration/radiometry physics, catalogue curation
and wheel/sdist packaging, native snapshot persistence and kernel internals do
not belong to a compatible request-lifecycle gate. Their science and installed
product tests remain in their own owners and in release integration. A changed
resource, algorithm or interface brings the corresponding owner back into scope.
The Python `create_atlas()` API retains a direct generator fallback when no
chart command is supplied. The installed atlas CLI injects `wenu.cli.chart.main`
for serial/spawn workers. Sharing the command is implemented; a common request
lifecycle across ordinary drawing, ordinary generation and native sheets remains
a K3 obligation. Product-specific geometry does not justify duplicated lifecycle.
No existing tests are moved, deleted, weakened or re-marked by this selection.
The coordinate guide remains current; test orchestration changes no astronomy.

## Integration and receipt reuse

Use a full plugin-disabled production run for release closure and broad shared
changes whose reviewed impact warrants it. State that trigger in the PR rather
than invoking full integration automatically for every K3 revision. Include the
isolated SDK gate only if its contract/implementation is affected. Packaging,
visual and print acceptance remain separate checks when those outputs change.

Reuse exact receipts for unchanged owners only after comparing their executable
code, scientific fixtures/resources, dependencies, configuration, packaging and
test collection. Record tested/delivered revisions and relevant content
identity. Shared-service changes invalidate dependent receipts; a previously
passing full suite is not proof for changed consumers. Documentation/tooling
edits that preserve product sources, resources, dependencies, root collection
and product test bodies do not require repeating scientific integration.

## Shipped provider conformance gate

`wenu_kernel.conformance` is an optional stdlib test module included in the SDK
wheel. Provider packages build fresh offline `ProviderCase` factories and run
`provider_suite` beside their own science tests, without importing Wenu or
another provider's fixtures. Activity hooks must observe numerical work inside
metadata/planning as well as full evaluation. Mutation hooks must exercise
real potential aliases, or the owner documents that no mutable buffer exists.
Run cases for each admitted catalogue/model/reference/subset. Advertised reuse
requires a supplied executable case; canonical cases must exercise planning.

The eight common/capability checks cover stable/pure metadata, ordered states
and exact caching, cold/warm/request-order equivalence, immutable publication,
owned/borrowed lifetime, invalid selection/scale admission, optional direction
certification/refusal and optional canonical planning. The SDK applies them to
six constructed cases and fault-tests the harness. A separate isolated consumer
defines its own constructed provider and imports only shipped SDK modules.
Sample conformance is not a proof of physical accuracy, interval-wide bounds,
resource integrity or all descriptor combinations; retain those owner oracles.

Existing synthetic fault/recovery assertions and test IDs remain unchanged;
their test-side mixin is renamed to clarify that it is fixture-specific. Root
legacy pytest discovery and numerical/render suites are unchanged. The
coordinate guide remains current: this slice changes no time/frame science.

## Continuous migration and independent-module gates

Test reorganization starts with each implementation slice, not after the
freeze. The [as-is audit and functionality ledger](kernel_migration_audit_v1.md)
and [pinned file inventory](kernel_migration_inventory_v1.json) are the starting
point. Maintain them as owners migrate; a new source, command or test must not
silently escape the ledger. Baseline hashes remain historical evidence.

Classify tests on three independent axes: enduring owner, boundary level
(unit, provider conformance, immediate seam, installed product/release) and
cost/evidence (numerical, integration, visual, slow). Markers alone do not
provide dependency isolation. Pure validation tests must not require graphics
or another provider merely to collect. Keep domain fixtures with their owner;
share contract fixtures through the core conformance kit and use explicit
helpers rather than importing another test module.

For each owner extraction, record old-to-new test node IDs, protected faults,
independent oracle/resource provenance and fixture/import changes. Preserve
assertions or justify their replacement. Do not reduce a parametrized render
matrix until its actual interactions and measured cost are understood. Keep
representative real public paths and meaningful cross-option interactions.

Selection must follow semantic dependency direction, not only textual imports
or changed filenames. Each isolated package publishes an executable gate and
a selection manifest: changed owner, affected contracts/consumers, required
suites, excluded suites and rationale. A shared SDK semantic change, backend
upgrade, common fixture/resource schema, build change or unknown ownership
requires impact review and the corresponding consumer seams. A test cannot
be skipped merely because its file is outside the changed directory.

Prove installation, import, collection and execution with unrelated providers
absent before claiming package independence. Focused legacy selection can be
reviewed before that extraction; broad imports alone do not require executing
unrelated physics tests. Expand for actual semantic impact or unresolved
ownership, using the procedure above. Profile selected gates with `--durations`, separating collection, cold source
loading and warm work. No speed target is inferred from static file counts.

An internal change in package A, preserving the accepted public contract,
requires package A's tests and its kernel conformance tests. It must not
require running or installing package B, C, or product/rendering suites.
These are executable isolation gates, not a convention based on folder names.

| Change | Required owning verification | Unrelated suites |
|---|---|---|
| Documentation | Links, syntax, inventory and archival integrity | None |
| New appearance preset | Preset resource and shared loader contract | No astrometry/orbit tests |
| Star-provider implementation | Stellar physics plus kernel conformance | No galaxy/asteroid/satellite suites |
| Galaxy-provider implementation | Galaxy state plus kernel conformance | No stellar or moving-body suites |
| Projection | Geometry/projection contract and its immediate consumer | No catalogue acquisition/propagation suites |
| Atlas composition | Atlas/chart public contract and book outputs | No provider internal suites |
| Kernel contract or shared dependency change | Explicit affected-consumer matrix and integration evidence | Expand only for actual impact |

Release-level composition checks may test installed combinations. They are
owned by the integration/release layer and are not a hidden prerequisite for
every independently compatible package change. Cross-domain integration
remains necessary when the shared contract itself changes; that is a separately
reviewed kernel version change, not ordinary package maintenance.

## Faults the contract gates must detect

- Core importing concrete providers or graphics; one provider importing another.
- Importing/loading stars requiring planet, galaxy or satellite dependencies.
- In-place mutation of snapshots, metadata or cached state.
- A changed observer invalidating unrelated physical catalogue states.
- Updating stars reevaluating the unchanged galaxy provider.
- Stale dependent star-connected constellation geometry after propagation.
- Provider unload/resource-close failure leaking state into another request.
- A provider returning an unsupported frame/status/time combination or hiding
  absent parallax, velocity, coverage or uncertainty as zero.
- A product bypassing the kernel to call an old position source.

Use synthetic/fake providers with call counts and fault injection for these
barriers. Keep independent numerical science oracles in their owning packages.
Keep cold-start, order-independence, public-path, offline-resource and
scientific fault coverage; speed is not a reason to replace them with mocks.

## Documentation checks

Tests protect navigable active links, valid Python examples, public imports,
complete source ownership, current CLI/configuration documentation and the
exact preservation of archived editions. Do not require historical acceptance
sentences, elapsed times or obsolete plans to remain in active guides.

The old 238-test documentation diary is preserved byte-for-byte in the
[baseline archive](archive/pre_kernel_20261017/tests/test_current_documentation.py.txt).
Its historical assertions are not collected as a current test suite. Current
operational checks are retained or replaced explicitly. The subsequent audit
repairs stale user-guide/fixed-sky documentation tests and preserves their
original editions in its inventory; scientific and product test files remain
unchanged. See the [cleanup ledger](documentation_cleanup_v1.json).
