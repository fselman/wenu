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
That SDK-only slice left the production pin unchanged; the subsequent galaxy
adapter now pins its accepted source and supplies its own installation gate.

## Catalogue lookup SDK prerequisite

The dev8 prerequisite is accepted at main `9dd1909f`: 204 Mac SDK tests,
36 documentation tests, eight tooling tests and 69 consumer tests plus nine
subtests. It also passed the same 204 tests against an isolated built wheel
without Wenu/scientific dependencies. The portable kit covers mixed/unknown
lookup epochs, source provenance, request/evidence refusals, lifecycle and
lookup-vector invariance; its external consumer uses only its own synthetic
provider. These are contract checks, not captured astronomical accuracy oracles.

For a future SDK contract/implementation change, run its independent source and
isolated-wheel gates plus affected existing consumers. A compatible provider
composition uses accepted SDK evidence and its own owner/seam tests instead.
`kernel-catalogue-lookup-compatibility` remains the reviewed stellar/galaxy
selection and is extended by the cluster routing gate below. Current provider
routing/dependency acceptance is described there; it must not be inferred from
an earlier SDK-only gate's exclusions.

## Open-cluster kernel routing

`kernel-open-cluster-routes` extends the accepted stellar/galaxy compatibility
selection because the shared direction-table adapter now supports aligned row
epochs. It selects the existing cluster source/epoch/selection/cache/symbol owner
seams and public position contract, plus new returned-vector/refusal/warm-cache,
source identity, qualified/unknown epoch, mask/units and shipped conformance
checks. The actual native page is compared pixel-for-pixel against the accepted
raw-centre route for both cold and saved skies. Saved source identity, existing
source-free process, older snapshot variants and public atlas-sheet consumption
remain exercised. No snapshot schema, atlas lifecycle or render algorithm changes,
so the long serial/spawn page batch is not repeated for this adapter.

The root pin moves to accepted SDK dev8 at main `9dd1909f`. The installed
wheel/sdist/editable consumer test therefore verifies actual cluster lookup through
a separately installed SDK wheel, keeping its stellar and galaxy assertions.
Run documentation and tooling separately. SDK implementation/conformance are
unchanged from their 204-test Mac acceptance, so do not rerun that independent
suite. Acquisition/curation, unrelated providers, observer/projection numerical
oracles and the full production suite are excluded. Install the local accepted
SDK package before Mac verification; an old installed dev7 cannot execute the new
capability merely because Wenu source changed.

## Selected-cluster astrometry ingestion

`open-cluster-astrometry-ingestion` runs the existing Hunt photometry/packaged-data
seams, five focused source-ingestion/attachment tests and one archive packaging
check. Captured source records verify PM convention, units, actual values, missing
RV and the distinction between standard errors and dispersion. Constructed faults
exercise changed digests/ReadMe/unit/meaning, duplicate IDs, absent clusters,
wrong names/centres/source assignments, a changed selected-catalogue byte stream
and corrupt product bytes. All 513 IDs/order and all 132 original columns, masks,
units, descriptions and metadata must remain identical after explicit enrichment;
the existing immutable runtime record must mirror recovered provenance/units.
Four Dias-only solutions remain unadopted. A fresh output directory and refusal
of existing versions protect publication. Ingestion tests forbid network access.

The new archive-only test checks exact companion/specification/receipt bytes in
wheel and sdist using the existing packaging owner. No runtime module, dependency,
active curated bundle, SDK, snapshot, coordinate/projection/render algorithm or
request lifetime changes. Accepted installed-consumer and atlas pixel evidence
therefore remains valid; do not rerun those broad gates, the independent SDK or
the full production suite. Run documentation and stdlib tooling separately.
Source acquisition is an explicit one-file operation outside tests and charts.

## Cluster source qualification contract

`cluster-astrometry-qualification` checks the new source-evidence record against
actual accepted catalogue/companion byte hashes and all four retained Dias rows,
plus the existing explicit-enrichment and unqualified-epoch contracts. This is
evidence integrity and unchanged admission, not a numerical propagation oracle.
No source resource, active selector, implementation, dependency or SDK changes.
The record and proposed model contract live under developer documentation.
Run documentation and stdlib gate-tooling checks separately. Reuse the accepted
archive/installation and chart evidence; no packaging, numerical, atlas, full
production or independent SDK repeat. The nominal provider gate below supplies independent numerical/refusal and
isolation checks. Add certificate proofs and actual affected consumer seams when
those features are implemented; neither nominal motion nor source qualification
alone establishes ancient-date accuracy.

## Nominal cluster provider gate

`cluster-motion-provider` selects the new enduring motion owner, existing
source-qualification/enrichment seams and one targeted archive/installed-wheel
check. Scalar-trig initial PV data plus ERFA PV updates form an independent
numerical oracle, including both poles, RA wrap, forward/backward and long nominal
baselines. An analytic perspective case checks RV sign/effect. Frozen-time fault
injection must fail this oracle. These checks validate the mathematical model,
not physical accuracy in antiquity. Other cases cover source metadata/units,
canonical half-day/subday times, unavailable inputs, singular-domain refusal,
immutable copies, wrong bindings, unsupported accuracy/time/coverage refusal, lifecycle
and the SDK's eight portable provider-conformance checks. Cluster epoch queries
in a shared session must leave stellar and static galaxy evaluation counts at zero.

The existing archive scaffold is reused without removing its previous assertions.
The new case checks exact module/admission bytes in wheel and sdist and performs
an isolated installed-wheel kernel query against the explicit accepted SDK path;
default fixture lookup remains unchanged. No root dependency/build/SDK changes.
Run documentation and stdlib tooling separately. Do not repeat the full SDK,
unrelated family, broad installation, atlas pixel/serial-spawn or production gates:
no default consumer, observer/projection/render algorithm or snapshot schema
changes. Those seams become required when the new physical model is adopted.

## Cluster motion reuse gate

`cluster-motion-reuse` selects the enduring `test_cluster_state.py` owner and
the targeted isolated installed-wheel consumer. It retains ERFA/analytic motion
oracles and adds independent 80-digit Decimal direction checks over certified
intervals, including both endpoints, poles, perspective approach and zero
velocity. The analytical convex-cone proof lives in the API reference; finite
sampling alone is not accepted as a certificate proof. A frozen elapsed-time
fault must be rejected by the verified numerical floor.

The changed portable conformance factory supplies an actual bounded-reuse query
and certification activity hooks for the advertised capability; all eight SDK
checks run through that factory. Owner tests count exact object/time evaluations:
inside-interval reuse does no full evaluation, a fast object alone recomputes
outside its interval, stricter requests reject old looser certificates, and
repeated reuse retains the original anchor. Foreign/reused/corrupted anchors,
whole-interval and out-of-domain requests fail closed. Reproducible-mode results
remain independent of request order. The existing prohibited-family spies now
exercise bounded queries as well; no unrelated stellar/galaxy evaluation occurs.

The existing packaging case additionally executes actual certificate reuse in
an isolated installed Wenu wheel against the accepted unchanged SDK. Run it once
through this gate, not also through the parent provider gate. Source ingestion,
resources, dependencies/build, SDK implementation, chart/snapshot routes,
observer/projection/rendering and atlas behavior are unchanged; retain their
accepted receipts. No full SDK, broad installation, unrelated-family or full
production rerun. Run documentation and tooling separately.

## Shared astrometric Cartesian output

`astrometric-cartesian` selects the generic and cluster state owners, unchanged
native consumer seams and the extended installed-wheel case. The shared core
and explicit source adapter change; SDK/source resources/dependencies/observer,
projection/rendering and snapshot schemas do not. Reuse accepted SDK evidence;
no full production or SDK repeat. Direction default identities and independent
ERFA/analytic/Decimal/reuse tests remain selected, not replaced.

New faults protected are normalized-away distance, velocity/RV sign or SI-unit
loss, wrong split-JD/source epochs, cross-representation cache/evaluation, hidden
accuracy/reuse admission and unavailable mixed selections. Independent scalar
trigonometry plus ERFA PV updates check Cartesian output at poles, wrap and
past/future nominal times. An 80-digit Decimal oracle checks exact-input PV
arithmetic on constructed four-family records. Numerical agreement does not
certify physical/Cartesian absolute accuracy. A separate Cartesian portable
conformance factory and isolated SDK-only mixed-family execution supplement
those oracles. Installed wheel/sdist checks retain the direction/default checks
and execute real Cartesian kernel queries as well. No old assertion is removed.
The new tests stay in existing enduring owners. Run documentation and stdlib
tooling separately; do not also run the parent factoring/native gates.

## Shared astrometric engine factoring

`astrometric-core-factoring` runs the new enduring generic-engine owner, the
existing complete cluster owner, the targeted installed-wheel test and native
consumer seams. The source adapter keeps source/unit/centre qualification;
propagation/domain/certification move to one stdlib/SDK engine. The existing
numerical-corruption test retains its node/assertions and now injects elapsed-time
failure into the actual moved owner. No old oracle or test is removed.

New faults protected are object-type dispatch, dependency on concrete catalogues,
caller-owned SI buffers, inconsistent SDK bindings/error budgets and bypass of
shared domain validation. Synthetic star/cluster/PN/SNR records share one actual
provider and run eight portable conformance checks. A -I -S subprocess loads only
the engine and accepted SDK, evaluates a real query and forbids Wenu/Astropy/NumPy
imports. This is module isolation, not whole-product/package independence.
Existing ERFA/analytic/Decimal propagation and interval proofs, cluster conformance,
selected native vectors/refusals and real cold/saved/pixel/fresh-process consumers
remain selected. The installed-wheel test retains its assertions and checks both
modules in archives and actual execution. Run documentation and stdlib tooling
separately. No SDK/source-resource/dependency/observer/projection/renderer or
snapshot-schema change; do not rerun full SDK or production suites.

## Barycentric convention subset

`astrometric-conventions` selects the existing generic astrometric owner and
extends the existing isolated installed-wheel cluster consumer. New protected
faults are time relabelling, wrong defining constants/sign, collapsed split JD,
position scaling omission, incorrect velocity scaling, altered conversion
receipts, mismatched source/model/resource and incomplete/reordered batches.
The closest existing tests are the Cartesian exact-input Decimal, binding/refusal,
actual SDK batch and isolated-module cases in `test_astrometric_state.py`.

Independent 90-digit Decimal time references and ERFA conversions cover both
directions, past/future dates and half-day boundaries. An injected zero-L_B
fault demonstrably fails the same Decimal oracle. Position scaling in both
directions has independent Decimal references and a linear-trajectory commutation
check. Synthetic four-family kernel queries and SDK-only isolated execution
retain evidence/order and refuse warm faults. The existing wheel/sdist owner
checks the new module and converts actual installed cluster Cartesian output.
No existing assertions/oracles are removed.

Run documentation and tooling separately. Provider propagation, direction reuse,
native charts/snapshots, observer/projection/renderer and SDK implementation are
unchanged; reuse their accepted receipts, including the 89-case Cartesian Mac
gate. Do not repeat the parent Cartesian/native gate, independent SDK or full
production suite. No backend/ephemeris/EOP/UTC/TT adapter, observer parallax,
physical accuracy or supported observation domain is admitted by this subset.

## Offline reception input gate

`astrometric-reception` selects five additive cases in the existing observer
resource owner and the extended installed-wheel cluster consumer. The closest
existing tests protect observer resource identity/immutability; the existing
Cartesian installed query protects the new reception-to-propagation handoff.
New protected faults are UTC leap-second collapse, wrong TT offset, hidden
scale relabelling, global leap/resource drift, predicted/extrapolated EOP use,
wrong site/units, stale backend identity and accidental Observer/network access.
Analytic leap/TT checks are independent of Time.tt. A published ERFA APCO13
observer PV reference uses explicitly synthetic EOP inputs and accounts for
that reference's TT ephemeris argument. These are numerical composition checks,
not independent physical ephemeris or target apparent-place guarantees.

A deliberate zero-DTDB fault must change the accepted event. Tests retain
unknown total error channels, exact TDB/TCB receipts, file-copy immutability,
site effects and warm refusal/recovery. The installed consumer preserves all
previous source/direction/reuse/Cartesian/convention assertions and queries a
real cluster at the actual prepared TCB event. New module bytes ship in wheel
and sdist. Run documentation and tooling separately. The legacy Observer,
CoordinateService, provider core, SDK, default charts/snapshots and all target
apparent/projection/render code remain unchanged; reuse their accepted gates.
Do not repeat the prior parent/convention/native gates, full SDK or production
suite. Target parallax/correction/cache/public-consumer gates remain pending.

## Finite observer gate

`astrometric-observer` extends `astrometric-reception` without duplicating its
installed case. The existing observer-resource owner now adds finite observer
science/refusal cases. Its closest tests are the explicit reception, published
ERFA observer reference and immutable resource/binding cases. Protected faults
are double observer subtraction, lost distance, wrong TCB/TDB scaling, second
space motion, double annual/diurnal aberration, altered context/model/time,
partial state publication and invented apparent/range precision.

Independent analytic parallax/range cases span multiple distances and the
infinite-distance limit. An independent Lorentz boost checks aberration within
the explicitly omitted small solar-potential difference; a separate Astropy
finite-distance ICRS-to-AltAz route checks the full composition within the known
final-CIP/theoretical-CIP difference. Neither is claimed as a physical ephemeris
accuracy bound. Counts require one LD, AB and ATIOQ call per selected object,
full recomputation on exact repeats and no `pmpx`/`atciq` call. Deliberate double
translation and double aberration demonstrably fail the same numerical oracles.
Actual mixed-family SDK batches preserve source epochs/order/unknown evidence;
singular or corrupted requests fail atomically and valid requests recover.
The existing wheel/sdist case retains all previous assertions and realizes an
actual installed cluster batch at the prepared reception event.

Reception model version 2 adds a frozen numeric ERFA handoff, Sun position,
retained UTC label and full context digest; it does not persist these in old
snapshots or change numerical reception input generation. Parent reception
checks therefore run once through this gate. Run documentation and tooling
separately. Provider/SDK/source-resource/dependency/build, native/default chart,
projection/renderer and saved-sky implementations are unchanged. Reuse their
accepted evidence; no parent duplicates, full SDK or production run. Observed
chart/saved adoption has its separate consumer gate below; independently bounded
physical errors remain pending.

## Cluster observer contract and implementation gates

The contract-only milestone adds the scientific ownership/admission contract,
as-is inventory and future gate matrix. Run `documentation`, stdlib tooling and
`cluster-observer-contract` once. The latter retains the existing real
`test_cluster_motion_consumer_refuses_missing_inputs_binding_domain_and_observation`
case from the native consumer owner: motion without a valid explicit native or
reception context still refuses.
It is current refusal evidence, not an observer numerical test. No production
code, provider/SDK, resources, dependency, serialization, build or collection
changes; do not repeat provider numerical/installation, full SDK, atlas or full
production suites for this documentation milestone.

Future runtime gates are separate bounded changes, selected from their actual
diffs. They must retain the following independent faults/oracles; writing this
matrix does not create tests or mark them passed.

| Future slice | Required acceptance evidence |
|---|---|
| Cartesian cluster admission/evaluation | Actual SDK-returned SI PV, velocity availability and separate model/reference; independent scalar-trig/analytic or ERFA PV oracle; multiple epochs/poles/wrap; unavailable mixed batches, source/time/coverage refusal; immutability, lifecycle, ordered duplicates and source identity |
| Cartesian provider conformance/installation | Shipped Cartesian conformance case with full evaluation and explicit unsupported reuse/accuracy; isolated installed Wenu/SDK consumption and no unrelated provider evaluation; repeat SDK core only if its contracts/code change |
| Time and common-coordinate admission | Explicit conversion receipts, independent scale references and boundaries, equivalent reception events, wrong-scale/model/resource refusal; qualified spatial/time convention and TCB/TDB scaling where needed, not a change of labels |
| Finite-distance observer realization | Independent analytic observer-translation/parallax cases at different ranges; infinite-distance limit; separately admitted apparent-place oracle, resource-bound time/EOP/ephemeris evidence and vacuum horizon conversion |
| Correction ownership | Faults that double-apply proper motion, observer subtraction, aberration or an extra stellar light-time delay must fail; same-backend self-comparison alone is insufficient |
| Numerical versus physical error | Retain all unknown source/model channels; a native angular certificate must be refused as a translated apparent bound; no invented zero range/time/observer uncertainty |
| Cache and lifecycle | Count full state/observer evaluations; exact-repeat behavior; change site/time/EOP/ephemeris/model/policy separately, including equal RA/Dec but changed distance; warm failures and partial batches refuse; unrelated provider calls remain zero |
| Canonical chart/saved consumption | Real cold/saved/fresh-process geometry and observer-context equivalence, actual public chart output and query-failure tests; original source rows/masks/digests/default lookup unchanged; no persisted-state reinterpretation |

Use the existing cluster, coordinate-service, observation/resource and reusable-sky
test owners after inspecting their closest tests; add a new owner only for a real
enduring service boundary. Freeze constructed fixtures as synthetic; capture a
real backend oracle only with exact bytes/version/provenance and actual execution.
An IERS warning or network-disabled execution alone does not prove coverage.
No observer model is accepted until its specific resource/backend/numerical
criteria are recorded and executed; physical cluster accuracy remains separate.

## Galaxy routing and shared catalogue adapter

`kernel-galaxy-routes` selects inherited nonstellar owner/geometry seams, the
existing stellar provider/Stars owners, public position contracts, cold/saved and
source-free consumers, actual galaxy/stellar page pixel comparisons, saved-sky
CLI and installed wheel/sdist consumption. It checks returned-vector influence,
refusal without fallback for every migrated route, optional source epochs,
explicit legacy origin, source-table immutability and the shipped eight-case
provider conformance kit. The isolated SDK is accepted unchanged from PR #253;
its full gate is not repeated for this provider composition. Run documentation
and tooling separately, with no parent-gate duplicates or full production run.
The production pin changes to accepted dev7, so installation evidence is required.
For the installation-only followup, `galaxy-installation-retry` reruns the failed
wheel/sdist/editable consumer case only. The Mac's other 183 tests and nine
subtests at `04ad8e1e` remain valid. The isolated child disables ambient `.pth`
processing; therefore the fixture builds and installs a separate local SDK wheel
and supplies that target explicitly. Both Wenu and SDK ambient poison packages
must remain unused. This verifies actual installed stellar and static galaxy
queries without depending on the host's editable SDK. No production change or
parent/SDK/scientific repeat is required.
No catalogue bytes, snapshot schema, observer/projection mathematics, render
algorithm or atlas lifetime changes. Single-outline geometry uses its array
directly instead of concatenating a one-member list.

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

## Native cluster motion consumer gate

`cluster-motion-native-consumers` selects the changed open-cluster public/native
seams, layer-realization and request-context owners, saved-source cold/restored
geometry, actual PNG equality and fresh-process offline consumption. Existing
default cluster pixel and legacy/fixed-row snapshot tests remain selected. New
faults are source/digest mismatch, unavailable row fallback, ignored returned
vectors, wrong requested epoch/scale, lost order/duplicates/provenance and shared
model installation. The former static-only context assertion now positively
admits explicit native evaluation epochs; all observation/frame/equinox refusals
remain. The native geometry guard additionally refuses mismatched returned time.

The provider model, numerical/reuse implementation, source bytes, SDK, dependency,
snapshot serialization and observer mathematics are unchanged. Reuse their
accepted numerical/conformance/installation evidence; do not rerun their owner
gates, broad packaging, full SDK or production suites. No CLI/atlas worker dispatch
or canvas changes, so serial/spawn atlas batches are excluded. The existing default
native-page pixel test protects unchanged atlas output. The shared context changes
justify the complete layer/request-context tests and static-neighbour checks.
No historical tests are removed or moved. Run documentation and tooling separately.
This native gate does not enable observer-dependent motion or CLI selection;
those now have their separate observed-consumer and ordinary-selection gates.

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


## Explicit observed cluster Python consumer gate

`astrometric-observer-consumers` covers the changed cluster adapter, shared layer
context and pre-projection admission guard. The closest native motion, layer and
request realization tests remain selected. New owner tests protect Cartesian
query bypass, wrong units, lost source/reception identities, changed site/time,
tampered receipts, unavailable input and query refusal after a successful call.
Changed returned Cartesian positions must change geometry and range; a fake
unmigrated/misbound layer must fail before projection/rendering.

Cold and restored source skies must produce identical degree geometry and
raster pixels through `CelestialSphere.draw_chart`, plus actual SVG files. A
fresh process repeats public drawing with source reload and network blocked.
The existing installed-wheel cluster test additionally calls this layer API
with real selected source bytes and an explicit independently prepared context;
its packaging fixture's one-row default remains a lookup catalogue.

Run tooling, `documentation` and `astrometric-observer-consumers`. Reuse accepted
source propagation/convention/observer numerical oracles and installation recipe;
no SDK, science algorithm, resource bytes, dependencies/build, snapshot schema,
projection/renderer, atlas dispatch or CLI/TOML change. No full SDK/production
repeat is required. Ordinary horizontal CLI/configuration selection now has its
separate gate below; total physical accuracy remains pending.


## Ordinary cluster model selection gate

`cluster-astrometry-selection` extends the accepted observed-consumer gate and
selects the changed configuration schema/translation, CLI/view/request/export,
spatial-selection and sequence-identity seams. New tests live in the existing
packaged configuration, request-realization and installed-command owners.

Real TOML and CLI model/ID overrides must reach one full Cartesian query and
actual SVG output through the ordinary mixed-layer chart pipeline. A lookup
pre-cull/legacy observation spy must remain unused for the explicit model.
CLI lookup override must perform no Cartesian query. Existing appearance
controls remain independent; the real wide-field test explicitly enables
content via its existing adaptive policy. Request/resource/site/time mismatch,
query refusal, default restoration and immutable source metadata remain checked.

Default lookup provenance/sequence identity omit the added model field, while
active admissions are retained. Existing sequence/manifest, configuration overlay,
shared export/lifecycle, view/drawing and public consumer tests protect this
request-contract addition. Installed wheel/sdist bytes now also verify changed
packaged defaults and request/CLI owners; installed parsing and the accepted
public cluster observer seam run without ambient Wenu imports.

No provider/observer numerical algorithm, SDK, source resources, dependency/build,
snapshot schema, projection/renderer or atlas dispatch changes. Reuse accepted
numerical/conformance receipts; do not repeat unrelated physics or full production.

## Native constellation-label routing gate

K3.07 uses `python tools/run_test_gate.py native-label-routing --run` with plugin
autoload disabled. This selects the label, constellation geometry, public position
and stellar owners plus cold/saved native anchor and PNG comparison (including
PDF export) and restored fresh-process execution. Fault injection changes the
real kernel return and verifies the anchor moves; kernel failure cannot fall back
to catalogue angles. Public-only fixtures forbid private table reads. Empty and
missing-coordinate inputs, faint unfiltered source stars and existing observed
label behavior remain covered. No SDK/provider numerical, installation, source
resource, dependency, snapshot schema, projection or renderer changes require
repeating their accepted lower-level gates. Run documentation and tooling checks
alongside this gate. Local Python 3.12 evidence: 95 focused cases passed in
37.96 s and 8 tooling cases passed. Documentation: 33 executable cases passed;
three archive-dependent checks require the complete Mac checkout. Remote-tree
links/anchors and all 73 preserved archive blob hashes were independently
verified. Complete Mac acceptance remains pending.

## Observed stellar routing gate

K3.08 uses `python tools/run_test_gate.py observed-stellar-routing --run` with
plugin autoload disabled. Select the stellar, label, constellation-geometry,
public-position and observed-cache owners, existing layer/request realization
seams and native cold/saved page regression. New real-kernel fault injection
changes source directions after observer-cache fill and verifies changed stars
and endpoints, then refuses direct Alt/Az/chart/figure calls without fallback.
Public-only observed label tests forbid source-table access. An explicitly
synthetic offline Earth PV fixture executes actual Skyfield and Astropy chains,
compares against direct pre-migration chains, and compares actual chart geometry
and PNG buffers; it is compatibility evidence, not ephemeris accuracy evidence.
Existing source-only/native snapshot transport remains unchanged. Retain accepted
lower-level SDK conformance/installation evidence; no full SDK/production repeat.
Local Python 3.12 evidence: 124 focused cases passed in 35.91 s and eight
tooling cases passed. Documentation: 33 cases passed; three archive-dependent
checks require the complete Mac checkout. Active links/anchors and all 73
preserved archive hashes were independently verified against the remote Git
tree. Run the complete documentation and focused gates on the Mac; acceptance
remains pending.

## Catalogue coordinate-default gate

K3.09 uses `python tools/run_test_gate.py catalogue-coordinate-defaults --run`
with plugin autoload disabled. It extends the accepted nonstellar-admission gate
and adds coordinate vocabulary/service, constructed point/grid/boundary/regional
callers and public position contracts. New tests reject an invented default epoch,
preserve explicit source epochs, compare identical ICRS-to-B1875 directions under
unknown versus explicit epoch metadata, and verify actual packaged Messier,
Caldwell, galaxy, globular, PN and SNR source gaps remain null and strictly refused.
Existing snapshot v5 and legacy admission/corruption, known/unknown source epoch,
source-free restoration and public saved-sky CLI checks remain selected. No new
provider physics, source bytes, SDK or installation boundary changes justify a
full SDK/production repeat. Run documentation and eight tooling checks alongside
this focused gate. Local Python 3.12 evidence: 248 cases passed in 83.83 s
and eight tooling cases passed. Documentation: 33 cases passed; three checks
require archive files absent from the execution copy. Active links/anchors and
all 73 preserved archive hashes were verified against the remote Git tree.
M5 source qualification remains open; complete Mac acceptance is pending.

## Approved catalogue-lookup admission and PM policy

The K3.09 lookup-admission slice reuses `catalogue-coordinate-defaults`; its
selection already contains the changed nonstellar owner and accepted family,
coordinate and snapshot seams. Added cases exercise explicit lookup acceptance
for all six real catalogue selections without altering source data/default
geometry, strict physical refusal after lookup, absent identity/edition/byte
binding/provenance/units, and a qualified angular reference without a motion
epoch. Input-declaration validation remains unchanged. Run the documentation
and eight tooling checks too. No full SDK/provider/production repeat is needed.
The PM-only policy clarification is documentation for AX.13; no new propagation
algorithm or interval accuracy claim is tested or implemented in this slice.

Local evidence for the approved lookup-admission slice: 260 focused cases passed
in 85.88 s and eight tooling cases passed. Documentation: 33 cases passed; three
checks need archive files absent from the execution copy. Active links/anchors
and 73 preserved archive hashes were independently verified against GitHub.
Complete Mac acceptance remains pending.

## Galaxy routing closure gate

K3.10 uses `python tools/run_test_gate.py galaxy-routing-closure --run` with
plugin autoload disabled. Select galaxy and shared nonstellar/cache/public-position
owners, restored known/unknown/static epoch and source-free snapshot seams,
actual legacy/cold/saved galaxy atlas pixels (PNG plus PDF/SVG export), and
inherited PN/SNR/globular cache regressions. New real-kernel injections change
centres after observed cache fill, check independent expected centre/ellipse
positions, and verify no second outline query. All public/native/label/observed
paths propagate lookup admission or kernel refusal after a warm result. The real
packaged source exercises lookup validation without upgrading physical gaps.
The optional pre-cache state hook defaults to the accepted legacy route for
other families; no other-family migration is claimed. Reuse unchanged SDK science,
conformance/installation and atlas lifetime evidence; no full SDK/production
repeat. Run documentation and eight tooling checks alongside this gate. Mac
acceptance remains pending.

Local Python 3.12 evidence: 155 focused cases passed in 51.97 s, including
restored-source warm refusal and exact legacy/cold/saved galaxy PNG equality;
eight tooling cases passed. Documentation: 33 cases passed; three archive checks
require files absent from the execution copy. Active links/anchors and all 73
preserved archive hashes were independently verified against the remote Git
tree. Complete documentation and focused Mac acceptance remain pending.

## Generic nonstellar routing gate

K3.12 uses `python tools/run_test_gate.py nonstellar-routing --run` with plugin
autoload disabled. It extends galaxy-routing-closure because source-bound provider
construction/vector decoding moved to the common owner without changing the
galaxy model or dedicated other-family defaults. Generic Messier/Caldwell tests
inject changed real SDK results into public/native/label/observed consumers and
refuse lookup or kernel evaluation after cache fill. The portable provider suite
checks generic lookup protocol/lifetime. Named target/object-centre and binocular
seams verify returned vectors/refusal, retaining explicit-coordinate construction.
Selection and public view owners remain selected. Real Messier and Caldwell
snapshots compare cold/restored labels/outlines and legacy/cold/saved PNG pixels
with PDF/SVG exports, then refuse restored warm routes. Existing source-free
process and unknown/known epoch lineage tests remain selected. Run documentation
and eight tooling checks too. No changed SDK, source resource, dependency/build,
schema, numerical science or renderer warrants repeating full SDK/production
or installed-wheel gates; accepted lower-level evidence is retained.

Local Python 3.12 evidence: 211 focused cases passed in 68.14 s and eight tooling
cases passed. Messier/Caldwell legacy/cold/saved PNG pixels were identical, with
PDF/SVG exports and restored warm refusal. Documentation: 33 passed; three checks
need archive files absent from this execution copy. Active links/anchors and all
73 preserved archive hashes were verified against the remote Git tree. Complete
Mac documentation and nonstellar-routing acceptance remain pending.

## Globular routing gate

K3.13 uses `python tools/run_test_gate.py globular-routing --run` with plugin
autoload disabled. Changed globular owner tests inject real kernel vectors after
cache warming and check every public/native/label/observed consumer against
independent SkyCoord/ellipse results. Real packaged lookup/refusal tests retain
source gaps, strict physical refusal and globular provider identity. Inherited
nonstellar, public position and observation-cache owners remain selected. Actual
globular atlas output compares legacy/cold/restored PNG pixels with PDF/SVG
exports and native labels/outlines; restored warm routes must propagate refusal.
Existing all-family row/mask/unit/subset snapshot and source-free fresh-process
contracts remain selected. Half-light diameter/common names/structural metadata
retain their current tests. Reuse accepted shared provider conformance, numerical
science, installation and atlas lifetime evidence; no SDK, source resource, build,
schema, observation or renderer change warrants full SDK/production repetition.
Run documentation and eight tooling cases alongside this gate.

Local Python 3.12 evidence: 125 focused cases passed in 34.18 s and eight tooling
cases passed. A real globular atlas page retained identical legacy/cold/restored
PNG pixels with PDF/SVG exports; restored warm refusal and source-free process
checks passed. Documentation: 33 passed; three archive-dependent checks need
files absent from the execution copy. Active links/anchors and all 73 preserved
archive blob hashes were independently verified against GitHub. Complete Mac
documentation and globular-routing acceptance remain pending.

## Planetary-nebula routing gate

K3.14 uses `python tools/run_test_gate.py planetary-nebula-routing --run` with
plugin autoload disabled. The full PN owner includes retained true/probable
ingestion, curated selection/export contracts and fixed-symbol metadata, plus
real kernel changed-vector/identity tests and warm admission/kernel refusal. A
synthetic two-centre fault verifies identity-aligned native points, observed
request order/duplicates, minimum-size filtering, unchanged source metadata and
empty observed selections without a query. Inherited nonstellar/position/cache
owners remain selected. Real cold/restored PN symbols and actual atlas
legacy/cold/restored PNG pixels with PDF/SVG exports verify compatibility; restored
warm refusal, row/mask/unit transport and source-free fresh-process resume remain
selected. Reuse accepted shared provider science/conformance/installation and
atlas lifetime evidence; no SDK, source resource, dependency/build, schema,
observer/projection/renderer or SNR-route change warrants a full SDK/production
repeat. Run documentation and eight tooling checks alongside this gate.

Local Python 3.12 evidence: 129 focused cases passed in 37.76 s and eight tooling
cases passed. PN legacy/cold/restored PNG pixels were identical with PDF/SVG
exports; restored warm refusal and source-free process checks passed. An additional
full true/probable catalogue public-position check returned all 1,143 objects.
Documentation: 33 passed; three archive checks need files absent from the execution
copy. Active links/anchors and all 73 preserved archive blob hashes were verified
against GitHub. Complete Mac documentation and planetary-nebula-routing acceptance
remain pending.
