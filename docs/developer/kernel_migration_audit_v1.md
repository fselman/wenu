# Kernel migration: as-is functionality and test audit

## K4b.07 exact-epoch persistence candidate, 2026-10-28

**Base and selection:** #357 merged at `7407ea1b1a57a27b8175bb6dfaa76ed1b46264d6`;
Fernando confirmed clean synchronized Mac main, local/remote task-branch cleanup
and then said “proceed” after the proposed first exact-epoch scope. The selected
scope was committed before runtime implementation at
`12a549642d83e1a551445159e1fc2542152c0054` on `feat/stellar-epoch-persistence`.

The distinct derived-product lifecycle is owned by `stellar_epoch.py`, with an
explicit offline maintenance command. Existing live realization and persistence
now share the stellar owner's ordered availability selection; failures never
trigger query-time source fallback. Preparation uses real SDK direction/PV
queries and preserves the original source manifest/products and all model
coefficients. Reader validation/exact lookup constructs no provider/session and
does not propagate the saved event. No source/numerical/core/observer or chart
semantics, dependencies, installed entry points or collection settings change.

Six new owner test functions pass direct local execution using the existing
synthetic source fixture and actual stellar/provider/kernel modules, including
fresh-process and CLI subprocesses. Sixteen corruption and five failure/race
variants detect invalid data and unsafe publication. The live-realization
selection/reuse check also passes. An initial refusal-test exception mismatch
was corrected and the same tests rerun; failed logs remain retained.
No pytest or complete Wenu astronomy stack is installed here. Full focused Mac
and documentation gates and retained real-source preparation/reload size/time/
scientific parity remain pending; no actual catalogue run or parent K4b.07
acceptance is claimed. The coordinate guide remains current.

See the [implemented candidate API](implementation_reference.md#exact-epoch-stellar-catalogues)
and [focused gate](testing_policy.md#exact-epoch-stellar-persistence-gate).
Nearby-event policy, consumer adoption, companions and observer work remain
outside this candidate.

## K4b.06 observer-free consumer reconciliation, 2026-10-28

**Selected IDs:** K4b.06.R2/R3 assessment and R4 reconciliation. GitHub main is
`b295b88bc42e40fdbade44c0d04935188a99b579`, tree
`a2f3bcecb258a6c88cfb9a2a79e37b02d55d5e3f`. Fernando confirmed clean synchronized
Mac main and #356 branch cleanup; the subsequent guarded network diagnostic
also passed exact-base/clean/upstream checks. #356's corrected completion scope
passed all 36 Mac documentation cases in 4.62 s at
`cea277ec945daba3784499ed369d6a4c11abb4ae`, retained in
`~/Software/build/wenu/test/k4b06-completion-docs-v1-s50qa1l0`.

Fernando then asked “Can we postpone the bright-star comparison?” and selected
the proposed observer-free review with “proceed”. The roadmap now records R1
as deferred outside the current K4b.06 closure gate, not completed or cancelled.
This review makes no runtime, source, resource, dependency, default or collection
change.

Fernando accepted the bounded K4b.06 result on 2026-10-28 after all 36 Mac
documentation cases passed in 7.35 s at
`829c472530cc1a8d1e6eb26a2bdfa0f24a4401e9`. Retained user-reported evidence:
`~/Software/build/wenu/test/k4b06-consumer-docs-v1-cwm51a_g`.
R2/R3 and R4 are accepted, and K4b.06 is closed for the existing-source,
observer-free atlas integration. R1 comparison and observer-dependent product
adoption remain explicitly deferred; neither is claimed completed. This receipt
adds no new runtime acceptance; PR #357 merge/cleanup remains pending.


### Consumer and upstream astrometry boundary

Fernando clarified on acceptance that proper motion/parallax/observer machinery
is orthogonal to chart/atlas creation. Stars and shared services supply realized
positions with coordinate/event/status/provenance; charts consume those results
for framing, projection, labels, rendering and export. Future observer work
completes upstream source/observer realization and consumer composition, not a
chart-owned astrometric algorithm. Existing modern stars and measured source
parallaxes remain protected. Source distance/parallax, observer displacement,
finite model domains and missing-input policies require their own explicit
admissions; no changed scientific policy or full observer implementation is
selected by this clarification. The coordinate guide remains current.

### Public consumer disposition

The following entry points were inspected at the pinned base. “Covered” means
the exact accepted atlas composition, not a blanket acceptance of every caller
of the same renderer. No new native request family is needed for this review.

| Public path / existing owner | Preparation, framing and export finding | K4b.06 disposition |
|---|---|---|
| `AtlasSheetChartRequest`, `render_atlas_sheet`, `generate_chart_request` atlas dispatch; `wenu_chart atlas-sheet` | Requires an observer-free prepared sky, explicit optional stellar motion and optional mean-axis input; canonical request owner supplies scope, staging/no-clobber and cleanup; sheet owner supplies composition/report/export | Covered by #346/#348/#354 for native and dated-axis single sheets, Python and installed CLI; reuse receipts |
| `AtlasSheetChart.render`: ordinary rectangular sheet | Validates native realization, matching orientation and absent observer, then calls `RegionalChart.render` with atlas-owned projection/viewport/context | The existing regional rendering seam is already exercised by accepted ordinary atlas sheets. This is not ordinary regional request/auto-framing adoption |
| `AtlasSheetChart.render`: hemisphere sheet | Constructs `PolarPlanisphereChart` with atlas geometry/label policy and passes the native context; native polar render bypasses observer conversion | Covered by #354's polar sheet 1, both mean axes and serial/spawn cases. This does not accept a physical calendar/horizon/pouch product at an ancient epoch |
| `wenu_create_atlas`, `charts/atlas_publication.py` and workers | Same sheet service; process-local bound stellar view and captured integrity-bound inputs; counts use the same motion identity, outputs publish on success | Covered by #350/#354. Worker transport is not a persisted evaluated epoch catalogue |
| Atlas design and `wenu_plot_atlas` / `charts/atlas_index.py` | Design is geometry; standalone index can draw native catalogue layers without an observer. It has no propagated-epoch selection in this accepted slice; supplied publication index is explicitly static | Preserve existing native/static contract and disclosure. Do not claim an updated epoch index or add one as an unlisted closure prerequisite |
| `ChartRequest`, `prepare_chart_request`, `get_chart_view`, ordinary `generate_chart_request` / `wenu_chart` | Ordinary request requires `ChartObserverRequest`; preparation/view refuses an absent observer, and no ordinary stellar-motion input is admitted | Defer stellar-motion adoption for ordinary all-sky/full-sky (planisphere), regional, circumpolar and binocular products until full observer functionality; existing modern behavior is unchanged |
| Direct `RegionalChart` / `PolarPlanisphereChart` render/export | Both forward realization context through canonical rendering/export; polar native context is explicit. A manually specified regional geometry can reuse the seam, but `from_coordinate`/orientation and `from_constellations` framing depend on an observer | Retain existing low-level capability. Accepted atlas use supplies evidence for its own composition only; no standalone propagated request, new framing semantics or additional product acceptance is claimed |
| `export_polar_planisphere_pages`, `CommonYearCalendarRequest`, `PolarHorizonOverlayRequest`, associated pouch products | Page references use observer time; calendar calibration uses local standard-time midnight/longitude and sidereal time; overlays require matching observer latitude and observer-to-equatorial conversion | Physical observer-dependent product adoption is deferred. Native polar disk rendering does not qualify its calendar, horizon or terrestrial geometry |
| Observer-time sequences and fixed-sky/rotating-horizon products | Existing sequence owners construct or reuse ordinary observer-bound requests; fixed-sky orientation is a distinct observer construction | Defer stellar-motion adoption under the same observer boundary. A frozen Earth is not a substitute for the missing observer contract |
| `stellar_realization_sky`, stars, constellation lines/labels | The bound view refuses observer-bound/non-native use. Stars own source/model/event and session; lines/labels consume public returned positions and retain source membership | Preserve accepted isolation/refusal and modern catalogue behavior. No bypass, dummy observer or duplicated propagation policy |

The canonical source → spherical → domain guard → projection → projected →
preparation → renderer → furniture/export path is unchanged. The coordinate
guide remains current: stellar TCB event and TT mean-axis equinox are independent;
neither supplies an Earth/site observer. Full observer work must separately
define modern population-preserving composition as well as K4b.08's ancient/
future chronology, site and rotation policies.

### R1 retained inventory and explicit postponement

The Mac inventory selected **177 distinct HIPs using original Wenu V ≤ 3**,
with source manifest SHA256
`8747349e08f70a428b547f6d0131c47b6f935df73e6b7df9ef6b9d36aba4d365`.
Retained directory:
`~/Software/build/wenu/output/bright-star-source-review-v1-vzbxi6wk`.
Its `population` products retain full current source rows, Gaia/Hip2 records,
metadata, ordered HIPs and a completion manifest binding product bytes/hashes.
The supplied terminal evidence was inspected: 177 original and 177 Hip2
parallaxes, 61 Gaia parallaxes and one Gaia RV (HIP 108085). All original/Hip2
parallaxes in this particular selected sample are positive. The 116 Hip2 / 61
Gaia availability split is not an adopted quality ranking or replacement policy.

Two v1 comparison captures failed connecting to Strasbourg before receiving
catalogue data:
`~/Software/build/wenu/output/bright-star-comparison-capture-v1-mdgpel7m` and
`~/Software/build/wenu/output/bright-star-comparison-capture-v1-rywhs_ya`.
The second attempt followed VPN disconnection. A later Mac diagnostic timed
out for Strasbourg IPv4/IPv6 and the alternate hostname, while Harvard returned
HTTP 200. This establishes reachability differences at that time, not a proven
provider outage or VPN cause. A versioned Harvard recipe was supplied but has
no reported execution; it is not comparison evidence.

Retain the inventory, failed provenance and source dependencies. External
per-HIP UBSC/UBAD/HGCA comparisons, individual binary/orbit/systemic-RV evidence,
source suitability/gap table and unresolved provider reuse/licensing review
remain deferred under R1. No new acquisition is selected here, and no candidate
data, source ranking, production input change or redistribution is accepted.
Resume only by explicit selection; R1 remains discoverable after parent closure.

### R4 evidence and closure review

| Obligation | Existing accepted evidence / limitation |
|---|---|
| Propagation and scientific meaning | K4b.05 nominal reconstruction accepted with explicit limits; source/model/time-scale/covariance issues #326/#333 remain open. Physical/total historical accuracy remains unknown |
| Public sheet/CLI, dependent lines/labels and export | #346 source-loaded/restored J2000/J-8000 Python specimens; #348 installed CLI/TOML parity, reports and PNG/PDF/SVG acceptance; source membership and public-position responsibility preserved |
| Reuse and workloads | #346 warm full-source queries 0.949–1.158 s versus initial 18.279–22.325 s. #350 two-sheet serial 202.903/178.388 s versus two-worker 374.808/332.723 s at J2000/J-8000: parity demonstrated, serial faster for this workload; no universal speedup claim |
| Dated axes and polar/ordinary rendering | #354's eight actual-cache cases cover both mean axes × TT J2000/J-8000 × jobs 1/2, sheets 1 and 13. Scientific reports, pixels, counts, page order/physical sizes, defaults/source immutability and user visual review accepted |
| Population and modern compatibility | All 118,218 original objects remain in the source. Historical motion specimens contain 97,710 full-input + 17,395 angular + 2,850 Hip2 fallback models = 117,955 available directions and 263 explicit model gaps. Those gaps are not deletions or a modern-star membership cut. No historical-model fallback is silently inserted into modern charts |
| Source measurements | Measured parallaxes and other original astrometry/uncertainties/provenance remain source facts. Angular model selection or absent RV does not erase parallax or imply zero; nonpositive/uncertain measurements remain preserved without fabricated reciprocal distances. No production/source bytes change in this reconciliation |
| Explicit unfinished scope | R1 comparison postponed by Fernando; observer-dependent chart adoption deferred until full observer functionality. K4b.07 persistence, later observer work and K5 cross-K freeze remain separate |

Retained runtime/science/visual evidence is linked in the accepted receipts
below; no propagation, rendering, timing or visual review was rerun for this
documentation-only reconciliation. New workload claims are not inferred from
test counts. Failed and successful runs and their dependencies remain retained.
The complete Mac documentation gate passed and Fernando accepted this bounded
result as recorded above. K4b.06 is closed with the named deferrals. This does
not complete R1, observer-dependent products, physical qualification, persistence
or K5. The status receipt and subsequent K4b.07 assessment use the complete
documentation gate; no new runtime/science/visual pass is claimed.

## K4b.07 persistence as-is assessment, 2026-10-28

**Selection:** after accepting K4b.06, Fernando asked what follows in the roadmap
and said “proceed” after the K4b.07 as-is assessment/exact-epoch scope proposal.
This selects assessment and definition, not runtime implementation or the whole
K4b.07 backlog. Source inspected at PR #357 head
`829c472530cc1a8d1e6eb26a2bdfa0f24a4401e9`; main remains `b295b88b` pending
that PR's final status receipt/merge. No new branch or runtime gate is implied.

| Existing owner / actual interface | As-is capability and boundary | Persistence consequence |
|---|---|---|
| `stellar_enrichment.py::StellarEnrichmentSnapshot`, `load_stellar_enrichment` | Immutable original/Gaia/Hip2 bytes, fixed product names, strict finite JSON, manifest product identities and source metadata; explicitly no model adoption | Reuse validated source identity/bytes. Do not relabel this source snapshot as an evaluated epoch catalogue |
| `stellar_state.py::StellarMotionCatalogue`, `StellarMotionRequest` | Ordered admitted full/angular/Hip2 policies on one source, explicit finite TCB domain/event; original source retained; immutable `SpaceMotionRow` or `AngularMotionRow` coefficients and source event | Model inputs already exist for lossless storage/faithful future continuation. Preserve all IDs/statuses and the exact original coefficients; do not reconstruct them from rounded directions |
| `StellarMotionProvider(catalogue, representation='cartesian')` | Full-input catalogue exposes SI position and velocity through typed SDK batches; angular/Hip2 catalogues refuse Cartesian representation. Direction output separately exists for all admitted models | No new Cartesian numerical engine is required. Prepare direction states for chosen models plus Cartesian states where admitted; angular rows keep distinct coefficients/capabilities and measured source parallax |
| `_StellarRealization.positions`, `stellar_motion_identity` | Public stellar view selects first available model per source HIP, queries SDK and returns angles/NaN gaps; reports exact query reuse and model/source/event identity. Realization/session caches are process-local | Reuse selection semantics at the stellar owner; a persistent product needs a public validated data contract rather than serializing private caches or live sessions |
| `StellarMotionExecutionInput` | Captures motion document, external source directory and snapshot/design identities; each worker re-admits models and evaluates them. Live `StellarMotionRequest` transport refuses | Existing worker transport is not evaluated-state persistence or a self-contained epoch product; preserve its accepted contract |
| `sky/native_snapshot.py` | Validated v1–v6 source-only sky reconstruction, atlas design/layer metadata, hash-bound payloads, exclusive destination/staging and completion manifest last | Reuse publication/integrity patterns, not its source-epoch schema or private generic encoder as the new scientific product. Old snapshots retain their meaning |
| `astrometric_state.py`, SDK `DirectionState`/`CartesianState` | Same affine engine, separately typed angular/full inputs, explicit query/source/anchor events and uncertainty evidence; Cartesian temporal certificates are unsupported | Exact-event state serialization needs no kernel algorithm change. Persist known/unknown errors as returned; do not invent certificates or physical-error bounds |
| `astrometric_coordinates.py`, kernel `TimePoint`/`TimeService` | Split-JD event/scale; explicit TCB/TDB conversion and coordinate-convention receipts; historical chronology and TT frame orientation are separate services | First slice uses the already resolved TCB request only; no implicit UTC/TT conversion or reassignment of source event |
| `ephemeris.py`, `skyfield_ephemeris.py`, `astrometric_observation.py` | Separate resource-bound TDB target/centre states, body/segment coverage, common-event/state-convention conversion and finite modern reception admission | Earth/Solar System companion and observer products remain separately scoped. A native stellar epoch catalogue requires neither ephemeris nor observer resources |

Relevant existing test owners were inspected, not rerun: `test_stellar_state.py`
contains full Cartesian/direction axis/oracle/order, source preservation,
angular-Cartesian refusal, process-isolation and worker transport cases;
`test_astrometric_state.py` and kernel `test_cartesian.py` protect typed states,
distance/velocity/source-event semantics and exact cache behavior. Atlas/native
snapshot and source-audit tests protect their own formats. None proves the new
epoch product exists or survives fresh-process reload.

The [first-slice proposal](kernel_roadmap_v0.9.5.md#k4b07-proposed-first-exact-epoch-persistence-slice)
is now concrete enough for scope review. It remains proposed until Fernando
accepts its format/ownership/input/output/gate boundary. No new provider source,
numerical model, persistent format, preparation tool, loaded-epoch consumer,
nearby-window behavior or companion state has been implemented by this review.

## K4b.06 completion assessment, 2026-10-28

**Base:** GitHub main `50b3d4bd25c07eb4695dc101828b5c5b81fabf33`.
Fernando confirmed clean synchronized Mac main and deletion of the #355 task
branches, then requested completion of K4b.06. All 36 #355 documentation cases
passed in 4.97 s at `0cd43b989f8251c6731b0b7a62a28abce566b9d9`;
evidence `~/Software/build/wenu/test/dated-atlas-receipt-docs-v1-co9r1jmy`.
Fernando subsequently accepted the corrected completion scope with “accepted,
please proceed.” The original-V ≤ 3 review and supported observer-free consumer
reconciliation are now selected, with modern-star/parallax preservation and
observer-dependent deferral binding. The subsequent reconciliation above supersedes the remaining-work status of
this original selection receipt: R1 is postponed and R2/R3/R4 are accepted;
K4b.06 is closed for its bounded observer-free scope. No new
scientific/product workload was run for either documentation review.

| Existing owner | Observed source behavior | Closure consequence |
|---|---|---|
| `charts/request.py::ChartRequest` | Required observer and cluster-motion selection; no stellar-motion request | An explicit stellar public-input contract is missing outside the atlas route |
| `charts/request_chart.py::prepare_chart_request`, `charts/view.py::get_chart_view` | Ordinary chart preparation/view refuses absent observer | These observer-dependent public request/view paths are deferred by Fernando; do not invent observer-free semantics solely to force K4b.06 closure |
| `charts/request_generation.py` / `request_realization.py` | Ordinary export requires observer; realization supports observer-horizontal/Galactic and a distinct frozen-Earth construction. Atlas dispatch is separately observer-free | Preserve defaults and supported observer contracts. Do not use the frozen-Earth route to approximate an ancient observer or create a dummy observer for native products |
| `charts/regional.py::RegionalChart.render` | Accepts realization context and delegates through the sphere/domain/projection pipeline; constellation auto-framing still requires observer | Assess existing observer-free public behavior only. Auto-framing or other product behavior needing an observer is deferred; no new native product is selected implicitly |
| `charts/polar_planisphere.py::PolarPlanisphereChart.render` | Admits a native context without observer and bypasses the observer-to-ICRS conversion in that case | Native disk geometry is reusable. This does not qualify dated calendars/horizon overlays or ordinary observer-visible planispheres |
| `charts/all_sky.py`, `circumpolar.py`, `binocular.py`, `full_sky.py` | Existing family-specific observer/framing/projection contracts; context parameters alone do not establish native public requests | Record observer-dependent product paths as explicitly deferred until full observer functionality; preserve existing modern behavior |
| `sky/assembly.py::stellar_realization_sky` and `objects/stars.py` | Bound stellar view is isolated and observer-free; non-native realization refuses | Keep the stellar-owned public interface; a new observer view must be admitted explicitly, not enabled by removing this guard |
| `stellar_state.py::StellarMotionProvider` | Exposes separately admitted full-input Cartesian representation; angular catalogues reject Cartesian representation | The later full observer work can reuse the full-input engine. An angular representation cannot invent physical PV, but measured source parallaxes remain available source facts and modern stars must be preserved |
| `astrometric_observation.py::realize_astrometric_batch` | Uses typed Cartesian batches, explicit reception TCB event, TCB/TDB conversion and finite-observer correction policy; reception admits verified leap/final-EOP and finite model/resource coverage | Retain this service for later full observer functionality; its Cartesian input requirement is not grounds to exclude modern catalogue stars during K4b.06 |
| Existing test owners | Stellar view/motion/publication tests, ordinary request-realization/cluster composition, regional geometry and polar native/render contracts already exist | Extend these owners for real new seams; do not add milestone-only modules or repeat unrelated numerical proofs |

Inspected source blob identities include:
`ChartRequest 0c5f6341`, `request_realization 8a1f38d3`,
`request_generation 109e4f20`, `request_chart f6f76272`,
`view 1343b4ea`, `regional 1ab20490`,
`polar_planisphere bc5ad9a3`, `stellar_state 72c354f0`,
`Stars e79b3789`, `assembly 4820f01f`.
The exact pinned commit, not abbreviated blob labels, is the authority.

### Bright-star source question and review scope

Fernando's original question was which astrometric observations are best for
the brightest stars. The earlier assistant proposed a V ≤ 3 review against
UBSC, UBAD, HGCA and individual orbital/systemic-RV references; Fernando deferred
that review to K4b.06 production integration. The V ≤ 3 threshold was initially a recovered proposal; Fernando's subsequent
acceptance of the corrected completion scope selects that bounded sample.
It authorizes no source replacement or universal source ranking.

Primary documentation rechecked 2026-10-28:

| Source | Verified role | Review consequence |
|---|---|---|
| [UBSC, Zacharias et al. 2022; CDS J/AJ/164/36](https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/J/AJ/164/36?format=html&tex=true) | 1,423 all-sky bright stars; nearly complete to V=3 except three systems; ICRS astrometric parameters/covariances at J1991.25; known/suspected multiplicity flags. Its listed Hpmag is not Wenu V | Candidate alternative for missing/poor Gaia bright-star solutions; shared Hipparcos inputs and multiplicity preclude treating it as an independent universal oracle |
| [UBAD, Munn et al. 2022; CDS J/AJ/163/131](https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/J/AJ/163/131?format=html&tex=true) | 364 bright northern stars, current-epoch astrometry and Hip2-combined proper motions; includes stars missing from Gaia EDR3 | Useful northern comparison, not complete southern coverage or independent Hip2-free proper motions |
| [HGCA EDR3, Brandt 2021; CDS J/ApJS/254/42](https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/J/ApJS/254/42?format=html&tex=true) | Cross-calibrated Hipparcos, Gaia EDR3 and positional-difference proper motions with covariance/acceleration diagnostics | Compare baselines and acceleration/component evidence; do not simply select the smallest formal PM error as a systemic rectilinear motion |
| Published individual system/orbit and spectroscopic-binary RV evidence | Individual original references, component definitions and systemic versus instantaneous RV must be checked during the actual audit | No original orbital/RV value is asserted inspected or adopted by this assessment |

This initial source-role assessment preceded the 177-HIP inventory. The
[current R1 disposition](#r1-retained-inventory-and-explicit-postponement)
records the completed inventory and explicit postponement. External per-HIP
comparison and provider permissions remain unresolved; literature findings do
not complete that comparison. The admitted source remains unchanged.

### Corrected closure boundary and modern catalogue preservation

Fernando rejected the proposed initial modern observer product with
angular-only/missing-distance exclusions. His explicit correction requires no
loss of modern catalogue stars, use of measured source parallaxes when no better
qualified input is available, and deferral of any observer-dependent chart type
until full observer functionality is added. The [corrected completion boundary](kernel_roadmap_v0.9.5.md#k4b06-completion-boundary-2026-10-28)
records those instructions. The former full-input-only observed subset is
withdrawn; it was never implemented or accepted.

The source findings above remain valid observations about existing interfaces,
not permission to discard source measurements or reduce the modern population.
A selected angular-motion representation need not carry distance to propagate
directions; it must still preserve measured source parallax and its provenance.
Source catalogue barycentric direction/parallax and later observer displacement
are distinct responsibilities. No zero-parallax inference follows merely from
an angular-model selection.

K4b.06 now reconciles already-supported observer-free paths and the source review.
Ordinary request/view/chart types that require an observer remain deferred,
with existing modern behavior unchanged. Native regional/polar renderer seams
must not be promoted into new product/request families merely to bypass the
deferral. Final acceptance must distinguish modern catalogue availability from
historical-model availability, preserve source measurements, reuse accepted
atlas receipts and name the deferred observer consumers. This definition makes
no runtime/source selection changes and does not yet close K4b.06.

## Accepted dated-axis atlas result

PR #354's bounded K4b.06 mean-axis atlas slice is accepted and merged at
`d01248376d9f5e8400575f83053499549604817f`. Tested final head:
`0c900da15c99e37591a1a07f5495140b3263a4a0`. Fernando confirmed clean,
synchronized Mac main and local/remote cleanup of
`feat/k4b06-date-oriented-atlas`; he reconfirmed that base on 2026-10-28.
The [merged PR receipt](https://github.com/fselman/wenu/pull/354) records his
acceptance and the user-reported Mac evidence below. These are not claims that
the assistant independently inspected retained Mac run files.

All 155 distinct focused runtime cases are covered by 143 retained passes plus
the corrected 24-case layout owner (82.54 s; overlapping coverage, not 167 distinct
cases). The test-only explicit Agg-canvas correction preserved strict physical
margin assertions; no production tolerance or canvas change was needed.
All 36 documentation cases passed in 2.89 s and all eight tooling cases in
8.593 s. Retry logs/provenance:
`~/Software/build/wenu/test/dated-atlas-canvas-retry-v1-h0bd4cv6`.

The retained-source recipe v2 passed all eight publication cases: both
mean-equator/equinox and mean-ecliptic/equinox axes, TT J2000/J-8000 and
`jobs=1`/`jobs=2`, with polar sheet 1 and ordinary sheet 13. Stellar evaluation
remained a separately explicit TCB event. Python, installed CLI and publication
scientific reports and chart/report PNG pixels matched. Counts, serial/spawn
analysis, PDF page order/physical sizes and supplied static-index disclosure
passed. Native defaults matched prior CLI evidence before/after, and retained
source/snapshot bytes were unchanged. This establishes parity for the measured
workload, not a general speedup claim.

Actual-cache evidence:
`~/Software/build/wenu/output/dated-atlas-acceptance-v2-8gsytobv`;
comparison page `comparison-v2.html`; completion-manifest SHA256
`032c35cb3f9c2ff0bbc9f646fec3744f999a242b660fc7eee3e127cceed83280`.
The population remains 97,710 full-input, 17,395 angular and 2,850 Hip2 fallback
stars, with 263 explicit gaps. The count appendix selected 5,041 stars and
reported 263 invalid/unavailable positions; changing axes does not change
source/model membership.

Fernando confirmed line/label placement, reviewed the changed target-axis
footprints and poles, stated “So everything is OK” and requested merge/cleanup.
That acceptance, recorded in the PR, supersedes the immutable run's original
`visual_review: pending` field; do not rewrite the run. Recipe v1 stopped at
the legend-fit guard; v2 used explicit compact typography while retaining all
layers/fit checks. No production fix followed. Retain both failed and successful
runs, immutable enrichment source, saved source sky and their dependencies.

This accepts observer-free barycentric mean-axis single-sheet and serial/spawn
atlas views through existing owners. TT orientation and TCB stellar evolution
remain independent inputs. It supplies no observer, persistence, new source/model,
physical-accuracy guarantee or parent K4b.06 closure. The coordinate guide's
scientific meanings remain current; this receipt changes acceptance status only.
See the [remaining-obligation review](#remaining-k4b06-scope-and-bright-star-audit-placement)
and [roadmap selection status](kernel_roadmap_v0.9.5.md#current-position-and-next-item-selection).

## Date-oriented atlas as-is review, 2026-10-27

The pre-implementation assessment at `07a03aece766c86f316722200a03253550fbdfb7`
is retained in the [dated assessment archive](archive/kernel_audit_20261028/date_oriented_atlas_as_is_v1.md).
It identified the seams subsequently implemented and accepted through #354.
Use the accepted result above and current implementation reference for present
behavior; the original review is historical evidence.

## Accepted native atlas stellar publication and worker result

PR #350's bounded native atlas publication/worker slice is accepted and merged
at `9776052a9e7bc6a1786c0f6ccadd6e078eef74af`. Fernando confirmed clean,
synchronized Mac main and deletion of `feat/k4b06-atlas-stellar-workers`
locally and remotely. Tested head: `f4820501c5f3af60e18c15017513dee5fbc7ef11`.
All 90 focused Mac runtime cases passed in 68.30 s and all 36 documentation
cases in 2.98 s. Logs and provenance remain under
`~/Software/build/wenu/test/atlas-stellar-workers-v1-ctzrblha`.

The actual-cache run
`~/Software/build/wenu/output/stellar-atlas-acceptance-v1-b56p2g1p`
passed all four J2000/J-8000 TCB serial (`jobs=1`) and spawn (`jobs=2`)
cases for Orion sheet 13 and Dipper sheet 28. Fresh independent single-sheet
results also matched the previously accepted CLI specimens. Scientific reports,
chart/report PNG pixels, catalogue counts, serial/spawn analysis, PDF page
order/physical sizes and supplied static-index disclosure passed. The supplied
index in this run contained static layout geometry only. Each case retained
97,710 full-input, 17,395 angular and 2,850 Hip2 fallback stars, with 263 explicit
gaps; the magnitude-limited count appendix selected 5,041 stars and reported
263 invalid/unavailable positions. Retained source/snapshot bytes and the
checkout were unchanged. Completion-manifest SHA256:
`2a9cc22a9b4c27dceea13652a4c1ff5b793bb0a5bad721ac647467ecf2c65f19`.

Serial commands took 202.903 s at J2000 and 178.388 s at J-8000; two-worker
commands took 374.808 s and 332.723 s. This two-sheet workload demonstrates
parity, not parallel speedup. Fernando replied “OK.” after the comparison-page
and linked-book review request, then explicitly requested merge/cleanup.
These are user-reported Mac results and user visual acceptance, not independent
assistant inspection of the run files. Retain the run, source-only saved sky,
immutable enrichment source and related prior evidence with their provenance.

This closes only the selected native atlas publication/worker slice. Parent
K4b.06, other applicable product/frame/observer obligations and bright-star source
review remain open. Physical accuracy remains unknown; K4b.07 epoch-catalogue
persistence remains separate. No next runtime slice is selected by this receipt.

## K4b.06 production integration assessment, 2026-10-26

### Accepted stellar-owned native-sheet result

PR #346's bounded Python native atlas-sheet slice is accepted and merged at
`ab8a7e9ab1374a20c0eed3064d7555ed0a3b789e`; Fernando confirmed clean
synchronized Mac main and local/remote branch cleanup. At `0ec6515`, 59 selected
Mac runtime cases passed. At `4bf3dc63`, all 36 documentation cases passed in
3.04 s after the documentation-only correction. The actual immutable-cache run
`stellar-native-acceptance-v1-jriu3wpd` passed for freshly loaded and restored
source skies at J2000 and J-8000 TCB. Each case retained 117,955 available stars
and 263 explicit gaps; warm full-source queries took 0.949–1.158 s versus
18.279–22.325 s initially. The run resides under
`~/Software/build/wenu/output/`; completion-manifest SHA256 is
`313b02f098894bbfbc0144e2bafef5e9dc8665f2d2572092e4ae7466e480fd34`.
Fernando reviewed the comparison page and confirmed “Everything is OK”, then
requested merge/cleanup. These are user-reported Mac results and visual
acceptance, not a claim that the assistant independently inspected the run files.
Retain the run, source snapshot and provenance as acceptance evidence.
The parent K4b.06 stays open for its remaining product/worker/CLI obligations.

### Accepted native single-sheet CLI/TOML result

PR #348's bounded single-sheet CLI/TOML slice is accepted and merged at
`c319c88fc3dac04f8cedbef7ab443a8cd0cc1ace`. Fernando confirmed clean
synchronized Mac main and deletion of the task branch locally and remotely.
At `e0cfa8b8`, 49 stellar/configuration cases passed in 17.85 s, 27 atlas cases
in 9.75 s, and all 36 documentation cases in 3.06 s. Logs and provenance are
retained in `~/Software/build/wenu/test/stellar-motion-cli-v1-vxgntb1y`.

The actual installed-command run `stellar-cli-acceptance-v1-2uivsdha`, under
`~/Software/build/wenu/output/`, passed for Orion (sheet 13) and the Big Dipper
(sheet 28), at both J2000 and J-8000 TCB. All four reports matched independent
prepared Python requests exactly; chart and report PNG pixels matched, and
PNG/PDF/SVG checks passed. Every case retained 97,710 full-input Gaia, 17,395 Gaia
angular and 2,850 Hip2 fallback models, with 263 explicit gaps (118,218 source
objects). Retained source/saved-sky bytes and the checkout were unchanged.
Completion-manifest SHA256:
`5aeaf874684381ab337356aaf75bf4667df9ad7554adfdd6dbf644cfb58dd48c`.
Fernando confirmed line/label placement on present and ancient charts, then
requested merge/cleanup. These are reported Mac results and user visual
acceptance, not independent assistant inspection of those output files.
The parent K4b.06 and other product/worker/observer obligations remain open.

### Native atlas publication and worker assessment

At `c319c88f`, the existing publication dispatch and worker initializer contain
no motion binding. Both invoke the canonical chart command with a prepared
single-sheet request. Worker skies are source-only; the count appendix's parallel
parent constructs another source-only sky. Sizing analysis consumes rendered
products, and the optional index/selection pages are supplied static documents.
No new numerical engine or renderer is needed. A process-local stellar view,
integrity-bound data-only execution description, explicit worker finalization,
consistent catalogue-count input and complete publication provenance are the
concrete missing boundaries. See the
[proposed scope and gate](kernel_roadmap_v0.9.5.md#k4b06-native-atlas-publication-and-worker-scope).
Fernando selected this definition after roadmap-context review with “Proceed”;
the concrete details await review before runtime implementation. No production
or scientific contract changes are made by this documentation step.

**Selected work:** define the first production consumer slice after K4b.05
nominal-use acceptance, not another propagation-science investigation.
Fernando confirmed clean synchronized Mac main
`4e78cb9e76def88b069f837338d336ab7095253c`, PR #343 merge and local/remote
cleanup, then said "Proceed." His instruction places the bright-star audit
within production integration and keeps architecture migration central.
The definition plan was committed at `41a85e77502a7118b6bef07d1211beb0fc27fb55`
before the definition. PR #344 passed all 36 Mac documentation cases in 4.12 s
at `7edf0659`; Fernando accepted the scope and requested merge/cleanup.
It merged at `dc0d1d52`, with clean synchronized Mac main and local/remote
cleanup confirmed. He then explicitly required realization to belong to stars,
with lines/labels consuming their positions without epochs/astrometry knowledge,
and said "Indeed. Proceed." **The first slice below is selected with that
ownership correction; the first native Python sheet slice is now accepted as recorded above.**

### As-is assessment: existing owners and the missing connection

All paths below were read from the current GitHub base. The existing source
codec, motion admissions, SDK, spherical/projection services and renderer remain
their respective owners; there is no reason for another astrometric engine or
an alternate rendering pipeline.

| Existing owner / public seam | Current implemented behavior | Missing connection for propagated stars |
|---|---|---|
| `stellar_state.py` | Immutable full Gaia, Gaia angular and nominal-TCB Hip2 admissions/providers over `astrometric_state.py`; finite domains, source identity, availability and SDK queries already tested | Production request-owned selection/lifetime over these already admitted models; no new propagation arithmetic |
| `objects/stars.py::position` | Source-native selected positions; the compatibility `instant` argument is explicitly ignored | An explicitly opted-in propagated public path; passing an old compatibility date alone must not silently change behavior |
| `objects/stars.py::native_positions` | Full-source or sparse HIP lookup, independent of marker magnitude selection; retains source order, IDs/metadata and NaNs through real kernel lookup | Same public source/selection semantics at a common requested epoch, using the motion request rather than source-epoch lookup |
| `Stars.realize` | Native ICRS uses `_native_catalogue_coordinates`, whose `native_stellar_states` call still returns unpropagated source directions; observed route remains separate | Propagated values must enter this same spherical point geometry before existing projection/preparation/rendering |
| `sky/constellation_lines.py` | Native figure geometry calls public `stars.native_positions(self.star_ids)`; faint vertices, curated HIP edges, warnings and order are independent of marker selection | Obtain endpoints from public stellar positions, without request epoch/model knowledge; retain unavailable endpoint/edge behavior without invented connections |
| `sky/constellation_labels.py` | Calls public full-source native positions, assigns IAU groups and Serpens parts, then computes existing spherical means; faint source stars contribute | Keep source grouping stable, but calculate anchors from available propagated member directions; do not accidentally regroup moving stars into different constellations |
| `sky/realization.py` and `CelestialSphere.draw_chart` | Immutable layer context can carry an evaluation instant/scale; native guard checks returned geometry reference/time, allowing truthfully static layers with no evaluation instant | Bind the stellar owner once to the resolved event; dependent geometry preserves returned coordinate provenance without interpreting epochs. A context date alone does not turn stellar lookup into motion |
| `charts/atlas_sheet.py` | Public `AtlasSheetChartRequest`/`render_atlas_sheet` already support observer-free fixed-ICRS sheets through canonical chart owners; the render leaf creates a source-native context | A narrow opt-in native-sheet request can carry the motion binding into that existing route |
| `charts/request_generation.py` | `open_chart_request_scope`/`ChartRequestBuild` own the lease, temporary resources, rollback and cleanup; atlas-sheet execution uses the same owner | Extend that lifetime for a shared stellar realization; do not attach reusable live kernel/session objects to source catalogues or saved skies |
| Ordinary `ChartRequest`/`request_realization.py` | Current horizontal/Galactic/frozen-ecliptic routes and explicit cluster observer composition | These are broader observer/frame/CLI consumers. They are not an excuse to replace native-sheet rendering or run an unqualified ancient observer model |
| `sky/native_snapshot.py` | Data-only source snapshots and reconstruction with existing source metadata; no Gaia motion-selection or evaluated-state persistence | Reuse source snapshots with an explicit separate motion request. Never reinterpret an old native snapshot as propagated, or serialize live sessions as catalogue data |

Inspected Git blobs include Stars `a760d09c`, lines `ca97552d`, labels
`61c4b61c`, layer context `78ba79ef`, sphere `f639334d`, native sheet
`ec464408`, request lifecycle `109e4f20`, and snapshot `fcfd16bb`.
The stellar admission blob remains `78e8ab33`, as accepted in K4b.05.
This is source inspection, not a claimed end-to-end production motion run.

The label distinction is material. Today both membership and anchors come from
the same source positions. Simply replacing that array by propagated angles
would change IAU membership/Serpens grouping as stars cross fixed boundaries.
That would violate the retained membership/name contract. The source grouping
and epoch-dependent anchor calculation therefore need separate explicit roles.

### Selected first production slice: stellar-owned native-ICRS realization

**Selected result:** an opt-in Python native-ICRS atlas-sheet request that binds
one epoch-dependent realization to the stellar owner. Stars expose its positions;
figure endpoints and label anchors follow through the public stellar interface.
Only stars/their adapter know the epoch, admitted astrometry, model order and
SDK query/reuse policy. Lines and labels do not configure or perform propagation.
They preserve returned geometry provenance without interpreting motion settings.

The first slice covers the following bounded responsibilities:

1. **Explicit inputs and routing.** The caller supplies the validated immutable
   enrichment source/binding, finite admitted model domains, one common resolved
   TCB `TimePoint`, and an explicit ordered selection of already admitted
   direction catalogues. Each HIP uses the first catalogue in that supplied
   order declaring it available. Full Gaia / Gaia angular / Hip2 is a possible
   explicit caller order, not a hidden default or a new best-data claim.
   Validate consistent retained HIP/source/photometry identity across bindings.
   A model's declared missing-input status may select the next supplied model;
   an SDK, integrity, epoch/domain or numerical refusal must abort, not trigger
   fallback to another model or old native coordinates.
2. **Stellar ownership and request lifetime.** Stars and their stellar adapter
   own source/model/epoch routing and actual SDK queries/reuse. The existing
   request scope binds that stellar view once and closes its owned resources on
   success/failure, preserving the borrowed sky/source without shared mutation.
   Lines/labels ask only for stellar positions; they receive no epoch, astrometric
   admission, model-selection options, propagation provider or session. There is
   no provider/session per line edge, label, renderer or style. Generic kernel
   services gain no Gaia/HIP, chart, catalogue-decoding or naming policy.
3. **Public positions, identity and gaps.** Extend the public stellar lookup/
   realization path by explicit opt-in, preserving existing no-motion methods.
   Return results joined by original HIP identity and source order, never by
   incidental batch order. Preserve original V photometry, names, components,
   source records and selection/vertex metadata. Retain unavailable IDs with
   explicit status/reason and unavailable coordinates; do not publish NaNs as
   valid kernel states, invent PM/RV, silently paint an old static position or
   drop objects from the retained source.
4. **Figures and anchors.** Markers retain existing render-local selection.
   Figures obtain all needed faint endpoints through public stellar positions
   and preserve curated topology, finite-segment handling and missing-endpoint
   reporting. Label membership/Serpens partition comes from source-native public
   identity/geometry; anchor means use available propagated directions of those
   original groups, with the existing minimum-count/empty rules. Names and
   membership do not change because an extrapolated star crossed an IAU boundary.
5. **Canonical product integration.** Add the opt-in binding to the existing
   native atlas-sheet request/lifecycle and bind it to the stellar owner. Feed
   stars' returned positions into the existing `Stars.realize`, line/label
   geometry and `CelestialSphere.draw_chart` routes. Do not pass motion settings
   through line/label options; those consumers only preserve returned provenance.
   Projection/domain clipping, preparation, renderer, furniture and export stay
   in their current owners. Static grids/deep-sky/diffuse layers remain truthfully
   static; a historical stellar specimen is not a physical evolution model for
   every layer. Report common epoch, source/model choices, gap counts and unknown
   physical accuracy without forging one physical model/error bound for mixed rows.
6. **Isolation and source snapshots.** Preserve current no-motion defaults and
   source-only snapshot semantics. A restored sky may use an explicitly supplied,
   validated motion binding; it cannot acquire one implicitly. Initial unsupported
   worker/transport combinations must refuse before output rather than silently
   render native stars. Source snapshots do not become evaluated-state snapshots.

This is an assembly/consumer change over admitted services, not a geometry
protocol, new observer implementation, catalogue replacement, dependency/pin
change or package extraction. Extend existing responsibility owners. New helpers
are justified by shared lifecycle/source boundaries, not by “K4b.06” filenames.

### Acceptance for the selected slice

The closest existing protections are
`test_native_position_routes_use_returned_kernel_direction_and_propagate_failure`
in `tests/test_position_providers.py`,
`test_native_edges_follow_the_same_kernel_results_as_stellar_positions` and
`test_native_line_geometry_uses_only_the_public_native_id_interface` in
`tests/test_constellation_geometry.py`,
`test_native_label_anchors_follow_kernel_results_and_propagate_refusal` in
`tests/test_constellation_labels.py`, and
`test_native_epoch_guard_rejects_mismatched_layer_time_before_projection` in
`tests/test_layer_realization.py`. Existing stellar tests protect names/NaNs/
selection and immutable source inputs. Request-generation and atlas CLI tests
already protect supplied-sky leases, failure cleanup and public sheet execution.

Extend those existing owners to detect: returned-state bypass; wrong epoch or
per-HIP identity/model joins; differences between markers/endpoints/anchors;
classification changing when a star crosses a boundary; missing faint vertices;
silently static unavailable stars; fallback after a warm SDK refusal; mutable
source/selection state; leaked resources; order-dependent repeated requests;
source-only saved reconstruction being misrepresented as propagated; and
line/label code depending on epochs, motion admissions or SDK sessions.

Constructed cases should use distinct epochs, permuted batch order, real model
availability gaps, failing providers after success and two otherwise identical
requests sharing one sky. A deliberate bypass of the shared realization in any
one of stars/lines/labels must fail the public seam test. Keep geometric mean,
projection and numerical propagation proofs with their existing owners.

Use the actual diff to choose a focused composition of existing
`native-stellar-routing`, `native-label-routing`, request-lifecycle and
`atlas-sheet-routing` protections; run independent motion-owner tests only if
their implementation/contracts change. No wholesale SDK/other-family/full-suite
rerun or new milestone-specific test file. If the reviewed gate manifest changes,
include the existing tooling/inventory integrity checks and documentation gate.

Real Mac acceptance should use the already accepted immutable source, a source-
loaded and restored sky, explicit common J2000 and J-8000 TCB requests (10,000
nominal Julian years apart, not a recovered civil “today”), and a native sheet
through the public production request. Inspect geometry and PNG/PDF/SVG outputs
for common star/edge/anchor epochs, preserved names/photometry, visible gap
disclosure and unchanged default-page appearance. Keep physical print/classroom
acceptance separate and avoid a future-date observer/EOP dependency.

Measure admission time, first/second same-epoch query/render time, changed-epoch
time, queried HIP counts, per-model SDK evaluation/reuse counters and output
workload separately. Report hardware, source/model/coverage/accuracy identities
and unavailable counts. Demonstrate reuse within the real request lifetime
without inventing a speed target or treating a numerical cone as physical error.

### Remaining K4b.06 scope and bright-star audit placement

Reviewed GitHub main `d01248376d9f5e8400575f83053499549604817f` after #354.
The native Python sheet, explicit single-sheet CLI/TOML, native atlas
publication/workers and dated mean-axis atlas views are accepted through PRs
#346, #348, #350 and #354. None of those bounded acceptance gates remains pending.
The following is an as-is reconciliation of existing obligations, not selection
of new runtime work or a changed milestone order.

| Boundary | As-is evidence | Remaining obligation / disposition |
|---|---|---|
| Native and dated-axis atlas sheets/publication | `AtlasSheetChartRequest` admits explicit motion and optional frame input; the canonical executor/publication binds them and #354 accepts both axes, polar/ordinary sheets and serial/spawn parity | Retain accepted receipts and evidence. No repeat implementation or blanket physical-accuracy claim |
| Ordinary regional, planisphere and other applicable chart consumers | `ChartRequest` has cluster-motion selection but no stellar-motion input. `chart_request_realization_context` requires an observer; the atlas branch of `generate_chart_request` is separately observer-free | Fernando subsequently deferred observer-dependent chart treatment until full observer functionality; atlas acceptance does not cover these public paths, whose existing modern behavior remains preserved |
| Stellar ownership and observer refusal | `stellar_realization_sky` rejects an observer-bound sky; `Stars.realize`/`_spherical_geometry` reject non-native realization of the bound stellar view | Preserve stars as source/model/event owner and lines/labels as public-position consumers. Observer-dependent consumers are deferred until full observer functionality. Preserve source measurements and modern population; never bypass the refusal with a frozen Earth. K4b.08 records ancient/future terrestrial qualification |
| Workload and final product reconciliation | Accepted native and dated atlas runs supply real-source workload/reuse, default compatibility and visual evidence for their exact public paths | Reuse applicable evidence; measure/accept newly selected consumers separately. Reconcile the complete applicable inventory at K5 before freeze, without treating accepted atlas gates as pending |
| Bright-star source review | R1 original-V ≤ 3 inventory now retained; comparison subsequently postponed by Fernando | Unfinished follow-up outside the current K4b.06 closure gate; preserve inputs/failed runs. No source replacement or acquisition is selected by this reconciliation |
| Evaluated epoch persistence and general transport | Atlas workers already admit captured data-only inputs; source-only saved skies remain source-only, and live request/session transport refuses | Persistent evaluated catalogues, preparation/reload, nearby-epoch policy and optional companion states belong to K4b.07. They are not missing #354 worker gates |

The source findings above were checked against `charts/request.py`,
`charts/request_realization.py`, `charts/request_generation.py`,
`charts/atlas_sheet.py`, `objects/stars.py` and `sky/assembly.py` at the pinned
base. This documentation review executes no new observer/product acceptance.

The earlier placement of the bright-star audit within K4b.06 is superseded by
Fernando’s explicit postponement recorded above. Retain its accepted sample and
uncompleted comparison as R1, outside the current closure gate. Keep the accepted
current source for architecture wiring and improved admitted inputs later.

Fernando subsequently selected K4b.06 completion and explicitly required modern
population/parallax preservation plus observer-dependent chart deferral, as
recorded in the corrected assessment and roadmap boundary above.
Exact-epoch publication/reload/parity remains K4b.07's first proposed slice,
not activated implementation. K4b.08's site/time/rotation/ephemeris/correction
definition remains separately pending; it is not silently inserted before
K4b.07 or baseline K5. This review selects no new order.

K5 still reconciles the complete consumer and science/capability inventory before
contract freeze. Stellar extraction remains K6 after K5, followed by remaining
families and release gates. Source/model policy stays outside generic services.

### Definition-task verification and decision

Inspected the actual source/test owners and existing gate selections above.
Local documentation checks passed four cases (11 deselected); the three relative
links/anchors in the new scope sections resolve. These focused checks do not
replace complete Mac documentation/archive/public-import acceptance.
No production/test/source/dependency/schema/default bytes were changed or
consumer execution claimed. The coordinate guide/API/source map remain current.
Complete Mac definition acceptance subsequently passed 36 cases in 4.12 s at
`7edf0659`; PR #344 was accepted, merged and cleaned up. The concrete first
slice is selected with Fernando's explicit stellar-ownership correction above.
This edit records the implementation boundary; it does not claim runtime changes
or execution. Documentation acceptance for the correction remains pending.

## K4b.05 qualification review after reference comparisons, 2026-10-26

**Accepted outcome, 2026-10-26:** Fernando said “Accepted as described” after
all 36 Mac documentation tests passed in 3.65 s at `a8c0dd08`, with a clean
synchronized task branch. K4b.05 is **closed for nominal stellar-motion
reconstructions with the documented limitations below**. Physical ancient-position
accuracy remains unestablished, #326/#333 remain open, and pending sibling
K4b.02/AX.13 scope is unchanged. K4b.06 is not activated by this acceptance.
Fernando's accompanying bright-star source question is a read-only research
request, not a data-adoption or model-change decision.

**Authority/base:** Fernando selected this review with "Proceed" after PR #342
merge/cleanup and confirmed clean synchronized Mac main
`df4eae36fede007a2089f89cdcd436ad8e69a3a7`. At `4034e69b`, its final
Mac gate passed 36 documentation tests in 4.02 s and verified the complete
literature report against the uploaded visual specimen without propagation.
The selected review plan was committed first at
`f4ffdd160b8f7ee0bcaac4ad42fe7221fc80da4a`.

### As-is inspection and evidence continuity

Re-read the active roadmap, scientific contracts, coordinate guide, current
architecture, API/source map and testing policy. Inspected the actual
`stellar_state.py`, `astrometric_state.py` and existing stellar test owner.
The production owners are byte-identical to accepted PR #330/`5da8220f`:
stellar blob `78e8ab33d804ddfd5be5f31d48be9d310bbad4a7` and shared-motion
blob `77afec40b6c46f2096418cee14708104227eb929`. The current stellar test
blob is `0441c2744dac8878217e13fbc04e4215e6dc1639`; later finite-comparison
and explicit remote-epoch tests supplement the older receipt. This review
does not claim to rerun those numerical suites.

Full and angular admissions still require finite declared TCB coverage,
source-bound inputs and explicit policies. The full model uses reciprocal
positive parallax and the spectroscopic-RV proxy; the angular model omits
radial perspective. Hip2 remains an explicit nominal-TCB interpretation with
unverified native epoch/rate convention. Actual states retain measurement and
physical-model uncertainty as not evaluated. The independent numerical evidence
is about that admitted computation, not an empirical bound on the past sky.

[Issue #326](https://github.com/fselman/wenu/issues/326) and
[issue #333](https://github.com/fselman/wenu/issues/333) were read and are open.
No new source clarification or covariance repair was established. Their
resolution requirements remain attached to their respective source claims.

### Updated obligation and intended-use matrix

This is the current matrix. The
[2026-10-24 review](#k4b05-bounded-closure-review-2026-10-24) remains dated
provenance; its proposed finite comparison and unperformed-ESA status are
superseded by the later accepted receipts.

| Obligation / claim | Current accepted evidence | Disposition for the proposed nominal-atlas use |
|---|---|---|
| Numerical motion and finite coverage | PR #330 independent no-light-time spherical expression, fault detection and actual-cache directions; later test/domain/refusal receipts | Supported for the implemented nominal models and tested cases. Caller coverage is not a physical-validity interval; numerical reuse tolerance is not total position accuracy. |
| Finite perspective omission | [PR #339](#k4b05-finite-perspective-comparison-2026-10-25): sixteen HIPs retained, 15 matched pairs/65 pair gaps at source and +/-1,000/+/-10,000 yr; independent scalar/vector checks | The previously proposed comparison is completed. Differences are star- and epoch-dependent: at +10,000 yr HIP 87937 differs by ~26.088 deg, HIP 57939 by ~2.127 deg, HIP 59774 by ~5.354 arcsec. Angular-only motion cannot be treated as a universally accurate substitute; neither model is thereby physically validated. |
| Gaia formal angular measurement uncertainty | [PR #332](#k4b05-offline-gaia-uncertainty-report-implementation-2026-10-23): qualified five-parameter matrices and four-parameter angular marginals, independent derivative/Monte Carlo checks, 805,735 angular evaluations | Completed conditional offline diagnostic. It is not production SDK error evidence, a hard confidence radius, full-model RV covariance or a total error budget. No statistical prior or RV independence is silently adopted. |
| Missing RV / distance | Same report's hypothetical-zero-RV derivative and explicit proxy/gap records; finite paired comparison above | Sensitivities and nominal models available where admitted; missing physical measurements remain missing. No zero RV measurement, RV distribution, distance prior or universal cutoff follows. |
| Hip2 source time/rate | [PR #336 source review](#k4b05-hipparcos-2-time-convention-assessment-2026-10-24) plus [PR #337 population sensitivity](#k4b05-real-cache-hip2-time-convention-sensitivity-2026-10-24): all 2,850 fallback rows, unchanged source/model identity | Nominal angular directions remain admitted by the existing user-approved convention. Native source-scale/rate verification is unavailable pending #326. The tested hypothetical maximum ~1.591 mas at +50,000 yr does not resolve that fact or bound other errors. |
| Hip2 covariance | [PR #334](#k4b05-hipparcos-2-covariance-qualification-2026-10-23) standard decoding plus [PR #335](#k4b05-hipparcos-2-source-precision-investigation-2026-10-23) precision/outlier investigation | Diagnostics complete; production/propagated Hip2 covariance remains unavailable pending #333 and nonstandard-solution evidence. No forced rescaling, diagonal substitute or F2 clipping assumption. |
| Binaries, photocentres and acceleration | Source/component/solution flags preserved; existing providers contain no orbit/systemic-RV/Galactic-acceleration evolution | Known unmodelled physical limitations, not proven small errors. Acceptance would disclose them for nominal illustrations; no automatic quality veto, acceleration extrapolation or binary correction is authorized. |
| Missing PM and retained membership | 118,218 retained HIPs: 115,105 Gaia angular, 2,850 Hip2 fallback, 263 unavailable to these motion admissions; 97,710 full Gaia models overlap the angular population | All identities/statuses retained. No fabricated PM and no silently static “historical” position. No-PM approximation remains pending sibling K4b.02/AX.13 work; closure here cannot accept that sibling on its behalf. |
| Historical dates and mean axes | K4b.03 explicit chronology receipts and K4b.04 finite TT long-term mean-axis model; source/evaluation/equinox labels distinct | Accepted nominal composition capability. It does not reconstruct ancient clocks, observer/Earth rotation or horizon appearance. Native motion is TCB; a TT equinox is separate. The +/-200,000-year mean-axis domain cannot cover the +250,000/+450,000 native-shape specimens. |
| ESA Orion / Ursa Major comparison | [PR #340 assessment](#k4b05-esa-comparison-feasibility-assessment-2026-10-26) and [PR #341 execution/viewing](#k4b05-native-icrs-qualitative-diagnostic-candidate-2026-10-26): 147 rows/52 evaluated/95 gaps, media viewed, corrected plots verified | Requested bounded qualitative assessment performed. Broad evolving-pattern agreement only; detailed trajectory agreement is inconclusive because original inputs/epochs and stereo/viewpoint differ. Inconclusive is a recorded result, not an unperformed experiment or a numerical reproduction. |
| Literature comparison | [PR #342](#k4b05-literature-figure-comparison-preparation-2026-10-26): attributed source figures, 126 rows/46 evaluated/80 gaps, 63 refusal checks, uploaded report inspected and hash-linked | Clear qualitative agreement with Kaler/Lowell's future Dipper deformation; limited Orion/Bears subset consistency. No pixel residual, exact original-input reconstruction, ancient-pole test or physical certificate. Two Antonello papers are one research line. |
| Ordinary historical atlas / workload / reuse adoption | No such consumer change is present in these diagnostics | Still unavailable through this work. K4b.06 must connect the selected admitted states to stars, finite figure endpoints and labels, measure workloads/reuse and accept ancient product specimens through the canonical pipeline. A diagnostic Python recipe is not the normal atlas command. |

Model population counts overlap and must not be added. Formal uncertainties,
finite model differences, numerical cones, hypothetical convention scenarios
and visual resemblance are different evidence categories; none substitutes for
the missing total physical uncertainty.

### Accepted intended-use decision

**Fernando accepted this disposition on 2026-10-26:** K4b.05 qualifies
*nominal stellar-motion reconstructions with disclosed limitations*.
This intended use can include an illustrative atlas for about 10,000 years ago
after K4b.06 consumer integration. It makes no universal angular-accuracy
promise, no claim that angular-only and full propagation are interchangeable,
and no complete physical reconstruction of everything visible at that date.

The accepted disposition is:

1. Retain the accepted full, measured-PM angular and nominal-TCB Hip2 capabilities
   with their existing explicit admission/domain/refusal contracts. Do not turn
   the diagnostic F/G/H display priority into a production selection policy.
2. Accept the completed independent numerical and finite perspective comparisons
   and the bounded ESA/literature visual assessments at their stated precision.
   Keep detailed ESA agreement inconclusive rather than requiring inaccessible
   original inputs to support a claim we would not make.
3. Accept the documented omitted dynamics/source limitations for nominal
   illustrations only. Keep physical/total accuracy and physical epoch validity
   unknown; a request for a guaranteed physical tolerance remains unsupported.
4. Keep #326/#333 open for source-time/covariance claims. They need not veto the
   already admitted nominal direction use, but their unresolved claims must not
   be presented as verified. No-PM and other pending sibling scope stays pending.
5. K4b.05 closes for that bounded intended use. K4b.06 still needs its own
   selected implementation slice and acceptance; K4b as a whole, K5 freeze,
   extraction and release do not thereby close.

**Alternative:** if the desired product instead needs a guaranteed physical
angular error over a chosen historical interval or a reconstructed observer sky,
K4b.05 cannot close for that claim from this evidence. Agree the specific
claim/stars/domain and needed source/model qualification first. This alternative
does not silently activate a list of new models or investigations.

### Next gate and review limits

The intended-use decision is accepted. A next K4b.06 slice remains to be
separately selected; this is not automatic implementation authority. That slice
should explicitly select its consumer/API path, source/model
choice, retained-ID/gap behavior, date/frame request and benchmark/ancient
specimens, using existing state and geometry services. Its public seam tests
must detect stars/lines/labels using different epochs or bypassing the admitted
states; its numerical/visual/workload evidence remains separate from this review.

This branch changes documentation only. The architecture, source map, API,
coordinate guide, test selections and scientific meanings stay current.
No source acquisition, author contact, computation rerun, runtime change,
uncertainty certificate, issue closure or consumer adoption. The accepted
intended-use limitation disposition changes no computational scientific policy.
Four closest local documentation contracts passed: developer-root/index authority,
Python syntax, obsolete imports and roadmap diagrams/order. All fifteen local
links/fragments in the new review/status sections resolve. Full inventory,
archive and installed-public-import execution require the complete Mac checkout;
they are not claimed rerun here. The complete Mac review gate at `a8c0dd08`
subsequently passed 36 tests in 3.65 s. The acceptance-status Mac documentation gate at `2b6c8a6a` passed all 36 cases
in 3.63 s with clean synchronized task status. PR #343 merged at `4e78cb9e`;
clean synchronized Mac main and local/remote cleanup were confirmed. No numerical
or visual run was repeated.
Prior literature execution and report-integrity receipts remain accepted.

## K4b.05 literature-figure comparison preparation, 2026-10-26

**Authority/base:** Fernando requested literature before the closure review,
selected published figures where coordinate tables are absent, supplied the
Kaler photograph and 1998/page 68 citation, and said "OK. Proceed."
PR #341/main `2d34779b143238f02c095fb6d127afaf5986a1cb`, clean synchronized
Mac main and cleanup were already confirmed. Its final documentation gate passed
36 cases in 3.76 s; both reports/reviewed-image identities passed without repeated
propagation. The literature plan preceded executable work at
`734aed0acb50a635f238a16fc490840d01f54510`.

### Primary references and extracted figures

The primary PDFs were downloaded and selected pages/figures actually inspected.
The external versioned reference packet embeds selected figure extracts and
Fernando's unchanged photograph. Third-party media, publications, generated
plots and the temporary recipe remain outside the repository.

| Reference | Recovered evidence | Comparison limits |
|---|---|---|
| [Antonello 2010](https://archeoastronomia.altervista.org/wp-content/uploads/2019/07/SIA8_29.pdf), “Analisi dei moti propri stellari e forma delle costellazioni,” in M. Incerti (ed.), Mensura Caeli, UnifePress, pp. 353–356; Fig. 27.1 p. 356/PDF page 8 | Present/34,000-years-ago Orion–Sirius–Procyon field; Hipparcos astrometry and Barbier-Brossat & Figon (2000) RV catalogue; uniform rectilinear motion; relative shape without precession; measurement/binary discussion. | No full plotted input/coordinate table or exact present event/scale recovered. Our seven-star Orion sample omits Sirius/Procyon, where much visible change occurs, and the Milky Way/background. Redistribution licence unverified. The printed W equation uses the RA-motion symbol where the normal-triad expression requires declination motion; do not implement it literally. Existing Wenu numerical reference remains the oracle. |
| [Antonello 2016](https://doi.org/10.5281/zenodo.220954), “Sky Simulations for the Palaeolithic Epoch,” MAA 16(4), 329–334; Fig. 1 p. 331/PDF page 3 | Bears field labelled 28,000 BC; Berger long-term Earth geometry, with Laskar/Vondrák comparisons. DOI [archive 220954](https://zenodo.org/records/220954) supplied Full45.pdf and declares CC BY 4.0. | No full per-star inputs/coordinates or exact scale/calendar/projection recovered. Seven-star Dipper sample excludes Ursa Minor/Arcturus and dated pole/grid. Same author/research line as 2010; not independent validation. Myth/archaeology interpretation is separate. |
| Kaler, James B. (1998), Stars, Scientific American Library, p. 68; Lowell Observatory credit | User-supplied edition/year/page and original photograph of present/+250,000-year seven-star diagrams; Bayer labels alpha through eta. | Original Lowell author, source table, method, projection and exact “now” event unrecovered. Book year is provenance, not an assigned stellar epoch. No general redistribution licence established. |
| [De Lorenzis & Orofino 2018](https://doi.org/10.1016/j.ascom.2018.09.006), Astronomy and Computing 25, 118–132 | Accessible abstract/preview describes 24 bright-star software/precession comparisons, including Orion/Big Dipper members; independent methodological context. | Full text not obtained. No table/figure asserted inspected or reproduced; not an executed Wenu oracle. |

Downloaded/source SHA256 identities:

- Antonello 2010 PDF:
  `4e0c51ca5a8f6ff7860e92b9111306dd62b21c0e20263e29d0053921a3aaa4c8`.
- Antonello 2016 DOI-archive PDF:
  `e5d06165d0956415e5124166eabb1e2e48fec2aeb6f8d215fbefede2ffa99b27`.
- Original user photograph IMG_0257.jpg:
  `c1216351a618ded711371972c43a249b4afe57c621247b19e7196af9b436766c`.

External figure provenance records PDF page/crop rectangles, raster scale and
output hashes. Crops are rasterized without mirroring, rotation, redrawing or
geometric fitting. The photograph is unchanged. Attribution and licence limits
travel with the packet; no general republication right is claimed.

### External diagnostic, dates and scope

The offline versioned recipe reuses the immutable source, actual SDK admissions/
sessions, unchanged source-solution digests, independent spherical reference and
canonical stereographic service. All fourteen prior HIPs remain; no acquisition
or inferred RV. The three scenarios retain 126 HIP/model/epoch rows, including
separate global admission refusal and per-HIP missing-input statuses.

| Case | Explicit query convention | Display boundary |
|---|---|---|
| Orion | 0/-34,000 TCB Julian years from each retained solution epoch | Seven stars only; wider source field retained as context |
| Bears | J2000 and nominal J-27999 TCB, common to all models | Astronomical-year interpretation of 28,000 BC is an explicit comparison convenience, not recovered paper chronology; native shape only, no dated pole/grid reproduction |
| Kaler | 0/+250,000 TCB Julian years from each retained solution epoch | Published open chain alpha–beta–gamma–delta–epsilon–zeta–eta, explicitly separate from Wenu production topology |

Domains cover both past/future query ends and all source epochs. Gaia full,
Gaia angular and nominal-TCB Hip2 results/gaps remain separate. Combined panels
choose F then G then H only if both epochs are available for that star; display
priority is not production policy. Projection checks require RA left/native
ICRS north up. No pixel fit or paper-frame equivalence is claimed.

Output is no-clobber ~/wenu-output/stellar_literature_comparison_v1. The packet's
reference hashes are checked and HTML assembles the source figures with generated
model panels. A completion manifest binds rows, source/code/admission/SDK records,
report and recipe. Actual-cache execution and visual agreement remain pending.

### Local preparation checks

The unchanged closest numerical set passed 34 cases (124 deselected). External
AST-only reuse of the existing independent parameterized reference, with an
explicitly larger past domain, passed 21 full/angular/Hip2 cases at
0/-34,000/+250,000 years. Repository test collection is unchanged.
A constructed nine-object source exercised all three report scenarios: 126
rows, 42 evaluated directions, 84 gaps and 63 unavailable/outside-domain checks;
maximum independent chord residual 2.3055512673781017e-16. A reversed-negative-time
oracle fault failed as intended. Three synthetic plot exports were produced and
inspected; they are not constellation reconstructions and are excluded from
the reference packet. The reference-only HTML states execution is pending.

Four locally available documentation contracts passed: developer-root authority,
Python syntax, obsolete imports and roadmap diagrams/order. A broader partial
checkout attempt had seven missing-file failures (links/assets, application
sources, user guides and inventory inputs); it is not a passing full gate.
New literature links/anchors resolve. The actual Mac and uploaded-image receipts
below supersede the preparation-only pending status. Scientific contracts and
coordinate guide remain current. K4b.05 parent and #326/#333 remain open;
K4b.06 and normal atlas adoption are not activated.

### Actual Mac run and uploaded visual assessment

At `a2275f3e763995fdf691df6b1da81a9da28dd3f9`, the complete Mac
documentation gate passed 36 cases in 4.44 s. The immutable-source recipe
completed with 126 rows, 46 evaluated directions, 80 explicit gaps and 63
unavailable/outside-domain refusal checks. No global admission refusal was
reported. Maximum independent spherical chord residual:
`3.7238012298709097e-16`. The terminal ended with clean synchronized task status.

| Case, two epochs | Full evaluated/gaps | Gaia angular evaluated/gaps | Hip2 evaluated/gaps |
|---|---|---|---|
| Orion | 0 / 14 | 0 / 14 | 14 / 0 |
| Bears | 2 / 12 | 6 / 8 | 8 / 6 |
| Kaler | 2 / 12 | 6 / 8 | 8 / 6 |

All Orion combined directions use Hip2 angular fallback. Both Dipper cases use
full HIP 59774, Gaia angular 53910/65378 and Hip2 angular for the other four.
Missing rows are preserved model alternatives, not missing stars in the combined
seven-star figures. The console's Bears "2000 yr"/"-27999 yr" values are epoch
keys J2000/J-27999 TCB, not elapsed offsets. JSON rows/plot titles retain the
explicit common-epoch convention.

Output: /Users/fselman/wenu-output/stellar_literature_comparison_v1.
Reported completion-manifest SHA256:
`5c9b5382250c3bff36ea7b12a16982f492d4de72edb10acf4e24c97374c075f7`.
Recipe SHA256:
`5e662c78ccc6042414e48e0975f4c2569786aa5c65256290b46fd24cd99d645a`.

Fernando uploaded the generated HTML, which was parsed and its six embedded
images decoded and actually inspected. The three references match their retained
figure/photo hashes. Uploaded HTML SHA256:
`56a58611e0a63ac16fbbbd48b25034838570bf4fc1205c0b1361d69852a4de95`.

| Wenu image | Uploaded embedded-image SHA256 |
|---|---|
| Orion | `6da3402cc70e8dd48933afbcb0d79a26f138d98936b5bd4a53a678a8f5b6846b` |
| Bears | `ee139f235883b975948db838e5517c61ab9053a44bcb91a67b55c63c5c6a7952` |
| Kaler | `7d205f0bf5e0b3ab06262b87e3d2c96a78b172914696241b5e1a9cdd7d817f6d` |

| Comparison | Actually observed outcome | Disposition |
|---|---|---|
| Antonello 2010 Orion, -34,000 yr | The seven principal stars retain their recognizable arrangement in both published panels. Wenu likewise shows modest change, largest here for HIP 27989 (~0.281 deg) and 25336 (~0.144 deg), much smaller for the remaining five. | Broad qualitative consistency for the selected Orion subset. Fine agreement is unresolved at the published figure's resolution; the conspicuous Sirius/Procyon changes and background are outside our sample. |
| Antonello 2016 Bears, 28,000 BC | The seven-star Dipper remains recognizable in both views. Wenu displacements from J2000 are roughly 0.72–1.15 deg for the selected combined models. The source uses a pole-centred dated grid while Wenu is native-ICRS north-up; the figure/field cannot be directly overlaid. | Limited shape-level consistency; detailed agreement remains inconclusive. No ancient-pole, Ursa Minor/Arcturus or observer comparison was performed. |
| Kaler/Lowell Dipper, +250,000 yr | Both show the handle opening sharply at zeta–eta, eta lying well below/right of zeta in the displayed figure, and the alpha–beta end becoming much flatter than today. Wenu's future combined seven-star pattern closely resembles the published qualitative pattern, with the same explicitly chosen open-chain connectivity. | Clear qualitative agreement in the principal deformation; strongest of the three illustrations. No pointwise residual, exact model/input reproduction or physical-accuracy validation follows. |

No reference pixels were measured, rotated, stretched or fitted. Diagram
agreement cannot identify the missing original Lowell recipe or certify the
mixed Wenu models. Physical uncertainties, binaries/lifetimes, Hip2 time/covariance
issues #326/#333 and the K4b.05 parent remain open. This completes inspection of
the supplied visual specimen. Final Mac documentation at `4034e69b` passed
36 tests in 4.02 s; the complete manifest/products and uploaded HTML linkage
passed without propagation. PR #342 merged at `df4eae36`; clean synchronized
main and local/remote branch cleanup were confirmed.



## K4b.05 native-ICRS qualitative diagnostic candidate, 2026-10-26

**Authority:** Fernando approved Orion offsets 0/+10,000/+100,000/+450,000
and Big Dipper offsets 0/+10,000/+60,000 TCB Julian years on 2026-10-26.
Clean synchronized Mac main `c8544528ad51a28c344beb26adf27c925e7e346e`
and PR #340 merge/cleanup were already confirmed. The explicit plan was committed
at `451a0845bf96aeca0d0f8af694d2c0a99886a6c4` before executable work.
The actual immutable-cache run and corrected-plot visual review are now complete.
The bounded comparison outcome is qualitative and inconclusive for detailed ESA
trajectory agreement. Final Mac documentation passed 36 cases in 3.76 s and
both reports/reviewed-image identities passed; PR #341 merge/cleanup is confirmed.

### As-is and bounded implementation

The retained principal Orion HIPs are 27989, 24436, 25336, 26727, 26311,
25930 and 27366; Big Dipper HIPs are 54061, 53910, 58001, 59774, 62956,
65378 and 67301. Membership and permitted finite figure edges are checked against
the existing `src/wenu/data/constellations/western/constellationship.fab`.
Only edges with both endpoints in the selected sample are plotted; absent
intermediate vertices are not replaced with invented segments. This is a
fourteen-star diagnostic, not a complete constellation or TGAS background.

The existing spherical-reference test in `tests/test_stellar_state.py` now
also evaluates +60,000/+100,000/+450,000 years with an explicit longer numerical
coverage for all three full/angular/Hip2 cases. Existing short and negative
offsets remain. No production numerical implementation, resource, test owner,
dependency, interface, ordinary chart route or default changes.

A versioned external recipe, `wenu_esa_qualitative_diagnostic_v1.py`, uses the
existing immutable snapshot and actual KernelSession.evaluate calls. It retains
all source objects in admissions, all fourteen selected HIPs and 147
HIP/model/epoch report rows. Available full, Gaia-angular and Hip2 fallback
directions remain separate. The recipe verifies retained solution digests,
SDK identities/times/evidence, per-source-epoch offsets, independent spherical
directions, unavailable-object and warm outside-domain refusals. Each group's
coverage contains all retained input epochs and ends at its latest source
epoch plus that group's largest approved offset. Source epoch labels are read
from the validated source, not inferred from the constellation or filenames.

A global catalogue/domain admission refusal is recorded as global
`admission_refused` rows, not falsely attributed to missing per-star measurements.
It does not drop those HIPs or silently retry a different full model.
Successful remaining admissions can still be reported. Source byte/digest
checks remain mandatory. Domain-dependent catalogue/model bindings are reported
separately from unchanged source-solution digests.

Plots use existing kernel spherical-frame and stereographic services, native
ICRS north-up/east-left axes, separate model panels and shared axes per group.
Projection centres are explicit diagnostic choices, not recovered ESA viewpoints.
Only approved epoch endpoints are queried; dashed connectors join those samples
and do not claim continuously sampled trajectories. Solid figure chords retain
the selected source topology. Raw vectors, times and projected endpoints are
saved for inspection. These diagnostic exports do not activate ordinary atlas
or propagated stellar chart consumers.

Output is outside the repository under
`~/wenu-output/stellar_esa_qualitative_v1`, with JSONL state/gap rows, selected
original source records, summary/admission/SDK/code identities, projection
records, the exact recipe, and PNG/PDF for each group. It refuses to overwrite
that directory; the product-hash completion manifest is written last. An
interrupted/incomplete directory is evidence to inspect, not permission to
overwrite it. The source manifest remains the accepted
`8747349e08f70a428b547f6d0131c47b6f935df73e6b7df9ef6b9d36aba4d365`.

### Reference media and actual qualitative comparison

The [Orion video](https://www.esa.int/ESA_Multimedia/Videos/2017/06/The_future_of_the_Orion_constellation)
was opened in the browser and played. The initial image and a later frame at
player time about 1:02 of 1:12 were inspected; the bright-star pattern visibly
changes. No exact mapping from those player times to scientific epochs was
recovered and no per-star endpoint was measured.

The [Hipparcos stereo page](https://www.cosmos.esa.int/web/hipparcos/stereo-images)
was directly accessible in the browser, despite the earlier HTTP-451 text-fetch
route. Both linked present and +60,000-year colour GIFs were opened and viewed.
Their red/green split and changed pattern are visible. No channel midpoint was
interpreted as barycentric RA/Dec and no stereo depth was measured. Original
inputs, exact epoch conventions and projection/depth recipe remain unresolved.
No reference media was redistributed as a deliverable.

Visual inspection of Fernando's actual v1 plots exposed a diagnostic presentation
fault: with these configured SphericalFrames, `flip_ew=True` puts increasing RA
on the right, despite the east-left caption. A direct RA-centre +/-0.1-degree
check confirms `flip_ew=False` gives increasing RA left and increasing
declination up for both centres. This is a recipe setting/caption error, not a
change to projection semantics or evidence of a numerical propagation failure.
V1 is preserved as the original run, not silently overwritten.

The external `wenu_esa_qualitative_replot_v2.py` reads only manifest-verified
v1 rows. It corrects orientation and assembles complete figures with explicitly
labelled per-HIP diagnostic priority full Gaia, otherwise Gaia angular,
otherwise Hip2 angular fallback. This display selection is not a new production
adoption or a claim of matched source epochs. It selects 49 of the original
147 rows without new propagation. V1 retains all models/gaps. The recipe
checks both centre orientations, input identity and unchanged v1 products,
and saves a separate no-clobber v2 report with completion manifest.
Recipe SHA256:
`1cba67139c46464f5ec0b09fc02ae2871b1c0ac5fcbf1c3ab7ef69047624185a`.

Fernando supplied both corrected PNGs, which were actually inspected.
The labels and geometry now place increasing RA left and native north up.
All seven stars appear in each combined figure. Orion's isolated HIP 24436
is a consequence of retaining only selected source-topology edges; it is not
a missing evaluated star or a reason to invent a replacement connection.
Big Dipper model tags show HIP 59774 full, HIPs 53910/65378 Gaia angular and
the remaining four Hip2 angular. Orion uses Hip2 angular for all seven.

| Comparison | Observed Wenu result | External comparison disposition |
|---|---|---|
| Orion | +10,000-year points nearly coincide at this display scale; +450,000-year endpoints visibly deform the upper figure while the belt/lower stars move less. The actual report gives HIP 27989 displacement 3.715798122 degrees and HIP 25336 1.901875496 degrees at +450,000 years. | Both the viewed ESA sequence and Wenu show an evolving pattern. That broad phenomenon alone does not establish trajectory agreement. ESA's narrative about leaving its field cannot be checked against this different sample/frame; the exact input/epoch/projection mapping is absent. Detailed agreement is **inconclusive**, not passed. |
| Big Dipper | All seven-star figure endpoints are now visible together. At +60,000 years the bowl/handle geometry changes, with displacements about 1.44–2.31 degrees in the selected nominal models. | Consistent only with the broad changing-figure phenomenon visible in the ESA pair. Its nonlinear stereo display, preliminary inputs and unknown exact epoch/model recipe prevent defensible per-star or pixel residuals. Detailed agreement is **inconclusive**, not passed. |

The apparent modest changes do not contradict a measured ESA coordinate table:
no such table was recovered. Do not tune inputs to match the visual products
or infer a universal validity/error bound. This is a completed bounded
qualitative inspection with explicit unresolved comparability; it does not
close K4b.05's source/model/physical qualification or authorize K4b.06.

Uploaded corrected-image SHA256 identities:

- `orion_trajectories_v2.png`:
  `c91b0554e6b4667345c383146aa1c34bfcb092b528a65d84daf50df9f5367f08`.
- `big_dipper_trajectories_v2.png`:
  `175d911839999f8c3a77f8cbecc8ff63ac73d37f5162658524f7313113de9c40`.

These uploaded bytes establish which pictures were reviewed. Their v2
completion-manifest/product linkage is checked separately on the Mac.

### Numerical and acceptance receipts

The closest existing set passed locally: 34 cases, covering the extended
spherical-reference cases and retained finite-perspective/refusal cases.
A deliberately coherent +10,000-year time cap initially triggered the engine's
exact numerical guard. With the same cap injected into that internal checker,
the independent extended spherical oracle failed for full/angular/Hip2; patches
were restored and the 34-case set passed again.

A broader partial-owner probe returned 152 passes/nine subtests, five
deselections and one unchanged application case blocked by missing
`wenu.objects`. It is not a complete passing owner run. No production defect
was inferred. The external recipe's constructed nine-row fixture retained 147
rows, 63 evaluated directions and 84 gaps, exercised 42 refusal checks and
produced four inspected plot exports. Source-solution digests stayed the same
between coverages while model bindings differed. A separate approaching
radial-only trajectory retained 28 explicit global long-domain refusal rows
while shorter-domain/angular results survived. These remain synthetic receipts,
not the actual population.

**Actual Mac, `824f85207cc150ad1b62f6a8e2f995ac8e98d17b`:** 34 focused
cases passed in 9.00 s; 36 documentation cases passed in 5.01 s. The recipe
SHA256 `016bb73bb5eb149bc35fa3b53f6b42df40bd28def1573818e108038e1689aebd`
completed against the accepted immutable source. All source/solution digests,
imported Wenu/SDK identities and final clean synchronized task status passed.
There were 42 unavailable/outside-domain checks and no global admission refusal.

| Group | Full Gaia evaluated/gaps | Gaia angular evaluated/gaps | Hip2 angular evaluated/gaps |
|---|---|---|---|
| Orion, four epochs | 0 / 28 | 0 / 28 | 28 / 0 |
| Big Dipper, three epochs | 3 / 18 | 9 / 12 | 12 / 9 |

Total: 147 rows, 52 evaluated directions, 95 explicit unavailable rows.
Maximum independent spherical chord residual:
`3.188872858294072e-16`; this is a nominal numerical comparison, not
observational accuracy. V1 completion-manifest SHA256:
`0fc40aed93676b40ce55e549677d1635c4d44085ce5b39ab3b22c31e8013dcd4`.
The output is `/Users/fselman/wenu-output/stellar_esa_qualitative_v1`.
Corrected images are in the separate `stellar_esa_qualitative_v2` directory.

The v2 replot's synthetic checks passed explicit F/G/H selection, 49 retained
selected rows, both centre orientations, deliberate wrong-flip detection and
four exports. It does not repeat propagation or alter v1 source/results.

The coordinate guide remains current: native ICRS motion is separate from
date-oriented mean axes, observer reconstruction and physical validity.
Final Mac documentation acceptance passed 36 cases in 3.76 s; the v2 manifest
is `f71a0da16d2f0bb03551d505d999a7cd678a7ff8bf1ec4b8bf5ea6285f97bfe1`.
Both reports and reviewed-image identities passed without repeated propagation.
Numerical execution and supplied-image inspection are complete.
K4b.05 parent, issues #326/#333 and K4b.06 remain open.


## K4b.05 ESA comparison feasibility assessment, 2026-10-26

**Selected scope and base:** Fernando selected the bounded K4b.05 assessment
with “Proceed” and confirmed clean synchronized Mac main
`8a0e3e08437ccce2685ddd2e5c84e00f442d85ff` at
`/Users/fselman/Developer/wenu`. Selection was committed at
`5057fc426c49d2948803d716aa964155a6d128af` before these findings.
This is the versioned repository assessment, not an executed ESA/Wenu comparison.
Orion was assessed first, then Ursa Major. No source cache, runtime, model,
domain, dependency, chart consumer or scientific error policy was changed.

### Primary-source recovery

Sources were checked on 2026-10-26. Directly retrieved ESA pages are distinguished
from search-retrieved ESA text. No video was played, frame measured, stereo
image interpreted, media downloaded/redistributed or author contacted.

| Reference | Recovered evidence | Remaining obstacle |
|---|---|---|
| [Orion story](https://www.esa.int/Science_Exploration/Space_Science/Gaia/The_future_of_the_Orion_constellation), 2017-06-09, directly read | Future interval 450,000 years; field 40 by 20 degrees; TGAS, bright Hipparcos stars and ground observations. Narrative checkpoints include Betelgeuse leaving the field near +100,000 years, Aldebaran crossing its lower part and Hyades crossing diagonally. Stellar birth/death is omitted. | No complete per-star source list, input values, RV selection/default policy, executable recipe, exact starting event/scale or projection specification recovered. Checkpoints are published descriptions, not newly viewed or measured agreement. |
| [Orion video page](https://www.esa.int/ESA_Multimedia/Videos/2017/06/The_future_of_the_Orion_constellation), directly read | Product ID 378614, duration 72 seconds, credit ESA/Gaia/DPAC; links the all-sky product and a speeded-up version. | Page/credits do not supply numerical stellar endpoints. The linked speeded-up page returned HTTP 451. No mapping from player seconds to individual scientific epochs was established. |
| [Linked all-sky animation](https://www.esa.int/ESA_Multimedia/Videos/2017/04/The_motion_of_two_million_stars), directly read | Galactic coordinates, rectangular projection and 750-year frame spacing over five million years. | These are this product's conventions; a link from Orion does not establish identical axes, sampling or projection for Orion. |
| [ESA ESAC method story](https://www.esa.int/About_Us/ESAC/Two_million_stars_on_the_move), 2017-04-21, directly read | All-sky population: 2,057,050 TGAS plus 24,320 bright Hipparcos stars, Tycho-2 appearance. Note 2 specifies 235,966 RV measurements from RAVE, GALAH and APOGEE and linear velocity extrapolation. Initial positions are described as measured during 2014–2015. | Useful new method evidence for the linked product, but no per-star RV assignment, missing-RV rule, exact epoch/scale, numerical outputs or Orion-specific identity equivalence. Do not transfer its population or RV recipe silently to Orion. |
| [Hipparcos stereo page](https://www.cosmos.esa.int/web/hipparcos/stereo-images) | Direct retrieval returned HTTP 451; search retrieval returned ESA text. The Ursa Major section specifies present/+60,000-year illustrations near RA 12 h, Dec +60 degrees, field about 36 by 31 degrees. The associated preliminary 30-month imagery uses nonlinear displayed distances and an approximately two-light-year inter-eye baseline, credited to L. Lindegren and linked to ESA Bulletin 77. | Exact preliminary input solutions, starting epoch/scale, RV handling, projection and nonlinear depth mapping were not recovered. The same page also describes later catalogue-based stereo fields; those must not be substituted for the preliminary Ursa Major pair. Search text is not inspection of the GIFs or original Bulletin article. |

The ESAC story supplies a more specific constant-space-velocity/RV provenance
than the previous assessment. It does not establish which radial inputs were
used for Orion's bright stars, nor that the missing RVs were zero. Its qualitative
statement about useful extrapolation durations is not a per-star physical error
bound for Wenu. The recovered descriptions are external illustrative targets,
not observations of future stellar positions.

### Media-use boundary

The Orion video page offers either CC BY-SA 3.0 IGO or the ESA Standard Licence.
The linked [CC deed](https://creativecommons.org/licenses/by-sa/3.0/igo/)
requires attribution and the applicable ShareAlike conditions for adaptations.
The directly read [ESA media terms](https://www.esa.int/ESA_Multimedia/Terms_and_conditions_of_use_of_images_and_videos_available_on_the_esa_website)
distinguish educational/informational uses, item-specific credits and third-party
rights. This assessment links the products only. It grants no underlying-data
licence and makes no redistribution decision for the Ursa Major images.

### Actual Wenu owners and domain distinction

Inspected unchanged `src/wenu/stellar_state.py`,
`src/wenu/astrometric_coordinates.py` and `tests/test_stellar_state.py` at the
accepted base, together with the existing API/scientific/coordinate contracts.

| Boundary | Actual implementation/evidence | Consequence |
|---|---|---|
| Stellar motion admission | Full and angular adapters require a finite caller-declared TCB TimeSpan, bind that coverage into identity and validate rows over it. Full inputs use the declared reciprocal-parallax and spectroscopic-RV proxy; angular inputs omit radial perspective. | The recent +/-10,000-year comparison is an evidence domain, not a hard-coded universal stellar cutoff. A longer explicit run needs a selected protocol, per-row domain admission and new evidence; silently widening it would change the run's model binding. |
| Long-term mean axes | LongTermFrame enforces finite TT validity inside Julian epochs -198000 through 202000, with an independently explicit TT equinox. | Orion's remote endpoint cannot use this date-oriented mean-axis model. Native ICRS directions require no date-oriented precession; stellar propagation and frame orientation remain separate. |
| Latest real sample | The retained sixteen-HIP receipt contains only three matched full/angular objects, and many bright figure stars lack full Gaia inputs. The accepted report does not contain ESA-matched source inputs. | Do not portray three common models as full Orion/Big Dipper coverage, invent RVs, or treat DR3/Hip2 results as a reconstruction of TGAS/preliminary Hipparcos. |
| Products/graphics | Ordinary stellar chart consumers still use their accepted lookup routes; propagated stellar consumer adoption is K4b.06. | No ordinary wenu_chart request becomes an ESA propagated comparison through this documentation change. Keep a future diagnostic run separate from product adoption. |

A published “years from now” label cannot be silently anchored to a precise
TCB/TT event. Publication date, observing interval and catalogue reference epoch
are different facts. Missing epoch information must stay explicit in any
qualitative comparison. A future native-ICRS protocol could avoid the mean-axis
limit, but would not solve unknown ESA conventions, physical errors or stellar
lifetimes.

### Feasibility and proposed disposition

**Numerical reproduction:** currently blocked for both products by unmatched
input/method/epoch information. No defensible zero-residual or pixel-parity
oracle is available from the reviewed pages. Missing evidence on these pages
does not prove that original numerical material does not exist.

**Qualitative comparison:** feasible in principle, subject to a selected
execution protocol and actual media inspection. For Orion, compare identified
bright-star trajectory directions and relative figure changes with the published
narrative, explicitly separating source-edition and projection differences.
Wenu's HIP-retained sample cannot reproduce the complete TGAS background or
Hyades population. For Ursa Major, compare the seven-star pattern only after
resolving orientation and separating stereo/depth effects; do not infer
barycentric RA/Dec by averaging colour channels with an unknown nonlinear
distance transformation.

**Recommended next bounded selection, proposed only:** a native-ICRS qualitative
diagnostic protocol for the retained Orion and Big Dipper figure stars, preserving
all missing-input statuses and existing source bytes. Agree exact elapsed TCB
sample times and domains first; decide whether to inspect earlier frames within
existing evidence or admit new nominal +60,000/+450,000-year runs. Explicitly
exclude date-oriented Orion axes, physical accuracy claims, new source
acquisition and ordinary chart adoption. Verify actual SDK-state directions,
coverage refusals, immutable input identities and versioned external report
products, then inspect and record real reference media before claiming agreement.

Alternative: continue reference recovery until original inputs and epoch labels
permit numerical reconstruction. No contact, catalogue capture or domain
extension is activated by either proposal. The qualitative route may satisfy an
explicitly agreed illustrative comparison disposition; it cannot silently close
the roadmap's numerical/scientific qualification requirements.

**Assessment exit:** source recoverability, comparison roles and domain choices
are documented. Coordinate meaning is unchanged; the coordinate guide remains
current. K4b.05 parent, issues #326/#333 and K4b.06 remain open. Closest local
documentation checks and complete Mac acceptance are recorded separately; no
ESA residual, visual agreement, numerical endpoint run or physical-error bound
is claimed.

Local verification: four unchanged existing functions in
`tests/test_current_documentation.py` passed by direct stdlib execution:
developer-root authority, documented Python syntax, obsolete-import exclusion
and roadmap diagrams/exit ordering. New assessment/roadmap heading targets and
changed-document whitespace checks passed. This is a partial-checkout receipt,
not the complete 36-case Mac documentation gate; pytest and the full installed
Wenu environment were not available here. No runtime tests were needed for this
documentation-only change. Complete Mac documentation acceptance remains pending.


## K4b.05 finite perspective comparison, 2026-10-25

Fernando selected the previously proposed bounded comparison with "Proceed"
and confirmed clean synchronized Mac main
`2d5e911f336caff7d960c19b2134b67786b0353d`. Roadmap selection preceded
executable work at `d0b805b1823e94b77e83f3dba7f030ff8c97f76b`.

### As-is assessment and comparison method

The existing `stellar_state.py` full and angular admissions share source Gaia
position/PM/epoch facts and the shared affine engine. Full motion uses a positive
reciprocal-parallax distance and spectroscopic-RV proxy; angular motion omits
radial perspective. Existing tests independently verify each against the
spherical no-light-time expression, but did not measure their finite paired
omission effect. No production correction is needed for this comparison.

Let `t` be elapsed TCB Julian years, `mu` the nonnegative total angular PM in
radians per Julian year, and `k` the nominal radial rate `RV * parallax / au`
in reciprocal Julian years with consistent units. Full departure along the
positive PM bearing is `atan2(mu*t, 1+k*t)`; angular departure is
`atan2(mu*t, 1)`. Their signed principal difference can independently be written
`atan2(-mu*k*t*t, 1+k*t+(mu*t)**2)`. This avoids subtracting nearby angles and
keeps the correct branch beyond 90 degrees. Its absolute value is the finite
great-circle separation. The sign is full minus angular along the source's
positive PM bearing, not an RA/Dec offset. No physical accuracy follows.

The new test-only scalar helper lives with the existing spherical oracle in
`tests/test_stellar_state.py`; no new runtime API/report mode or test owner is
introduced. Ten constructed pairs exercise actual SDK sessions at source and
+/-1,000 and +/-10,000 years (100 directions total). They compare unsigned
separation from cross/dot products and signed orientation about the source
motion-plane normal with the scalar expression and retain the separate spherical
vector check. Source-epoch/zero-RV/zero-PM limits, both signs, RA wrap and poles,
strongly nonlinear approach/recession, immutable source/admission data, distinct
model/reference identity and unknown measurement/physical errors are explicit.
One additional SDK seam verifies retained gaps, common-object selection and
unavailable/domain refusal after success.

### Verification and actual Mac cache receipt

All eleven new cases pass locally. Replacing the finite effect with a local
zero-RV derivative and independently dropping full radial motion each caused
seven comparison failures; both faults were restored. The three zero-effect
cases stayed passing as expected. Existing Decimal, spherical, cone, source and
cold-isolation tests are retained, not duplicated. The combined stellar/shared-core/cluster and source-audit run passed 515
cases and nine subtests in 4.25 s, with three unchanged full-application
composition cases deselected because this partial checkout lacks those owners:
`test_catalogue_metadata_controls_kernel_and_all_native_outputs`,
`test_catalogue_source_identity_checked_before_publication` and
`test_cluster_admission_preserves_all_source_rows_masks_and_immutable_metadata`.
The complete Mac receipt below subsequently covers the three unavailable
application-composition cases without exclusions. Four closest documentation
checks and six available tooling cases passed locally; the two repository-wide
tooling selections were subsequently included in the complete Mac tooling run. No full SDK,
installation, catalogue acquisition or product run is repeated for this test-only
change. All 681 relative links and 186 fragments across 38 active documents
resolve against the full GitHub tree and actual Markdown targets.

**Actual Mac verification at `04e27e77a513b95c7ebd54e5a2eef1e66de75499`,
PR #339:** the first focused run passed 344 cases and nine subtests in
12.98 s, failing only the existing `inspect.getsource(mixed_provider)`
cold-isolation check. Its cached code referenced the retired Dropbox checkout,
although the current checkout was `/Users/fselman/Developer/wenu`.
The same unchanged failed case passed alone in 5.22 s using a fresh temporary
`PYTHONPYCACHEPREFIX`. Together these cover all 345 focused cases and nine
subtests, with no exclusions; no single fully passing 345-case run is claimed.
Subsequent complete gates passed 173 source-audit cases in 5.17 s,
36 documentation in 4.24 s and eight tooling cases in 7.910 s.
The task branch was clean and synchronized after the checks and actual report.

**Actual immutable-cache run:** the validated source manifest remained
`8747349e08f70a428b547f6d0131c47b6f935df73e6b7df9ef6b9d36aba4d365`.
All sixteen original sample HIPs remain across 80 HIP/epoch rows at source
and +/-1,000 and +/-10,000 TCB Julian years. Common full/angular availability
is exactly HIP 59774, 87937 and 57939: 15 paired rows, evaluated as 30 SDK
directions. The other 65 rows retain explicit pair gaps. Full availability
is three, with six missing associations, five Gaia position-only solutions
and two missing Gaia RVs. Gaia angular availability is five, with six missing
associations and five position-only solutions; Hip2 fallback availability is
eleven, deferring five entries to available Gaia angular models. Hip2 is not
substituted into any full/angular comparison, and no missing RV is assigned.

Unsigned model separations below are arcseconds. The signed full-minus-angular
departures are positive for every nonzero entry in this actual sample; this is
an observed sample result, not a sign convention imposed on all stars.

| HIP | -1,000 yr | +1,000 yr | -10,000 yr | +10,000 yr |
|---|---:|---:|---:|---:|
| 59774 | 0.0532424820 | 0.0532969137 | 5.2997575499 | 5.3541878164 |
| 87937 | 603.4412779736 | 682.7187802435 | 34000.3377578619 | 93916.8041368476 |
| 57939 | 76.2868680167 | 77.9714977967 | 6292.9785700039 | 7657.1856328879 |

Source-epoch differences round to zero at the displayed precision.
At +10,000 years, the latter two separations are about 26.0880 and 2.1270
degrees. Thus a small local hypothetical-RV derivative is not a substitute for
a finite remote-epoch model comparison. These are differences of two nominal
models with the same captured inputs, not measured physical errors or an
inferred universal angular-model lookback limit.

Maximum unsigned separation and signed-departure residuals against the
independent scalar expression are both `1.6653345369377348e-16` rad.
The maximum separate spherical-reference vector-chord residual is
`8.959779580913775e-16`. All are below the conditioned `5e-14`
reference threshold; measurement and physical-model evidence remain unknown.

The recipe verified unchanged on-disk source bytes, detached admission records,
imported implementation/SDK identities against the tested checkout and all three
accepted solution digests:

- Full Gaia SI: `032f76e398eadf136fd9aa59a3c2b3a66d4dc25d9da74bc995b4bdb6088cfe8f`.
- Gaia angular: `6d3e46ff0aa8bd707ea4b8f169b55fdd41c3bc85d65250d7a801c541ebb38602`.
- Hip2 angular: `b5b6cfe20919eec5c815f50b348b55579e2b2631e8f0510be201d874e85875c1`.

The no-clobber report is outside the repository at
`~/wenu-output/stellar_perspective_comparison_v1`. Products are
`perspective_rows_v1.jsonl`, `perspective_sources_v1.json`,
`perspective_summary_v1.json` and `perspective_recipe_v1.py`;
`perspective_manifest_v1.json` was written last. Completion-manifest SHA256:
`f446893384eda80257fb77c54e0fb3e96b4a3be8044e83caad2b50f0540b8533`.
Executed versioned recipe SHA256:
`c1d254c68e6f6803ca332d912d217d99c4b37748ffe15e3e6449d8966146fbde`.
The receipt ended `CACHED PERSPECTIVE COMPARISON COMPLETE` and
`source_and_models_unchanged=true`.

Before handoff, a separate explicitly synthetic recipe run verified 45
constructed HIP/epoch rows (ten pairs, 35 gaps), product hashes and no-clobber;
wrong source-manifest identity, changed solution identity and a deliberately
wrong independent reference each refused before publication. Those synthetic
publication checks are distinct from the actual 80-row Mac receipt.
Only final documentation-receipt acceptance and PR review remain for this
bounded comparison; no parent closure or subsequent runtime task is implied.

Source and production model identities, coordinate guide, source map and API
reference remain current and unchanged. The earlier closure matrix below remains
historical evidence for the parent; its proposed finite comparison is now
selected by the dated roadmap section. ESA execution, physical epoch/error
qualification, binaries, issues #326/#333, K4b.05 parent closure and K4b.06
adoption remain separate. No acquisition, new physical model, policy, dependency,
package, default or consumer change is part of this slice.

## K4b.05 bounded closure review, 2026-10-24

**Historical review:** subsequent PR #339/#341/#342 comparisons supersede this
section's next-gate and comparison-pending statements. Use the
[current qualification matrix](#k4b05-qualification-review-after-reference-comparisons-2026-10-26)
for present decisions; the dated original evidence below is retained.

**Decision:** K4b.05 remains open. Its completed bounded numerical and diagnostic
deliverables are accepted evidence; they do not collectively certify physical
ancient positions or complete the separately requested ESA comparisons.

Fernando selected this documentation/assessment review with "Proceed" after
PR #337 merge/cleanup and clean synchronized Mac main
`3506bb2309d29ae3be6f443f9debeb4843e13cc5`, with 36 documentation tests
in 3.17 s. The review plan preceded these findings at
`45ab8a8cd12dd2a6db8693b1dfab84a92252e883`. This review does not select a
new implementation, error policy, physical model, catalogue acquisition,
source/issue closure or K4b.06 adoption.

### Basis and meaning of completion

The [roadmap ledger](kernel_roadmap_v0.9.5.md)
is reconciled against the [scientific contracts](scientific_contracts.md),
current source/test owners and the dated receipts below. "Completed" describes
a bounded accepted deliverable; "still required" describes an outstanding
agreed comparison or parent-level qualification/disposition; "unresolved"
describes evidence that the current work has not established. It does not
silently require implementation of every omitted effect.

The actual owners inspected at the pinned base are `stellar_state.py`,
`astrometric_state.py`, their existing test owners, and the documented offline
audit interfaces. The two production owners and stellar test owner have the
same Git blobs as the accepted PR #330 tested commit `5da8220f`.
Their accepted numerical evidence can therefore be cited for those same
owners without pretending that this documentation review reran their science.
The GitHub PR records for #325/#327/#328/#330/#331/#332/#334/#335/#336/#337
confirm their merges. Issues #326 and #333 are still open. Dated assessment
proposals below remain provenance, not an active implementation queue.

### Requirement and evidence table

| Existing obligation | Completed bounded evidence | What remains / classification |
|---|---|---|
| Matched nominal stellar propagation against an independent mathematical expression | [PR #330 receipt](#k4b05-no-light-time-reference-implementation-2026-10-23): 147 synthetic SDK directions plus 133 actual cached-source directions, independent spherical no-light-time expression, two detected coherent motion faults, unchanged identities | **Completed** for the adopted no-light-time arithmetic and tested samples. Independence is mathematical implementation, not a separate physical model or ESA reproduction |
| Time/calendar and long-term axes as prerequisites | K4b.03 PR #327 and K4b.04 PR #328 retain source/input/evaluation/equinox labels; explicit calendar conversion receipts and separate mean-frame orientation | **Completed** bounded prerequisite slices. Ancient observer/time realization and physical frame error are not thereby qualified; those limits are not duplicate K4b.05 implementations |
| Gaia conditional measurement uncertainty | [PR #332 receipt](#k4b05-offline-gaia-uncertainty-report-implementation-2026-10-23): 115,105 positive-definite Gaia covariances and 805,735 angular evaluations; independent finite differences/Monte Carlo; explicit marginalization and gap handling | **Completed** offline angular-model conditional report. Full-input RV-covariance independence and total/source/systematic uncertainty remain **unresolved**, not admitted into SDK evidence |
| Missing-RV sensitivity | PR #332 evaluates an explicit derivative about a hypothetical zero-RV anchor; 115,049 rows have a positive-parallax proxy; rows without it retain gaps | **Completed** local sensitivity report. It is not a finite physical interval, an RV prior or a measurement of zero RV. Suitability of neglected perspective for a particular requested chart/error remains **unresolved** |
| Perspective in complete versus angular models | Full SI normalization retains radial perspective with reciprocal-parallax distance and the spectroscopic RV proxy. Both models independently pass the matched oracle; angular motion deliberately omits the radial term | Nominal implementations are **completed**. A finite, matched real-source full-versus-angular omission comparison is not in the accepted population receipts; it is one proposed way to advance the still-required perspective qualification, not a newly imposed universal prerequisite |
| Hip2 epoch and PM-rate convention | [PR #336 source review](#k4b05-hipparcos-2-time-convention-assessment-2026-10-24) and [PR #337 population receipt](#k4b05-real-cache-hip2-time-convention-sensitivity-2026-10-24): all 2,850 fallback models, separate epoch/rate/combined scenarios, source/model identity preserved | **Completed** assessments; the actual 2007 epoch/rate declaration remains **unresolved** in issue #326. A small hypothetical effect does not verify a source fact or mandate a production conversion |
| Hip2 covariance | [PR #334 diagnostic receipt](#k4b05-hipparcos-2-covariance-qualification-2026-10-23): 2,682 standard fallback reconstructions and 168 nonstandard gaps; [PR #335 precision assessment](#k4b05-hipparcos-2-source-precision-investigation-2026-10-23) does not explain the large mismatches by ordinary printed precision | **Completed** diagnostic/precision work. Covariance admission remains **unresolved** in issue #333; raw matrix inversion and empirical agreement bins are not physical/source qualification |
| Binaries, photocentres, acceleration and stochastic/VIM solutions | Original identities and flags remain; PR #337 explicitly counts nonstandard suffixes. Current full/angular providers contain no orbit, systemic-velocity correction or Galactic acceleration model | Preservation/disclosure is **completed**. Physical binary/acceleration errors and useful lookback domains remain **unresolved**; no default flag veto, long-term acceleration polynomial or new orbit model is selected |
| Missing inputs and retained membership | 97,710 full Gaia models, 115,105 Gaia angular models, 2,850 Hip2 fallback models; all 118,218 HIPs retained. Missing PM or unsupported capability refuses rather than acquiring a zero measurement | **Completed** for the admitted model families and their refusals. The 263 original lookup-only entries remain unavailable for these motion admissions. No-PM approximation is pending K4b.02/AX.13 scope, not silently added as a new K4b.05 prerequisite |
| Epoch domains, numerical error and reuse | Current core checks explicit finite same-scale coverage and singular trajectories; exact admitted-coefficient numerical/cone checks and SDK refusal/conformance evidence remain applicable | **Completed** computational guards for the declared nominal model. Measurement/model/date/frame error and a physical-validity interval remain **unresolved**. A finite domain or angular reuse tolerance is not a total physical accuracy guarantee |
| ESA Orion and Ursa Major | [Existing reference assessment](#k4b05-reference-and-method-assessment-2026-10-23) identifies published products, source/projection/epoch gaps and qualitative versus numerical roles | Actual comparison is **still required** by the agreed roadmap. No numerical reconstruction, measured-frame comparison or qualitative agreement was executed in the accepted receipts. Original per-star inputs, exact conventions and Ursa Major stereo viewpoint remain **unresolved** |

The numerical model counts above are overlapping capability populations, not
numbers to add. Complete-input Gaia models also have angular inputs. Hip2
fallback follows actual Gaia angular availability, not the older
preferred-input inventory. Unknown uncertainty channels remain unknown even
for stars that have a nominal state.

### What currently prevents parent closure

There is no accepted execution receipt for the requested ESA comparison.
The reference assessment is complete but is not that comparison. Missing
original inputs/conventions may prevent a numerical reproduction; the roadmap
allows an explicitly qualitative comparison when reference precision does not
support a numerical angular test. No comparison outcome may be invented from
the existence of an ESA illustration.

Perspective, binary/missing-input limitations and physical epoch domains
also need an explicit parent-level disposition for the intended use. The
existing contracts already permit nominal angular calculations with unknown
physical error; they do not demand that every unknown be replaced with a new
model. This review neither revokes that accepted capability nor approves
a physical-accuracy claim. A future closure decision must say which claims
are supported, which limitations Fernando accepts for a bounded use, and
which requested capabilities remain unavailable.

Issues #326/#333 block verification of their respective source-time and
covariance claims. They are not an automatic veto of every already accepted
nominal direction or published identity. Conversely, retaining those issues
does not automatically close the broader physical qualification. A new
conversion, corrected covariance, error prior, binary exclusion or physical
lookback threshold would require separate explicit agreement.

### Recommended next bounded gate — proposed, not selected

**Candidate:** finite perspective-omission comparison on matched existing
Gaia inputs, within K4b.05. This is a practical next qualification because the
accepted RV report supplies a local derivative, whereas a finite full-versus-
angular model difference can be strongly nonlinear at remote epochs.
The comparison uses the two already accepted models; it introduces no physics
or new source and does not claim that either model is physical ground truth.

Proposed first scope: the existing sixteen-HIP review set in the PR #330
receipt, retaining every member and actual availability. That receipt gives
three common full/angle inputs (HIP 59774, 87937 and 57939); the remaining
members must keep their explicit full-model gaps, not receive invented RV.
Recheck availability from the same manifest-bound snapshot before running.
Evaluate both models through the actual SDK at their matched native source
epoch and elapsed +/-1,000 and +/-10,000 TCB Julian years, inside the
intersection of their explicit domains. Compare finite native ICRS direction
separations and an independently expressed no-light-time departure difference.
Keep source, model/reference and all accepted solution digests intact.
Report each star, sign, epoch and missing-input reason; no population-wide
statistics or error prior follows from this small, RV-selected sample.

Proposed acceptance uses the existing stellar/shared-core and source-audit
owners only if executable checks change: source-epoch agreement, matched
zero-RV mathematical limit (explicitly synthetic), finite nonzero-RV cases
of both signs and near-pole/wrap cases, source/model identity, domain/refusal
and actual SDK return paths. Preserve the existing Decimal, spherical oracle,
cold-isolation and numerical cone tests; do not repeat them in a new owner.
A failure of the independent finite-model comparison must not be hidden
by tuning source parameters or by comparing a derivative as a global bound.
The separate Mac cache receipt and documentation gate remain necessary.
This review does not implement or authorize that candidate.

**Alternative next selection:** execute the agreed ESA comparison track first.
It needs original input/method recovery for a numerical reproduction, or a
clearly labelled qualitative procedure that discloses unmatched newer sources,
epochs and the enhanced-depth stereo view. Its published +60,000-year Ursa
Major and +450,000-year Orion endpoints cannot silently enlarge existing
admissions; Orion also exceeds the admitted +/-200,000-year mean-axis range.
Any extended nominal coverage must be proposed and agreed for that comparison,
not inferred from a future animation or from a passing short-domain test.
No ESA download, contact, numerical run or visual agreement is claimed here.

### Boundaries and exit from this review

Measured workloads, propagated-ID chart/figure/label integration and ancient
product specimens remain K4b.06. Observer/horizon reconstruction, new
light-time or gravitational/binary models, and source acquisition are not
selected by this review. K5 reconciliation/freeze and package extraction keep
their existing dependencies. A proposal above is not a new hidden queue or
permission to reorder those milestones.

The source map, implementation reference, coordinate guide and existing
test selections remain current: this review changes no runtime meaning.
It records PR #337's completed merge/Mac cleanup receipt, corrects stale
active PR #330 merge status, and supplies this evidence matrix plus the
next-gate proposal. Four focused current-documentation checks passed locally:
developer-root/index authority, documented Python syntax, absence of obsolete
public-import recommendations, and roadmap diagrams/ordered gates. All 177
relative link paths and 116 active fragments in the four changed documents
resolve against the actual remote tree and loaded targets. No unavailable
archive, source-inventory or installed-import gate is claimed passing here;
Fernando subsequently ran the complete Mac documentation gate at
`c4f131a6c8d031dafbc0d508b1eaa96c0451ae10`: all 36 tests passed in
3.56 s. The task working tree was clean and synchronized, and the diff check
passed. Background Git auto-packing separately reported bad refs for
conflict-named files under `.git/logs`; this receipt does not establish local
Git metadata integrity or resolve those errors. PR #338 was subsequently merged at `2d5e911f`; K4b.05 remains open.


## K4b.05 real-cache Hip2 time-convention sensitivity, 2026-10-24

Fernando selected this bounded assessment with "Proceed" after PR #336
merge/cleanup and confirmed clean synchronized Mac main
`69af07bc01cd852d0674efcf6a29b20b5e0d50ee`, with 36 documentation tests
in 3.65 s. The plan preceded population execution at
`940c4a9b4e768d6c095f0fefd16af70843eff83a`. The actual Mac receipt below
was supplied by Fernando at that commit. This is an offline assessment,
not a production report mode or a catalogue/model correction.

### Source and result identity

The existing `load_stellar_enrichment` validator admitted source manifest SHA256
`8747349e08f70a428b547f6d0131c47b6f935df73e6b7df9ef6b9d36aba4d365`
from `~/.cache/wenu/stellar/stellar_enrichment_source_v1`.
The existing `admit_stellar_hipparcos2_motion` used the explicit
`nominal-tcb-deferred-qualification` policy and a finite domain extending
50,001 nominal Julian years either side of the native epoch. Its angular
solution digest was
`b5b6cfe20919eec5c815f50b348b55579e2b2631e8f0510be201d874e85875c1`.

The actual run retained all 118,218 HIP statuses: 115,105
`gaia_angular_model_available`, 2,850 `hip2_angular_fallback` and
263 `no_hipparcos2_source`. It independently rechecked source-file hashes
against the in-memory validated bytes and compared the unchanged admission
record before publishing. The two imported implementation owners were
byte-compared with the checkout and their paths/hashes recorded.
The receipt reports `source_and_model_unchanged=true`.

Outputs under `~/wenu-output/hip2_fallback_time_sensitivity_v2` are
`hip2_time_rows_v2.jsonl`, `hip2_time_summary_v2.json` and
`hip2_time_manifest_v2.json`. The last hashes the two products and was
published last, after exclusive output-directory creation. Existing output
refuses rather than being overwritten. Completion-manifest SHA256:
`33ad58dd31db937af767ec664ab6be17a6e4137a9be9d2ba5bc77885c1c2d839`.
Executed scratch assessment code SHA256:
`204c154e116cef31559b49d8e85da12ceb5a7a82597eccbc0ffde71fb9c5be83`.
The script and outputs are outside the repository; the report retains code,
source, field-reference, implementation and admission provenance.

### Method and checked representation

Use the [previous assessment's hypothetical TDB/TCB convention](#k4b05-hipparcos-2-time-convention-assessment-2026-10-24),
not a newly inferred Hip2 time scale. The native source epoch remains
J1991.25 with null source scale. The defining TDB/TCB relation gives an
epoch-label shift of approximately 6.972352471684277 seconds; the distinct
rate factor is 1-L, L=1.550519768e-8. Neither supplies an ancient TT conversion.

For each admitted direction u and native tangent v expressed per Julian
year, nominal time coefficient T is compared with T+d, where Y=31557600:

- Epoch only: d=-delta0/Y.
- Rate only: d=-L*T.
- Combined: d=-L*T-(1-L)*delta0/Y.

Evaluate nominal-minus-scenario angle stably as

`atan2(-d*norm(cross(u,v)), dot(u,u)+(2*T+d)*dot(u,v)+T*(T+d)*dot(v,v))`.

This cross/dot factorization avoids subtracting nearly identical directions
and preserves the actual admitted vector components. Signed results follow
increasing native proper motion; report percentiles use absolute differences
in mas with nearest rank ceil(p*N/100), N=2,850. The complete rows retain all
statuses and each fallback's nine offsets/three signed scenarios; summary
records absolute 50th/90th/95th/99th/100th percentiles and top-ten HIP identities
with original source flags. Equal maxima use ascending numeric HIP as the
deterministic tie-breaker. At T=0 every rate-only value is zero, so its printed
HIP 25 is a tie-break result, not a distinguished physical outlier.

F2 is not a parsed enrichment-snapshot column. Version 2 reads it from
`original_record_ascii` using the existing
[field reference](data/hipparcos2_covariance_reference_v1.json), after checking
source edition, record length and original-row SHA256. Blank F2 is explicitly
missing; it is not used in the angular sensitivity calculation. Sn/So/Nc
and original-record identity are retained. The first scratch attempt stopped
on that representation mismatch before publication; v2 corrects only the
assessment extraction, not the source or production codec.

The extraction was verified locally against all 117,955 records of the
already cached raw table after its accepted
`c45d6325bd59dd691764af173a9702e543804a2b6c1d9fea59210e8332e50a4a`
SHA256 check, recovering 77 stored F2=99 rows. Missing-F2 status and corrupted
record refusal checks passed. There was no new source acquisition.
The v2 numerical formula passed 108 independent 80-digit Decimal cases with
maximum difference 1.0765026228421702e-24 rad (check tolerance 1e-23), and
2,700 rotated-vector checks with maximum difference
2.2944893655590035e-16 rad (check tolerance 6e-16). These numerical thresholds
check the scratch calculation, not physical catalogue accuracy.

### Actual population results

All offsets are elapsed nominal TCB Julian years from the source label.
Offsets +25/+35 are representative modern labels, not exact civil instants.

Combined hypothetical convention difference, absolute mas:

| T (years) | Median | 90th percentile | 99th percentile | Maximum | Maximum HIP |
|---|---:|---:|---:|---:|---:|
| -50,000 | 0.02514847674 | 0.1435452893 | 0.6939088434 | 1.589658086 | 71683 |
| -10,000 | 0.005024258509 | 0.02873203186 | 0.1455482105 | 0.8320356524 | 67593 |
| -1,000 | 0.0004959745096 | 0.002836530514 | 0.01439756353 | 0.08855601333 | 67593 |
| 0 | 0.000007169525125 | 0.00004100330230 | 0.0002081273169 | 0.001281126932 | 67593 |
| +25 | 0.00001974812630 | 0.0001129417050 | 0.0005732770880 | 0.003528803306 | 67593 |
| +35 | 0.00002477956677 | 0.0001417170661 | 0.0007193369886 | 0.004427872010 | 67593 |
| +1,000 | 0.0005103135595 | 0.002918537052 | 0.01481380949 | 0.09111624388 | 67593 |
| +10,000 | 0.005038597524 | 0.02881403182 | 0.1459635987 | 0.8344102459 | 67593 |
| +50,000 | 0.02516281491 | 0.1436271302 | 0.6943044689 | 1.590564415 | 71683 |

Separate component maxima, absolute mas:

| Absolute T (years) | Epoch-only maximum | Rate-only maximum | Maximum HIP |
|---|---:|---:|---:|
| 0 | 0.001281126952 | 0 | 67593 (epoch only) |
| 25 | 0.001281126319 | 0.002247677007 | 67593 |
| 35 | 0.001281125712 | 0.003146746318 | 67593 |
| 1,000 | 0.001280115297 | 0.08983612861 | 67593 |
| 10,000 | 0.001187296757 | 0.8332229491 | 67593 |
| 50,000 | 0.0004531641675 | 1.590111250 | 71683 |

At matching positive/negative remote offsets the separately printed component
maxima agree to the supplied receipt precision. Their combined effects are
smaller in the past because signed epoch and rate contributions partly cancel;
this is not a symmetry of every physical-motion uncertainty. In this tested
grid the largest combined effect is 1.590564415 mas (0.001590564415 arcsec)
at +50,000 years. The +35-year maximum is 0.004427872010 mas, or
4.427872010 microarcsec. These numbers quantify the declared convention
scenario only; they do not bound unknown source/model errors.

Fallback solution suffixes remain explicit: 5:2,682; 1:87; 7:76; 3:3;
0:1; 9:1. The 168 nonstandard solutions retain their accepted nominal angular
inputs and original flags; this assessment admits no binary/acceleration/VIM
model, covariance or physical long-term validity for them.

### Disposition and acceptance

The actual population calculation and unchanged-source/model checks are
complete. Issues #326/#333 remain open: this supplies neither source-level
time-convention clarification nor a remedy for covariance discrepancies.
K4b.05 parent qualification, ESA comparisons and K4b.06 consumer adoption remain
separate. No production files, tests, dependencies, sources or default models
change. The coordinate guide, scientific limits and implementation reference
remain current. Complete Mac documentation acceptance at
`0384833f5bc37aaa62887b9a093d3ec63d33e645` passed all 36 tests in 3.58 s;
clean synchronized task branch and diff checks are confirmed. The bounded
assessment's acceptance gate is complete. PR #337 is merged at `3506bb23`;
clean synchronized Mac main, local/remote branch cleanup and 36 documentation
tests in 3.17 s are confirmed. Issues #326/#333 and K4b.05 parent remain open.


## K4b.05 Hipparcos-2 time-convention assessment, 2026-10-24

Fernando selected this issue #326 assessment with "Proceed" after confirming
clean synchronized Mac main `bd7b9cb09539f3c9bed43bca40e53f66a8904e7f`.
The bounded plan was committed first at
`46e47c8d3e436f7fd05ec509dd67e63007f23b71`.
This is documentation and synthetic sensitivity analysis. It changes no
source bytes, model identities, production provider, SDK, dependency, default
or uncertainty admission.

### As-is ownership and source evidence

`src/wenu/stellar_state.py::_admit_hipparcos2_fallback` reads the source's
J1991.25 value while requiring its epoch scale to remain null. The separately
explicit `nominal-tcb-deferred-qualification` policy assigns the numerical
epoch and proper-motion rates to the nominal TCB axis. The same owner converts
mas per Julian year using 365.25 times 86400 coordinate seconds, then delegates
to the normalized-tangent engine. No physical TT-to-TCB conversion is performed.
The record retains the null source scale and unknown time-convention error.
Gaia angular inputs take precedence. These implementation facts are unchanged.

Primary-source review on 2026-10-24:

- [Corrected CDS I/311 ReadMe](https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/I/311?format=html&tex=true):
  RArad/DErad specify ICRS and Ep=1991.25; pmRA/pmDE specify mas/yr.
  Neither field layout explicitly names the epoch scale or the differentiation
  time scale. The 2008 correction history does not supply that declaration.
- [HEASARC Hipparcos new catalogue](https://heasarc.gsfc.nasa.gov/w3browse/all/hipnewcat.html):
  specifies epoch 1991.25 and proper motions per Julian year, without naming
  TT/TCB/TDB for those quantities. A Julian year's duration alone does not
  select a coordinate time scale.
- [van Leeuwen (2007), validation paper](https://arxiv.org/html/0708.1752v1):
  explains the re-reduction and refers detailed methods to the book; no explicit
  epoch/rate scale declaration was identified in the inspected article.
- [Book chapter 2, Hipparcos Astrometry](https://doi.org/10.1007/978-1-4020-6342-8_2):
  the publisher provides a subscription preview, and its accessible
  [two-page excerpt](https://page-one.springer.com/pdf/preview/10.1007/978-1-4020-6342-8_2)
  contains no identified time-scale declaration. The full chapter was not read.
  The [ESA DR1 external-catalogue page](https://gea.esac.esa.int/archive/documentation/GDR1/datamodel/Ch4/hipparcos_newreduction.html)
  returned HTTP 503; the original ESA volume-1 PDF returned HTTP 451.
- [HEASARC original 1997 catalogue](https://heasarc.gsfc.nasa.gov/W3Browse/catalog/hipparcos.html),
  RA_Deg/Dec_Deg, explicitly gives JD 2448349.0625 TT. This establishes the
  original edition's epoch statement, not the new reduction's rate convention.
  Reprocessing the same observations is not proof that every convention remained
  identical. No 1997/2007 numerical comparison was executed.
- [IAU 2006 Resolution B3](https://doi.org/10.1017/S1743921308023648),
  English resolution on printed pp. 41-42, defines the exact linear TDB/TCB
  relation. The [IAU NSFA defining-constants table](https://iau-a3.gitlab.io/NSFA/NSFA_fixed)
  independently transcribes the constants. These define time-scale conversion;
  they do not establish Hip2's published choice.

The accessible evidence therefore does not resolve issue #326. Neither the
word ICRS nor a barycentric origin determines the catalogue's time convention.
The accepted nominal policy must not be relabelled verified metadata.

### Separate epoch and rate sensitivities

Use an explicitly hypothetical TDB source convention to obtain an exact,
reproducible comparison with TCB; TDB's close modern relationship to TT motivates
this sensitivity example but does not make TT and TDB identical. This is not
an adopted interpretation of Hip2.

Let Y=31557600 seconds per Julian year, L=1.550519768e-8,
T0=2443144.5003725 and TDB0=-0.0000655 seconds. IAU B3 gives

`TDB = TCB - L*(JD_TCB-T0)*86400 + TDB0`.

The numerical Julian-epoch label J1991.25 is JD 2448349.0625. If that label
denotes a TDB event, its TCB label is later by

`delta0 = (L*(2448349.0625-T0)*86400 - TDB0)/(1-L)`

= 6.972352471684277 seconds. This is an epoch-label offset. The exact rate
relation is `dTDB/dTCB=1-L`, corresponding to 0.489306826306368 seconds
of elapsed-label difference per TCB Julian year. A proper motion expressed
per TDB Julian year becomes `mu_TCB=(1-L)*mu_TDB`. Keeping the original
number while changing the rate axis would be a distinct convention error.

TT/TCB conversion additionally requires the TT/TDB relation and its realization.
B3's modern millisecond-scale TT/TDB statement is not a validated
+/-50,000-year TT conversion. No ancient TT-to-TCB ephemeris calculation or
physical-error bound is inferred from this linear TDB example.

For the existing angular model choose synthetic orthogonal unit vectors u,e
and mu in radians per source Julian year. With T elapsed TCB Julian years
from the numerical nominal epoch, the nominal direction is
`normalize(u + mu*T*e)`. Compare the following tangent coefficients separately:

- Epoch-only: `mu*(T-delta0/Y)`; hold the rate number unchanged.
- Rate-only: `mu*(1-L)*T`; hold the epoch event unchanged.
- Combined hypothetical TDB interpretation: `mu*(1-L)*(T-delta0/Y)`.

For coefficients x,y, signed angular difference is
`atan(x)-atan(y)`. The local rate sensitivity is approximately
`mu*L*T/(1+(mu*T)^2)`; the epoch effect is approximately
`mu*delta0/Y/(1+(mu*T)^2)`. Thus linear `mu*L*T` alone overstates
the angular difference when the accumulated tangent displacement is large.
Opposite-time signs can cancel the two effects; unsigned columns cannot be
added as a general rule.

Executed synthetic positive-time examples, absolute differences in mas:

| PM (arcsec/year) | T (TCB Julian years) | Epoch only | Rate only | Combined |
|---|---:|---:|---:|---:|
| 1 | 0 | 0.000220941 | 0 | 0.000220941 |
| 1 | 35 | 0.000220941 | 0.000542682 | 0.000763622 |
| 1 | 1,000 | 0.000220935 | 0.0155048 | 0.0157258 |
| 1 | 10,000 | 0.000220422 | 0.154688 | 0.154909 |
| 1 | 50,000 | 0.000208678 | 0.732233 | 0.732442 |
| 10 | 0 | 0.00220941 | 0 | 0.00220941 |
| 10 | 35 | 0.00220940 | 0.00542680 | 0.00763620 |
| 10 | 1,000 | 0.00220422 | 0.154688 | 0.156893 |
| 10 | 10,000 | 0.00178893 | 1.25544 | 1.25723 |
| 10 | 50,000 | 0.000321316 | 1.12747 | 1.12779 |

These are parameter sensitivities within the unchanged angular approximation,
not total physical errors, source uncertainties, universal upper bounds or a
precision certificate. Perspective, binary/accelerated motion and uncertain
source parameters retain their previous limits.

### Reproducibility, verification and disposition

A scratch-only probe used Python 3.12.14, 80-digit Decimal arithmetic and
an independent binary64 normalized-vector cross/dot angle. It evaluated all
three cases for PM=0,0.1,1,10 arcsec/year at
T=-50000,-10000,-1000,-100,0,35,100,1000,10000,50000 years (120 comparisons).
Decimal atan used the half-angle identity
`atan(x)=2*atan(x/(1+sqrt(1+x*x)))` and an alternating Taylor series
terminated below 1e-85 in the reduced argument. Fraction arithmetic independently
checked delta0. The maximum Decimal/vector difference was
4.356127989456561e-17 rad, below the declared 5e-16 numerical check tolerance.
This tolerance checks calculation agreement, not source/physical accuracy.

Installed ERFA 2.0.1.5 `tdbtcb(2448349,0.0625)` gives
6.972352471683951 seconds, agreeing with the defining-constant calculation
within 1e-10 seconds. This is a reference-library check of the TDB conversion,
not an independent physical time realization. Probe SHA256:
`2d9787096cd17a18aa7499ea40abc9a6fa5a93b813ee3060d39bb5cd1b94688c`.
The equations, grid and algorithms above specify the reproducible experiment;
the scratch probe is not a new production tool or a catalogue fixture.

No complete manifest-bound Gaia/Hip2 enrichment snapshot was available in this
assessment checkout. No fallback-population percentiles or individual fallback
corrections are claimed. Previously accepted 2,850 fallback entries are not
silently substituted with the full raw Hip2 population. No catalogue acquisition,
annex capture, source mutation or author contact occurred.

Issue #326 stays open: explicit source-level evidence for both epoch and rate
conventions is still needed. A later conversion would require its own agreed
model/resource identity and independent acceptance. Issue #333, K4b.05 parent
qualification and K4b.06 consumer adoption remain open. The source map,
implementation reference, architecture and existing test selection remain
current; the coordinate guide and scientific limits link this assessment.
Four focused current-documentation checks passed in the partial assessment
checkout: developer-root/index authority, documented-Python syntax, obsolete
public-import recommendations and roadmap diagrams/ordered exit gates. All
four new assessment links resolve to the actual audit heading. Fernando's
complete Mac documentation gate at `bfa904a2b7d2259bdd4cf32ac38e67f78e8fbb42`
passed all 36 tests in 4.61 s, including installation/import and archive/inventory
coverage. Clean synchronized task branch and diff checks are confirmed.
This closes the bounded assessment's test gate, not issue #326 or the K4b.05
parent. PR #336 awaits explicit merge authorization.

## K4b.05 Hipparcos-2 source precision investigation, 2026-10-23

Fernando selected this assessment with “Proceed” after PR #334 merge and
confirmed clean synchronized Mac main `ffa7d7a7`, branch cleanup and
36 documentation tests in 3.11 s. The revision-93 plan was committed first at
`9f806edc67a0130c61744e8695ee70471fe6f686`.
This assessment changes documentation only. Architecture, source map, coordinate
guide, diagnostic implementation, passive reference, all source bytes,
production models and tests remain current and unchanged.

### Primary-source findings

The [corrected CDS I/311 ReadMe](https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/I/311?format=html&tex=true)
specifies F2 as F5.2, the five formal errors as F6.2 and the fifteen UW fields
as F7.2. It records replacement files on 16 September 2008 after earlier errors
in goodness-of-fit values. It does not define 99 as a saturation flag.
The format itself can represent 99.99; field width alone does not establish
a cap at 99.00.

[Michalik et al. (2014), Appendix B, equations 34–40](https://arxiv.org/html/1407.4025v2#A2)
describes the CDS-specific diagonal scaling and correction to published
standard errors. Reinspection agrees with the implemented published-error
recipe. Its separate catalogue-combination policy is not a repair for these
discrepancies. No replacement convention was found.

[van Leeuwen (2007), sections 2.4–2.7](https://arxiv.org/html/0708.1752v1)
discusses transit errors, calibration and special cases, but supplies no
identified explanation of this exact stored-F2 pattern.
[Brandt, Michalik & Brandt (2023)](https://doi.org/10.1093/rasti/rzad011)
independently discusses Hip2 overfitting and recalibrated IAD/parameter errors.
That is a separate physical/statistical limitation: it does not establish
that our particular UW-diagonal mismatches are caused by overfitting, nor
authorize replacement data or an empirical correction.
The ESA overview returned HTTP 451; it was not directly read. Searches found
no verified primary statement that F2=99 is clipping. Author clarification,
if desired, would be a separate explicitly authorized contact.

### Read-only precision experiment

The already cached raw `hip2.dat` is 32,673,535 bytes, SHA256
`c45d6325bd59dd691764af173a9702e543804a2b6c1d9fea59210e8332e50a4a`.
No catalogue, annex or intermediate data were acquired. NumPy 2.3.5 was used.
A scratch-only exploratory probe (SHA256
`2085ced9b00c0413608db52cdea7a89bd6ba267404531f95ef1875b95b611096`)
read all 115,112 Sn-suffix-5 rows. It independently reproduced the accepted
all-standard-source discrepancy bins 537/153/51/6 above 1%/2%/10%/100%.
These are not the Mac fallback-only bins 68/44/22/5.

For reproducibility, let D contain the printed formal errors, B be the
published-error triangular factor, and T=B D. Then
T diagonal entries are the raw packed diagonal weights; off-diagonal entry
(i,j) is raw UW(i,j) times sigma(j) divided by u. With X=inverse(T), each
decoded-to-quoted sigma ratio is the Euclidean norm of row i of X.
This equivalent dimensionless calculation preserves the dependence on printed
errors without mistaking mixed mas/year conditioning for physical accuracy.

For each printed UW, error and F2, assign an exploratory interval centred on
the stored value, with common half-width h; keep Ntr and solution type exact.
Calculate positive u endpoints from F2 endpoints using the existing
Wilson–Hilferty inverse. Form T entry intervals using interval multiplication
and positive division. Compute triangular inverse intervals by back substitution:
X(ii)=1/T(ii), and X(ij)=-sum(T(ik) X(kj), k=i+1..j)/T(ii).
Bound row norms using the smallest and largest absolute value in each inverse
entry interval, squaring and summing. A zero-crossing entry has minimum zero.
The probe pads arithmetic outward with nextafter and adds 1e-12 at the norm-square
sum. This is exploratory floating-point interval arithmetic, not a formally
certified interval implementation or a statistical confidence interval.

At h=0.005, the cells correspond to a nearest-rounding hypothesis for
two-decimal fields. At h=0.01 they are a deliberately broader symmetric
sensitivity check, also encompassing an error of less than one printed unit.
Neither is an assertion about the producer's actual rounding or clipped values.
Dependency overestimation makes these enclosures permissive: enclosing unity
is necessary for consistency under the assumed cells, not proof that a single
set of inputs reproduces all five errors simultaneously.

| Hypothetical half-width | Rows with some sigma-ratio enclosure excluding 1 | Of those, F2=99 | Of those, other F2 | Above-10% cases still excluding 1 |
|---|---:|---:|---:|---:|
| 0.005 | 238 | 68 | 170 | 51 |
| 0.01 | 101 | 63 | 38 | 51 |

Thus this experiment supplies strong evidence that ordinary decimal precision
does not explain the large discrepancies. It does not claim that every
other row is consistent, or that precision accounts for every small difference.

Illustrative worst-component ratios using the broader h=0.01 cells:

| HIP | Stored F2 | Midpoint ratio | Exploratory ratio enclosure |
|---|---:|---:|---:|
| 71502 | 99.00 | 54.0359 | 43.5143–65.9173 |
| 71681 | 99.00 | 12.1504 | 11.1959–13.3743 |
| 104214 | 19.44 | 1.84942 | 1.69917–2.01048 |
| 26549 | 99.00 | 3.04121 | 2.84369–3.25273 |
| 63081 | 99.00 | 3.03847 | 2.76142–3.34366 |
| 63721 | 99.00 | 2.25163 | 1.98824–2.54330 |

Independent inversion of B-transpose B agrees for these six examples with
relative tolerance 2e-9 and absolute tolerance 1e-10; these are numerical
cross-check tolerances, not source-admission thresholds.
All midpoint ratios and three deterministic random full-catalogue perturbations
per half-width (NumPy default_rng seed 333) stayed inside the enclosures.
These checks test the exploratory calculation; they are not a proof of coverage
or a distribution for physical errors. With UW/errors fixed, changing only F2
by +/-0.005 changes any reconstructed sigma by at most 0.106% in this catalogue.

### F2 pattern, inference and unresolved decision

All-standard-source F2 ranges from -5.12 to 99.00, with 77 entries exactly
99.00. Their descriptive discrepancy counts above 1%/2%/10%/100% are
69/62/40/6. The other 115,035 rows have counts 468/91/11/0.
The largest non-99 examples are HIP 104214 (84.9425%), 88802 (50.1629%),
101453 (24.5227%), 112317 (23.1897%) and 36669 (14.5751%).
These counts are source-wide, not fallback counts.

The pile-up at 99.00, lack of larger stored values and concentration of
extremes there are consistent with a cap or another exceptional encoding,
but do not establish its meaning, the original uncapped values or a valid
replacement u. Ordinary +/-0.005 F2 uncertainty cannot represent an unknown
amount of clipping. Non-99 exceptions require a broader explanation.
Do not fit an effective F2 or renormalize a covariance to force agreement.

[Issue #333](https://github.com/fselman/wenu/issues/333) remains open. This
assessment rules out no published association or Hip2 position/PM input.
All reconstructed Hip2 covariances remain diagnostic-only; the 168 nonstandard
fallback solutions remain separate. A source-level clarification or independently
qualified replacement covariance would be needed before admitting affected
errors. This assessment does not select annex/IAD reprocessing, new acquisition,
physical uncertainty propagation, K4b.06 or a production fallback policy.
Issue #326 and K4b.05 parent remain open.

Verification: raw-source hash, independent six-case inversion, whole-catalogue
baseline reproduction and interval sampling were executed locally. Three closest
documentation checks passed by direct Python invocation; pytest is unavailable
in this runtime. The complete documentation gate and Mac branch review remain
separate acceptance.


## K4b.05 Hipparcos-2 covariance qualification, 2026-10-23

Fernando selected this next slice with “Proceed”, then confirmed clean
synchronized main `5971acb9`, PR #332 branch cleanup and 36 Mac documentation
tests in 3.55 s. The plan was committed before decoder implementation at
`33f158dc980edd2262f3f0e1dac6b28e7110a930`.

As-is: the immutable source preserves the entire corrected 276-byte Hip2
record. The existing maintenance audit/report/test owners are extended.
A new passive reference declares corrected source identities and Ntr/F2 slices;
the acquisition profile is unchanged. Source codec, production providers/SDK,
state/model identities, source bytes, Gaia report mathematics, dependencies,
renderer and defaults are unchanged. Architecture/source-map responsibilities
remain current; the coordinate guide records the source covariance convention.

Primary review: the
[CDS ReadMe](https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/I/311?format=html&tex=true)
defines field order and solution types. The
[Gaia archive's indexed Hip2 description](https://gea.esac.esa.int/archive/documentation/GDR2/Gaia_archive/chap_datamodel/sec_dm_external_catalogues/ssec_dm_hipparcos_newreduction.html)
directs covariance users to
[Michalik et al. 2014, Appendix B](https://arxiv.org/html/1407.4025v2#A2).
The latter clarifies CDS-specific diagonal scaling and published-error
normalization. The book/DVD and catalogue-combination conventions are distinct.
Direct ESA page access was blocked; it is not claimed directly read.

The standard Sn-suffix-5 decoder uses the published-error convention,
retains all source flags, verifies numerical matrix/spectrum/solve properties
and exposes diagonal differences. It does not force agreement, extrapolate
nonstandard solutions or propagate position errors. Every retained HIP and
fallback applicability is explicit in a separately hashed, no-clobber report.

### Real cached raw-catalogue reconstruction

No new acquisition: the existing `hip2.dat` is 32,673,535 bytes, SHA256
`c45d6325bd59dd691764af173a9702e543804a2b6c1d9fea59210e8332e50a4a`.
All 115,112 standard rows reconstruct numerically; maximum solve identity
residual is 1.274e-13. The per-row maximum absolute relative sigma discrepancy
has percentiles 50/90/95/99 of 0.00416003/0.00544708/0.00605809/0.00814235.
Counts above descriptive 1%/2%/10%/100% bins are 537/153/51/6.
These bins are not admission thresholds.

Large outliers include HIP 71502 (RA sigma 46.10 quoted versus 2491.053 mas
decoded), HIP 71681 (19.15 versus 232.681 mas) and HIP 104214 (Dec sigma
6.85 versus 12.669 mas). Several extreme records have stored F2 exactly 99;
this is not proof of clipping/saturation, and there are non-99 outliers.
Published decimal rounding is not assumed to explain the large discrepancies.
[Issue #333](https://github.com/fselman/wenu/issues/333) tracks the unresolved
source interpretation. Matrices remain diagnostic-only, unadmitted for
propagated uncertainty. The actual Mac combined-source/fallback receipt below is distinct from these
all-standard-source statistics.

### Verification and remaining scope

Fifteen new synthetic cases protect packing, non-unit fit/error scaling,
independent normal-matrix reconstruction, flags/refusal, exposed diagonal
disagreement and the real snapshot/CLI/report seam. Both deliberate scaling
faults fail all three nearest numerical cases; both are restored.
The final complete source-audit gate passed 173 cases in 5.37 s. Three available
documentation checks passed in 0.47 s; six standalone tooling cases/nine subtests
passed in 0.07 s. Full tooling and archive/import checks unavailable in this
partial checkout are not claimed passing. All 227 relative links and 134 active
fragment links across 11 target documents were verified against the actual Git
tree/content. Existing Gaia numerical/report and source admission definitions
are AST-unchanged; only the existing CLI main function is extended.
### Mac acceptance and fallback review

At tested commit `32c13c1a5b66c284f5cfed0181176c19ec966e64`, the complete
Mac gates passed: 173 audit cases in 3.58 s, 36 documentation cases in 2.69 s,
and eight tooling cases/81 subtests in 11.82 s. NumPy was 1.26.3.
The actual report `~/wenu-output/hip2_covariance_qualification_v1` completed,
retaining all 118,218 HIP entries. Provenance SHA256 values:

- Source manifest: `8747349e08f70a428b547f6d0131c47b6f935df73e6b7df9ef6b9d36aba4d365`.
- Passive covariance reference: `b9c0a9109e5ef0ed4aec037f88c805b1c8dd1ee1265c2b5e884a33b1730c1f6e`.
- Report owner: `6ea9bd105feed85cfa28d2b3c0de0e59d95c987e670c1c0587db6f89a74bf27e`.

All-source statuses are 115,112 decoded standard, 2,843 nonstandard and 263
without a Hip2 source. The 2,850 angular fallback entries split into 2,682
decoded standard and 168 nonstandard solutions. For the standard fallback
subset, the maximum per-star sigma discrepancy is the largest absolute
relative decoded-versus-quoted difference across the five source components:

| Percentile | 50 | 90 | 95 | 99 | 100 |
|---|---:|---:|---:|---:|---:|
| Discrepancy, percent | 0.423027262 | 0.597412854 | 0.743817673 | 6.22509563 | 5303.58618 |

Fallback counts above descriptive 1%/2%/10%/100% bins are 68/44/22/5;
2,614 of 2,682 (97.5%) are within 1%. These are not admission thresholds.
The fifteen largest fallback discrepancies all have stored F2 exactly 99;
the largest five are HIP 71502, 71681, 26549, 63081 and 63721.
This strengthens the motivation to investigate source encoding/fit-statistic
limits but does not prove clipping or explain non-99 outliers in the full
catalogue. No quoted errors or source astrometry are altered.

Fernando's “proceed” accepts recording these receipts and merging the diagnostic
work. Mac synchronization and merged-branch cleanup remain separate.
 Unexplained diagonal outliers, Hip2 source
time scale (#326), nonstandard covariance, propagation, physical accuracy,
K4b.05 parent and later consumer adoption remain open.

## K4b.05 offline Gaia uncertainty report implementation, 2026-10-23

Fernando selected this bounded report with “Proceed” after PR #331 merge and
confirmed clean synchronized Mac main `9395ad21`, branch cleanup and
36 documentation tests in 3.47 s. Plan committed before implementation at
`600a2b2b87de4b8f39a7ba4f44b10cb3ba665fbb`.

As-is: the existing source codec preserves verified immutable bytes and units;
the audit tool owns offline source diagnostics/publication, and its existing
test file owns synthetic source and command seams. Production model errors are
still unknown. Extend this maintenance boundary, not the provider or SDK.
Reconstruct the Gaia five-parameter matrix, validate its correlation spectrum
and propagate the four-parameter angular marginal with an analytic normal-triad
Jacobian. Source 95 pseudocolour is marginalized. The target transported tangent
basis and local one-standard-deviation axes are explicit. Negative eigenvalues,
invalid or missing fields remain gaps; no matrix repair, hidden RV or distance.

A separate local derivative at hypothetical zero RV is reported per km/s using
a positive reciprocal-parallax proxy. It does not use a missing-RV prior or
claim finite scenario/physical coverage. HIP membership/source identities,
production states/model digests, SDK uncertainty fields, observer/frame routes,
default charts and dependencies are unchanged. Hip2 decoding, full RV-dependent
measurement propagation and physical/dynamical qualification remain deferred.

The publisher now shares the existing staging/no-clobber/manifest-last boundary.
The report reads only a manifest-bound source and refuses source/output overlap.
Every HIP is retained with explicit source gaps and per-offset statuses.
Its manifest binds output bytes; summary binds source/reference/offsets/policy,
report code and numerical-library versions. Existing scientific/code owners
remain unchanged outside the maintenance tool. The coordinate guide records
the tangent-plane distinction; source map/architecture responsibilities remain
current because no production module or service changes.

Local verification after restoring both faults: all 158 source-audit cases
passed in 6.06 s (33 new cases); three available documentation checks passed
in 0.31 s; six standalone tooling cases/nine subtests passed. The full tooling
repository-path checks cannot resolve missing owners in this partial checkout;
they are not claimed passing and remain in the complete Mac gate. All 220
relative links and 128 active fragment links across 11 target documents in
the changed documentation were checked against the actual Git tree/content.
No archive or product-import check unavailable here is claimed passing.
**Mac acceptance at `652087cb6243fcbb22ad01b475f2ec2238d040d5`:**
158 audit cases passed in 4.57 s; 36 documentation cases in 3.31 s;
eight tooling cases/81 subtests in 10.38 s. The actual read-only report
`~/wenu-output/stellar_uncertainty_v1` completed using source manifest
`8747349e08f70a428b547f6d0131c47b6f935df73e6b7df9ef6b9d36aba4d365`
and report-owner SHA256
`555afe3fe3aaaadfde95e7d8317e37bc1bee1ad62256bf3ea0a1e1259fde8acb`.
All 118,218 HIP entries are retained. All 115,105 Gaia covariance matrices
passed as positive definite, yielding 805,735 angular evaluations across
seven native offsets (0 and +/-100, +/-1,000, +/-10,000 Julian years).
The 2,106 position-only and 1,007 unassociated entries retain explicit gaps.
RV sensitivity evaluated 805,343 times for 115,049 stars; 56 further Gaia
motion entries lack a positive-parallax proxy. No invalid-matrix or propagated
variance failure was reported.

Major-axis formal standard-deviation percentiles, arcsec:

| Elapsed TCB Julian years | Median | 90th | 95th | 99th | Maximum |
|---|---:|---:|---:|---:|---:|
| -10,000 | 0.2573 | 0.9872 | 1.705 | 4.335 | 16.92 |
| -1,000 | 0.02573 | 0.09872 | 0.1705 | 0.4334 | 1.692 |
| 0 | 0.0000199 | 0.00007576 | 0.0001312 | 0.0003374 | 0.001367 |
| +1,000 | 0.02573 | 0.09871 | 0.1705 | 0.4334 | 1.692 |
| +10,000 | 0.2573 | 0.9872 | 1.705 | 4.334 | 16.92 |

The selected 16-HIP review reports +/-10,000-year formal axes for Gaia entries
53910 (9.7308/9.7306 arcsec), 59774 (2.1148/2.1148), 65378
(7.5548/7.554), 87937 (0.29308/0.29306) and 57939 (0.15265/0.15265).
The remaining selected Orion/Big Dipper entries retain association or
five-parameter-input gaps; this report does not substitute Hip2 errors.
Fernando accepted proceeding with merge/cleanup and subsequent bounded Hip2
covariance qualification. Only this conditional Gaia-report slice is accepted:
full RV covariance, physical ancient-position accuracy and K4b.05 parent
remain open. Mac synchronization/cleanup of the merge remains separate.

Primary references reviewed 2026-10-23:
[Butkevich & Lindegren (2014), Sect. 5.4, Eqs. 61–65 and no-light-time Sect. 5.5](https://arxiv.org/abs/1407.4664)
for the fixed normal-triad convention and
[Gaia DR3 source schema](https://gaia.aip.de/metadata/gaiadr3/gaia_source/)
for units/errors/correlations. This implements a conditional angular diagnostic,
not the paper's full light-time model. Numerical acceptance and actual Mac
source report are separate; K4b.05 parent, ESA comparison, issue #326 and K4b.06
remain open.

## K4b.05 ancient-position uncertainty and missing-RV assessment, 2026-10-23

**Authority and scope:** Fernando selected this bounded assessment with “Proceed”
after PR #330 merge and confirmed clean synchronized Mac main/branch cleanup at
`fde11d831e0a7c4b870eec8b7f7358c686e9bc60`. Plan committed before assessment
outputs at `b4a24bb8c235f0a24b582de33079102f05bad9c5`. Source/method review,
explicitly synthetic analytic examples and a next-step proposal only:
no production covariance propagation, catalogue acquisition, RV prior,
new model/SDK/certificate, source mutation or consumer adoption is implemented.
**Mac acceptance:** Fernando ran the full documentation gate at
`82405290cb040bd386e450e6cf75284736ec62d5`: 36 passed in 3.61 s,
with a clean synchronized task branch. The read-only inventory loaded the
existing source manifest `8747349e08f70a428b547f6d0131c47b6f935df73e6b7df9ef6b9d36aba4d365`
and reported the following actual cache results:

| Population / field check | Entries |
|---|---:|
| Retained HIP population | 118,218 |
| Associated Gaia sources | 117,211 |
| Gaia solution 31 / solution 95 / position-only solution 3 | 108,652 / 6,453 / 2,106 |
| Gaia angular inputs with all five finite nonnegative errors and ten finite correlations within [-1,1] | 115,105 |
| Associated Gaia sources with finite RV and finite nonnegative RV error | 98,161 |
| Hip2 rows with five finite nonnegative errors and 15 finite UW values with nonzero diagonal | 117,955 |
| Hip2 standard solution suffix 5 | 115,112 |
| Hip2 angular fallback inputs | 2,850 |
| Hip2 fallback with standard suffix 5 and both field checks | 2,682 |
| Hip2 fallback outside that standard subset | 168 |

The Hip2 solution-suffix inventory is 5: 115,112; 7: 1,338; 1: 1,371;
9: 104; 3: 25; 0: 5. These are field-level completeness/range checks only,
not matrix positive-semidefiniteness, UW inversion, propagated uncertainties,
RV/astrometry independence admission or physical-accuracy evidence. The RV
count includes all associated Gaia sources and is not the full-model count.
No source bytes or production model identities changed. Fernando accepted
proceeding with assessment merge/cleanup; numerical report implementation
remains a separate bounded selection.

### As-is data and capability assessment

Inspected existing owners: `stellar_enrichment.py`, `stellar_state.py`,
`astrometric_state.py`, acquisition/profile JSON and
`fetch_stellar_astrometry.py`; existing source/stellar/shared-core tests remain
their acceptance owners. The prior PR #330 comparison establishes numerical
agreement for the nominal motion model, not measurement/model accuracy.

| Evidence in the current source design | What can be assessed next | Missing qualification |
|---|---|---|
| Gaia acquisition vocabulary includes five astrometric errors and ten correlations, RV/error, solution/quality flags and pseudocolour metadata | Reconstruct a per-source five-parameter covariance where actual fields are finite, correctly scaled and jointly consistent | Approved columns do not prove actual non-null row coverage. Snapshot validation checks schema/units and source lineage, but does not admit a positive-semidefinite covariance or validate every error/correlation semantically. |
| Gaia angular models use only position and both PMs | Propagate the marginal four-parameter covariance through the actual normalized angular model | This is uncertainty conditional on the angular approximation; omitted perspective is a separate model effect. Dropping unused parallax dimensions means marginalization, not conditioning them to exact zero. |
| Full Gaia model uses reciprocal positive parallax and a spectroscopic RV proxy | Conditional no-light-time measurement propagation with a six-dimensional input vector | RV correlations with astrometry are not supplied by the reviewed main-table error vocabulary. A block-diagonal extension is an explicit independence assumption, not measured zero covariance. RV errors omit unknown systemic/companion/convection corrections. |
| Hip2 capture retains five formal errors, all 15 UW entries, Sn/So/Nc and the complete original row | Decode and validate covariance for suitably qualified solution types, using the corrected captured edition | Parser agreement with raw bytes is not covariance validation. Standard, extended/acceleration, stochastic, photocentre and VIM solutions must be distinguished. Extended solutions have separate annex parameters/weights not captured by this source profile. |
| Original lookup retained for 263 entries absent from Hip2 | Preserve membership and disclose source gaps | No new PM, RV or uncertainty model is inferred for these lookup-only entries. |

Primary-source review on 2026-10-23:

- [Gaia DR3 main-table metadata](https://gaia.aip.de/metadata/gaiadr3/gaia_source/)
  directly confirms error/correlation/RV vocabulary. The
  [ESA DR3 data model](https://gea.esac.esa.int/archive/documentation/GDR3/Gaia_archive/chap_datamodel/sec_dm_main_source_catalogue/ssec_dm_gaia_source.html)
  direct fetch returned 503; indexed primary text was available.
  [Gaia EDR3 astrometric-solution paper](https://arxiv.org/abs/2012.03380)
  confirms that solution code 95 adds pseudocolour: it is not an RV measurement
  or six-dimensional space-motion solution. The five astrometric parameters'
  covariance submatrix is a marginal covariance of that fitted solution; do not
  condition on exact pseudocolour to claim smaller errors. Its angular RA error
  convention is the local tangent increment `d(alpha*) = cos(delta)*d(alpha)`,
  not the derivative of the product `alpha*cos(delta)`; no second cosine factor.
- [CDS I/311 ReadMe](https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/I/311?format=html&tex=true)
  was read directly. Note G1 gives `C^-1 = U^T U`, with packed columns
  `(u1); (u2,u3); (u4,u5,u6); (u7,u8,u9,u10); (u11,...,u15)`.
  Validate units/RA convention, invertibility, conditioning and diagonal
  agreement with formal errors. Do not interpret weights as correlations,
  automatically multiply by formal errors again, or assume a leading weight
  block supplies the full marginal covariance of an extended solution.
  Missing annexes/semantics require disclosure or refusal, not a fabricated
  diagonal covariance. No annex acquisition is selected.
- [Butkevich & Lindegren (2014)](https://arxiv.org/pdf/1407.4664), Sect. 5.5,
  Appendix C and Appendix E, supplies the matched no-light-time Jacobian and
  its model limitations. Covariance propagation is a local uncertainty
  approximation, distinct from the rigorous finite-light-speed model and from
  Galactic/companion dynamics. This assessment does not implement them.

### Measurement propagation proposal

Proposed first deliverable is an explicit offline report, retaining the current
production models and their unknown error channels. Reconstruct `C0` with
`Cij = rho_ij * sigma_i * sigma_j` for qualified Gaia rows, with declared order
`(alpha*, delta, parallax, pmra*, pmdec)` and mixed units converted consistently.
Check required fields, symmetry, finite/nonnegative variances, correlation range
and positive semidefiniteness/conditioning; range checks alone are insufficient.
Report numerical-rounding tolerances, and refuse invalid matrices instead of
silently clipping correlations, adding jitter or zero-filling gaps. A singular
positive-semidefinite covariance is not automatically invalid; distinguish it
from an indefinite matrix and from singular propagation geometry.

Propagate the admitted nominal mapping using `Ct = J C0 J^T`, expressed in the
target tangent plane or as a constrained direction-vector covariance to avoid
longitude/pole singularities. Independent finite differences and labelled Monte
Carlo cases should verify the analytic Jacobian within a stated linear regime.
Check source epoch, both elapsed-time signs and long intervals. Nonlinearity,
low parallax S/N or close passages can invalidate Gaussian/first-order
interpretation even when nominal propagation remains mathematically defined.

A useful limiting check is one tangent coordinate:
`variance(t) = variance(0) + 2*t*cov(position,PM) + t^2*variance(PM)`.
For illustration only, neglecting the initial term/correlation, synthetic PM
standard errors 0.03 and 1 mas/yr imply 0.03 and 1 arcsec after 1,000 years,
or 0.3 and 10 arcsec after 10,000 years. These are not measurements of the
selected Orion/Big Dipper stars. Covariance ellipse axes are statistical
standard deviations, not a guaranteed angular radius; joint confidence also
needs an explicit probability/distribution convention. Input-date uncertainty,
frame/precession uncertainty and correlated systematics remain separate channels.

### Missing-RV sensitivity: analytic assessment

For the unchanged no-light-time model, define total angular PM `mu`, initial
distance `D`, and radial rate `rho = vr/D`, in compatible units. Angular
departure along the source great circle is
`phi(t) = atan2(mu*t, 1 + rho*t)`. Direct differentiation gives

`dphi/drho = -mu*t^2 / ((1+rho*t)^2 + (mu*t)^2)`.

Multiplying by `drho/dvr = 1/D` gives local angular sensitivity per velocity
unit. For a finite RV interval use exact endpoint/scenario calculations and
check domain/closest-approach issues; do not extrapolate this derivative into
a global bound. When both `abs(rho*t)` and `abs(mu*t)` are small,
`abs(delta_phi) approximately mu*abs(delta_vr)*t^2/D`.
The expression follows from the already adopted no-light-time equations;
it is not an extra light-time or gravitational correction.

Explicit synthetic examples, evaluated with Astropy unit conversion and the
analytic derivative at the hypothetical scenario `vr=0`:

| Initial PM (mas/yr) | Distance (pc) | Elapsed years | Local sensitivity (arcsec per km/s) |
|---:|---:|---:|---:|
| 100 | 100 | 1,000 | 0.0010227119 |
| 100 | 100 | 10,000 | 0.10226881 |
| 1,000 | 10 | 1,000 | 0.10226881 |
| 1,000 | 10 | 10,000 | 10.203140 |

Independent finite scenario differences between hypothetical RV 0 and +1 km/s
were respectively 0.0010227015, 0.10225835, 0.10225835 and 10.192740 arcsec.
The difference from the derivative is finite-step nonlinearity, not a production
error. Scenario zero is not an adopted missing RV or a measured value.
These illustrations show why no common lookback cutoff follows from PM
availability alone. If distance is missing or unqualified, physical sensitivity
per km/s cannot be inferred; report sensitivity to the unspecified radial rate
and the unresolved distance/RV product instead. Even zero instantaneous PM
does not establish absence of orbital acceleration.

With measured RV/error, a conditional statistical contribution is possible
subject to the documented proxy/independence assumptions. Without measured RV
there is no measured RV variance: report sensitivity or caller-declared,
explicitly hypothetical scenarios, not a Gaussian sigma or finite physical
accuracy guarantee. No default velocity distribution/bound is selected here.

### Limits and concrete next gate

Formal catalogue covariance does not include all source/frame systematics,
binary/photocentre versus systemic motion, long-term acceleration, uncertain
time convention, or omitted dynamics/light time. Keep these visible even for
a small formal ellipse; quality flags are diagnostics, not identity vetoes,
and a universal RUWE threshold is not introduced. Do not blindly extrapolate
Hip2 acceleration polynomials over millennia.

The next proposed numerical slice is a read-only offline uncertainty/sensitivity
report in the existing stellar audit owner, with no mutation of native models,
SDK evidence or source snapshots. Start with qualified Gaia five-parameter
measurement covariance and angular four-parameter marginals, then an explicitly
declared RV-independence option for full-input models; defer Hip2 decoding until
encoding/solution-type checks have independent evidence. A six-parameter Gaia
fit can later use the qualified marginal five-parameter matrix without pretending
its pseudocolour is an RV.

Proposed acceptance: synthetic diagonal/correlated/PSD/indefinite/missing-input,
pole/wrap, epoch-zero and both-time-sign cases; analytic versus independent
finite-difference/Monte Carlo checks; RV derivative versus finite scenarios;
clear matrix/order/unit/proxy/coverage identity, no implicit missing values or
false confidence bounds; actual existing-cache counts and selected-star output
verified separately on the Mac. The exact report format, owner edits and bounded
implementation still need Fernando's selection and a committed plan.
K4b.05 parent, ESA comparisons, issue #326 and K4b.06 remain open.


## K4b.05 no-light-time reference implementation, 2026-10-23

Fernando selected the bounded numerical comparison with “Proceed” after PR #329
merge, Mac synchronization and branch cleanup at `439b8a67`. Plan committed
before implementation at `932bab6976aec7a761c1e9f2dd12529d49d9aeb6`.

Only `tests/test_stellar_state.py` changes executable code. Its test-only
`stellar_no_light_time_reference` follows the no-light-time reference assessed
below, evaluating the great-circle angular departure and bearing with independent
Astropy unit conversion. It does not read production SI/derivative rows, call
the shared propagation engine or delegate to another library's motion routine.
This is an independent numerical expression of the same adopted model, not
independent dynamical physics.

Seven explicitly synthetic input configurations cover oblique direction,
longitude wrap, pole/near-pole, high PM, both RV signs, radial-only and zero
motion. Each of full Gaia, Gaia angular and nominal-TCB Hip2 routes is queried
through the actual SDK at seven epochs: source and elapsed +/-100, +/-1,000,
+/-10,000 Julian years. Hip2 comparisons use the actual rounded fixed-width
synthetic capture coordinates, not pre-capture values. Twenty-one parameter
cases cover 147 returned directions; measurement/model evidence remains unknown,
and source bytes, model/reference and source/evaluation/anchor identities are
checked. The vector-chord comparison threshold `5e-14` (about 0.01 microarcsec
for these small residuals) is a test threshold for these conditioned inputs,
not a source/physical/universal numerical bound.

Two coherent fault injections change the shared engine's affine coefficients:
drop radial velocity or exchange Cartesian x/y velocity. Baseline agreement
passes; each fault produces a chord discrepancy above `1e-5` and breaks the
reference assertion even though the engine's internal affine check sees the
same erroneous coefficients. Existing exact arithmetic/domain/refusal and
cold dependency-isolation tests remain the owners of their separate claims.

Local validation: all 23 new cases passed. Combined stellar/shared-core/cluster
and source-audit owners passed 456 cases and nine subtests in 14.94 s, with
three pre-existing full-application cases deselected because this partial
checkout lacks their dependencies/assets. No other cases were excluded.
The complete unfiltered Mac gates subsequently passed; see the acceptance below.

Existing Wenu topology confirms these cached-source comparison groups:

| Group | HIP identifiers |
|---|---|
| Seven Big Dipper stars, subset of the UMa figure | 54061, 53910, 58001, 59774, 62956, 65378, 67301 |
| Seven principal Orion figure stars | 27989, 24436, 25336, 26727, 26311, 25930, 27366 |
| High-motion stress cases from the reference review | 87937, 57939 |

Topology source:
`src/wenu/data/constellations/western/constellationship.fab` at `439b8a67`.
The sample is an identity selection, not a claim all have full Gaia inputs or
that ESA used exactly these source solutions. The actual Mac cache comparison
must disclose availability per model/HIP, preserve accepted full/angular/Hip2
solution digests, compare the same seven native relative epochs and report
residuals separately from physical uncertainty.

**Complete Mac acceptance, 2026-10-23:** tested commit
`5da8220ff821680f7c133acaa191f6aaffa9e82a`, PR #330. All 334 stellar/shared-core/
cluster cases and nine subtests passed in 10.08 s; 125 source-audit cases in
2.44 s; 36 documentation cases in 2.48 s; eight tooling cases and 81 subtests
in 9.01 s. No exclusions. Fernando's gate receipt confirms the clean synchronized
task branch.

The actual cache manifest remained
`8747349e08f70a428b547f6d0131c47b6f935df73e6b7df9ef6b9d36aba4d365`.
The 16 selected HIPs were evaluated at source and elapsed +/-100, +/-1,000,
+/-10,000 native Julian years. Full Gaia availability was three (HIP 59774,
87937, 57939), Gaia angular availability five (HIP 53910, 59774, 65378, 87937,
57939), and Hip2 fallback eleven (HIP 54061, 58001, 62956, 67301, 27989,
24436, 25336, 26727, 26311, 25930, 27366). Thus all 16 have Gaia angular or
Hip2 fallback inputs; the full-input subset overlaps angular availability.

| Model | Available sample stars | Directions | Maximum vector-chord residual | Full retained-population models |
|---|---:|---:|---:|---:|
| Full Gaia | 3 | 21 | 8.959510885851885e-16 | 97,710 |
| Gaia angular | 5 | 35 | 8.959779580913775e-16 | 115,105 |
| Hip2 angular fallback | 11 | 77 | 3.188872858294072e-16 | 2,850 |

All 133 directions passed the independent spherical reference threshold.
Full-model gaps among the selected stars were six without a published Gaia
association, two missing Gaia RV and five Gaia position-only solutions.
Gaia angular had six unassociated and five position-only gaps. Hip2 correctly
deferred five entries to their available Gaia angular model. These are input/
selection disclosures, not inferred zero values or new identity decisions.
All 118,218 original objects remain retained.

Accepted solution digests checked unchanged by the actual Mac recipe:

- Full Gaia SI: `032f76e398eadf136fd9aa59a3c2b3a66d4dc25d9da74bc995b4bdb6088cfe8f`.
- Gaia angular: `6d3e46ff0aa8bd707ea4b8f169b55fdd41c3bc85d65250d7a801c541ebb38602`.
- Hip2 angular: `b5b6cfe20919eec5c815f50b348b55579e2b2631e8f0510be201d874e85875c1`.

The receipt ended `CACHED STELLAR REFERENCE CHECK COMPLETE`; measurement and
physical-model evidence remained unqualified. No numerical ESA reproduction,
source acquisition, covariance/light-time/dynamics implementation, consumer
adoption or K4b.05 parent closure is claimed. Production code, source snapshot,
SDK and dependencies are unchanged. PR #330 is merged at `fde11d83`;
its bounded comparison does not close physical/ESA numerical qualification.


## K4b.05 reference and method assessment, 2026-10-23

**Selected scope:** Fernando’s “Proceed” after the ESA reconstruction and
Butkevich–Lindegren reference-assessment proposal. The documentation plan was
committed at `80d4d4230d25d0c02c83c629b489aed5df28fc28` before these findings.
Inspected production/test owners at `351e4ddf613feff2b13eb781445205e6103ef608`;
the plan commit changes no runtime. This assessment does not close K4b.05,
execute a reference comparison, select numerical implementation or authorize
source acquisition. K4b.06 consumer adoption and Hip2 time-scale issue #326
remain separate.

### ESA comparison evidence

| Product | Verified evidence and retrieval | Recoverability and comparison role |
|---|---|---|
| [Orion story](https://www.esa.int/Science_Exploration/Space_Science/Gaia/The_future_of_the_Orion_constellation) and [video](https://www.esa.int/ESA_Multimedia/Videos/2017/06/The_future_of_the_Orion_constellation), 2017-06-09 | Direct ESA text read: 450,000-year future sequence, 40 by 20 degree field, TGAS plus Hipparcos bright stars and ground-based information. Video credit ESA/Gaia/DPAC; its page offers CC BY-SA 3.0 IGO or ESA Standard Licence. | No machine-readable output positions, complete per-star input/edition list, RV policy, equations, exact starting epoch/time scale or projection specification found on these pages. Link/view evidence only: video frames were not measured. Suitable as a qualitative external target until those details are recovered. |
| [Hipparcos stereo images, Ursa Major](https://www.cosmos.esa.int/web/hipparcos/stereo-images) | Direct fetch returned HTTP 451; search retrieval supplied the ESA page text. It describes present and +60,000-year views, centred near RA 12 h, Dec +60 degrees, field about 36 by 31 degrees. The images are credited to L. Lindegren and associated with ESA Bulletin 77. | The page describes preliminary 30-month Hipparcos results, nonlinear depth enhancement and about a two-light-year stereo eye baseline. It is not established as a final 1997/Hip2 input set or an ordinary barycentric chart. Exact epoch, per-star values/RVs, projection, numerical outputs and media rights remain unresolved. Use qualitatively; do not extract RA/Dec directly from the stereo images. |

These sources are published extrapolations, not measurements of an ancient sky.
The retrieved pages do not establish an independent ancient numerical catalogue.
The absence of a table on the reviewed pages is not proof that none exists.
No ESA media/data/code were acquired or redistributed; a video licence does not
establish permission for an unidentified underlying dataset. No contact was sent.

### Mathematical reference and actual Wenu model

Primary reference: A. G. Butkevich & L. Lindegren (2014),
[Rigorous treatment of barycentric stellar motion](https://doi.org/10.1051/0004-6361/201424483),
A&A 570, A62; [author manuscript arXiv:1407.4664v2](https://arxiv.org/pdf/1407.4664).
The 18-page manuscript was retrieved; the publisher HTML was blocked.
Relevant reviewed material: Sect. 4 (TCB/parameter conventions), Sect. 5.5
(no-light-time propagation), Sects. 5.3–5.4 and Appendix C (covariance),
Sect. 6 and Appendices D–E (light-time/model limitations).
Its rigorous finite-light-speed model and no-light-time limit are different
comparison cases. Appendix E uses differential Galactic acceleration relative
to the SSB; companion motion needs object-specific treatment. This is a
mathematical/limitations reference, not observational ground truth.

The following mapping is an assessment of Wenu's inspected implementation:

| Owner | Actual current behaviour | Assessment consequence |
|---|---|---|
| `stellar_state.py:StellarMotionCatalogue` | Full-input admission constructs distance from positive reciprocal parallax, source direction/normal triad, tangential velocity from both measured PMs, and radial velocity from an explicit spectroscopic proxy. Gaia metadata supplies native ICRS/SSB/TCB conventions. | Compare the existing nominal model with the paper's no-light-time limit first; do not silently reinterpret spectroscopic RV as a measured astrometric/systemic velocity. |
| `astrometric_state.py:RectilinearAstrometricProvider` | Evaluates affine SI position and constant velocity, normalizes for native direction, checks explicit finite domains and numerical cones; no catalogue-specific dynamics or observer resources. | An independent spherical-form direction calculation can test adapter conversion plus engine composition without changing the generic core. |
| `AngularMotionRow` and Gaia/Hip2 angular admissions | Normalizes source direction plus elapsed-time transverse angular derivative; does not use distance or RV. Hip2 retains an explicit nominal-TCB policy. | A zero radial term is a mathematical comparison limit, not a measurement of zero RV or admission of a finite distance. Keep missing-input model discrepancy distinct from numerical error. |
| Existing stellar/shared-core tests | Axis and spherical-differential source-conversion oracles, Decimal affine/PV/angular calculations, domain/refusal/conformance/cold isolation and long-frame composition already exist. | Extend these owners only for a demonstrated new external-reference fault; do not duplicate exact affine arithmetic tests or invent a separate motion engine. |
| Source evidence and uncertainty records | Source errors/correlations retained; full covariance propagation, binary/systemic correction, source-conversion physical error and total physical accuracy remain unimplemented/unqualified. | Reference agreement cannot populate unknown error fields or certify a lookback domain. No uncertainty or accuracy policy changes in this assessment. |

An algebraic check explains the intended comparison. Write Wenu's admitted
position as `D*u0`, velocity as `D*mu0 + vr*u0`, and elapsed native time as
`t`, in compatible units. Its direction is therefore proportional to
`(1 + (vr/D)*t)*u0 + t*mu0`. Normalizing this vector gives the spherical
no-light-time expression in Sect. 5.5, Eq. (84), with radial proper motion
`vr/D`. This establishes an algebraic relationship under matched inputs;
it is not an executed numerical comparison or justification of the RV proxy.
The angular model has the same algebraic form with the radial term omitted;
real missing RV/distance remains unknown.

**Reference recommendation:** use the no-light-time equations for the first
like-for-like implementation oracle. A rigorous light-time result may later
measure omitted-model effects, but should not become a zero-residual oracle
for the unchanged nominal model. Covariance and dynamical qualifications need
their own evidence and explicit scope. Astropy/ERFA calls are useful secondary
checks only after inspecting their time, RV and light-time conventions; a
different library name alone does not establish independent physics.

### Concrete next comparison proposal, not yet implemented

The smallest numerical slice is a test-only independent spherical no-light-time
oracle in the existing stellar/shared-core test owners, preserving production
code, model identities, source snapshot and defaults. First cover synthetic
labelled cases at source epoch and elapsed +/-100, +/-1,000 and +/-10,000 Julian
years, including pole/wrap, high transverse motion, positive/negative RV,
radial-only and missing-input angular cases. Compare returned directions using
stable vector angular/chord metrics, with a justified numerical tolerance
distinct from physical uncertainty. Match native TCB dates and PM convention,
avoid inadmissible origin crossings, and retain refusal/isolation checks.

Then inspect a bounded selection from Fernando's existing immutable cache:
the seven Big Dipper stars, the principal Orion figure stars, and high-motion
stress cases such as HIP 87937 and HIP 57939. Verify actual Wenu topology/HIP
membership, inputs and availability before fixing this selection; do not acquire
or invent missing measurements. Publish per-object input/model availability and
separate full-input from angular/Hip2 fallback results. The sample and epoch
list are proposed, not an accepted numerical/physical domain.

For ESA reproduction, recover the original input set and exact epoch conventions
before asserting numerical agreement. The Ursa Major relative +60,000-year and
Orion +450,000-year products exceed the initial proposed numerical sample;
neither authorizes enlarging an admitted Wenu domain, using a remote precession
frame beyond its domain, or extrapolating stellar lifetimes. Native ICRS
comparisons can be considered separately from date-oriented axes. If the ESA
numerical information remains unavailable, report qualitative agreement only,
with documented projection/viewpoint differences. Do not tune production values
to match an image or claim pixel-level equality with newer source astrometry.

**Assessment exit:** reference choice and missing evidence are documented;
no comparison residuals, propagated covariance, ancient physical accuracy,
performance results or new acceptance totals are claimed. Proposed numerical
work needs Fernando's bounded selection and a committed plan before
implementation. Complete Mac documentation acceptance remains separate.


## Catalogue metadata audit, 2026-10-18

Inspected source: PR #248 head `90d51334`, based on accepted main `bf804cbb`;
the ingestion correction in this PR follows that inspection. Static searches
cover production Python and the separate kernel for epoch, equinox, frame,
origin/centre, unit, catalogue edition, provenance, manifest and resource
identity literals. The findings below trace the significant candidates into
loaders, normalized tables, source ECSV/ReadMe/provenance documents, snapshots
and public geometry. This is a metadata audit, not numerical revalidation of
unmodified providers or proof that every literal is wrong.

**Result:** catalogue-specific knowledge is duplicated beyond the stellar
position bug. Wenu cannot yet claim that every scientific consumer obtains its
metadata from a source record. The stellar path is corrected here; the remaining
findings are explicit migration work, ordered before the affected provider can
be considered modular or frozen. Never replace an unknown epoch by J2000.
The open-cluster followup now consumes the already-preserved `position_epoch`
and `RA_source` fields and carries source metadata into geometry. At inspected
base `c0dee24c`, the active 513-row table declares 509 J2016.0 Hunt positions and
four unknown Dias epochs. Selection retains row lineage/masks; only uniformly
known selections expose a scalar epoch. Snapshot v4 validates that header, while
v2/v3 compatibility recomputes geometry from preserved rows rather than trusting
the historical J2000 stamp. K3.09 now removes the remaining shared implicit
measurement-epoch defaults; other nonstellar source qualification remains open.

| ID / priority | Owner and evidence | Consequence and required action | Verification owner |
|---|---|---|---|
| M1 / fixed | `objects/stars.py` and `stellar_state.py` repeated epoch, source edition and provenance, despite `epoch_year` and the packaged Hipparcos ReadMe | Ingest through `stellar_catalogue.py`; metadata document binds exact source bytes, preserves original fields and mirrors a validated immutable record. Native geometry and kernel queries obtain their epoch/edition/provenance from it. Missing or conflicting metadata is refused. | `test_stellar_state.py`, stellar/public-position owners |
| M2 / fixed | `sky/constellation_lines.py` and `sky/constellation_labels.py` supplied their own Hipparcos epoch/provider descriptions | Native endpoints inherit returned position specifications; label metadata comes from the stellar interface. Native and observed label inputs now use the public stellar state interface through accepted K3.07/K3.08. | Native constellation geometry and frozen label/gap consumers |
| M3 / fixed | `sky/native_snapshot.py` embedded J1991.25 both in writing and admission and did not persist the source metadata envelope | New schema v3 persists metadata, verifies it against source identity/row epochs and restores the same runtime record. v1/v2 compatibility uses an explicit source-bound packaged profile; unidentified legacy sources are refused. Nonstellar snapshot assumptions remain M6. | Snapshot admission/corruption, v1/v2 compatibility, source-free process and serial/spawn consumers |
| M4 / accepted PR #273 | `icrs_catalogue_spec` now defaults to `epoch=None`; `ICRS_ASTROMETRIC_SPEC` no longer assigns J2000.0. Explicit admitted stellar and cluster epochs remain unchanged | ICRS axes alone establish no measurement epoch. Shared raw point/curve observation helpers, celestial north, constructed points, native grids and transformed B1875 boundary outputs inherit unknown epoch. Stellar/open-cluster source owners still supply their own epochs; diffuse geometry already supplies None. No numerical frame transform or source bytes change. | `catalogue-coordinate-defaults`: vocabulary/transform/point/grid/boundary/regional callers plus nonstellar and snapshot admission |
| M5 / mechanism implemented; source gaps open | `objects/nonstellar.py` preserves source fields/metadata/units and mirrors declared coordinate facts in a frozen `NonStellarCatalogueMetadata` record bound to input bytes. Native and observed specifications consume it; source provider identity replaces copied labels. Conflicting declarations and strict incomplete admission fail before publication | Missing facts remain null and discoverable in `missing_fields`; `require_complete()` and strict load refuse them. Legacy charts retain the explicit `legacy-unverified-catalogue-encoding` model. Actual source frame/origin and model-required epoch/scale gaps must be resolved before physical provider closure. Galaxy static directions do not require a measurement epoch. Their centre consumers now use the kernel with an explicitly unknown origin when missing; shape axes/PA remain above it. Compatibility is not evidence of accuracy. | `nonstellar-admission`: owner regressions, real family geometry, cold/saved/source-free and public CLI consumers |
| M6 / header defaults fixed; legacy interpretation explicit | Snapshot v5 derives fixed headers from each provider, stores nonstellar records, checks source identity/table metadata/units/header agreement and retains the separate open-cluster row contract | Readers admit v1-v4 historical formats without treating their J2000 headers as measurement epochs. Missing legacy units/digests are not reconstructed as facts. Resource gaps from M5 remain open; the shared coordinate helper correction is verified separately under M4. | Existing corruption owner plus nonstellar record/header conflicts, actual known/unknown epoch round trips and legacy admission |
| M7 / accepted PR #301 | `sky/ceres.py::CERES_SOLUTION` loads complete source facts from `data/ceres_solution_v1.json`; numbered/comet installed identities retain their acquisition manifests | Ceres schema and descriptor identity are validated; existing receipt/SPK digest/target/frame checks remain. Source facts no longer require a Python-literal edit. Complete Mac acceptance passed (211 focused, 36 documentation, eight tooling). | Minor-body resources/ephemeris and Ceres public state/track owners |
| M8 / accepted PR #309 | TSIS edition facts were embedded in `satellites/radiometry.py` | K3.36 moves the unchanged facts into packaged JSON and an immutable validated record, retaining public aliases, exact external byte admission and numerical/malformed-resource oracles. Mac: 61 focused, 36 documentation, eight tooling; no spectrum redistribution is admitted | Satellite radiometry resource/parser owner |
| M9 / runtime metadata and v6 transport accepted PR #289 | `sky/milky_way.py` and `sky/magellanic_clouds.py` provide fixed source descriptions/ICRS semantics while loaders retain chiefly source paths and feature levels | The K3.16 source envelope now preserves original properties, byte/geometry identity and captured provenance; v6 transports it and v1–v5 retain explicit legacy gaps. Physical declarations absent from sources remain absent. No fictitious stellar epoch is assigned. | Isophote loading/native geometry and saved-ring consumers |
| M10 / inference repaired; physical qualification unknown | `skyfield_ephemeris.py` retains byte/coverage identity, reports unqualified model by default and labels explicit caller declarations | K3.25 removes filename inference. Independent source/model qualification remains unknown rather than fabricated. | `test_skyfield_ephemeris.py` rename/explicit declaration owner |

Examples already following the intended boundary include satellite OMM records
(`satellites/elements.py` reads epoch, frame, centre and time system and validates
its supported contract), SPK segment centre/frame/coverage checks, manifest-bound
comet resources and hashed observer-location records. Preserve these checks.

### Nonstellar source declaration audit

Rechecked the packaged admission records at main `d7ad9923` on 2026-10-19,
including both Messier and Caldwell. The following describes the embedded metadata of the actual active tables,
not reconstructed measurement facts. Source bytes and all original declarations
are retained; no catalogue files are changed. Strict admission still refuses
these gaps. K3.09 remains partial: removing shared defaults does not establish
missing physical source facts or close M5. The primary-source assessment below
remains the existing 2026-10-18 evidence, not a claim of a new external review.

| Catalogue | Declared frame | Measurement epoch/scale | Edition/provenance | Remaining admission work |
|---|---|---|---|---|
| Messier/HEASARC | Absent | Absent | Sky Catalog reference and HEASARC URLs retained | Frame/origin and epoch/scale |
| Caldwell/OpenNGC | ICRS/J2000 | Absent | Release, membership URL, source-file URLs/digests retained | Origin and epoch/scale |
| Galaxies/OpenNGC | Absent | Absent; optional for the explicit static model | Release/license/source-file URLs/digests retained | Frame/origin; epoch/scale do not block static admission |
| Harris globular clusters | Absent | Absent | December 2010 edition reference and HEASARC/McMaster URLs retained | Frame/origin and epoch/scale |
| Strasbourg-ESO PN selection | ICRS/J2000 as served by TAP | Absent | 1992 edition, HEASARC and comparison/selection provenance retained | Origin and epoch/scale |
| Green remnants | ICRS/J2000 | Absent | 2024 October edition and CDS/original-source URLs retained | Origin and epoch/scale |

Primary documentation checked 2026-10-18:
[HEASARC Messier](https://heasarc.gsfc.nasa.gov/w3browse/all/messier.html)
describes RA/Dec in the requested equinox, and
[HEASARC Harris](https://heasarc.gsfc.nasa.gov/w3browse/all/globclust.html)
explicitly describes an input equinox of 2000. Neither statement establishes a
common measurement epoch/time scale for these rows or a precision ICRS origin
solution. The initially unavailable release-pinned OpenNGC documentation was
subsequently retrieved through GitHub at `v20260501`:
[README](https://github.com/mattiaverga/OpenNGC/blob/v20260501/README.md)
(blob `11b2668f5aacd1224e932094024612435528d879`) says coordinates usually come
from NED, and [field guide](https://github.com/mattiaverga/OpenNGC/blob/v20260501/NGC_guide.txt)
(blob `7e5e1447c3cccd54cd5cbebb29387e5b30b05cc1`) labels RA/Dec as J2000 epoch.
Those statements do not establish a new precision frame/origin solution for
each source row. No catalogue bytes or coordinate frame declarations are changed.
The user-selected galaxy chart model is explicitly static; measurement
epoch/scale are provenance rather than admission prerequisites for that model.
Other required source facts remain open and are refused in strict mode. Legacy chart
compatibility is an explicitly labelled interpretation, not a metadata repair.

<a id="m5-source-assessment-and-proposed-admission-distinction-2026-10-19"></a>

### M5 source assessment and agreed admission distinction, 2026-10-19

**Assessment base:** accepted main `2df8954b15ebbe36cddaf977355efdd53a65f2a8`.
The shared-default correction is accepted through PR #273: 248 focused Mac,
36 documentation and eight tooling cases passed. This assessment changes no
catalogue bytes, runtime admission rule, SDK contract or numerical calculation.

Primary evidence rechecked for the actual packaged editions:

| Source | Supported declaration | Limit of this evidence |
|---|---|---|
| [HEASARC Messier](https://heasarc.gsfc.nasa.gov/w3browse/all/messier.html), RA/Dec definitions | Coordinates are expressed in the requested equinox | No common measurement date/scale is established by that wording; an equinox is not a motion-reference epoch |
| [HEASARC Harris](https://heasarc.gsfc.nasa.gov/w3browse/all/globclust.html), RA/Dec definitions | Original cluster-centre coordinates use equinox 2000 | This is not an explicit common measurement epoch or a new precision ICRS frame solution |
| [OpenNGC v20260501 guide](https://github.com/mattiaverga/OpenNGC/blob/v20260501/NGC_guide.txt) and [README](https://github.com/mattiaverga/OpenNGC/blob/v20260501/README.md) | Guide labels RA/Dec with J2000 epoch terminology; README identifies heterogeneous inputs, usually NED for coordinates, with per-object source information | Retain the source's terminology. These documents do not establish one common observation date/time scale or independently qualify every row's frame/origin. Pinned blobs remain `7e5e1447c3cccd54cd5cbebb29387e5b30b05cc1` and `11b2668f5aacd1224e932094024612435528d879` |
| [HEASARC Strasbourg-ESO PN](https://heasarc.gsfc.nasa.gov/W3Browse/nebula-catalog/plnebulae.html), RA/Dec and Ref_Position definitions | Certain/probable PN originally have 1950 equatorial coordinates, while possible PN originally have 2000 coordinates; the service presents a requested equinox and retains positional references | Wenu selects certain/probable PN. Its preserved header saying ICRS/J2000 as served by TAP is acquisition metadata, not proof supplied by this overview of a precision ICRS conversion. Do not silently switch to B1950 or assert the existing numbers are wrong; conversion provenance requires separate evidence |
| [Green 2024 October documentation](https://www.mrao.cam.ac.uk/surveys/snrs/snrs.info.html) and [CDS VII/297 ReadMe](https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/VII/297?format=html&tex=true) | J2000 equatorial positions identify source centroids, generally from radio maps, with resolution depending on remnant size | These are not automatically central-star/neutron-star coordinates or a centre-of-mass motion solution. A radio-centroid position cannot acquire a compact object's proper motion merely by cross-identification |

The [HEASARC coordinate-converter help](https://heasarc.gsfc.nasa.gov/Tools/convcoord_help.html)
uses FK5 for its J2000 option. That is evidence about that tool only; it does not
establish the original TAP response's frame or justify rewriting Wenu's source
records. No new TAP query, catalogue acquisition or coordinate conversion was
performed. Initially failing raw GitHub/CDS URLs were recovered through the
GitHub connector and the CDS HTML ReadMe; unavailable links were not treated as
evidence. Existing packaged frame declarations remain preserved and unpromoted.

**As-is admission:** `NonStellarCatalogueMetadata.missing_fields_for` requires
frame and origin for both models, and additionally epoch/scale for its default
source-epoch model. Galaxies already use a separate static-direction chart
model, while the SDK/shared catalogue adapter already support catalogue lookup.
Thus some remaining refusals concern the requirements of the selected model,
not information that another documentation search can manufacture.

**Agreed by Fernando on 2026-10-19:** distinguish baseline catalogue lookup
from physical model admission, incorporating his proper-motion-only clarification
and explicit instruction to incorporate the policy and proceed. Policy agreement
is recorded before implementing the bounded K3.09 admission distinction.

1. A catalogue lookup returns preserved positions through existing kernel
   interfaces, retaining IDs, units, edition, byte binding, original reference
   labels and known metadata. Missing measurement epochs remain unknown.
   Incomplete reference evidence remains explicitly labelled compatibility
   interpretation, never strict physical qualification or a fabricated origin.
2. Each physical capability retains its own required inputs. Known position,
   reference epoch and both PM components suffice to admit angular propagation
   without distance or RV; no universal PM-only time cutoff is imposed. Distance
   is required for distance-dependent observer parallax. Full space motion has
   separate requirements and perspective treatment. Uncertainties, approximation
   limits and requested angular accuracy control suitability. No missing
   input becomes zero, no new lookback interval is certified, and no expansion
   or central-star/nebular-centroid substitution is introduced.
3. Baseline routing can be accepted with those explicit limitations while the
   unresolved physical qualification stays separately visible. This would not
   claim that source facts have been recovered or automatically close K5, the
   positional extension, or any other family's routing milestone.

Fernando selected the lookup/physical-admission distinction rather than blocking
baseline routing until every source has a full physical solution. Original source
metadata and incomplete qualification remain visible. No catalogue replacement,
coordinate conversion or new physical model is authorized by this admission slice.

Selected K3.09 implementation: extend the existing nonstellar admission owner with
an explicit catalogue-lookup policy and public validation method. Require source
identity, edition/provenance and angular units; retain strict physical admission
unchanged. Lookup coordinate meaning must disclose unresolved reference facts,
not promote missing facts to verified ICRS/barycentric states. No other family's
kernel routing or reduced-input propagation is activated here. Gate: extend the
existing catalogue-coordinate-defaults selection with lookup/strict separation,
missing required lookup inputs, disclosure and source immutability coverage.
The accepted native/observed and snapshot seams remain selected. SDK, source
bytes, dependencies/build, snapshot schema and renderer remain unchanged.

Existing well-governed satellite/SPK/comet resource admission remains unchanged.

Not every literal is catalogue metadata. ICRS/TEME support restrictions, NAIF
frame identifiers, serialization version identifiers, mathematical unit
conversions, IAU-defined nominal constants and an explicitly selected model or
grid equinox are contracts or definitions. They remain in their owning code or
configuration. Catalogue edition facts, measurement epochs, acquisition dates,
resource digests and source-specific units must come from data records. This
distinction prevents replacing useful scientific constraints with arbitrary
metadata acceptance.

The source map and machine inventory include the new ingestion owner and shared
synthetic metadata fixture. The expanded focused gate adds ingestion, schema
and installation checks because those boundaries changed. The separate
`open-cluster-metadata` gate verifies the bounded M4/M6 cluster correction;
other unmodified provider physics is audited statically here, not claimed newly
tested or repaired.

## Open-cluster motion and lookup audit, 2026-10-18

Inspected accepted main `5f8fca4c4a391ea54aba05401163bb1c245ce7ff`.
Resource blob identities were checked against that GitHub tree. Counts below
describe these exact Wenu derivatives, not completeness of the published catalogues.

| Resource | Rows | Proper-motion pairs retained | Position lineage |
|---|---:|---:|---|
| Dias HEASARC ECSV | 1,931 | 1,872 finite pairs, declared mas/yr | Measurement epoch not declared; J2000 frame/equinox text is not a measurement date |
| Hunt/Reffert full Wenu derivative | 7,167 | No motion columns | ICRS, source label J2016.0; no explicit numerical epoch scale in this metadata |
| Hunt/Reffert V5 derivative | 431 | No motion columns | Same source metadata as full derivative |
| Active curated v0.2 | 513 | 331 finite Dias pairs (332 unmasked, one nonfinite) | 509 Hunt centres/J2016.0; four Dias centres/unknown epoch |

All four Dias-centred rows have finite Dias motions. The other 327 finite Dias
pairs accompany Hunt-selected centres; a cross-catalogue combination needs an
explicit reviewed astrometric policy, not column presence alone. Current
`OpenClusters.position(instant)` ignores the instant; neither native nor observed
cluster geometry applies these retained motions. Observer/date transformation is
separate and does not replace physical source motion.

Primary-source verification (2026-10-18):
[CDS Hunt/Reffert ReadMe](https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/J/A+A/686/A42?format=html&tex=true)
defines cluster `pmRA` as mean motion multiplied by cos(dec), `pmDE`, their
standard errors and dispersions, parallax/error and radial-velocity fields.
The published catalogue therefore has astrometry omitted by Wenu's derivative.
[HEASARC OPENCLUST documentation](https://heasarc.gsfc.nasa.gov/w3browse/all/openclust.html)
defines mean RA/Dec motions in mas/yr, motion errors and references, and radial
velocity/error fields. Its displayed RA description alone does not settle the
cos(dec) convention; check the original CDS source before propagation. A mean
motion dispersion must not silently substitute for uncertainty of the mean.

Before propagation, ingest a source-bound standard astrometric record retaining
the selected centre's source/epoch/scale/frame/origin, motion convention/units,
available uncertainties and correlations, distance/parallax, radial velocity and
their source identities. Preserve masks and raw columns; absent motion is
unknown, never zero. Prefer the matching Hunt solution for a Hunt centre after
source verification, with an explicitly declared alternative for Dias-only rows.
No acquisition, automatic cross-source merge or resource-byte change occurs in
this prerequisite. Re-ingestion must retain the existing 513-object membership
unless a separate selection change is requested.

The ingestion prerequisite now recovers the published aggregate astrometry in a
versioned companion bound to the accepted 513-row catalogue bytes. All 509 Hunt
IDs/names/centres match exactly; 502 have radial velocities. The four Dias-only
rows have masked Hunt fields and an explicit unresolved-adoption policy. Existing
Dias columns, member photometry, masks, selection and active resource are unchanged.
The reader consumes the captured CDS ReadMe through Astropy; source byte offsets,
units and descriptions are not reimplemented for this recovery. All retained
fields and reviewed meanings enter the source-bound metadata envelope. Explicit
offline attachment is checked through the existing immutable cluster record.

ReadMe and aggregate gzip checksums exactly match the earlier photometric
acquisition. The aggregate was retrieved once on 2026-10-19; no member table or
per-cluster network queries were needed. Scientific-use policy/attribution and
article CC BY 4.0 statements are recorded with primary-source URLs; no blanket
CC0 or OpenNGC relicensing claim is made. Tests contain exact captured records
and the original ReadMe, not reconstructed fixed-width provider fixtures.
The preserved v1 time-scale/origin gaps require explicit qualification/adoption;
unavailable cluster-mean covariances remain unknown. Mean cluster motions do not
redefine the densest-point centre. Numerical
propagation and default adoption require a separate reviewed model.

The accepted SDK dev8 introduces `catalogue_lookup`: it admits incomplete
per-object source epochs without invoking the galaxy static model and refuses
physical epoch accuracy, velocity and temporal reuse. The cluster adapter now
binds preserved metadata/fields/units/masks and original/derived digests to its
resource identity. Native/public/observed/saved centres use returned kernel
vectors without fallback; production pins accepted main `9dd1909f`. This is
source lookup, not source-metadata closure or motion propagation. Only a later
explicit propagation model may claim positions at a new epoch.
For ancient charts, bulk cluster motion and changes to member distribution are
different questions; translating a present-day symbol does not reconstruct the
historical membership or morphology.

## Cluster propagation qualification and model contract

**Inspected base:** `fed1305e76455f952cca4c2a49afd14205ce30b7`.
**Source review:** 2026-10-19 UTC. The
[source-bound qualification record](data/cluster_astrometry_qualification_v1.json)
separates direct declarations, inherited conventions, unresolved lineage and
proposed model policies. It binds the accepted selected catalogue, original Dias
snapshot and Hunt companion/specification by SHA-256. It preserves four exact
record pairs from the original B/ocl and Dias 2014 tables, together with full-file
hashes, sizes, URLs and source row indices. No catalogue bytes are changed.

### Source qualification

Hunt & Reffert [Paper II, sections 2.1 and 3.3](https://arxiv.org/html/2303.13424v2)
uses Gaia DR3 astrometry, derives density-mode centres and calculates core-member
mean motions. [Paper III](https://arxiv.org/html/2403.05143v2) updates this catalogue.
ESA's [reference-system definition](https://gea.esac.esa.int/archive/documentation/GDR3/Data_processing/chap_cu3ast/sec_cu3ast_intro/ssec_cu3ast_intro_refsystems.html)
and [DR3 data model](https://gea.esac.esa.int/archive/documentation/GDR3/Gaia_archive/chap_datamodel/sec_dm_main_source_catalogue/ssec_dm_gaia_source.html)
define barycentric ICRS directions, TCB and Julian-year epochs. Together with the
captured cluster ReadMe's epoch 2016.0, this supports **source-derived inheritance
of J2016.0(TCB) and solar-system-barycentric direction conventions** for the Hunt
aggregate. It is an inference from this specific documented chain, not an explicit
new statement in the cluster ReadMe or a general rule inferred from a name.
The old v1 null declarations remain preserved; adopting this qualification in a
runtime solution requires a separate versioned ingestion/admission step.

All four Dias-only entries (NGC 2239, NGC 2252, NGC 6514 and NGC 6885) identify
D14 as their proper-motion reference in the original
[B/ocl table and reference list](https://cdsarc.cds.unistra.fr/ftp/cats/B/ocl/).
Their two mean motions exactly match the
[Dias et al. (2014) table](https://cdsarc.cds.unistra.fr/ftp/J/A+A/564/A79/).
Its ReadMe explicitly defines cluster RA motion as mu_alpha times cos(delta),
ICRS. That convention is now resolved for these four motions. D14 labels its
coordinates at J2000.0; they agree with the retained centres within tabular
rounding, but the [HEASARC position description](https://heasarc.gsfc.nasa.gov/w3browse/all/openclust.html)
establishes only J2000 equinox. The retained centre's epoch lineage and time scale
are not yet proven, so those four numerical source epochs stay unknown.

Do not import uncertainty semantics along with a matching mean value. The
B/ocl and D14 error fields differ substantially for all four rows; both original
values are preserved in the audit record. No conversion or interpretation is
adopted without its original methodological evidence. D14's cluster-star
correlation is not a full covariance matrix for the cluster mean. Hunt likewise
has no published full cluster-mean astrometric covariance. A density maximum is
not a material point whose trajectory has been measured independently.

### Proposed propagation boundary

The first nominal numerical subset is now implemented through the explicit
[cluster provider API](implementation_reference.md#nominal-cluster-motion-provider).
The implemented cluster provider now also verifies numerical direction bounds
and certifies reuse against exact arithmetic on its admitted binary64 SI model.
Measurement, input-conversion and physical-model uncertainty remain separate and
uncertified. Interactive selective reuse and reproducible full-model fallback use
the unchanged SDK; chart/snapshot adoption remains open. See the
[proof and API](implementation_reference.md#cluster-direction-reuse-bound).
Keep `catalogue_lookup` as the default until explicit adoption and compatibility
acceptance. Register a distinct versioned cluster-centre motion model; never
silently change the meaning of a saved lookup state.

The explicit nominal model uses a coherent rectilinear barycentric astrometric
solution, following ESA's [standard-motion definition](https://gea.esac.esa.int/archive/documentation/GDR3/Data_processing/chap_cu3ast/sec_cu3ast_intro/ssec_cu3ast_intro_motion.html).
Given the source direction u, local east/north bases p and q, distance d and
mu_alpha_star/mu_delta, the model construction is

\[
 b_0=d u,\qquad v=d(\mu_{\alpha *}p+\mu_\delta q)+v_r u,
 \qquad u(t)=\frac{b_0+(t-t_0)v}{\lVert b_0+(t-t_0)v\rVert}.
\]

Angles, distance, velocity and elapsed time must first use coherent units and
TCB conventions. This describes an astrometric chart-centre approximation;
its time argument is light arrival at the barycentre, not a reconstructed
simultaneous emission event. A spectroscopic RV used as an astrometric proxy
must be declared as model policy. Use a reviewed existing numerical service
and independent oracle rather than implementing a second chart pipeline.

Distance selection is explicit: a chosen source distance estimator and its
percentiles must not silently become inverse mean parallax or Gaussian errors.
The 502 available RVs are candidate inputs, not 502 certified trajectories.
The full model must refuse missing RV. An angular-only approximation, if offered,
is a separately named opt-in model with omitted perspective effects reported;
unknown RV must not be published as a measured zero. Four Dias-only entries
remain unavailable for physical propagation until their missing facts are
qualified. A mixed request must report unavailable objects explicitly, without
silent omission or a raw-coordinate fallback labelled as propagated.

Transporting today's density maximum with a mean core motion is an explicit
modelling assumption. It does not reconstruct membership, tidal tails, internal
motions, angular size or morphology in antiquity. Keep shape/display parameters
above the state provider. Galactic acceleration and centre-model uncertainty
need an evaluated budget before any ancient-date absolute-accuracy claim;
do not invent a universal range of thousands of years.

### Uncertainty, validity and reuse

Keep three separate questions: measurement/model accuracy relative to the real
sky, numerical accuracy relative to the chosen model, and the error from reusing
an older computed state. Missing initial-centre errors, covariances or systematic
bounds remain unknown. A small proper-motion standard error or source dispersion
alone cannot supply the missing total uncertainty or a hard confidence bound.
An absolute angular-accuracy request must refuse unevaluated physical errors.
A nominal model evaluation may instead return explicitly unknown physical errors.

The provider owns finite physical/model coverage and proves a reuse certificate
over an admitted interval. For a held direction at anchor a, certify

\[
 \sup_{t\in I}\operatorname{angle}(u(t),u(a))+
 \epsilon_{\mathrm{numerical},a}\leq\epsilon_{\mathrm{reuse}}.
\]

A proper-motion-times-elapsed-time estimate is useful for screening; full
rectilinear motion needs a bound accounting for perspective and changing distance.
Unknown physical validity cannot be repaired by satisfying this computational
reuse inequality. No reuse chains: propagate from the original admitted solution,
and associate reuse with an original computed anchor. The existing SDK checks
certificate identities, metric, scope, time scale, coverage and error channel;
it does not infer a physical bound from catalogue motions. Existing same-scale
sessions require explicit TCB queries or a separately admitted time conversion,
not a relabelled TT request. Numerical backends must establish their own coverage.

Cache identities include source bytes, adopted qualification, centre/motion/
distance/RV policy, model/backend versions, time conventions and requested subset.
Only changed object families/solutions are invalidated. Updating cluster epochs
must not re-evaluate static galaxies or unrelated providers. Tests must cover
source facts, refusal, independent motion oracles, pole/wrap/zero-motion cases,
forward/backward epochs, strict-accuracy refusal, certificate boundaries and
unrelated-provider call counts. Add chart/saved/installation seams when routing
or transport changes; do not pre-emptively rerun unrelated suites for this contract.

## Original functionality and test audit

**Audit revision:** 1, 2026-10-18. **Inspected revision:**
`856fed20d2e38da3e315c1b15ed9c2e14b51d678`, PR #236 before these amendments.
Production still matches the accepted `6708f54a` baseline. No kernel runtime,
catalogue, dependency or science test is changed by this audit.

## Finding and limits

Wenu has useful geometry, ephemeris, observer and renderer boundaries, but
its installed package and test suite do not yet provide independently testable
astronomical modules. The main problem is responsibility and dependency
coupling, rather than simply the number of tests. The current broad package
facade eagerly imports product/domain owners. Even `from wenu.coordinates`
first initializes `wenu`; a narrow-looking import is not proof of isolation.

The [machine-readable inventory](kernel_migration_inventory_v1.json) pins all
262 production Python files and all 239 Python files under `tests` to Git blob
identities. It includes eight installed commands and 118 operational artifacts
(examples, tools, packaged notebooks and the build helper). AST inspection
was supplemented with targeted source/test review of the public interfaces,
boundary rules, shared fixtures, atlas, catalogue, rendering and scientific
routes. The [source map](source_tree.md) supplies current module responsibilities.

This is static evidence, not a fresh pytest collection, coverage report or
performance profile. Imports identify dependencies, not assertions reached at
runtime. File completeness does not prove every execution path is covered.
The functionality ledger below records located test owners; each runtime
migration must add named public-path and failure evidence before marking its
row complete. Unknown or untested behavior remains explicit.

## Measured suite structure

| Static measurement | Result | Interpretation |
|---|---:|---|
| Test modules | 226 | Plus two helpers and eleven example-fixture scripts |
| Test function definitions | 2,440 | Not the parametrized collected-case count |
| Parametrization decorators | 313 | Includes useful interactions; not automatically redundancy |
| Modules containing integration / visual / slow markers | 11 / 3 / 2 | A marker can apply to only one test in a mixed file |
| Modules containing none of those three markers | 212 | Cannot select reliable cost tiers from present marks |
| Modules importing the broad `wenu` facade explicitly | 86 | Submodule imports can also initialize the facade |
| Modules with top-level Matplotlib imports | 30 | Collection itself can require the rendering stack |
| Explicit fixture declarations by scope | 21 function / 8 module | No central `tests/conftest.py` at the inspected revision |

The last full production receipt remains 3,606 passed in 1,136.74 s on the
Mac, before documentation cleanup. K1's 15-test receipt covers its selected
documentation gate only. Neither receipt establishes the current full collected
count or explains where those 19 minutes are spent. Profile representative
owner gates with `--durations`, separately measuring collection, cold source
loading and warm numerical work, before promising a speedup.

### Concrete coupling and repetition candidates

| Evidence | Why selection is currently too broad | Required treatment |
|---|---|---|
| `test_open_clusters.py`: 1,034 lines, 32 definitions | Catalogue science, curation tools, observer realization, projection and PNG/PDF/SVG drawing share a file and imports | Split by provider, maintenance, realization and renderer responsibility as each owner migrates |
| `test_atlas_cli.py`: 1,612 lines, 40 definitions | Input validation, subprocess entry, physical layout, reports, snapshot/worker lifecycle and rendering matrices share one owner file | Retain installed-path and lifecycle integrations; move pure validation and furniture contracts to their owners |
| Atlas grid/orientation matrix | 3 polar choices × 2 grid settings × 2 orientations × 2 minute-label settings invoke real drawing | Verify the fault/interactions before reducing cases; test orthogonal option translation below rendering and retain meaningful visual interactions |
| Atlas report sizing matrix | 2 typography × 2 dimensions × 2 star choices × 2 polar choices | Separate arithmetic/selection from physical book-layout evidence; do not delete combined cases merely for speed |
| `test_style_contracts.py`: 1,445 lines, 69 definitions | Pure resolution and rendered/observer behavior are mixed | Keep style semantics independent of providers; retain a small public render seam |
| `test_reusable_canonical_sphere.py` | Real maximal-sky module fixtures and multiple chart families intentionally cross owners | Keep as integration/order-independence coverage, not a provider development gate |
| Three pouch tests import `test_polar_pouch_rendering` | A test module becomes another test's fixture library | Move shared fixtures into an owning helper/conftest with explicit dependencies |
| Package/dependency boundary tests | Valuable AST restrictions coexist with runtime imports of the complete package | Retain existing rules; add core/provider import and collection checks in genuinely minimal installations |

There is no evidence here for deleting independent scientific oracles,
positive/negative cases, cold-start behavior, order independence, immutable
snapshot tests or public CLI coverage. Parametrization is not by itself a
performance defect. A profile and a protected-fault map must precede reduction.

## Current functionality ledger

Source paths are relative to `src/wenu`; test names are under `tests`.
These are responsibility groups, not proposed giant packages. Several groups
need multiple eventual packages. Existing public names remain supported.

| Capability | Current source owners / located test evidence | Migration obligation |
|---|---|---|
| Time, frame, origin, status, epoch/equinox | `coordinates.py`, `coordinate_service.py`; `test_coordinate_vocabulary.py`, `test_coordinate_service.py` | Typed kernel/realization adapters; preserve meanings and failure admission |
| Position and Cartesian ephemeris protocols | `positions.py`, `ephemeris.py`, `skyfield_ephemeris.py`; `test_position_providers.py`, `test_ephemeris.py`, `test_skyfield_ephemeris.py` | One uniform state interface; retain resource chains, coverage, centres and units |
| Observer lifetime, site and observed cache | `observer.py`, `sky/realization.py`; `test_observer_resources.py`, `test_observer_boundaries.py`, `test_observed_cache.py`, `test_layer_realization.py` | Separate native state from realization, resource ownership and observation invalidation |
| Native catalogue assembly and reusable sky | `sky/maximal_sphere.py`, `sky/celestial_sphere.py`; `test_maximal_sphere.py`, `test_reusable_canonical_sphere.py` | Compatible facade/session assembly; remove concrete-provider coupling |
| Stars and visual symbols | `objects/stars.py`; `test_stars.py`, `test_stellar_symbols.py`, `test_stellar_magnitude_legend.py` | Add honest Gaia propagation through star provider; keep photometry/membership/marker law separate |
| Names, components and research policy | `star_designations.py`, `stellar_research.py`; `test_star_designations.py` | Preserve HIP/component identities, curated/contextual labels and source provenance |
| Constellation figures, labels and official boundaries | `sky/constellations.py`; `test_constellation_geometry.py`, `test_constellation_boundaries.py`, `test_constellation_labels.py`, `test_constellation_resolver.py` | Stellar endpoints consume propagated IDs; official boundaries retain defining frame |
| Nonstellar/Messier points and object identity | `objects/nonstellar.py`; `test_nonstellar_catalogue.py`, `test_nonstellar_points.py`, `test_object_center.py` | Retain label-only versus scientific layers and independent source membership |
| Open clusters and curated selection | `objects/open_clusters.py`; `test_open_clusters.py`, `test_curated_catalogues.py` | Independent provider and curation owner; preserve sizes, membership, criteria and original sources |
| Globular clusters | `objects/globular_clusters.py`; `test_globular_clusters.py` | Independent provider and its own science/conformance gate |
| Galaxies and extended geometry | `objects/galaxies.py`; `test_galaxy_catalogue.py`, `test_galaxy_geometry.py`, `test_deep_sky_polygons.py` | Preserve direction, angular dimensions, orientation and no fabricated velocity |
| Planetary nebulae | `objects/planetary_nebulae.py`; `test_planetary_nebulae.py`, `test_curated_catalogues.py` | Separate catalogue/criteria from display scale and default bundle |
| Supernova remnants | `objects/supernova_remnants.py`; `test_supernova_remnants.py` | Preserve provider-specific geometry and data fidelity |
| Milky Way and Magellanic isophotes | `sky/milky_way.py`, `sky/magellanic_clouds.py`; `test_isophotes.py`, `test_magellanic_clouds.py` | Extended celestial geometry adapter; not artificial point-body states |
| Equatorial, ecliptic, Galactic and AltAz grids | `sky/coordinate_grids.py`; `test_coordinate_grids.py`, `test_altaz_grid.py` | Constructed reference geometry; observer dependencies explicit |
| Horizon, visibility and masks | `sky/horizon.py`, `visibility.py`; `test_visibility.py`, `test_horizon_reference.py`, `test_horizon_mask_geometry.py` | Realization/local geometry service; no mutation of native sky |
| Spherical/projected geometry and clipping | `geometry/`; `test_spherical.py`, `test_projected.py`, `test_clipping.py`, `test_geometry_pipeline.py` | Preserve topology, metadata, IDs and guard/clip ordering; no provider dependency |
| All three projection implementations | `projections/`; `test_mollweide_projection.py`, `test_polar_azimuthal_equidistant_projection.py`, `test_projection_regression.py` | Keep Mollweide, stereographic and polar azimuthal equidistant; no astronomical transform hidden in alignment |
| Five ordinary chart families and target/group centres | `charts/`; `test_all_sky_chart.py`, `test_full_sky_chart.py`, `test_regional_chart.py`, `test_canonical_circumpolar_example.py`, `test_canonical_binocular_example.py`, `test_target_resolver.py` | Every public product consumes state via session/realization; preserve centre/mask independence |
| Styles, detail, modes, independent layer selection | `charts/composition.py`, `configuration/`; `test_style_contracts.py`, `test_detail_policy.py`, `test_chart_composition.py` | Pure product services; avoid loading numerical providers for option translation |
| Furniture, labels, references and physical legends | `charts/`; `test_chart_furniture.py`, `test_legend_export.py`, `test_reference_label_placement.py`, `test_constellation_labels.py` | Keep physical units, collision policy and scientific/appearance distinction |
| Matplotlib and PNG/PDF/SVG export | `rendering/`, `svg_document.py`; `test_matplotlib_renderer.py`, `test_svg_output.py`, `test_svg_cross_product_acceptance.py`, `test_output_policy.py` | Preserve semantic SVG, fonts, vector/raster choices, single save and no-clobber contracts |
| Polar planisphere pairs and calendar | `charts/polar_planisphere.py`; `test_polar_planisphere_pair.py`, `test_polar_calendar.py`, `test_polar_classroom_disk_freeze.py` | Preserve both projections, fixed classroom scene and physical scale |
| Polar pages, pouches, sheet assembly | `charts/`; `test_polar_page_export.py`, `test_polar_pouch_export.py`, `test_polar_pouch_sheet.py` | Preserve physical printable products, calendar/reference furniture and accepted appearance |
| Ordinary temporal sequences, resume and playback | `temporal.py`, `charts/sequence.py`; `test_temporal.py`, `test_chart_sequence.py`, `test_sequence_manifest.py` | Query common state/realization; preserve civil versus physical time, manifests and resume identity |
| Fixed-sky baseline and rotating-horizon reference | `charts/fixed_sky_sequence.py`, `charts/fixed_sky_orientation.py`, `charts/fixed_sky_baseline.py`; `test_fixed_sky_sequence.py`, `test_fixed_sky_orientation.py`, `test_fixed_sky_baseline.py` | Preserve distinct anchor/local instants and both scientific and graphical oracles |
| Major planets, Moon and apparent directions | `solar_system_directions.py`, `sky/solar_system_points.py`; `test_apparent_major_planets.py`, `test_moon_direction_validation.py`, `test_solar_system_directions.py` | Existing backend and one light-time owner; preserve body/barycentre distinctions |
| Resolved disks, appearance and frozen/observed sequences | `solar_system_appearance.py`, `solar_system_disk_geometry.py`; `test_moon_disk_display.py`, `test_venus_disk_display.py`, `test_frozen_earth_disk_sequences.py` | Keep physical versus magnified display geometry and chronology conventions |
| Natural-body tracks and temporal components | `sky/solar_system_tracks.py`, `temporal_components.py`; `test_solar_system_tracks.py`, `test_solar_system_track_cli.py`, `test_temporal_components.py` | Sample requested instants via kernel; preserve fixed chart axes and component admission |
| Numbered asteroids and offline minor-body resources | `minor_body_*.py`; `test_minor_body_ephemeris.py`, `test_minor_body_resources.py`, `test_minor_body_identity.py` | Separate asteroid provider; preserve exact manifests, coverage and close/rollback behavior |
| Comet discovery, identity, acquisition and photometry | `comet_*.py`, `minor_body_acquisition.py`; `test_comet_discovery.py`, `test_comet_numerical_validation.py`, `test_minor_body_acquisition.py` | Separate maintenance, physical provider and model magnitude; no rendering-time network |
| Antisolar reference | `antisolar.py`; `test_50a5b_antisolar_evidence.py` | Preserve observer-relative reference and provenance; not a new physical body |
| Satellite element snapshots and SGP4/TEME | `satellites/`; `test_satellite_elements.py`, `test_satellite_sgp4.py`, `test_satellite_snapshot_admission.py`, `test_satellite_topocentric.py` | Independent satellite provider; retain EOP/time/resource domain and Vallado evidence |
| Sampled-provider satellite candidates | `satchecker.py`, `satellite_presentations.py`; `test_satchecker.py`, `test_satellite_presentations.py` | Explicit provider/maintenance adapter; do not conflate candidates with exact visits |
| Exact crossings, batch selection and tracks | `satellite_crossings.py`, `satellites/`; `test_satellite_crossing_oracle.py`, `test_satellite_crossing_acceleration.py`, `test_satellite_crossing_batch.py`, `test_satellite_exact_tracks.py` | Kernel states for non-chart consumers too; preserve conservative completeness and solved-evidence route |
| Exact reports, tabular interchange, CLI and advisories | `satellite_crossing_reports.py`, `_satellite_tabular_reports.py`, `satellite_planning_advisories.py`; `test_satellite_crossing_reports.py`, `test_satellite_crossing_cli.py`, `test_satellite_planning_advisories.py` | Retain canonical identity, Unicode/null losslessness, atomic publication and offline advisory behavior |
| Satellite illumination and finite-Sun shadows | `satellites/`; `test_satellite_illumination.py` | Retain native/topocentric geometry, shadow transitions, physical domains and independent evidence |
| Bolometric and spectral solar radiometry | `satellites/`; `test_satellite_radiometry.py` | Preserve solar constant, exact TSIS resource/native sampling and uncertainty limits; no new Moonlight claims |
| Atlas geometry, layouts and standalone index | `atlas_design.py`, `charts/atlas_index.py`; `test_atlas_design.py`, `test_atlas_cli.py` | Public chart contract below atlas; all registered layouts including hemispheres |
| Atlas publication, reports, saved sky and workers | `charts/atlas_publication.py`, `sky/native_snapshot.py`; `test_atlas_cli.py` | Preserve frozen resources/coverage/design binding, chart numbering, physical sheets, PDF assembly and atomic failure cleanup |
| Configuration overlays, preset resources and translations | `configuration/`, `resources.py`, `translations.py`; `test_configuration_user_overlay.py`, `test_configuration_runtime_closure.py`, `test_translations.py` | Keep schema/precedence, separate layout/index/style protocols and localized labels |
| Canonical examples and installers | `example_scripts/`, `cli/examples.py`, `cli/notebooks.py`; `test_canonical_examples.py`, `test_example_installer.py` | K3.37 repairs retired notebook consumers and verifies direct notebook installer/package delivery; complete Mac acceptance pending |
| Curation/acquisition, resource packaging and offline tools | `resources.py`, `src/curated_catalogue_packaging.py` (outside Wenu), `tools/`; `test_curated_catalogues.py`, `test_repository_sources.py`, `test_open_clusters.py` | Separate maintenance/build gates, exact resource identity and offline fixtures; do not automatically execute network tools |

Full inventory prevents silent disappearance of small modules or operational
scripts not individually named above. Not every maintenance script is an
accepted public API or independently tested tool: classify each before changing
it. Five packaged notebooks were inventoried; at the baseline no direct notebook-installer test
reference was located in the 239 Python test files. Treat that as a coverage
review item, not proof that all notebook behavior fails or is untested indirectly.

Unfinished features remain unfinished: automatic/provisional minor-body
selection, detailed atlas object inventories, satellite reflected-light and
detector science, and numerical Moonlight. The current
[scientific contracts](scientific_contracts.md) govern these limits.

## Explicit native cluster motion consumer boundary

Native Python chart layers now accept an admitted motion catalogue per call and
a matching explicit TCB context epoch. `OpenClusters.position` and native layer
realization query the accepted provider/kernel and use returned vectors, retaining
ordered/duplicate identities and original state provenance. Source digest and
complete identity-set mismatches, unavailable selected rows and kernel failures
refuse without lookup fallback. Default lookup, source table bytes and metadata
remain unchanged. Observer-dependent motion is refused.

Restored v5 source skies inherit the same facade; they do not reload original
catalogues, install the model globally or become persisted epoch states. The
canonical chart guard admits matching epoch-bearing barycentric astrometry while
static neighbours retain source meaning. The consumer gate covers real saved/cold
geometry/pixels, fresh-process offline use, default native page compatibility and
the shared context/failure contracts. Provider science/SDK/reuse are unchanged;
their accepted receipts remain separate. CLI/TOML model selection, observer
adoption and any evaluated-state snapshot format remain open.

## Continuous test migration and closure evidence

1. **K1, now:** inventory and classify before runtime work. Repair the stale
   atlas index/test and three fixed-sky documentation checks found by this audit.
   Preserve the exact old test editions in the audit archive, with blob IDs in
   the inventory. Production/scientific tests remain unchanged.
2. **Every K2 onward slice:** identify changed owner, its public contract,
   affected consumers and closest existing assertions. Separate mixed tests
   when that owner changes. Record old node IDs to new node IDs, protected
   faults, retained independent oracles and fixture ownership. Do not defer
   all test reorganization to the final release or perform a speculative
   mass move before an actual implementation boundary exists.
3. **K2:** core unit and shared provider-conformance gates collect/run in a
   minimal environment with synthetic providers only. Contract tests are a
   reusable kit run independently against each provider, not one suite requiring
   every provider. Prove forbidden imports/dependencies are absent at startup
   and collection, not merely absent from selected test execution.
4. **K3–K5:** each current functionality row gains migration status, owning
   package/service, public entry points, instrumented query evidence, immediate
   seam/failure cases and an acceptance receipt. Audit direct position reads,
   saved-sky restoration and worker startup for bypasses. Keep numerical,
   visual, print and classroom acceptance separate. Pure layout/installation
   code need not query the kernel; every scientific state consumer must.
5. **K6–K8, package by package:** extract corresponding tests/fixtures and
   build an isolated wheel/environment gate with unrelated providers absent.
   The package is not complete until this passes. Keep installed product
   combinations in a separate release gate. A compatible internal provider
   change does not run that release gate or another provider's science suite.
6. **K9:** reconcile all inventory entries and functionality rows, including
   resources, tools, examples/notebooks and non-chart consumers. Any removed
   assertion needs an explicit replacement/fault argument; any capability
   changed or retired needs separate approval. Remaining gaps cannot be
   silently reported as migration coverage.

An owner/dependency-based selection manifest must accompany the first isolated
runtime gate. It records what changed, selected suites, relevant contracts and
why other suites are excluded. Follow [testing policy](testing_policy.md) for
changes to shared contracts/dependencies, unknown impact and integration.

## Verification of this audit

All 262 cached production modules and all 239 fetched test-side Python files
were checked against their exact baseline Git blobs and parsed. Public scripts
were read from `pyproject.toml`; imports, fixtures, markers and parametrization
were counted from ASTs. Targeted source/test pairs above support the findings.
No current duration, full-suite pass or executable modularity is claimed.

After the amendments, 32 actual documentation test functions executed directly
and passed in this environment. Active links/anchors were additionally checked
against the Git tree and amended documents. Three injected inventory faults
(omitting a source module, a test-side file or an installed command) each failed
the inventory gate and were restored. Pytest and Wenu runtime dependencies are
unavailable here: this is not a pytest receipt. The public-import execution and
original cleanup archive checks require the complete Mac gate below.

The amended documentation gate includes `test_current_documentation.py`,
`test_user_guide.py` and `test_fixed_sky_documentation.py`. A fresh Mac result
is required for that amended gate. Current runtime remains the accepted
production tree; K2 has not begun.

Preserved originals: [user-guide tests](archive/kernel_audit_20261018/tests/test_user_guide.py.txt)
and [fixed-sky documentation tests](archive/kernel_audit_20261018/tests/test_fixed_sky_documentation.py.txt).

## K3.16 diffuse geometry assessment and architectural resolution

**Inspected base:** main `21653198502b2b6687af8d82556a7f98922eb4fd`,
2026-10-19. Fernando selected K3.16 with “proceed” after its bounded proposal.
This assessment did not authorize a new SDK capability or snapshot format;
the subsequent service-kernel clarification is recorded below.
No runtime, SDK, source-resource, dependency or serialization change is made here.
K3.16 remains open for runtime work under the architectural resolution below.

### Source and runtime evidence

| Owner/resource | Preserved evidence | Remaining admission gap |
|---|---|---|
| Milky Way canonical `milky_way_d3.json` and five runtime single-level GeoJSON files | D3-Celestial blob `ce06eaa01d80a4eed149c538d2d162c919b58a84`, captured provenance/BSD licence; canonical SHA-256 `c6cf082cb0ffb9a6080858f673eb8f119df585b00730a5bcfd5ea43dc3f98627`; OL1–OL5 MultiPolygons | GeoJSON has no document/feature frame or epoch declaration. README says source celestial longitude/latitude degrees. Existing runtime ICRS encoding is compatibility interpretation, not recovered source qualification. Bind the canonical/provenance and actual loaded split bytes without inventing a measurement epoch |
| LMC/SMC derived GeoJSON | Document properties explicitly declare ICRS, RA/Dec degrees, outer-to-inner levels and `g_flux`; features retain cloud/level/fraction. Captured sidecar declares Gaia DR3, processing, ADQL and product digests | Loaders discard these document/source properties. No morphology measurement epoch, distance or physical origin is declared; do not assign Gaia's stellar reference epoch to a derived contour |
| LMC product identity | SHA-256 `9ad2298999577bbf96a2ad743b90106c3e971948ed2cc832e2fd33cb59f2fc4e` matches the captured sidecar | Keep byte-bound identity and processing provenance in a runtime envelope |
| SMC product identity | SHA-256 `348d0f485088d6c40efb70dd04fcad3247aa7d9a0e1fe26611b6b10e3f972695` matches the captured sidecar | Same requirement; retain cloud-specific identity and levels |
| `sky/milky_way.py`, `sky/magellanic_clouds.py` | Existing `features` preserve compounds/rings/holes; Milky Way realization also computes filled-side, area and pole-winding metadata. Native and observed paths consume raw rings; observer cache identities use paths/revision/levels | Admit immutable source/reference/geometry identity before native output or warm-cache reuse. Preserve topology and original vertex encodings. Observation/projection/rendering remain above the kernel |
| `sky/native_snapshot.py` | v5 records diffuse features plus source paths and Cloud fractions; manifest binds source digests. Restoration assigns those fields directly | Original GeoJSON document/feature properties and a runtime metadata envelope are not serialized. Extending source metadata transport requires an explicit format/legacy-admission design, not relabelling old snapshots as newly qualified |

No acquisition was run and no captured source or licence record was changed.
The PM/parallax selection used when deriving the Cloud maps does not turn their
contours into member-star states or a motion model.

### Architectural resolution: agreed service kernel

Fernando clarified on 2026-10-19 that spherical geometry and projections belong
to the shared service kernel, and subsequently requested these architectural
decisions be documented. The [agreed target and prior-K disposition](kernel_roadmap_v0.9.5.md#proposed-architecture)
are authoritative. The existing state SDK remains one component of that kernel.
Its lack of a compound-ring StateBatch variant is not, by itself, a missing
prerequisite for diffuse geometry migration.

The earlier proposal to add a new SDK geometry query/result/admission capability
and require a new snapshot format was not approved or implemented. It is withdrawn
as the default solution. Direct use of shared spherical geometry/topology and
projection services is valid kernel routing, not an exception to closure.

K3.16 will start from existing SphericalPolygons and the current geometry,
coordinate/observation and projection interfaces. Source-specific contour ingestion,
levels, fractions and qualification remain domain responsibilities; generic ring
operations and projection mathematics belong to reusable kernel services. No
artificial body/ObjectRecord is created for each contour vertex. A new query
protocol needs a concrete discovery/lifetime/dispatch requirement before it can
be proposed again; naming something a kernel does not establish that requirement.

The M9 source and snapshot evidence above remains valid. The runtime envelope
must preserve declared versus absent coordinate facts and byte-bound provenance;
metadata-preserving transport and explicit legacy/source-free behavior still
require a concrete bounded design. This architecture decision does not choose a
snapshot version, alter existing schemas, relocate code or authorize acquisition.

### K3.16 acceptance direction under the agreed boundary

- Source/geometry owners: `test_isophotes.py` and `test_magellanic_clouds.py` retain
  exact vertex/topology/level/Cloud fraction and source-metadata/refusal coverage.
- Geometry, observer and projection seams: retain independent filled-side,
  pole-winding and hole oracles; test public geometry-service use, source/returned
  geometry identity and warm-cache refusal where admission changes.
- Snapshot/product composition: preserve native/observed cold/restored geometry,
  actual atlas PNG/PDF/SVG, legacy admission and source-free process evidence for
  each transport change actually implemented.
- Dependency/installation checks: demonstrate the changed service boundary without
  concrete catalogue/product/renderer imports. Run independent SDK tests only if
  that component's code/contracts actually change; a new SDK release/pin is not
  automatically required for calling existing geometry services.

K3.16 runtime admission/transport is accepted through PR #289 after Fernando’s explicit
2026-10-20 agreement to the v6 design and successful Mac comparison retry. The Wenu-owned
`sky/isophote_sources.py` receipt preserves original properties, byte/geometry
identity and captured provenance. New v6 snapshots require and validate that
receipt; v1–v5 restore explicit legacy metadata without source access or invented
qualification. Shared kernel services retain all existing geometry mathematics.
The original assessment above records the as-is v5 evidence, not the current
transport implementation. No other pending milestone is activated.

## KG.01 shared geometry service inventory

**Assessment base:** main `cb40ede9ad0be68e6a4863c8d7b6d2c3dbb87a93`,
2026-10-19; tree `c2b9ee88c80d71bf5d71c99a2b98842eeec40c91`.
Fernando selected KG.01 after accepting revision 32. This is an assessment,
not the KG.02 interface decision, a runtime migration or the KG.06 completed-K
audit. The [machine inventory](kernel_migration_inventory_v1.json) records
`geometry_service_assessment`, inspected owner blob hashes and 66 direct
absolute-import consumer modules. All 512 locally available production/test
Python files were checked against accepted Git blobs with no mismatch.
Imports inside functions are included; relative package exports were inspected
separately. Import references locate potential callers, not executed coverage.

### Existing services and dependency boundaries

All paths below are relative to `src/wenu/`. These are current owners, not
proposed final package names.

| Current owner and public entry points | Actual responsibility/dependencies | KG.02 disposition to resolve |
|---|---|---|
| `geometry/spherical.py`: SphericalPoints, SphericalCurves, SphericalPolygons, SphericalGrid | NumPy arrays in degrees, required CoordinateSpec from `coordinates.py`, per-entity IDs/labels/names and metadata; validates dimensions/counts and grid spec equality | Reuse the data model first. Decide shared CoordinateSpec ownership and explicit topology/metadata contracts; arrays are not admitted physical state batches |
| `geometry/projected.py`: ProjectedPoint(s), ProjectedCurve(s), ProjectedPolygon(s), ProjectedGrid | NumPy planar records, finite masks and bounds; no source/provider/renderer imports in this module | Preserve collection identity and metadata after splitting; define planar scale and mutable ownership rather than treating these as immutable SDK states |
| `geometry/frame.py`: SphericalFrame, SphericalCoordinates | NumPy spherical rotations, inverse and matrix construction; frame transform normalizes longitude to [-180,180) | Generic geometry service; distinguish this orientation rotation from astronomical frame/time conversion |
| `geometry/viewport.py`: Viewport | Frozen dataclass, finite rectangular bounds, contains/size/centre helpers, NumPy | Mathematical rectangle is reusable; product chooses its extent/aspect/physical page scale |
| `geometry/clipping.py`: clip_point_to_viewport, clip_curve_to_viewport, clip_polygon_to_viewport, clip_polygon_to_convex_boundary, clip_line_segment_to_viewport, polygon_centroid | NumPy plus projected records/Viewport; nonfinite breaks and fragmented curves; convex-boundary polygon operations | Retain existing supported algorithms and their failure/empty/fragment semantics; do not claim a general spherical Boolean polygon engine |
| `projections/stereographic.py`: StereographicProjection | NumPy, spherical/projected records, SphericalFrame and Viewport; vector/scalar and collection dispatch, forward/inverse, radius helpers, legacy AltAz wrapper | Existing public service starting point; preserve EW orientation, position-angle order and antipode NaN breaks |
| `projections/polar_azimuthal_equidistant.py`: PolarAzimuthalEquidistantProjection | Subclasses StereographicProjection; overrides forward/inverse/radial math and domain checks | Preserve inherited dispatch and linear angular-radius behavior; explicitly specify supported projection capabilities rather than assuming all APIs identical |
| `projections/mollweide.py`: MollweideProjection | NumPy and geometry records; equal-area forward projection, seam-aware curve/polygon splitting, pole/winding handling, per-piece metadata expansion | Keep seam preparation with applicable mathematics. This class does not expose the same inverse/radius interface as stereographic |
| `rendering/preparation.py`: project_geometry_for_viewport, projection_cap_for_viewport, project_polygons_to_projection_cap, clip_polygons_to_projection_cap, clip_polygons_to_latitude, clip_to_latitude | Imports NumPy and geometry records; contains spherical cap clipping/intersection/slerp, filled-side complements, winding-band stitching and metadata propagation | **Mixed owner:** reusable mathematical services coexist with magnitude sizing, point_styles, radial_label_offset and diameter_marker_areas. Extract responsibilities through agreed interfaces; moving the whole module would move appearance policy into the kernel |
| `sky/milky_way.py`: _native_ring_interior and layer realization | Numerical solid-angle/orientation math combined with source ring interpretation, hole/level metadata, observed-cache and resource loading | Identify the reusable math separately from catalogue filled-side convention and source qualification; K3.16 still owns M9 admission/transport |
| `coordinates.py`, `coordinate_service.py` | CoordinateSpec/status vocabulary versus Astropy-backed scientific realization and metadata propagation | Geometry depends on the vocabulary today. Scientific conversion is a separate service/backend boundary; do not pull Astropy conversion into a plain spherical rotation |
| `charts/projection_selection.py`, `charts/boundaries.py`, `charts/styles.py` | Projection/frame allowlist and lazy construction; boundary construction plus label-anchor/style policy; horizon threshold and appearance preparation | Product selection, labels and policy stay outside; review generic boundary primitives individually. A chart's horizon cut is not the projection singularity guard |
| `rendering/matplotlib.py`, `_matplotlib_primitives.py`, `_matplotlib_axes.py` | Draw projected values, compound paths and viewport artists | Renderer remains outside; geometric service must not depend on Matplotlib |
| `sky/celestial_sphere.py`: draw_chart | Orders layer realization → selected projection callback → preparation → renderer; owns concrete layers | Retain canonical orchestration. Correct ownership/imports without introducing a parallel scientific/rendering pipeline |

### Topology and domain contracts that already cross boundaries

SphericalPolygons represents implicitly closed rings, with at least three
vertices; holes and compound-polygon identity are not dedicated typed fields.
Existing consumers use metadata such as `is_hole`,
`spherical_interior_left`, `spherical_interior_area_sr`,
`projection_cap_topology_inversion` and projection-source latitude arrays.
Mollweide seam splitting and cap clipping can turn one source entity into
several pieces. IDs, labels and per-ring attributes must expand with those pieces;
they cannot be blindly zipped against the original unsplit arrays.

The cap service performs spherical clipping **before** unsafe planar polygon
projection. Its viewport entry point derives a near-hemisphere cap using the
projection's radial inverse capability; it delegates normally when that
capability or a polygon/viewport is absent. Later viewport clipping and
chart-specific horizon/mask policy remain distinct. The current capability is
duck-typed, not a frozen common protocol. KG.02 must document those supported
branches before KG.04 changes ownership.

Geometry dataclasses generally retain writable NumPy arrays using
`np.asarray`; metadata dictionaries are shallow copies. The frozen
SphericalFrame does not imply every returned array is immutable; supplied
rotation matrices are copied and marked read-only, while construction validates
their shape, not a general arbitrary-matrix orthogonality guarantee.
Projection instances hold mutable configuration fields. KG.02 must state
ownership/lifetime/aliasing and compatibility rules; KG.01 neither changes
these semantics nor promises an immutable kernel geometry API.

### Callers and import isolation

The machine inventory records exact import names for every detected direct
absolute-import consumer, grouped conceptually here:

| Consumer group | Observed use | Boundary consequence |
|---|---|---|
| Object facades: stars, nonstellar, galaxies, open clusters and PN | Produce/consume spherical collections; dedicated globular/SNR behavior also inherits shared nonstellar mechanics | Keep object identity/source/model decisions outside shared math. Indirect inheritance and dynamic calls require later KG.06 review, not just import counts |
| Sky layers: points, constellation figures/labels/boundaries, grids, horizon, diffuse contours, solar-system/satellite/sequence layers | Construct spherical values and use existing observation/preparation helpers | Preserve supported coordinate status/spec and source identity; not every ring vertex is a physical provider object |
| Regional/full/all-sky/polar/circumpolar charts, atlas design/index/publication, reference and mask helpers | Construct projections/boundaries; call cap-safe projection, clipping and label anchoring | Chart policy remains outside; mathematical service calls should become explicit public dependencies |
| CoordinateService, positions, solar-system directions/disk geometry, temporal components and ephemeris adapters | Exchange geometry or frame rotations across science/product seams | Separate numerical geometry from backend-specific realization; do not infer identical scientific semantics from array shape |
| Renderer/primitives/label placement and geometry/projection implementations | Consume projected records or apply shared geometry | Kernel interfaces may be imported by a renderer, never the reverse |

A fresh subprocess importing `wenu.geometry.spherical` loaded
`wenu.observer`, `wenu.objects.nonstellar`, `wenu.charts.regional`,
`wenu.rendering.matplotlib`, Matplotlib, Astropy and Skyfield.
This confirms the broad `wenu/__init__.py` application facade defeats independent
geometry import today. Separately, `rendering/__init__.py` eagerly exports
Matplotlib implementations and preparation functions together. The algorithm
bodies' narrow direct imports do not establish package isolation. The existing
stdlib state SDK stays separate; no new geometry wheel or dependency is selected
by this finding. KG.02 must propose concrete placement/import compatibility.

### Existing test owners and protected faults

These tests were inspected/located, **not rerun as numerical acceptance** in
this documentation-only assessment. Their current success is not asserted here.
No new test selection, production resource, dependency or build change is made.

| Existing owners under tests/ | Evidence/faults to retain in the corresponding migration |
|---|---|
| test_spherical.py, test_projected.py, test_projected_collections.py | Dimensions/counts, grid grouping, metadata copying, finite/bounds and collection identity |
| test_spherical_frame.py | Identity, inverse round trip, orthogonal constructed rotations, scalar input and public import |
| test_projection_regression.py, test_projected_geometry_projection.py, test_projection_geometry.py | Existing stereographic formula, EW flip, dispatch/types/metadata, argument refusal and antipode disconnected breaks |
| test_polar_azimuthal_equidistant_projection.py | Known pole/quadrants, forward/inverse round trip, linear radius, PA/flip order and invalid-domain refusal |
| test_mollweide_projection.py | Known centre/equator/seam/pole coordinates, local equal-area scale, seam splits, finite breaks and winding closure |
| test_clipping.py, test_viewport.py, test_projection_and_clipping_contracts.py | Viewport/convex clipping, split curves, cap-before-projection ordering, four-corner cap coverage, horizon composition, filled-side complements and winding-band fragments |
| test_viewport_rendering.py, test_projection_selection.py | Renderer viewport composition and product projection/frame admission |
| test_isophotes.py, test_magellanic_clouds.py | Real/source and synthetic rings, hole/level/fraction selection, independent filled-side/raster membership and observed-cache behavior |
| test_reusable_canonical_sphere.py and affected atlas/polar product owners | Source-free/cold/restored geometry and output equivalence at integration acceptance; exact specimens chosen from the actual later diff |

KG.02 must map these owners to the concrete interface/placement diff and add
only missing seam/isolation evidence. Numerical oracles must remain independent
of the service implementation. KG.05 needs actual output acceptance in addition
to unit geometry tests; this inventory alone does not establish it.

### Findings and next bounded work

1. **KG01.F1:** mathematical clipping/topology shares rendering preparation with
   appearance helpers; split by responsibility rather than moving the whole file.
2. **KG01.F2:** geometry import runs the broad application facade; establish an
   independent service import with compatibility for old callers.
3. **KG01.F3:** CoordinateSpec ownership and implicit topology/metadata expansion
   need explicit public contracts.
4. **KG01.F4:** generic ring math is mixed with source-specific interior policy;
   preserve source facts while identifying the reusable operation.
5. **KG01.F5:** writable arrays, shallow metadata copies and mutable projection
   configuration need honest lifecycle/aliasing semantics.

**KG.01 acceptance:** PR #282, main 887408ae; 36 Mac documentation tests
passed at 20de328c and Fernando confirmed clean synchronized main/cleanup.
KG.02 was subsequently selected explicitly; its
[public contracts and placement proposal](kernel_contract_k1.md#14-kg02-geometry-service-contracts-and-placement-plan)
address KG01.F1–KG01.F5. This is a design delivery, not runtime migration.
Do not relocate implementations, invent a geometry query, change science,
force a snapshot version or activate K3.16 here. The coordinate guide remains
current because this assessment changes no scientific semantics or runtime
ownership. The later KG.06 audit will determine modifications to completed K
deliveries using the established services, retaining their applicable receipts.


## KG.05 composed geometry acceptance

Selected on 2026-10-20 after PR #285 and clean main 608bc91d. This is
integration/evidence work within the agreed KG sequence. No production code,
mathematics, dependencies, catalogue bytes or snapshot schema change.

| Evidence | Owner and claim |
|---|---|
| Canonical and compatibility identity | Existing spherical and projection/clipping contract tests retain exact public aliases and keep appearance policy outside kernel |
| Independent installed services | Existing isolated kernel-wheel consumer runs base imports without NumPy and numerical geometry with NumPy, blocking Wenu, Astropy, Skyfield, Matplotlib, pandas and SPICE |
| Real atlas composition | Existing two-chart cold/saved/serial/spawn test exports PNG/PDF/SVG, compares PNG pixels and verifies physical PDF pages and book assembly |
| Real polar composition | New north/south cold/restored test uses actual catalogues, native realization, composed stereographic geometry and real PNG/PDF/SVG; compares source/projected records and PNG pixels, checks vector document sizes, and forbids source reload |
| Physical page policy | Existing polar-page export/rendering owners retain A4 composition, calendar, registration and text-layout checks |
| Retained lower-level evidence | PR #284 and #285 Mac receipts cover unchanged numerical tests, source-free subprocess reconstruction and root wheel/sdist/editable packaging; no blanket repeat |

### G05-1: equidistant full-catalogue composition gap

The same real polar specimen with `polar_azimuthal_equidistant` fails on both
poles with `ValueError: longitude must be finite`. The magnitude-4 specimen has 519 stellar rows, including one non-finite
position (HIP 55203); `PolarPlanisphereChart.project_equatorial_geometry` sends
points to projection before latitude filtering, and the equidistant numerical
service requires finite longitude. The stereographic path accepts these inputs.
This discovery is **not** a licence to filter sources or relax numerical guards
inside KG.05. Its scope is a concrete audit/correction candidate for KG.06/KG.07.
The existing finite-input projection tests remain valid; they did not establish
this full-catalogue composition claim. No general equidistant output acceptance
is claimed. Strict expected-failure cases keep the failing specimen executable;
an unexpected pass requires review and removal of the marker with the correction.

KG.05 delivers the evidence and this explicit finding; it does not close all
geometry integration, K3 or K5. KG.06 must determine the responsible boundary
and whether correction is needed in previously accepted deliverables. KG.07
must verify any agreed correction, including the unmarked equidistant specimen.


Local verification: 15 selected composition cases passed and the two precise
G05-1 cases were expected failures. The 196.98-second combined run had 14 passes,
two expected failures and one missing-cache-file failure; fetching the unchanged
`tools/render_48e4_polar_pages.py` from the exact GitHub base resolved that final
case (1 pass, 0.93 seconds). No test or repository tool was changed to resolve it.
After tightening the expected-failure guard to require the exact diagnosed
message, both G05-1 cases still reproduced (8.79 seconds). Eight tooling cases
passed. Documentation: 33 passed; three checks require archive/evidence files
omitted from this local cache and remain for the complete Mac checkout. New
links/anchors passed; complete Mac documentation and composition gates are pending.
The coordinate guide remains current: this task changes evidence, not numerical
semantics or ownership. A low-DPI rendered polar specimen was visually inspected;
this is not a new print/style approval or a classroom/production-suite claim.


## KG.06 completed-K service-boundary audit

**Inspected base:** main `52c8315cd3bd58386c105f3edf05ee2354292796`, selected
by Fernando’s 2026-10-20 proceed after PR #286 and clean synchronized main.
This is a read-only implementation/caller assessment and documentation delivery.
No production, dependency, resource, schema or test assertion changes.

**Decision:** retain the accepted state/catalogue routes; they do not need a
blanket redo. One demonstrated geometry-composition correction, **G06.C1**, is
assigned to KG.07. Known partial K3 work remains partial. This audit does not
activate KG.07, K3.16, new AX science or package extraction.

### Method and service direction

The complete GitHub tree has 291 production/SDK Python files; every local blob
matched the inspected base. Actual definitions/callers were followed through
Kernel/Session/TimeService, catalogue adapters, public positions, observed-cache
inputs, request scopes, native reconstruction and projection dispatch. An AST
import scan of all 22 kernel modules found no application, catalogue, backend or
renderer imports; only numerical geometry/projection leaves use optional NumPy.
These static checks establish placement/import facts, not numerical accuracy.

Application assembly/source adapters may call state and geometry services.
Kernel code must not import them. Geometry records and polygon vertices do not
need ObjectRecords or state queries. Source-specific ellipse/glyph definitions,
constellation membership/anchor policy and page layout remain above the shared
geometry operations. The label mean helper is not bypassing a public kernel mean
service (none exists); this audit demonstrates no need for an additional API.
Broad `wenu` legacy imports still assemble application dependencies; canonical
`wenu_kernel` imports, not the broad facade, carry the independent-service claim.

### Per-deliverable dispositions

Each completed K0/K1/K2/K3 and KG item has an entry below and a machine-readable
record in `completed_k_service_audit.deliverables` in the migration inventory.
That record names actual owner paths, callers, services, test owners and remaining
limits. PR numbers identify bounded acceptance, not automatic parent closure.

| ID / accepted PRs | Actual boundary reviewed | Disposition / retained evidence |
|---|---|---|
| K0.01 / #234, #235 | Pinned baseline tree and preserved receipt | Retain; no redo; test_current_documentation.py |
| K0.02 / #235 | Exact preserved Git blob ledger; no runtime dependency | Retain; no redo; test_current_documentation.py |
| K0.03 / #235, #270, #280, #281 | Shared-service diagrams and explicit scope control | Retain; no redo; test_current_documentation.py |
| K1.01 / #236 | Inventory describes source/test/operational owners; not routing proof | Retain; no redo; test_current_documentation.py |
| K1.02 / #236, #237, #240, #241, #255, #283 | State/reference and coordinate contracts distinguish physical and geometry domains | Retain; no redo; test_records.py |
| K1.03 / #236, #238, #239, #240 | Independent error channels, exact cache and certified angular reuse; unknown is not zero | Retain; no redo; test_reuse.py |
| K2.01 / #237, #242 | Explicit references/provider ownership; synchronous session lifecycle | Retain; no redo; test_sessions.py |
| K2.02 / #237, #238, #239 | Validate admission before exact cache; bounded/canonical reuse requires provider certificates | Retain; no redo; test_reuse.py |
| K2.03 / #240 | SI Cartesian representation separate from angular direction and velocity availability | Retain; no redo; test_cartesian.py |
| K2.04 / #241 | Explicit directed time conversion admission, coverage and rounding receipt; no implicit chain | Retain; no redo; test_time.py |
| K2.05 / #242, #255 | Provider supplies offline cases/activity/mutation hooks; core imports no concrete provider | Retain; no redo; test_conformance.py |
| K3.01 / #243 | Application owns SPK/session/resolver rollback; kernel does not acquire resources | Retain; no redo; test_minor_body_resources.py |
| K3.02 / #244 | Request-local mutation journal/lease and ordered cleanup; no kernel/product reverse dependency | Retain; no redo; test_request_generation.py |
| K3.03 / #246 | Shared request scope; native observer-free realization and existing composed export | Retain; no redo; test_request_generation.py |
| K3.04 / #248 | Source-bound metadata and immutable rows; application snapshot is not a persisted StateBatch | Retain; no redo; test_stellar_state.py |
| K3.05 / #247, #248 | Finite rows -> owned Kernel/Session -> returned states; NaN source rows retained only as geometry | Retain; no redo; test_stars.py |
| K3.06 / #248 | Public Stars.native_positions; finite endpoints and inherited coordinate specification | Retain; no redo; test_constellation_geometry.py |
| K3.07 / #271 | Public full-source native positions; constellation grouping/minimum/anchor placement remain product policy | Retain; no redo; test_constellation_labels.py |
| K3.08 / #272 | Kernel-derived inputs precede cache lookup; retained Skyfield no-deflectors stars/figures and Astropy labels | Retain; no redo; test_stars.py |
| K3.09 / #249, #250, #251, #273, #274 | Unknown epochs remain None; source-bound lookup admission is distinct from physical qualification | Retain; no redo; test_nonstellar_catalogue.py |
| K3.10 / #252, #253, #254, #275 | static_direction; returned centres feed native/observed points/outlines before caches | Retain; no redo; test_galaxy_geometry.py |
| K3.11 / #249, #255, #256 | catalogue_lookup; row epochs/masks/order preserved; returned vectors precede observation cache | Retain; no redo; test_open_clusters.py |
| K3.12 / #276 | catalogue_lookup; generic/Messier/Caldwell membership and target-centre consumers use returned states | Retain; no redo; test_nonstellar_catalogue.py |
| K3.13 / #277 | family catalogue_lookup; half-light/structure/common-name policy remains source/product owned | Retain; no redo; test_globular_clusters.py |
| K3.14 / #278 | family catalogue_lookup; native points/observed symbol centres use returned states; fixed glyph scale remains product owned | Retain; no redo; test_planetary_nebulae.py |
| K3.15 / #279 | family catalogue_lookup; signed IDs and source shell centres; missing-PA circle remains product policy | Retain; no redo; test_supernova_remnants.py |
| KG.01 / #282 | Five original coupling/contract findings mapped to actual owners | Retain; no redo; test_current_documentation.py |
| KG.02 / #283 | Explicit geometry/state separation, units/topology/aliasing and optional dependency contract | Retain; no redo; test_current_documentation.py |
| KG.03 / #284 | Canonical records/frame/viewport/ring mathematics; identical legacy aliases | Retain; no redo; test_spherical.py |
| KG.04 / #285 | Numerical services moved unchanged; appearance retained in application | **KG.07 correction G06.C1**; test_projection_and_clipping_contracts.py |
| KG.05 / #286 | Real cold/saved atlas and stereographic polar composition; strict equidistant failing specimen | **KG.07 correction G06.C1**; test_projection_and_clipping_contracts.py |

### Accepted AX composition affecting K seams

No new science is reviewed for enablement. Each accepted AX ID also has its own
machine-readable disposition; the grouped table only keeps this view compact.

| Accepted items / PRs | Composition and retained limits | Disposition |
|---|---|---|
| AX.01–AX.03 / #257–#260 | Source qualification stays cluster-owned; object-independent complete-input core uses SDK state/reuse; angular certificates do not become apparent/Cartesian guarantees | Retain source, numerical, conformance and refusal receipts |
| AX.04–AX.05 / #261–#262 | Per-call native adoption and observer contract; default lookup remains unchanged | Retain; contract alone enables no runtime |
| AX.06–AX.08 / #263–#265 | Generic rectilinear core, actual Cartesian batches and explicit TimeService/convention receipt; cluster adapter calls the core | Retain; no family-specific duplicate propagation required |
| AX.09–AX.10 / #266–#267 | Concrete ERFA/Astropy backend owns leap/EOP/code/site admission; shared realization consumes evaluated state once | Retain independent parallax/Lorentz/resource/correction-count evidence; no hidden extra light time |
| AX.11–AX.12 / #268–#269 | Explicit reception guards before projection and horizontal request/CLI selection; saved sky reconstructs sources | Retain; no new frame/model or real stellar/PN/SNR motion |

### G06.C1 correction contract for KG.07

**Origin G05-1; affected acceptance KG.04/KG.05, downstream of K3.05.**
`Stars._native_catalogue_coordinates` queries only finite rows through the state
provider. Missing-coordinate rows deliberately retain IDs/metadata as geometry,
never DirectionStates. `SphericalPoints.finite` exposes this distinction.
`StereographicProjection.project_points` currently passes the entire coordinate
array to `project_spherical`; its equidistant subclass rejects non-finite
longitude in `_project_aligned`. `PolarPlanisphereChart` reaches this before
latitude filtering. This is the shared point-geometry dispatch boundary, not a
reason to change catalogue membership or state admission. The numerical guard
was retained unchanged by KG.04; the failure is not evidence of altered formulas.

The existing strict north/south failing specimens reproduced at this base
(two expected failures, 20.13 s). Additional read-only probes of real native
stars, figures, anchors and Milky Way polygons found the same stellar failure
on both poles; figures, anchors and polygons projected successfully. A temporary
finite-only point view isolated that failure and projected successfully on both
poles. This diagnostic is not an implemented workaround or full output acceptance.

The bounded correction belongs in the existing shared point-projection adapter:
project finite input rows, retain missing-row slots and entity metadata, and
keep strict scalar/domain checks. Preserve all finite formula/order/flip/frame
behavior, empty batches and invalid finite latitude/opposite-pole refusal. Do
not fabricate zero vectors, drop source IDs, relax `_project_aligned` validation,
modify scientific sources or compensate in Matplotlib/chart appearance policy.

| KG.07 verification owner | Required fault/evidence |
|---|---|
| `test_projected_geometry_projection.py` | Mixed/all-missing/empty points preserve row order, IDs, names, labels and metadata; finite coordinates agree with direct numerical calls; source arrays remain unchanged |
| `test_polar_azimuthal_equidistant_projection.py`, `test_projection_and_clipping_contracts.py` | Strict numerical invalid-domain refusal, both poles/frame/flip and canonical/legacy identity remain intact |
| `test_stars.py::test_missing_native_positions_never_become_zero_direction_states` | Missing source positions stay out of state publication; no catalogue membership repair |
| `test_reusable_canonical_sphere.py::test_kernel_geometry_polar_cold_saved_outputs` | Remove both strict xfail markers only with correction; both equidistant and stereographic poles must export cold/restored identical geometry/PNG pixels and real PDF/SVG sizes |
| Installed consumers in `test_curated_catalogues.py` | If kernel bytes/version/pin change, verify isolated numerical wheel plus root immutable pin/wheel/sdist/editable access; retain unrelated state/time/provider science receipts |

### Unresolved work already assigned elsewhere

| Finding | Actual owner / disposition |
|---|---|
| G06.U1: observer resource/cache identity | K3.18 now adds active EOP/leap/backend content and live SPK descriptor admission before shared cache lookup, accepted PR #291 after 402 focused Mac cases. M10 model/source qualification remains K3.25. Earlier receipts retain their original limits. |
| G06.U2: assembly and atlas private helpers | K3.19 now delegates concrete reconstruction to application assembly (Mac verification pending); `charts/request_generation.py::_render_atlas_sheet_request` still imports private atlas helpers under K3.21. K3.03 lifetime/dispatch receipt did not close these boundaries |
| G06.U3: generic realization placement | The object-independent core/time/observer adapters remain transitional Wenu owners consuming the SDK; no kernel reverse import was found. Concrete ERFA/Astropy realization stays outside the stdlib core. Complete service/facade placement review remains K3.18/K5.02; no new module/protocol is selected |
| G06.U4: source qualification and remaining geometry | Nonstellar physical gaps and constructed/unitless compatibility are disclosed, not qualified by passing lookup. Diffuse metadata/transport is K3.16; constructed references K3.17; product closure K3.20–K3.24/K3.39–K3.40. KG services do not close those pending consumers |

### Evidence retention and audit limits

Retain the exact accepted PR receipts only for the services/routes they tested.
K3.04–K3.15 returned-state, source admission, mutation, identity/order, cache
refusal and restored-source tests still protect the intended faults. KG.03/04
finite-data numerical/isolation/install evidence remains applicable; KG.05 adds
real composed atlas and stereographic output while exposing G05-1. None proves
Gaia propagation, all observer resource identities, every K3 consumer, final
print/classroom appearance or a frozen SDK. No lower-level science suite was
repeated for this documentation-only audit. The coordinate guide remains current:
no scientific meaning, ownership or numerical implementation changes here.



Audit integrity checks: 43 unique deliverable IDs cover all 31 accepted K/KG
items and AX.01–AX.12; all 91 referenced owner/test paths exist in the inspected
Git tree. All 73 archived blobs match the preservation ledger. Present active
Markdown links/anchors pass; omitted local archive/evidence targets are checked
against the complete tree. The documentation gate has 33 local passes; its
three archive/evidence checks require the complete Mac checkout. No SDK/provider
numerical suite rerun is claimed. Complete Mac documentation acceptance remains
pending on this audit branch.


## KG.07 G06.C1 point-projection correction

Selected on 2026-10-20 after accepted PR #287, main 9e71ab49 and clean Mac
cleanup. This implements only the demonstrated G06.C1/G05-1 correction. G06.U1–U4
remain with their existing K3 obligations; no new science, source qualification,
schema, renderer/style policy or diffuse transport is activated.

`StereographicProjection.project_points`, shared by the equidistant subclass,
now preserves missing-coordinate rows as NaN projected slots and calls the same
numerical operation for finite rows only. Entirely finite input retains the
original call and operation order. The numerical equidistant guard itself is
unchanged: direct missing/invalid numerical input and finite invalid latitude or
opposite-pole geometry still refuse. Source IDs/names/labels/metadata and original
read-only arrays remain intact; the stellar adapter still admits only finite
rows as states. No source row is deleted and no zero vector is fabricated.

The existing projected-geometry owner gains mixed, empty, all-missing and
finite-invalid-domain regressions. On the old implementation ten cases failed
and four passed; the failure was reproduced before changing the owner. The real
north/south polar export test removes both expected-failure markers. It requires
successful cold/restored outputs for both projections, including exact PNG
pixels, source/projected records and physical PDF/SVG dimensions. The installed
isolated numerical consumer also executes the corrected mixed batch and retains
strict direct numerical refusal.

Kernel dev11 is pinned by immutable commit `f0a2e247d9ed0061d256891fcf4962d1c41fd4f9`.
The root distribution requests the same optional geometry extra. Changed kernel
bytes justify isolated wheel and root wheel/sdist/editable verification; no new
dependency or package is introduced. Numerical formulas, resource bytes,
observation/correction ownership and native snapshot schema remain unchanged.
Complete Mac acceptance is pending. The coordinate guide records the missing
geometry/state distinction without changing scientific coordinate semantics.


Local verification covers all 103 correction-gate cases through focused
component executions: 102 unique cases passed; the unchanged LMC example is
blocked by missing local de440s.bsp and standard JPL TLS download validation.
The 102 include all four real polar specimens (452.72 s, no expected failures),
18 finite/alias/native-atlas compatibility cases, 78 unit/domain/source-admission
cases and both isolated-kernel/root-installation cases. A six-case followup also
verifies that finite stereographic results exactly match the old full-batch
numerical call with missing rows present. Only `project_points` differs in the
projection method ASTs. All 205 source SDK and eight gate-tooling tests pass.
Documentation has 33 local passes; three checks need archive/evidence files
omitted from this cache. Present active anchors are checked separately against
actual documents and missing destinations against the complete Git tree. North
and south equidistant PNG specimens were visually inspected as render evidence,
not a new print/style/classroom approval. Complete Mac gates remain pending.

The built dev11 wheel also passed the complete isolated stdlib SDK gate: 204
passed and one optional numerical test skipped with NumPy deliberately absent.
The separate installed numerical consumer exercises the corrected service with
NumPy present and application/backend/render imports blocked. The SDK selection
manifest records current source/test digests and this bounded acceptance.


## K3.17 constructed-reference service routing assessment

**Base:** main `6e6fcd964a23d7aa5a4bc4e398e43381ad93977f`, after accepted
PR #289 and clean synchronized Mac receipt. Fernando selected K3.17 on
2026-10-20 following its explicit constructed-reference proposal (roadmap revision 41).

The inspected production paths already use the established services. No runtime
routing defect was demonstrated, so this delivery retains their implementations
and adds missing consumer/refusal evidence rather than replacing working science.

| Existing owner/consumer | As-is route and retained responsibility | Closure evidence |
|---|---|---|
| `sky/coordinate_grids.py` | Source-specific meridian/parallel/plane sampling and equinox selection stay with the grid; typed kernel curves pass through `CoordinateService` to native ICRS or observer AltAz. Native realization uses a local copy | Existing cadence/equinox/local-state contracts plus changed service results/refusal across FK5, true ecliptic and Galactic planes |
| `sky/points.py` | Pole/keypoint definitions retain their defining frames; existing service handles native ICRS and the subsequent observer transformation. No physical provider query is created | Changed native service coordinates reach the point collection; observed consumers return the actual service result; refusal reaches both paths |
| `sky/constellation_boundaries.py` | Sample official constant-RA/Dec edges in FK4/B1875, including existing pole-closure handling, before transformation. Membership maps ICRS queries back to that defining frame | Independent Astropy/source preservation tests retained; changed native/observed return coordinates and membership results are consumed; refusal has no raw-coordinate fallback |
| `sky/horizon.py`, `charts/horizon_mask.py` | Altitude-zero and visible hemisphere remain observer-local geometry. Existing kernel records, inverse projections and domain projection service feed above/crossing/below chart policy | Local horizon refuses fixed native realization; existing visibility/round-trip/complete-sphere tests retained; crossing-mask preparation uses returned shared-domain geometry and propagates refusal |
| `charts/_masking.py`, `charts/reference_furniture.py`, `charts/reference_policy.py` | Mask composition/appearance and furniture/keypoint/label policy remain chart responsibilities. Boundaries/grids/points use the owners above; projection/domain calls use established shared services | Existing independent mask composition, frame/equinox, appearance, label/semantic and request-reuse contracts |
| `sky/native_snapshot.py` | Existing v6 restoration reconstructs original reference classes through the sky layer registry, preserving grid definitions and FK4 boundary data; no new schema or special reference-state format | Real cold/restored reference geometry agrees, altered shared-service values reach both paths, and service refusal reaches both without original-source loading |

Source geometry, transformations, sampling, mask algorithms, renderer, dependencies,
SDK code/pin, resources and snapshot format are unchanged. Kernel geometry aliases
already denote the canonical classes. Accepted K3.16 atlas/four-polar PNG/PDF/SVG
and source-free-process receipts remain applicable because their production tree
is unchanged. No full SDK, parent export or production-suite repeat is required.

This is bounded reference routing evidence, not a full kernel freeze. K3.18 still
owns complete observer/backend/resource identity and cache invalidation; accepted
maximal boundary caches are not recertified against those broader identities here.
K3.19 application assembly and K3.39/K3.40 remaining geometry/consumer review stay
open. Product construction does not become physical-object propagation.

The coordinate guide remains current: no coordinate meaning, frame/equinox,
provenance or correction ownership changed. Gate: `constructed-reference-routing`,
plus tooling and documentation. Acceptance remains pending the focused Mac receipt.

## K3.18 observer resource and cache assessment

Base: accepted PR #290/main `56f5e8ff`. Fernando selected this existing milestone
on 2026-10-20 after the bounded observer/resource/cache proposal.

| Existing owner | Finding and disposition |
|---|---|
| `observer.py` | Already owns/finalizes one ephemeris and closes idempotently. Add byte/descriptor admission at geometry reuse, refusing closed/changed resources; retain request ownership. |
| `sky/observed_cache.py` | Site/time/name/path alone concealed changed EOP/leap/backend inputs. Extend its existing key rather than introduce another cache or transform service. |
| `objects/stars.py`, `sky/constellation_lines.py` | Existing maximal stellar cache/figure consumers already share that key and query native state before lookup; retain no-deflectors Skyfield science. |
| Nonstellar/cluster points/outlines, PN symbols, boundaries, MW/Clouds | Existing shared point/polygon helpers already reach the same key. Keep source/selection/topology policies with their owners. |
| `coordinate_service.py`, `astrometric_coordinates.py`, `astrometric_observation.py` | Retain the generic backend adapters, explicit time conversions and offline receipt/correction ownership. The nominal observer realizer has no warm observer cache. No scientific rewrite or state-SDK change is needed here. |
| `charts/request_generation.py` | Existing owned/borrowed lifetime, rollback and cleanup contracts are retained and selected in the gate. |

The new boundary test applies an explicitly synthetic one-second UT1 offset to a
real local IERS-B table in memory. Warm transformed boundaries must change and
match a cold transformation; removing the resource-key contribution fails this
contract. A source-free restored-sky test exercises the same resource change.
Synthetic file tests protect byte/descriptor binding and refusal, not ephemeris
science. A local probe also verified the descriptor path against an actual SPK
shipped in the installed Skyfield test data, without downloading resources.

No new module/package, source bytes, kernel API/pin, geometry/projection/renderer
algorithm, observation model or snapshot schema is introduced. Final facade/
packaging review remains K5.02, M10 model qualification remains K3.25, and K3.19
assembly stays pending. The coordinate guide remains current: coordinate meaning,
mathematics, correction ownership and source provenance are unchanged.

## K3.19 application construction assessment

Base: accepted PR #291/main `37bcb851`; selected by Fernando’s 2026-10-20
“Proceed” after the concrete application-assembly explanation and clean receipt.

| Existing coupling | Refactoring |
|---|---|
| `CelestialSphere.add_*` directly imports/constructs astronomical classes | Move all 20 existing bodies to application `SkyAssembly`; retain explicit convenience delegates and generic ordered layer registry/chart pipeline. |
| `maximal_sphere.py` mixes profile/public entry points with concrete build sequences | Keep profiles/admission/facades; move the two existing ordinary/native sequences to the same application owner. |
| `NativeSkySnapshot.make_sky`, frozen facade classes and `_restore_fixed` reconstruct concrete families | Move construction/frozen facades to assembly; keep data encoding, validation, mapped records and v1-v6 semantics in the snapshot owner. |
| Atlas worker initialization calls `snapshot.make_sky()` | Retain this common route; verify supplied restore/refusal and real spawned output rather than add another worker factory. |

All 20 moved constructor bodies and both complete factory executable bodies
match the baseline AST after receiver/assembly-argument normalization. Their
mathematics, ordering and source policies are retained. The new module is an
enduring application composition boundary, not a scientific provider or kernel
leaf. Concrete snapshot metadata validation remains with the existing source
codec; the broad Wenu facade still imports families. Independent astronomical
package extraction is not claimed by this change.

Owner tests protect supplied assembly results, refusal/no fallback, defaults and
layer order. Existing full cold/restored geometry, source-free fresh process,
legacy/corruption and atlas PNG/PDF/SVG cold/saved/spawned tests remain selected.
The root wheel/sdist owner verifies the moved module and isolated installed use.
The coordinate guide remains current: no coordinate meaning, provenance,
correction ownership or scientific calculation changed.


## K3.20 ordinary chart consumer assessment

Assessed at main `2bdbc4a9963690f7c78cea483357292521a90f3a` after
K3.19 Mac acceptance and cleanup. This is a test/evidence closure of existing
ordinary chart consumers, not a new implementation of their mathematics.

| Consumer | Existing owner and service route | Verification |
|---|---|---|
| Five families | `request_chart.py` constructs FullSkyChart (planisphere), AllSkyChart, RegionalChart, CircumpolarChart and BinocularChart; `view.py` enters the same preparation owner | Request/view/family owner gates |
| Named and explicit centres | ResolvedTarget.coordinate uses the admitted catalogue lookup for named source records; explicit coordinates remain caller input. Object centre and RegionalChart.from_coordinate use CoordinateService | Actual KernelSession result changes alter regional/binocular centres; kernel refusal reaches preparation after success |
| Constellation/group framing | RegionalChart.from_constellations reads returned stellar layer geometry and optional official boundary geometry, retaining endpoint IDs and framing policy | Changed public geometry moves the centre; each selected geometry owner can refuse, without raw catalogue fallback |
| Field membership | spatial_selection reads spherical_centers where available, otherwise spherical_geometry; geometry IDs and the chart projection/viewport determine selection | All six fixed families follow changed centre results and refuse after success; unions/exclusions and explicit motion pre-cull exemption retained |
| Masks | Chart render owners pass constellation and horizon restrictions to existing domain/coordinate services and mask composition | Existing complete mask/horizon owner suites retain frames, winding and projection order |
| Content/detail/style/mode | Composition and detail application select/configure layers; they do not calculate catalogue positions. Canonical draw_chart asks layers for realized geometry | Existing layer/realization, detail, composition and style suites protect independence and render-local state |
| Context/title furniture | Target titles consume target.coordinate; legend centre coordinates use CoordinateService; magnitude counts consume rendered ProjectedPoints | Injected returned values appear in title/context, refusal propagates; existing legend count tests protect final viewport membership |
| Export and repeated requests | request_generation owns the existing request scope, composition and export; view/drawing share established lifecycle | Existing request owner suites protect rollback/order/ownership and per-product export |

No production bypass was demonstrated in these owners. No runtime relocation,
new coordinate protocol, numerical rewrite or kernel release is needed here.
The coordinate guide and scientific contracts remain current: source gaps,
lookup limits and observation methods are unchanged. Accepted K3.16/KG output
receipts and K3.19 real cold/saved/spawned atlas PNG/PDF/SVG and installation
receipts remain applicable because this delivery changes no production bytes.
The new tests label injected geometry and state changes as synthetic; they do
not claim physical model accuracy. K3.21 retains the chart/atlas private-helper
cycle, design/index/publication/report closure. Moving-body model qualification
and remaining provider migrations retain their separate K3 rows. K3/K5 remain
partial; this does not certify all Wenu functionality or independent packages.


## K3.21 atlas sheet and consumer assessment

Base: main `89756d957696b8baf2cd69f52f6a6878cc3a8484`, accepted K3.20.
The generic request owner previously imported six private atlas drawing/report
helpers and constructed the atlas sheet chart itself; atlas publication imported
its request type from that generic owner. The existing sheet chart/presentation,
validated request and render/report bodies now live in `atlas_sheet`. Both batch
publication and generic request execution consume its public contract. The
generic executor keeps scope, safe temporary staging and atomic no-clobber
publication. The new module separates one-sheet rendering from batch scheduling/book
publication and request-resource lifecycle. No new package or scientific
capability is introduced; legacy imports remain aliases.

AST comparison against the base confirms the moved request record and render
body are identical except owner imports, public-entry guards and replacing the
generic generation wrapper with its single existing ChartExportResult. The
executor wraps that result identically. Fourteen existing sheet/presentation/
report/layout definitions have identical ASTs after relocation; the leaf imports
neither the batch publication module nor generic request execution.
Layout, native frame, grid/label rules,
figures, report composition, PNG/PDF/SVG settings and finally-close are unchanged.

| Consumer | Disposition and evidence owner |
|---|---|
| Design/tiling/footprints | Existing constructed geometry with kernel projections; no catalogue state query required. Keep `test_atlas_design.py` |
| Standalone index | Existing canonical PolarPlanisphereChart/layer realization. New actual-kernel changed-vector and after-success refusal test in `test_atlas_cli.py`; retain index CLI/veil/scene tests |
| Sheet execution | Public validated request and render result; test executor consumes actual returned paths/results under its active lease, and refusal cleans staging without output |
| Sheet report and magnitude scale | Existing completed rendered-star geometry; retain count/area/physical-frame tests |
| Whole-catalogue appendix | Demonstrated raw-coordinate availability read replaced by full-source public native positions, IDs and magnitude metadata. Preserve first-HIP deduplication, source order, finite/magnitude filtering and values. Test returned NaNs, missing source fallback and real-kernel refusal |
| Publication/book | Existing CLI dispatch, exact design binding, deterministic page order, PDF assembly, no-clobber/race/failure contracts retained |
| Saved sky and workers | Existing source-free assembly, request scope and native realization; real cold/saved/serial/spawned PNG/PDF/SVG comparisons and cleanup gates remain required |
| Installed access | Existing wheel/sdist owner verifies changed module bytes and isolated public alias/count-result/refusal consumption without source checkout |

The coordinate guide and scientific contracts remain current: no numerical
formula, physical model, source bytes, dependency, SDK, snapshot v6 transport,
layout or rendering algorithm changes. Retain accepted lower-level numerical/
conformance receipts. Catalogue-count availability is not an evaluated-epoch
claim. K3.22 physical polar products and later moving-body/provider rows remain
separate; this does not freeze K3/K5 or extract astronomical packages.

An inherited portrait-review assertion required both frame dimensions to fill
the page exactly. The unchanged layout instead fits a fixed aspect ratio inside
both font-derived allowances. Running the original accepted rendering body
reproduced the same 219.797294 mm versus 220 mm assertion failure. The test now
requires the limiting-dimension fit, unchanged page aspect and containment in
both allowances; no tolerance widening or production layout change is used.
Independent full packaged-Hipparcos comparison with the old count function
returned identical report data, IDs and magnitudes: 5,041 selected, 263 invalid
and 112,914 fainter rows at magnitude 6.

## K3.22 physical polar product service assessment

Base: main `8d4b1ed593eaf19f4ad7594b64983ccde2b0e724`, accepted PR #294.
Fernando confirmed synchronized clean main and cleanup, then selected K3.22
after the kernel/product distinction. Plan revision 46 was committed before
test implementation. This bounded item does not activate K3.23.

| Existing owner | Service/caller finding | Disposition |
|---|---|---|
| polar_planisphere / polar_planisphere_pair | Canonical sky draw, CoordinateService observer conversion, ProjectionSelection and same-class kernel projections; cap/latitude functions alias kernel domain services | Retain unchanged; existing both-pole/projection/domain owners remain selected |
| polar_calendar / polar_calendar_furniture | Existing Astropy mean sidereal standard-midnight calibration and product 365-day scale; face projection supplies paper direction | Retain calibration; new returned-kernel-direction/refusal consumer check |
| polar_horizon_overlay | HorizonReference and CoordinateService supply ICRS horizon/reference geometry; public face/kernel projection precedes physical placement | New changed-coordinate/refusal checks for both projections and downstream pouch consumption |
| polar_page_export | CoordinateService returns ecliptic reference anchors, kernel projection maps them; existing composed chart export and finally-close own physical face output | New returned-anchor/refusal and second-face-failure figure-cleanup checks |
| polar_page_furniture/rendering, magnitude scale, style/detail/curation | Immutable physical/presentation records and existing canonical renderer/furniture boundaries | Retain classroom scene, physical dimensions, label clearances and single-save owners |
| polar_pouch_furniture/rendering/export, polar_pouch_sheet/rendering/export/preview | Consume resolved horizon/furniture; physical translation/rotation, fold/window/text and image previews are product policy | Retain unchanged; actual two-face and imposed-sheet PNG/PDF/SVG exports with A4 dimensions for both projection choices |

No raw catalogue-position bypass or duplicated shared projection implementation
was found in these owners. No production refactoring is necessary in this slice.
Geometry products do not require artificial object-state queries. Source-model
qualification, the final common coordinate/observer API freeze and astronomical
package extraction remain their existing later obligations.

New tests extend four existing owner modules. A fault injection bypassing the
public kernel projection result fails both calendar consumer cases (0-degree
change instead of the required returned 90-degree change). Unmodified routes
pass. Returned coordinate changes reach both pouch horizons; later coordinate,
projection and reference failures propagate. Existing calibrated calendar,
physical page/registration, pouch/window/hour/fold and classroom tests remain.

The focused physical-product gate passes 162 cases locally in 9.70 s, including
18 actual fabrication files (two projections, two faces plus one imposed sheet,
three formats). Retain accepted KG/K3.16 four real cold/restored polar scene
PNG/PDF/SVG and K3.21 installed/atlas receipts: no production bytes changed.

An exploratory overbroad selection also included the ordinary observer-visible
FullSkyChart planisphere owner, which belongs to accepted K3.20 rather than
physical K3.22. Exact-array comparisons there failed intermittently even with
all new K3.22 tests excluded. This is not reported as passing evidence or fixed
here; the final gate selects all physical polar owners and no ordinary
FullSkyChart owner. No production change or weakened assertion hides that
separate observation. Any additional correction needs its own agreed scope.

The coordinate guide and scientific contracts remain current. Eight tooling
cases pass; 31 documentation cases pass locally and five complete-checkout
archive/asset/inventory checks remain for Mac. All 20 polar production blobs
are exact accepted-base bytes; complete remote production/test inventories match.

## K3.23 observer-time sequence consumer assessment

Base: accepted PR #295/main `738c4fc6581be337cc4d0fa521ae52d6c33c3a92`.
Fernando confirmed clean main/branch cleanup and selected the ordinary temporal
sequence proposal. Revision 47 was committed before tests; the demonstrated
viewport correction was documented before editing its implementation.

| Existing owner | Assessment and disposition |
|---|---|
| temporal.py / sequence_arguments / configuration sequence translation | Retain existing UTC normalization, physical sampling, display timezone, frame naming and playback validation |
| charts/sequence.py | Already substitutes every frame instant and calls the canonical static generator with effective configuration; no duplicate numerical implementation found |
| request_generation / layer realization | Retain per-frame observer/context, resource ownership, common state/coordinate/geometry and canonical export pipeline |
| sequence_manifest.py | Retain schema 1, portable declared-plan identity, completion hashes, compatibility-before-render and selective resume |
| cli/chart.py | Retain existing sequence request dispatch and translated effective configuration |
| FullSkyChart.viewport | Same-chart frame export failed at strict composition validation after independently recomputed circle fits. Reuse its existing immutable result on the frozen chart; preserve every function body/formula and guard |

Two new sequence tests use a labelled synthetic observation backend with real
KernelSession, Stars, request preparation, realization, projection, renderer
and actual PNG saver paths. They establish consumption and time/cleanup routing,
not an observational numerical oracle. Simulation instants reach each context;
changed kernel-returned directions reach both frames and change PNG bytes.
A second-frame kernel refusal preserves only the first completion; owned
observers/leases close and resume renders only the unfinished frame.

Manifest checks distinguish physical versus civil instants (including repeated
civil hours), playback cadence, reference equinox and effective configuration.
Same-size corruption must fail SHA-256 verification, missing files regenerate,
and untouched frames reuse. Removing the hash check fails this regression.
Restoring uncached viewport computation fails the actual sequence consumer;
the corrected path passes. All FullSkyChart function bodies match the base AST:
only the import and viewport decorator change. Viewport immutability and strict
refusal for changed chart parameters are tested.

Focused local gate: 150 cases pass; the existing real two-frame catalogue
export/resume case is blocked by missing DE440s and a certificate-failed JPL
download (151 cases remain required on Mac). No ephemeris is substituted and
no skip/xfail is added. Eight tooling checks pass. Retain accepted lower-level
SDK/observer numerical and source/package/atlas receipts; the Mac real sequence
case separately establishes real integration at this revision.

Resume identity remains the existing declared request/configuration/timeline/
playback contract and verified output bytes. It does not establish automatic
current backend/resource equivalence or universal physical accuracy. K3.24
fixed-sky, K3.25 onward moving-body model work and K5 freeze remain open.
The separate exploratory ordinary horizon exact-array observation recorded in
K3.22 is not declared closed by this viewport fix. Coordinate/scientific guides
remain current; no frame, epoch, time-scale or observation formula changes.

## K3.24 fixed-sky consumer assessment

Base: accepted PR #296/main `4e62f47abdd4b341a40038697fdb601ecd1dbf99`.
Fernando confirmed clean main and branch cleanup, then selected the explicit
fixed-sky/frozen-baseline/rotating-horizon proposal. Revision 48 was committed
before implementation.

| Existing owner | As-is finding and disposition |
|---|---|
| fixed_sky_orientation.py | Already transforms constructed FK5/J2000 references through CoordinateService at anchor and local instants; retains the established tangent-angle correction, not a solar-hour shortcut. Production bytes unchanged |
| fixed_sky_sequence.py frame resolution | Observer construction preceded the cleanup try; local construction failure leaked the anchor. Anchor close failure also prevented local close. Register each successful acquisition in ExitStack; numerical orientation call and canonical request replacement remain unchanged |
| fixed_sky_sequence.py generation | Cold and loaded-sphere modes already call canonical static generation with effective configuration and frame-local time; retain generation body unchanged |
| fixed_sky_baseline.py | Independent observer-time complete-render baseline and PNG/SVG/PDF comparison helpers already use appropriate services; retain production bytes unchanged |

Before correction, the four cleanup-failure cases plus returned-orientation test
produced two failures and three passes: leaked anchor after local construction
refusal and unattempted local close after anchor close refusal. All five pass
after the scoped ownership correction. Every other function body in the sequence
module is identical; the orientation call is AST-identical. Original orientation
and baseline source files match the base bytes.

Coordinate-service instrumentation changes returned local geometry and observes
the resulting angle change; later refusal propagates. Anchor and local contexts
are recorded independently; J2000 equinox remains distinct from source epoch.
The existing independent projected-reference oracle retains its original
relative/absolute tolerances (1e-5/1e-12). This does not establish exact all-object
fixed-scene physics or new state propagation.

Constructed two-star output checks use a labelled synthetic observation backend
with real kernel/native stellar directions, Astropy coordinate services,
canonical request/layer/projected/renderer/saver paths. Cold versus loaded-sphere
runs agree in source/selected IDs, spherical and projected coordinates, PNG
pixels, normalized SVG graphics and actual rasterized PDF pixels. Realization
contexts use frame instants rather than the different anchor. The complete
observer-time baseline is generated separately and differs from the anchored
candidate; changing only the anchor leaves baseline plan identity unchanged.

A kernel refusal after warm reuse propagates without overwriting prior outputs;
owned observers close and the reused sky's request lease is released. Reuse
keeps one unbound container versus two cold builds, not cached evaluated states.
Effective configuration, layer registry and returned orientation are preserved.

Local final available gate: 45 passed in 6.29 s; eight existing real-Observer
cases are blocked by missing DE440s and certificate-failed JPL download. The
53-case Mac gate retains all eight without skip/xfail. Eight tooling cases pass.
No catalogue bytes, dependency/SDK, snapshot/manifest schema, numerical formula,
renderer algorithm or extraction changes. Coordinate/scientific guides remain
current; K3.25 and K5 remain separate.

## K3.25 major-planet and Moon state assessment

The existing SolarSystemPointLayer, AstrometricDirectionRealizer and
SkyfieldApparentDirectionRealizer already separate geometric state, one-way light
time and apparent correction. Retain those algorithms. Default point assembly had
called the raw EphemerisStateSource directly. A Wenu adapter now uses the existing
Cartesian SDK without changing it; each borrowed session is scoped to one original
request, with no reuse cache or ownership transfer. Custom injections and later
track/disk/minor-body consumers retain their separate obligations.

M10 filename inference is repaired: both DE-looking and arbitrary renamed files
remain unqualified unless a caller supplies a declaration, which is explicitly
labelled. Exact byte digest and segment coverage remain recorded. Independent
physical-model qualification is still unknown; this repair does not invent an
acquisition manifest or assert that any renamed file is a particular DE release.

Existing direction/apparent/point owners plus the new adapter seams protect returned
SI values, velocity, resource/request mismatches, out-of-coverage refusal, warm
refusal, retarded time, all seven planet targets and Moon, and single apparent
correction. Deliberately bypassing the default adapter fails the changed-direction
assertion. The real eight-body raw-versus-routed comparison requires installed
DE440s on Mac and refuses absent offline resources rather than downloading.

## K3.26 disk and sequence consumer assessment

Three existing default construction owners called raw EphemerisStateSource directly:
`sky/venus_disk.py`, `sky/solar_system_disk_sequences.py` and
`sky/frozen_earth_disk_sequences.py`. They now adapt geometric queries through the
existing K3.25 Cartesian service. Keep the raw reception/apparent backend and
explicit injected-factory compatibility. No numerical solver or geometry engine
is rewritten. The appearance and physical disk geometry modules are byte-identical;
sequence numerical ASTs are identical after normalizing adapter assembly and the
source variable. The Sun phase query at reception and frozen Earth/planet states
consume returned kernel values, not reconstructed provider inputs.

The three component display owners reused results on context equality and observer
identity before checking live resources. A new regression reproduced all three
returning cached geometry after resource closure. Existing observer-resource keys
now precede reuse (live SPK only for frozen geometry, without observer EOP); the same context object shares components, while a separate
context performs fresh source/kernel admission. All three regression cases pass.
The observer remains borrowed and no resource is closed by these adapters.

Returned-value/refusal seams cover existing single/observed Venus and Moon and
frozen Venus/Mercury routes, including exact epoch order, initial Earth vector,
Sun phase input and unchanged display-capability restrictions. Deliberately
bypassing default observed kernel assembly fails both body cases. Constructed
backend raw/routed comparisons generate equal nonempty PNG pixels via the canonical
CelestialSphere/projection/magnification/renderer pipeline for all three models.
Those seams are labelled synthetic and do not establish physical accuracy.

The full `resolved-disk-routing` gate includes real offline DE440s raw/routed
appearance and sequence parity at a fixed site/date. Local DE440s is absent, so
that case fails its explicit offline preflight and remains required on Mac with
no skip/download. K3.27 tracks, new capabilities, SDK changes and extraction are
outside this assessment; K3/K5 remain partial.

## K3.27 natural-body track consumer assessment

The existing sampler already evaluates each exact requested sample, inserts major
anchors, assembles apparent ICRS directions and performs one fixed-product-axis
transform. Retain it. Default binding and mixed-request planetary binding exposed
raw Skyfield target sources. The track owner now adapts these known planet/Moon
bindings through the existing Cartesian interface, preserving raw observer/apparent
roles and explicit generic protocol compatibility. No asteroid/comet source or
acquisition implementation changes. The actual mixed resource-session binding
method is exercised with constructed offline state fixtures, including closed
session refusal.

The shared component owner had reused geometry by context equality and observer
identity before live resource admission. A regression reproduced cached return
after resource closure; it now checks the established observer key and shares only
within the same context object. Paths and major symbols still share one trajectory;
a new equal-valued request must re-admit and can refuse without stale fallback.

Sixteen constructed returned-state/refusal cases cover eight natural-body
descriptors through default and mixed bindings. Bypassing the adapter fails all
sixteen; those fixtures are not physical-accuracy evidence. Two actual canonical
PNG comparisons cover full versus start-only components via public request
registration, style, preparation and drawing, preserving exact pixels and samples.
The sampling/one-transform function AST is unchanged after removing binding
adapter assembly; temporal policy, request registration and annotations are
byte-identical. Existing Ceres/comet compatibility cases remain in the gate.

The full natural-body-track-routing gate includes real offline DE440s parity at a
fixed site/date for eight scientific-API tracks. Local DE440s is absent; that case
refuses preflight rather than skipping/downloading. Existing chart admission still
rejects satellite tracks, so Moon API coverage is not a new UI capability.
K3.28/K3.29 state adoption and K5 freeze remain separate.

## K3.28 asteroid routing assessment

As-is inspection found `MinorBodyResourceSession` already owns manifest-derived
numbered identity, receipt/digest/frame admission, one SPK opening and borrowed
planetary composition. Point and track consumers already receive that binding.
The missing boundary was kernel transport: the accepted adapter admitted only
one resource and reconstructed a base state, which would discard minor-body
solution/segment fields. It now admits all explicit chain resources and uses
the original record with returned PV. The astronomical backend and its numerical
formulas remain unchanged.

M7 is implemented for acceptance: complete Ceres facts have moved verbatim into
`src/wenu/data/ceres_solution_v1.json`; the public constant and descriptor remain
compatible. Installed acquisition receipts/SPK hashes are still checked by the
existing owner. No new source facts or physical qualification are inferred.

The observer-only warm track key did not cover an independently closed asteroid
session. Both Ceres and numbered-asteroid regression cases returned stale warm
geometry before correction. The existing sharing owner now asks the resolver
to re-admit the binding before reuse. Changed source identities evaluate afresh;
the same admitted binding still shares samples within one request.

Local evidence includes retained state/lineage, returned-state/refusal and
dependency-domain tests; real synthetic-backend public request PNG parity for
both identities; deliberate adapter-bypass failures; and isolated installed
manifest access. Complete Mac acceptance passed through PR #301 (211 focused,
36 documentation and eight tooling cases), including real Ceres/DE440s parity.
Comet state/report adoption is addressed below; K3/K5 stay partial.

## K3.29 comet consumer assessment

| Existing route | Assessment and disposition |
|---|---|
| Manifest identity/solution → offline SPK session | Existing validated class/designation/alias/model/coverage/digest/frame owner retained; known comet target sources now use the accepted Cartesian adapter |
| Geometric source → point/track | Original state type, solution/non-gravitational parameters, segment and complete SPK chain survive returned PV; original light-time/apparent/sampling mathematics retained |
| Provider PsAng → point/major symbol | Adapter previously hid this optional hook; forwarding retains the existing value or absence and propagates provider refusal without deriving a new model |
| Warm track components | Observer key alone cannot admit a closed comet session; the existing asteroid resolver check now covers comets too |
| Discovery → typed rows | Existing explicit provider retrieval/parser/identity/provenance boundary retained; perihelion filter is not a visibility forecast |
| Photometry → typed sampled models | Existing bounded observer-specific Horizons acquisition/cache/parser retained; these scalar model quantities are not positional state queries |
| Typed records → table/JSON/CLI | Existing consumers retained and instrumented to require returned samples, missing values, extrema epochs and provenance; failed characterization cannot overwrite previous output |

No new numerical implementation, schema, source bytes, acquisition policy,
SDK/dependency or renderer change is required. Astronomical source/model
knowledge and product reporting remain outside generic state services. Automatic
selection/visibility and physical accuracy limits remain explicit. Synthetic
session/output seams do not replace the complete Mac gate's real Encke/161P
SPK and DE440s comparisons. K3.30 antisolar routing and K3/K5 closure remain open.

## K3.30 antisolar constructed-reference assessment

| Existing consumer | Disposition |
|---|---|
| Comet point missing-angle fallback | Replace raw Sun target input with existing Cartesian adapter for known Skyfield; retain raw observer/apparent roles and original direction calculations |
| Sampled comet symbol fallback | Reuse the same existing point-owner helper, keeping actual sample observer/time and fixed product axes |
| Provider PsAng | Preserve optional value, precedence and refusal; never perform an unnecessary Sun query |
| Conjunction/opposition exclusion | Preserve thresholds and head-only geometry; record unavailable constructed tangent |
| Explicit `CelestialPoints` antipode | Retain Astropy/unit-direction conversion and construction-time anchoring; transport immutable source/observation receipt on native and observed geometry |

No physical antisolar object, numerical rewrite, SDK/package/dependency change,
resource acquisition, saved-schema change or renderer algorithm is needed.
Before correction, all six point/symbol provenance/routing seam cases failed and
the explicit antipode receipt case failed. Bypassing the adapter after correction
fails both fallback cases. Raw/routed point and sampled-symbol PNGs agree through
the actual canonical renderer with labelled synthetic apparent inputs. All
original antisolar numerical function ASTs are unchanged. Independent retained
50A.5B evidence tests remain selected; real Encke/161P acceptance additionally
compares the original raw Sun chain with the adapted fallback using offline SPKs.
K3.29 is accepted through PR #302 (273 focused, 36 documentation, eight tooling
Mac cases); K3.30 complete Mac acceptance and K3/K5 closure remain pending.

## K3.31 satellite state service assessment

| Existing boundary | Disposition |
|---|---|
| Snapshot bytes and canonical OMM records | Existing digest/schema/ordering/full-NORAD validation, immutable data and external admission retained; no positional query invented for loading or selection |
| Scalar/accelerated SGP4 | Original calculation bodies retained privately; public calls transport returned SI Cartesian states through existing SDK in the current SGP4 owner |
| TEME native state | Explicit Earth-centred geometric reference; the ICRF-only ephemeris adapter is not reused by relabelling frames |
| Time/model/resource identity | Original split UTC JD, source epoch/age and model/version retained; explicit offline TAI transport labels bind installed leap-table identity, complete canonical record and optional supplied snapshot receipt |
| Array order and duplicates | Backend route and input sequence retained; unique SDK time rows restored to original ordered outputs |
| Geocentric/topocentric transformations | Existing Astropy TEME/ITRS, WGS-84 subtraction, EOP evidence/coverage and vacuum policies retained; consume returned kernel PV |
| Later products | One retained installed-snapshot scan protects assembly; K3.32–K3.36 completeness/product migration remains separate |

Before correction, both scalar/array transport seam cases and the observer
returned-PV case failed. Deliberately returning raw values after kernel admission
also fails all three cases: registration alone cannot satisfy the contract.
Original initialization, state construction and scalar/array calculation ASTs
are unchanged except private method names/dispatch. Element, snapshot,
external-admission, acquisition, Earth-fixed/topocentric and SDK owners are
byte-identical to the base. Existing Vallado near/deep-space vectors and separate
Skyfield/Astropy transformation evidence remain selected.

Registration is request-scoped and borrowed, with unknown uncertainty and no
reuse certificate or invented prediction-validity range. The original SGP4
status exception is preserved. Changed snapshot/time receipts before evaluation
refuse; successful earlier use cannot mask a later kernel or EOP refusal.
No new physical model, package/module, dependency, resource bytes, schema,
acquisition policy or renderer algorithm is introduced.

K3.30 is accepted through PR #303 (117 focused, 36 documentation and eight
tooling Mac cases), with clean main and branch cleanup confirmed. Complete
K3.31 Mac acceptance and K3/K5 closure remain pending.

## K3.32 sampled satellite candidate assessment

| Existing route | Disposition |
|---|---|
| Explicit query → submit/poll | Existing one-call provider boundary retained; no automatic retry or new network/acquisition policy |
| Exact receipt → normalizer → typed evidence | Existing identity, count, task/time/order/refusal validation retained |
| Exact local cache → explicit receipt replay | Original bytes and request/EOP identity retained; successful replay consumes the same parser, and later corrupt cache loads refuse |
| Typed evidence → text/JSON presentation | Existing record interface retained; changed synthetic sample values and response identity reach reports |
| Candidate track/sample/singleton → drawing | Already uses CoordinateService, kernel spherical records and canonical domain/projection/rendering; no production rewrite required |
| Licensing/coverage and physical meaning | Existing audited limitations retained; sampled candidates remain distinct from exact crossings, propagation and continuous coverage |

Three instrumented canonical-draw cases require returned coordinate values and
refusal after prior success. Discarding the returned service geometry fails all
three. A synthetic exact-receipt replay case requires changed provider values,
UTC/UT1 samples, response identity and candidate-only semantics in reports and
layers; dropping supplied RA fails that case. Network acquisition, SGP4 and
fabricated positional SDK queries are prohibited in these presentation seams.
Existing tests retain PNG/PDF/SVG exports, semantic identities, labels, error
states, corrupt-cache refusal and single explicit request behavior.

Production, source resources, numerical models, SDK/dependencies, serialization,
provider policy and rendering algorithms remain byte-identical to the base.
No live provider interaction or current permission/accuracy claim is made.
The coordinate and satellite scientific guides remain current: their meanings
and audited limitations are unchanged. K3.31 is accepted through PR #304 after
77 focused, 36 documentation and eight tooling Mac cases, followed by clean
main/cleanup confirmation. K3.32 complete Mac acceptance and K3/K5 closure remain
pending; K3.33 completeness/product obligations are separate.

## K3.33 exact satellite consumer assessment

| Existing route | Disposition |
|---|---|
| Complete/adaptive scan → SGP4 → observer service | Already consumes returned Cartesian kernel TEME states through the accepted public propagator and existing topocentric chain |
| Cone/shell selector → shared exact solver | Retain tri-state domains, no-false-negative invariant, complete ordered selection identity and explicit fallback/fail-closed policy |
| Multi-field coordinator → field-altitude service/admission/solver | Revalidate complete request and current airmass values before solving; retain order, independent intervals, chunks and atomic failure |
| Solved event → track realizer | Keep exact snapshot/object/model/epoch checks, event anchors, bounded adaptive sampling, original limits and returned state/refusal consumption |
| Retained track → path/event/singleton → chart | Existing coordinate/kernel geometry/domain/projection/rendering interfaces; no resampling or propagation during presentation |
| Matrix evidence and fresh worker | Existing strict bytes, identities, refusal/publication and explicit execution boundaries retained; new small synthetic workers exercise actual services |

No production rewrite is needed. New state seams require changed kernel PV to
change exhaustive events, selector outcomes and default track vertices; refusal
reaches exact solving and track realization after prior success. Separately
bypassing the kernel route at each of those three owners fails the seam.
Discarding coordinate results fails path/event/singleton drawing checks. A
cross-request stale-admission fault fails the current-service batch check.

Existing independent analytic/adversarial tests remain selected for tangent,
grazing, between-sample, disconnected, endpoint, seam/pole, tolerance and limit
behavior. A canonical one-record synthetic snapshot additionally produces a
narrow positive-duration pass whose exhaustive and accelerated events agree.
Fresh exhaustive/accelerated workers agree on actual positive synthetic results,
without invoking the historical medium production benchmark.

One existing airmass-boundary assertion assumed a particular refusal message.
The theoretical 30-degree boundary can round just below the computed threshold;
both the explicit exceeds and uncertifiable branches correctly refuse it. The
test now accepts those two refusal messages; numerical policy is unchanged.

Production/kernel sources, source bytes, numerical formulas, acquisition/policy,
SDK/dependencies, schemas and rendering algorithms remain unchanged. Coordinate
and satellite scientific guides remain current. Historical production matrix
receipts retain their original version/domain/performance meaning; this gate
makes no new production capacity or global continuous-error claim. K3.32 is
accepted through PR #305 after 61 focused, 36 documentation and eight tooling
Mac cases, followed by clean main/cleanup confirmation. Complete K3.33 Mac
acceptance and K3/K5 closure remain pending; K3.34 onward remains separate.

## K3.34 satellite report consumer assessment

Assessment base: main `0cde175ae859e172301936562fbab950f3be8892` (PR #306),
identical tree to tested `8db716de`. K3.33 is accepted after 86 focused cases
(221.47 s), 36 documentation cases (3.44 s) and eight tooling cases (6.958 s)
on Fernando's Mac, followed by confirmed clean main and branch cleanup.
Revision 58 selects this bounded consumer audit before implementation.

| Existing owner | Service boundary and disposition |
|---|---|
| `satellite_crossing_reports.py` | Validates ordered solved batch/domain values, source and context identity; canonical immutable report, no state recomputation. Retain implementation |
| `_satellite_tabular_reports.py` | One schema-derived projection of the report, strict reconstruction and explicit masks/Unicode null flags. Retain implementation |
| `cli/satellite_crossings.py` | Application-owned assembly of existing snapshot admission/coordinator, current validation, report and atomic no-clobber publication. Retain implementation |
| `satellite_planning_advisories.py` | Validated reports and caller-owned planning units, existing half-open overlaps and neutral general-profile output; no network/facility writes. Retain implementation |

The closest existing tests cover report identity/strict decoding, tabular round
trips, CLI protocol partition/status/path behavior and advisory overlap/profile
validation. New evidence extends those same owners: three real CLI input modes
consume changed Cartesian kernel values through the existing coordinator and
refuse state failure or changed altitude admission after success. All published
format identities/bytes are checked, with ordered positive/zero fields and a
real two-call validation subset. The installed elements are explicitly synthetic;
only altitude admission is replaced with a labelled synthetic service result.
Single-instant specimens test composition, not continuous events or physical
accuracy. K3.33 retains the independent adaptive/completeness/worker evidence.

Three solved-report/interchange/advisory cases preserve changed values, warnings,
Unicode labels, identities, order and null future-science fields while state and
network access are prohibited. Serialized ECSV corruption and a contradictory
VOTable null flag refuse. Staged-write and publication-race faults preserve
atomicity and the other writer. Deliberate implementation faults are checked
separately: all five experiments fail their closest cases (12 expected failures),
then every production file is restored and compared with the base.

No production change is necessary: these consumers already use their appropriate
result/service boundaries. Reports and offline overlap do not need artificial
state queries. Coordinate and satellite guides, source map and scientific models
remain current. Existing K3.31/K3.33 numerical/SDK/worker and unchanged installation
receipts are retained; no production benchmark or consumed external authority is
reused. Complete K3.34 Mac acceptance remains pending. K3.35 onward, extraction
and K3/K5 closure remain separate.

## K3.35 satellite illumination and shadow assessment

Assessment base: main `054176b9e1612c2f1138c72ddeabab96786b2c6b`, PR #307,
identical tree to tested `11ccdb2f`. K3.34 is accepted after 68 focused cases
(28.39 s), 36 documentation cases (3.87 s) and eight tooling cases (7.888 s)
on Fernando's Mac, followed by confirmed clean main and branch cleanup.
Revision 59 records the bounded K3.35 plan before implementation.

| Existing owner/boundary | Finding and disposition |
|---|---|
| Illumination evaluator Sun source | Known Skyfield source was called directly. Assemble the existing Cartesian adapter in the current constructor owner; preserve injected protocols and already adapted sources |
| Transition finder Sun source | Same direct Sun source gap. Use the same assembly helper; retain exact time/resource/EOP provenance |
| Transition satellite state | Public SGP4 already uses accepted Cartesian transport. Preserve it; map kernel refusal to the existing typed propagation failure with cause |
| Occultation, twilight, contact and complete transition numerics | Existing algorithms and policies comply; retain unchanged implementations and independent oracles |
| Bolometric evaluator and spectral/resource owners | No algorithm/resource change; retained bolometric compatibility cases run with the owner. K3.36 resource metadata remains separate |

The two new boundary checks fail before the changes: known Sun input has no
Cartesian assembly and kernel propagation refusal escapes the existing typed
illumination API. After the thin adapter/exception changes, returned Sun vectors
control twilight and occultation; returned Sun/satellite vectors reach the real
contact evaluator. Repeated use rechecks Sun query/resource and EOP refusal.
Custom sources retain their protocol and no mandatory resource attribute.
These fixtures are explicitly synthetic; they do not qualify captured SPK data
or physical accuracy. A separate real offline DE440s case compares the retained
raw-protocol geometry and short transition result with the adapted route.

Three deliberate faults bypass the Sun adapter, bypass the satellite state
transport or drop the typed kernel-refusal mapping; each must fail its closest
case before restoration. The original numerical/policy/result definitions are
AST-identical, and the final patch is checked against the exact base to exclude
other scientific changes. Existing independent spherical overlap, Sun altitude,
WGS-84/contact classification, hidden-pair transition, empty interval, budget,
tangent and directed-event evidence remains in the gate. Unchanged historical
SPICE/Skyfield validation tools/receipts are retained for their original domains;
no new external validation run, benchmark or consumed execution authority is
claimed. The real offline composition case requires the existing Mac resource
and never acquires it.

One production owner changes; source map responsibility remains current. The
coordinate and satellite guides record unchanged scientific meaning with the new
assembly ownership. SDK/dependency/build, source bytes, schemas, renderer and
radiometry-resource facts are unchanged. Complete Mac acceptance remains pending;
K3.36 onward, package extraction and K3/K5 closure remain separate.

## K3.36 solar radiometry and M8 assessment

Assessment base: main `3463c10211055a8b08505a676edaf8071e6a9917`, PR #308,
identical tree to tested `bde9d8f4`. K3.35 is accepted after 62 focused cases
(60.54 s), 36 documentation cases (4.95 s) and eight tooling cases (8.009 s)
on Fernando's Mac, including real offline DE440s parity, followed by confirmed
clean main and branch cleanup. Revision 60 records this bounded task first.

Bolometric and spectral consumers already use the appropriate accepted geometry
interface. They need no additional state queries. M8 is the demonstrated gap:
TSIS DOI/URL/date, byte identity, header/units, grid and audit integral were
Python source facts. The new packaged declaration moves those values unchanged
and is validated before a private frozen runtime record, compatibility aliases
and public identity defaults are published. Duplicate/unknown/missing fields,
invalid schema/type/date/digest/units/grid/integral or a fabricated redistribution
status refuse. No missing-data fallback is admitted. Existing public identity
fields/default values and provenance output remain compatible.

Existing parser, external CSV guard, resource validation, native trapezoidal
integration and all scaling expressions are AST-identical. The spectral
evaluator's only body change derives its two source-provenance strings from the
admitted metadata. Bolometric source and numerical policy are untouched. The
whole spectral owner retains malformed-resource/grid/uncertainty tests and safe
mocked LIME protocol cases; no LIME binary or other external tool is executed.
New complete-geometry cases prohibit state re-evaluation and retain distinct
bolometric/spectral integrals and uncertainty meaning. Same-length wrong CSV
bytes must fail digest admission before reaching the parser.

Metadata tests protect original byte identity, legacy constants/defaults,
immutability, strict admission and authoritative returned facts without fallback.
An installed-consumer test uses unmodified build rules: exact metadata bytes
ship in wheel and sdist, an isolated process imports and consumes the installed
metadata/numerical owner, and deleting the declaration makes a fresh import
fail. Only synthetic curated build fixtures and numerical specimens are used;
no captured spectrum is fabricated or redistributed.

Three deliberate faults return a stale metadata record, ignore duplicate keys
or bypass the external CSV digest; each must fail its closest case before
restoration. The original external TSIS receipt at accepted d1edeb46 (runtime
8e930db2) remains applicable to unchanged source bytes, admission values and
parser/integration mathematics. Its independent integral agrees within the
retained 1e-9 W/m² receipt tolerance. No fresh retrieval, new external CSV run,
current permission or additional physical accuracy is claimed. K3.35 observer/
Sun and shared SDK numerical/isolation receipts remain applicable.

One production owner and one declaration change; build rules, public exports,
SDK/dependencies, source CSV/SPK bytes, science-record schemas and renderer do
not. Source map and satellite guide record ownership; coordinate meanings and
the coordinate guide remain current. Complete Mac acceptance remains pending.
M8 closure does not close other metadata findings, K3/K5, extraction or K3.37.

## K3.37 public consumer assessment

Base `fc535c3b` includes accepted K3.36/PR #309: 61 focused cases in 74.02 s,
36 documentation cases in 4.75 s and eight tooling cases in 12.610 s. Fernando
confirmed clean main/upstream equality and both branch deletions.

As-is assessment found current command owners already compose accepted services:
chart/view/request, atlas-sheet publication, comet records/acquisition boundary,
satellite coordinator/report, and resource-only installers. No replacement
command, SDK protocol or scientific pipeline is needed. Public exports,
configuration/preset translation and generated labels remain unchanged.

Demonstrated corrections inside K3.37:

* All five notebooks fail on retired imports; they also contain retired direct
  renderer/sky methods and debugging recipes. Migrate their teaching requests to
  current public composition; preserve filenames/date/site/magnitude/reversal,
  but explicitly retire manual artist layout rather than claim visual parity.
* An sdist built with unmodified rules omits the notebooks. Explicit package-data
  patterns deliver all five through sdist-to-wheel installation.
* Six example view-preparation refusals leak owned observers. Close on failure;
  keep successful returned-view ownership. Planisphere furniture and binocular
  title setup also move inside existing cleanup guards. No request/math changes.

Existing owner tests cover public aliases, six example/CLI view parity, immutable
configuration/default/preset translation, precedence/isolation and labels. New
tests execute every notebook cell with returned-value/refusal seams, direct
installer bytes/skip/force and five actual canonical PNG exports using explicitly
constructed catalogue/observer data. They establish composition, not new
astronomical accuracy. An isolated installed process resolves all eight generated
command helps, all exports, six installed examples and both installer operations;
it cannot borrow the source checkout and prohibits network calls.

Retain K3.19 application assembly, K3.20 ordinary chart, K3.21 atlas, K3.22–24
polar/temporal, K3.29 comet, K3.31/33/34 satellite and K3.36 resource/science
receipts for unchanged owners. Installed help is not a new full product or
provider run. No acquisition, paused Moonlight or consumed external authority
is executed. Coordinate meanings are unchanged; the coordinate guide remains
current. K3.38 maintenance/acquisition/build consumers and K3/K5 remain open.

## K3.38 maintenance and resource assessment

Base `73118315` includes accepted K3.37/PR #310: 238 focused cases in 160.98 s,
36 documentation cases in 10.23 s and eight tooling cases in 36.194 s. Fernando
confirmed clean main/upstream equality and both branch deletions.

The as-is audit covers every one of the 86 Python files under tools
plus seven explicit resource/acquisition/build owners (93 paths total).
Per-path classifications are executable inventory, not inferred numerical
acceptance from imports. Source normalization/crossmatch, source-native layout,
immutable copying and standalone external helpers are separated from application
science; independent raw comparison legs remain independent. Existing query,
acquire/install/preflight policies are retained and not run against providers.

Two demonstrated corrections use existing owners only:

* Zodiac application helpers directly transformed the ecliptic pole and chart
  centre. Route both through CoordinateService; keep mean-ecliptic J2000,
  vacuum AltAz and FK5 J2000, same target-up formula/RA-Dec title and SkyCoord
  compatibility returns. Existing Astropy expressions remain parity oracles.
* The reusable benchmark constructed three observers before its cleanup guard.
  Constructor two/three failures leaked prior resources. ExitStack callbacks
  register each successful acquisition and attempt all closes, including after
  a view refusal or one close failure. Workload/report bodies are unchanged.

Existing curation/promotion/migration tests preserve source rows/units/masks,
cross-identifications, strict selection rules, versioned selectors and evidence
hashes. New build seams verify authoritative admitted products, fresh corruption
refusal before replacing a prior publication, and build admission/publication in
an isolated process that prohibits Wenu/SDK/numerical-provider imports. Catalogue
source preprocessing is not redefined as object-state evaluation.

Acquisition tests use synthetic transports and explicit temporary resources only.
They preserve cache/no-retry, identity and atomic publication mechanisms without
new source permission, acquisition or external model claims. Existing install,
science and independent validation receipts are reused for unchanged owners;
no full benchmark, Moonlight or consumed external execution is authorized.
Coordinate meaning is unchanged; the coordinate guide remains current. K3.38
is accepted through PR #311 at main `3df69c4a`, tested `6c7f487c`: 49 focused
cases in 30.74 s and 36 documentation cases in 7.71 s; eight tooling cases
passed in the preceding run. Branch cleanup and synchronized main are confirmed.
K3.39/K3.40 and K3/K5 remain open.

## K3.39 geometry and graphics boundary assessment

Base `3df69c4adcda182af197f155f398da612c7686e1`, after accepted K3.38/PR #311.
The bounded audit inspects 48 source owners: all kernel geometry/projection
leaves, Wenu legacy facades and renderer helpers, canonical chart adapters and
the relevant reference/legend/footer/export/semantic owners. Exact base blob
identities and routes are recorded in `geometry_rendering_routing.owners`.

**Disposition: retain existing production implementations.** KG already placed
the mathematics in the kernel. Wenu facades alias those same objects; appearance
policy remains in Wenu. Projection alignment is not a frame transformation.
Regional/full-sky guards already run before preparation. All-sky coordinate
realization precedes Mollweide; polar face-cap/latitude preparation precedes
drawing. Source lookup is not repeated by generic geometry or graphics helpers.
Application reference furniture legitimately uses CoordinateService/grid and
projection services; forcing it through object-state queries would be a regression.
Legends reuse supplied rendering; export retains the canonical one-save owner.

Closest existing coverage is `test_draw_chart_supports_geometry_and_preparation_options`,
`test_regional_chart_uses_canonical_projection_before_prepare`,
`test_renderer_has_no_astronomical_or_projection_dependency`, physical renderer
label/band contracts and `test_composed_export_renders_legends_and_saves_once`.
New tests extend these same owners: altered guard/projection returns reach
preparation and drawing; refusal after success cannot draw stale geometry;
helper-leaf imports include relative imports; prepared real-projection synthetic
scenes export all three formats with scientific re-entry forbidden.

Four deliberate faults each fail the closest new contract: bypass the chart
guard, discard a returned projection, re-enter CoordinateService in graphics,
and introduce a relative reverse import into a rendering helper. All are
restored before the final gate. All original test definitions remain unchanged.
The focused gate retains existing independent cap/complement/winding/clipping,
missing-row/domain/seam, physical layout, style independence, semantic SVG and
legend/export contracts. No lower-level numerical or visual oracle is replaced.

Local focused acceptance: 247 passed in 11.94 s. Complete Mac documentation and
focused acceptance remain pending. Accepted KG isolation/installation/numerical
and K3.16/K3.21/K3.22 real cold/restored/worker product receipts remain applicable
to unchanged source/SDK/projection/renderer implementations. No new source,
numerical/graphics algorithm, SDK/dependency/module/package, schema, acquisition,
network, performance benchmark or external execution. K3.40 and K3/K5 remain open.

## K3.40 complete consumer and receipt reconciliation

Base main `0deca8c31d170914d1f913bb22c1a0038d68e95f` after PR #312; the Mac
receipt at `c43369a1` passed 247 focused cases in 18.47 s, 36 documentation in
3.87 s and eight tooling in 9.015 s. Fernando confirmed clean synchronized main,
branch cleanup and the order K3.40, six real products, then Gaia. Revision 64
records this bounded scope before implementation.

The exact current tree reconciles 388 Python files, all 290 root exports,
20 declared-export modules, eight command targets and five notebooks. Every
source path is assigned a responsibility/route and bounded accepted evidence;
all K3.01–K3.39 IDs link to their original records and merged delivery revisions.
Explicit source/AST review covers the retained raw state and coordinate calls,
not just import counts. No new applicable baseline service bypass was found;
production implementations and original test definitions remain unchanged.

| Assessment finding | Resolution |
|---|---|
| Historical counts and partial statuses still looked current | Add an exact current census and receipt graph; preserve original per-slice history, failures and retries |
| K3.36/K3.37/K3.39 still said Mac pending in some current sections | Reconcile accepted PR #309/#310/#312 receipts and current roadmap/architecture |
| Legacy data-directory acquisition helper is outside the tools-only census | Classify its import-time download/write effects explicitly; inspect source without importing or executing it |
| Original full KG.07 Mac total is not persisted | Retain original local/component/isolation evidence and applicable unchanged core receipts; use accepted K3.16 real four-polar and K3.39 row/domain/alias evidence for affected scopes, without inventing the missing total |
| Whole-K3 wording could conceal remaining scientific obligations | Keep M5/M10 source/model gaps, Gaia/AX limits, legacy transport, satellite domains, ownership/error/reuse and K5/extraction exclusions explicit |

Closest existing protection is the complete repository-source inventory,
K3.38 maintenance census and K3.37 public export identity tests. Three added
tests in the same inventory owner reject omitted paths/exports, stale source or
notebook hashes, missing family receipt links, unreconciled sensitive calls and
erased scientific limits. Deliberately removing one source, corrupting one source
hash, removing a public export or erasing a model limit each fails its intended
contract. All faults are restored before the final gate.

The focused consumer-reconciliation gate retains dependency, assembly, public
sheet and canonical/legacy alias contracts. It does not rerun unchanged physical
oracles, full SDK/installations or catalogue/product export matrices. Import/call
evidence locates responsibility; accepted independent numerical and real product
receipts support the numerical/compatibility claims. Complete Mac reconciliation
and documentation acceptance remain pending. Candidate K3 closure means baseline
routing/compatibility only, not a frozen contract, new scientific qualification,
independent astronomical package or authorization for new resource acquisition.

The consumer-reconciliation Mac gate also retains the original LMC boundary
composition case that was locally blocked by missing DE440s in KG.07. It uses
the already installed offline resource; no acquisition or full lower-level
gate repeat is part of this reconciliation.


