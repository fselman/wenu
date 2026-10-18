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

## Static direction SDK extension

Run the independent core gate and an isolated dev7 wheel installation without
Wenu or astronomy dependencies for `static_direction` admission. The existing
record/session/reuse/conformance owners cover nullable source epochs, retained
declared epochs, refusals for other models, coverage/scale/error checks, atomic
failed batches and certified original-anchor reuse. The portable kit includes
plain/certified static cases and detects deliberately time-varying static output.
Run `kernel-static-compatibility` with this candidate SDK on PYTHONPATH for the
existing stellar adapter/Stars owners, plus documentation and tooling. No root
dependency, resource, snapshot, product routing or graphics code changes, so
atlas rendering, unrelated providers and the full production suite are excluded.
The production pin remains unchanged until a consumer requires the extension.

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
| `request-shared-lifecycle` | Scope unification reaching native atlas lifetime/default dispatch | Extends lifecycle with explicit/default command paths, real serial/spawn exports and existing cold/saved/spawned output equivalence |
| `kernel-native-stars` | Native stellar state routing and separate SDK dependency | Stellar owner/conformance, saved/fresh-process/worker consumers, legacy pixel comparison and wheel/sdist/editable native calls |
| `native-atlas-output` | Native canvas/layout/export and installed native consumption with unchanged scientific state | Three display-DPI/page-shape regressions, exact legacy pixels, real cold/saved/spawn equivalence, file-admitted CLI and installation |

The names are reviewed scopes, not automatic changed-file classifications.
A numerical, renderer, atlas, shared-schema or new-routing change cannot be
approved just because its file also appears in one of these gates. Review and
extend the selection and retain independent owner oracles as necessary.
The original request-configuration selection passed 286 tests in 91.56 s on
Fernando's Mac; 36 documentation tests passed in 2.51 s and eight tooling tests
passed in 0.083 s at `04c6ae21` (identical merge `7e1b1f9b`). The current shared-
lifecycle gate passed 247 tests in 232.56 s, with 36 documentation tests in
3.06 s and eight tooling tests in 0.360 s at `33c15593` (identical merge
`e5bd7c16`). PR #247's final Mac followup passed at `8e4be740` (identical merge
`bf804cbb`): eight tooling tests in 0.563 s, 36 documentation tests in 3.04 s
and seven native-output cases in 250.81 s. Their supporting tooling is
independently tested with the standard library:

```bash
python -I -S -m unittest discover -s tools/tests -v
python tools/run_test_gate.py documentation --run
python tools/run_test_gate.py request-configuration --run
```

For routine lifecycle work, choose `request-lifecycle` instead of
`request-configuration`; do not run both, since the latter includes the former.
Run documentation when it changes. Shared-lifecycle changes use
`request-shared-lifecycle` once,
which includes `request-lifecycle`. Configuration algorithms are unchanged, so
the additional disk/sequence/reference-policy owner gate is not repeated. The
change reaches atlas execution, so retain the
existing cold/saved/spawned comparison despite its previous approximately
126-second cost. No full production repeat or separate narrower gate is needed.
Future unchanged manifests do not require revalidating every gate. `--collect` is available for diagnosis, not an extra mandatory pass before
`--run`.

## Nonstellar ingestion gate

`galaxy-static-model` is the narrower followup for model-specific epoch
requirements. It runs the changed metadata owner and galaxy geometry owner,
all six fixed-table round trips, an actual static no-epoch galaxy preparation/
restore, the known source-epoch round trip and source-free fresh-process restore.
Tests span Julian years -10000 to +10000 without changing native galaxy centres,
retain supplied epoch provenance and demonstrate that frame and other provider
epoch requirements still fail when missing. The new strict no-epoch regression
fails on the previous implementation. Snapshot schema/resources, numerical
transforms, renderer, worker dispatch and SDK are unchanged; reuse PR #251's
corruption/public-command evidence. Do not run the broader parent gates too.

The subsequent `nonstellar-admission` gate extends this selection once. It adds
immutable record/strict-refusal/known-versus-unknown epoch and observed-provider
identity regressions, all existing snapshot corruption cases, seven nonstellar
metadata/header/digest/unit conflicts, a synthetic known-epoch round trip and a
real saved-sky CLI export. The inherited selection retains all six fixed families,
fresh-process source-free restore and v1-v4 compatibility. Strict source metadata
closure is not claimed by compatible chart output. Snapshot v5 changes coordinate
meaning/serialization, so these admission and consumer seams are required; unrelated
orbits, numerical transforms, projections, renderer algorithms, packaging and SDK
internals are unchanged and reuse prior evidence. Do not run the parent gate too.

`nonstellar-ingestion` covers the shared normalizer and its inherited galaxy,
globular, remnant and PN seams. It retains the existing normalization/geometry
owners and adds synthetic declared-unit, unconsumed-field, nested-metadata and
atomic failed-reload regressions. Packaged source tables are checked directly.
The fixed-table snapshot test covers all six families' rows/masks/units,
descriptions, metadata and selected geometry; fresh-process and legacy admission
checks cover the changed contents through the unchanged transport. No snapshot
schema or frame/epoch admission is changed. SDK, source acquisition/curation,
packaging, projection/render algorithms, atlas dispatch/workers and unrelated
body/satellite suites reuse their existing evidence. Those owners are required
again only if their contracts change. Run this gate once, plus documentation
and the stdlib tooling check for the edited gate manifest.

## Native stellar kernel gate

`kernel-native-stars` is independent of request-lifecycle selections. It runs
the native provider owner (including eight shipped conformance checks), the
existing stellar owner, the public position API guard, real full-catalogue
cold/saved/fresh-process and label/gap consumers, legacy-versus-kernel page
pixels, serial/spawn atlas equivalence and the real public producer. The new
external runtime dependency adds wheel/sdist/editable installation checks to
the existing packaging owner, including an actual native call and verification
that the SDK is not vendored inside Wenu. No prior test assertion is weakened.

Install the checked-out SDK separately before running this gate:

```bash
python -m pip install --no-deps --no-build-isolation ./packages/wenu_kernel
python -m pip install --no-deps --no-build-isolation -e .
python -I -S -m unittest discover -s tools/tests -v
python tools/run_test_gate.py documentation --run
python tools/run_test_gate.py kernel-native-stars --run
```

The provisional immutable Git dependency is documented in the
[adapter reference](implementation_reference.md#native-stellar-kernel-adapter).
The SDK source is unchanged since accepted PR #242; its 157-test suite is not
repeated. Adapter conformance uses the installed SDK. Native-only routing leaves
ordinary observed astrometry, other providers and scientific projection/render
algorithms unchanged, so unrelated orbital/radiometry/body suites and the full
production suite are excluded. The existing stellar owner still exercises its
observed seam. Installation and native real rendering remain Mac acceptance
requirements; controlled local harnesses are not substitutes for those checks.

The `native-atlas-output` followup selection reuses the initial Mac's 35
passing state/selection/snapshot checks when only native canvas construction
and the two new test-admission/metadata defects change. It runs seven cases:
the three polar/regional/hemisphere display-DPI regressions, legacy page pixels,
real cold/saved/spawn output equivalence, file-admitted native CLI and the
wheel/sdist/editable installed native call. The regression deliberately changes
ambient figure dpi from 100 to 200; all three shapes fail before the fix.
The regional case reproduces the reported 0.54-point label shifts and 990
mismatched image elements. The fix uses fixed 100-dpi offscreen layout rather
than changing pixel tolerances or the renderer's placement algorithms.
Run this smaller gate for that bounded followup; use `kernel-native-stars`
for changes to the stellar adapter itself. The coordinate guide remains
current because this followup changes display measurement ownership only.

### Public native positions and constellation endpoints

`native-stellar-routing` covers the next bounded consumer change on `bf804cbb`:
`Stars.position`, explicit HIP lookup and native constellation-line geometry.
It runs the stellar owner, stellar public-position cases, line cases
from the mixed geometry owner, and real saved/rendered consumers. The
nonstellar position providers, grids and boundaries in those mixed files are
not changed and are not rerun just because they share a file.

The closest position and native-line tests are extended without removing old
assertions. New faults protected are bypass of returned kernel vectors, silent
fallback after refusal, raw-table/private/Skyfield coupling in native lines,
missing faint endpoints, wrong identity joins, active-selection mutation and
incorrect source-epoch metadata. Real cold/saved positions and every endpoint,
source-free fresh-process APIs, frozen label/gap behavior, exact raw-coordinate
page pixels and serial/spawn output remain selected. Native label-anchor
calculation itself is deliberately not migrated in this slice.

```bash
python -I -S -m unittest discover -s tools/tests -v
python tools/run_test_gate.py documentation --run
python tools/run_test_gate.py native-stellar-routing --run
```

The metadata-ingestion correction expands the same gate with the adapter owner
and metadata admission tests, full-source snapshot equality, corruption/refusal,
v1/v2 compatibility and atomic publication, plus actual wheel/sdist/editable
installation. These checks are needed because a new metadata resource/module
and snapshot schema v3 now ship. Alternate-epoch synthetic metadata must reach
every native stellar API and the real kernel; missing or conflicting epoch,
scale, units, identity or provenance must fail before publication. Original
source fields must survive normalization and persistence.

SDK source and provider numerical algorithm remain unchanged. Reuse PR #247
display-DPI and PR #242 SDK evidence; do not rerun the 157 SDK tests,
orbital/radiometry physics, request-lifecycle gates or the full production suite.
The whole stellar owner still checks its observed seam; observed line tests
protect the unmodified observer-time route. Coordinate metadata changes require
the updated coordinate/scientific contracts, not a claim of proper motion.
The broader metadata audit is static evidence for unmodified providers; it is
not a claim that their open findings have been repaired or numerically retested.

## Request consumers and retained evidence

`native-metadata-resources` is the bounded Python 3.11 resource-reader repair
gate. At `9da34fc9`, the combined Mac run passed 79 cases and nine provider
subtests, with 40 setup errors and one installation failure all caused by the
same multi-part namespace `joinpath` call. Tooling (8) and complete documentation
(36) passed. Retain that evidence and repeat the 41 blocked cases plus the new
single-component traversal regression (42 cases); do not repeat the 79 passing
cases. The regression reads real packaged metadata through a reader with the
older one-child method signature and fails before the fix. Chaining joins
changes resource access only; coordinate/scientific contracts remain current.

`open-cluster-metadata` is the bounded followup gate for selected row epochs,
coordinate-source lineage, independent copies of source metadata and snapshot
v4/legacy admission. It selects the cluster ingestion/geometry/render seams,
the public position-provider contract, actual cold/saved lineage, corruption
guards, v1-v3 compatibility, source-free resume and real native pixel/CLI/spawn
consumers. Preserve observed selections/caches and source masks. The closest
existing selected-order and fixed-catalogue snapshot tests remain intact; new
regressions detect inherited J2000, metadata loss and invalid epoch publication.

```bash
python -I -S -m unittest discover -s tools/tests -v
python tools/run_test_gate.py documentation --run
python tools/run_test_gate.py open-cluster-metadata --run
```

Do not run the whole mixed open-cluster file: its curation, membership, photometry,
acquisition and plotting-tool algorithms are unchanged. SDK, stellar ingestion,
orbital/radiometry physics, dependency/build/resource bytes and renderer algorithms
are unchanged too. Retain their accepted evidence instead of repeating their
owner gates. The snapshot version/reader changes justify actual saved/spawn
consumption; no full production or package-installation repeat is needed.

The accepted baseline is PR #244, tested head `595ff557`, merged as `d36b1786`
with the same tree: 104 focused Mac tests and 3,415 production tests passed.
That receipt covers unchanged owners; it is not a claim that future changed
code passed all 3,415 tests. The inventory retains exact revisions and times.

| Actual route | Implication for selection |
|---|---|
| `generate_chart_request` → `build_chart_request` → `_prepare_with_sphere` | Journal/rollback owner tests plus real observer-time exports and report clipping |
| Ordinary CLI → `draw_chart_view_request` → helpers → export | Separate geometry route now using the common scope; retain direct drawing/CLI, partial setup/export failure and repeated-use restoration seams |
| Observer-time sequence → ordinary generator | Keep real two-frame export and resume, beyond mocked delegation |
| Fixed-sky reference/reuse → ordinary generator; complete-render baseline → observer-time pipeline | Keep both delegation/observer-lifetime routes and baseline planning; these delegation tests mock the generator, so they do not establish new full fixed-scene numerical equivalence |
| Atlas CLI → `wenu_chart atlas-sheet` → native `AtlasSheetChartRequest` branch | Preserves exact sheet geometry/paper and observer-free native sky; enters common lifecycle without ordinary configuration. Native lifetime/dispatch changes select real serial/spawn and cold/saved output equivalence |

Unchanged satellite crossing/acceleration/radiometry physics, catalogue curation
and wheel/sdist packaging, native snapshot persistence and kernel internals do
not belong to a compatible request-lifecycle gate. Their science and installed
product tests remain in their own owners and in release integration. A changed
resource, algorithm or interface brings the corresponding owner back into scope.
`open_chart_request_scope` owns entry, minor-body registration/resolver binding,
configuration journaling and close/failure rollback for all three routes. Its
returned `ChartRequestBuild` exposes `remember_attribute` to configuration owners;
those owners do not access the private journal. Native sheets omit ordinary
configuration and remain observer-free. Atlas serial/API/worker execution uses
an injected chart command or `wenu_chart atlas-sheet` by default; the direct
generator fallback is removed. Numerical realization, projection and native
sheet geometry are not unified into one model by this lifecycle change.
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
legacy pytest discovery remains unchanged. That SDK kit does not itself change
time/frame science; the current native adapter separately documents source
epoch and lookup semantics in the coordinate guide.

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
