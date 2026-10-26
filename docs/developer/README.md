# Wenu developer documentation

## K4b.05 native-ICRS qualitative diagnostic

Fernando approved the [explicit diagnostic epochs](kernel_roadmap_v0.9.5.md#k4b05-native-icrs-qualitative-esa-diagnostic)
after PR #340 merge/cleanup on 2026-10-26. The
[candidate and verification record](kernel_migration_audit_v1.md#k4b05-native-icrs-qualitative-diagnostic-candidate-2026-10-26)
extends the existing independent spherical test to +60,000/+100,000/+450,000
years. The actual Mac run passed 34 focused and 36 documentation cases and
retained all 147 report rows: 52 evaluated, 95 explicit gaps, unchanged source
identities and a maximum spherical chord residual of 3.188872858294072e-16.
Actual v1 plots exposed reversed diagnostic east/west orientation; a separate
v2 replot corrects it and labels the combined seven-star figures explicitly.
Both supplied v2 plots and ESA reference media were viewed. Broad pattern
changes are visible, but detailed ESA trajectory agreement is inconclusive
because source/epoch/viewpoint matching remains unresolved. Final documentation
and v2 product-integrity acceptance remain pending. No production model/default,
physical-accuracy claim, K4b.05 parent closure or K4b.06 adoption changes.

## K4b.05 ESA comparison assessment

The selected [ESA assessment](kernel_roadmap_v0.9.5.md#k4b05-esa-constellation-comparison-assessment)
starts from accepted main `8a0e3e08`, reconfirmed clean/synchronized on the Mac
on 2026-10-26. The [source recovery and feasibility report](kernel_migration_audit_v1.md#k4b05-esa-comparison-feasibility-assessment-2026-10-26)
recovers linked all-sky RV/linear-motion evidence while preserving Orion-specific
gaps and Ursa Major's preliminary stereo geometry. Numerical reproduction is
not yet supported by matched inputs; no visual agreement or endpoint run is
claimed. A native-ICRS qualitative protocol is proposed, not selected.
No domain extension, source acquisition or K4b.06 adoption is activated.
Complete Mac documentation acceptance remains pending.

## K4b.05 finite perspective comparison

Fernando selected the [finite full-versus-angular comparison](kernel_roadmap_v0.9.5.md#k4b05-finite-perspective-omission-comparison)
on 2026-10-25 after PR #338 merge and confirmed clean synchronized Mac main
`2d5e911f`. Eleven constructed comparison/SDK seam cases pass locally; a
local derivative substitution and dropped radial motion each fail the new
comparison. See the [method and bounded evidence](kernel_migration_audit_v1.md#k4b05-finite-perspective-comparison-2026-10-25).
The actual sixteen-HIP cache comparison completed at `04e27e77`: all 80 rows
were retained, with 15 matched pairs and 65 explicit gaps. The three common
stars reproduce the independent reference; source and solution digests are
unchanged. Mac verification covers 345 focused cases/nine subtests (one stale
bytecode failure passed in a fresh-cache retry), 173 source-audit, 36
documentation and eight tooling cases. The final documentation head
`af345e87` passed 36 Mac documentation cases in 6.15 s. PR #339 merged at
`8a0e3e08`; clean synchronized main and local/remote branch cleanup were confirmed.
K4b.05 parent physical/source/ESA qualification and K4b.06 adoption remain open.

The previous [closure evidence matrix](kernel_migration_audit_v1.md#k4b05-bounded-closure-review-2026-10-24)
remains the parent requirement ledger. PR #338 is merged at `2d5e911f`;
36 post-merge documentation tests and the editable installation were confirmed.

## Real-cache Hipparcos-2 time sensitivity

The selected K4b.05 [population assessment](kernel_migration_audit_v1.md#k4b05-real-cache-hip2-time-convention-sensitivity-2026-10-24)
completed on the Mac at `940c4a9b`: all 118,218 HIP statuses retained, with
2,850 Hip2 fallback models and unchanged source/model identity. The largest
combined hypothetical convention differences are 0.8344102459 mas at +10,000
years and 1.590564415 mas at +50,000 years. These are TDB/TCB sensitivities,
not inferred source conventions or physical-error bounds. Issues #326/#333
remain open. Complete Mac documentation acceptance at `0384833f` passed all
36 tests in 3.58 s. PR #337 is merged at `3506bb23`; clean synchronized
Mac main, local/remote task-branch cleanup and 36 documentation tests in
3.17 s are confirmed.

## Hipparcos-2 time-convention assessment

Fernando confirmed clean synchronized Mac main `bd7b9cb0` after PR #335,
whose task-branch documentation gate passed 36 tests. He selected the bounded
K4b.05 [issue #326 assessment](kernel_migration_audit_v1.md#k4b05-hipparcos-2-time-convention-assessment-2026-10-24)
on 2026-10-24. Accessible primary documentation does not establish both the
2007 epoch and proper-motion rate scales. Synthetic examples separate the
roughly seven-second reference-event offset from the time-rate effect, using
the exact TDB/TCB relation. Neither identifies Hip2's source convention.
Issues #326/#333 remain open; production models and source metadata are
unchanged. Complete Mac documentation acceptance at `bfa904a2` passed all 36 tests
in 4.61 s; PR #336 is now merged at `69af07bc`. Clean synchronized Mac main,
local/remote branch cleanup and 36 documentation tests in 3.65 s are confirmed.
Issues #326/#333 remain open.


## Hipparcos-2 source precision assessment

PR #334 is merged; clean synchronized Mac main `ffa7d7a7` and branch cleanup
are confirmed, with 36 documentation tests in 3.11 s. Fernando selected the
bounded issue #333 investigation. The
[assessment](kernel_migration_audit_v1.md#k4b05-hipparcos-2-source-precision-investigation-2026-10-23)
finds that ordinary printed precision does not explain the large discrepancies
in the tested numerical envelopes. F2=99 is a strong pattern, but its meaning
is unverified and non-99 exceptions remain. No covariance correction or admission
is established. Mac acceptance at `1c3d3b1c` passed 36 documentation tests
in 3.18 s; PR #335 is merged and clean synchronized Mac main `bd7b9cb0`
is confirmed.

## Hipparcos-2 covariance diagnostic report

PR #332 is merged; the Mac is clean/synchronized on `5971acb9` with branch
cleanup and 36 documentation tests in 3.55 s. The selected next K4b.05 slice
adds a maintenance-only standard Hip2 covariance qualification report.
The published recipe reconstructs matrices, but source diagonal outliers are
unresolved in [issue #333](https://github.com/fselman/wenu/issues/333).
No Hip2 uncertainty propagation or production model change is admitted.
See the [interface](implementation_reference.md#hipparcos-2-covariance-qualification-report)
and [gate](testing_policy.md#hipparcos-2-covariance-qualification-gate).
Complete Mac acceptance at `32c13c1a` passed 173 audit, 36 documentation
and eight tooling cases/81 subtests. The actual report retains all 118,218 HIPs;
2,682 standard fallback entries reconstruct, while 168 have nonstandard solutions.
Among standard fallbacks, 68 exceed a descriptive 1% sigma-discrepancy bin,
22 exceed 10%, and five exceed 100%. All fifteen largest fallback discrepancies
have F2 exactly 99, an observation rather than proof of saturation.
Fernando accepted this diagnostic-only slice for merge; issue #333 remains open.
PR #334 Mac synchronization and merged-branch cleanup are complete.

## Offline stellar uncertainty assessment and report

PR #331's assessment is merged; Fernando's Mac is clean and synchronized at
`9395ad21` after 36 documentation tests in 3.47 s and branch cleanup.
The bounded K4b.05 offline Gaia report passed complete Mac acceptance in PR #332 at
`652087cb`: 158 audit cases, 36 documentation cases, eight tooling cases/81 subtests.
All 115,105 Gaia covariance matrices passed as positive definite. The report lives in
the existing audit tool. It reports conditional angular measurement errors
and separate hypothetical missing-RV sensitivity; full covariance/physical
provider admission and Hip2 reconstruction remain separate.
See the [interface](implementation_reference.md#offline-gaia-conditional-uncertainty-report),
[scientific limits](scientific_contracts.md#offline-angular-measurement-errors)
and [acceptance gate](testing_policy.md#offline-gaia-covariance-and-rv-sensitivity-gate).
Actual cache execution and the selected-star/percentile review are complete; the
bounded conditional report is accepted for merge. Hip2 qualification follows
merge and clean synchronized Mac acceptance; production physical errors remain unknown.

**Current accepted slice:** K4b.02/AX.13 [explicit proper-motion angular model](implementation_reference.md#explicit-proper-motion-angular-model).
Main `8167bb39` and PR #323 merged-branch cleanup were confirmed clean/synchronized on
the Mac. K4b.01 remains accepted: 97,710 complete-input stellar models and all
118,218 original objects retained. The shared engine now separately types angular
unit-direction/tangent inputs, with no fabricated physical distance or velocity.
The explicit Gaia angular adapter needs position, epoch and both PM components;
parallax and RV remain untouched source facts. Full-input SI/model bindings and
ordinary charts/source lookup remain unchanged. The normalized tangent model
omits perspective/parallax and retains unknown source/physical errors; its finite
caller-selected domain has no universal short PM cutoff. Mac acceptance at `41c47e16` (PR #323) passed: 173 motion/cluster cases plus
nine subtests, 125 source-audit, 36 documentation and eight tooling cases plus
81 subtests. The unchanged snapshot admits 115,105 angular models, including
17,395 additional to the full-input subset; all 118,218 objects remain. Fifteen
sampled directions agree with the independent Decimal oracle within
`1.5700939560399132e-16` vector chord difference. The original full-input SI
digest is unchanged. PR #323 is merged and Mac branch cleanup is complete. Missing-PM approximations, Hip2 qualification,
observer/product adoption and external redistribution remain separate.

**Current bounded result:** K4b.02 Hipparcos-2 angular fallback passed Mac acceptance in PR #325 at `d71ee8da`. Fernando
explicitly adopted a nominal TCB convention and deferred the source epoch/rate
qualification to [issue #326](https://github.com/fselman/wenu/issues/326).
`admit_stellar_hipparcos2_motion` now admits measured Hip2 position/PM where
Gaia angular inputs are unavailable, through the same angular engine. Its
separate identity binds the explicit nominal policy while preserving the
original null source scale. No TT-to-TCB conversion, physical PV or accuracy
bound is claimed. All HIP records and accepted Gaia bindings remain unchanged.
The complete Mac gates passed: 203 stellar/shared-core/cluster cases (nine
subtests), 125 source-audit, 36 documentation and eight tooling cases (81
subtests). Actual admission adds 2,850 Hip2 angular models to 115,105 Gaia
models: 117,955 total; all 118,218 records remain. Both Gaia digests are unchanged.
The 263 original lookup entries stay preserved; no ordinary chart changes.
PR #325 is merged at `dc2035da`; clean synchronized Mac main and branch cleanup
are confirmed, with 36 documentation passes.

**Current bounded result:** K4b.03 historical date/time semantics passed Mac
acceptance at `ceeb894b`, PR #327. The step was selected by
Fernando on 2026-10-23. The existing convention boundary now accepts explicit
proleptic Gregorian/Julian dates, astronomical/BCE/CE numbering and known or
unknown source-date uncertainty. It preserves original labels, two-part time
and an explicit TimeService conversion receipt to TCB. No civil-clock,
Delta-T, historical observer or precession model is inferred. Complete Mac gates
passed: 257 stellar/shared-core/cluster cases (nine subtests), 125 source-audit,
36 documentation and eight tooling cases (81 subtests). Twenty-four historical
states passed the independent Decimal check; all Gaia/Hip2 digests are unchanged.
PR #327 is merged at `e2a231b5`; clean synchronized Mac main and branch
cleanup are confirmed, with 36 documentation passes.

**Current bounded result:** K4b.04 long-term frame orientation passed Mac
acceptance at `97921fe8`, PR #328. The step was selected by
Fernando on 2026-10-23. The existing convention owner admits separately explicit
corrected Vondrak/Capitaine/Wallace mean equatorial/ecliptic axes through ERFA,
with finite TT validity and an explicit TT frame equinox. Native stellar TCB
times/source/model records are preserved in a derived view. No time-scale
relabel, observer reconstruction or default chart change. Complete Mac gates
passed: 311 focused cases/nine subtests, 125 source-audit, 36 documentation and
eight tooling cases/81 subtests. All 48 actual derived directions passed the
Decimal arithmetic check; accepted stellar digests are unchanged. PR #328
remains unmerged, with no next runtime item selected.
See the
[qualification review](kernel_roadmap_v0.9.5.md#k4b02-hipparcos-2-fallback-qualification).

**Existing Wenu production baseline:** `6708f54a0d8984c0be348b2c8cb02b311646a02b`, 2026-10-17.
PR #234 is integrated. Its tree is identical to `ea8dc505`, which passed all
3,606 plugin-disabled Mac tests in 1,136.74 s; 16 overlay tests passed in 4.03 s.

K3.16 now implements [diffuse source metadata and v6 saved-sky transport](implementation_reference.md#diffuse-contour-source-admission-and-saved-skies),
following Fernando’s explicit 2026-10-20 agreement. Accepted through PR #289 after the Mac comparison retry.
Older v1–v5 skies remain readable with honest legacy metadata limits.

K3.17 now verifies [existing constructed-reference service routes](kernel_migration_audit_v1.md#k317-constructed-reference-service-routing-assessment).
The as-is assessment found established coordinate/geometry routes already in use;
this task adds closure evidence and preserves production implementations. Focused
Mac acceptance is complete through PR #290 (99 focused, 36 documentation and eight tooling cases).

K3.18 now corrects [observer resource checks and shared warm-cache identity](implementation_reference.md#observer-resource-lifetime-and-geometry-cache-identity) in existing owners.
K3.18 is accepted through PR #291 after 402 focused, 36 documentation and eight tooling Mac cases.

K3.19 moves existing concrete construction into [application assembly](implementation_reference.md#application-sky-assembly),
leaving central sky/factory/snapshot APIs as delegates. Source-free restoration and worker paths use that owner; accepted through PR #292 after 169 focused, 36 documentation and eight tooling Mac cases.

K3.20 now verifies [ordinary chart consumer routing](kernel_migration_audit_v1.md#k320-ordinary-chart-consumer-assessment) through existing services, without production rewrites. Accepted through PR #293 after 389 focused, 36 documentation and eight tooling Mac cases.

K3.21 now exposes the [public atlas sheet contract](implementation_reference.md#public-atlas-sheet-contract) and routes catalogue-count availability through full-source native stellar positions. Accepted through PR #294 after 425 focused, 36 documentation and eight tooling Mac cases.

K3.22 now verifies [physical polar product service routing](kernel_migration_audit_v1.md#k322-physical-polar-product-service-assessment) without production rewrites. Products retain their Wenu owners; coordinate/kernel geometry services already supply their scientific geometry. Accepted through PR #295 after 162 focused, 36 documentation and eight tooling Mac cases.

## Read for current work

| Document | Authority |
|---|---|
| [Current architecture](current_architecture_v0.9.md) | What the code does now; known missing barriers |
| [Implementation reference](implementation_reference.md) | Existing API entry points and extension owners |
| [Source tree](source_tree.md) | Complete production-module inventory |
| [Scientific contracts](scientific_contracts.md) | Current scientific invariants and capability limits |
| [Coordinate guide](coordinate_system_guide_v0.9.5.md) | Scientific vocabulary, mathematics and calendars |
| [Configuration schema](configuration_schema_v2.md) | Implemented schema-v2 configuration |
| [Satellite guide](satellite_guide.md) | Satellite science and current limitations |
| [Testing policy](testing_policy.md) | Focused verification now and module independence target |
| [As-is migration audit](kernel_migration_audit_v1.md) | Current functionality, pinned source/test inventory and continuous test migration |
| [Proposed kernel contract K1](kernel_contract_k1.md) | Proposed SDK types, operations, capabilities, errors and conformance gates |
| [Assistant instructions](assistant_instructions.md) | Contribution and delivery workflow |

The [executable test selections](../../tools/test_gates_v1.json) and
[runner](../../tools/run_test_gate.py) define reviewed documentation and request
gates. See the testing policy for scope, exclusions and pending normal-runtime
acceptance; focused selection does not claim independent product installation.

## Roadmap and scope control

The [agreed roadmap](kernel_roadmap_v0.9.5.md) is the single forward-work authority.
It now includes the [current position and next-item selection](kernel_roadmap_v0.9.5.md#current-position-and-next-item-selection),
all known [intermediate milestones](kernel_roadmap_v0.9.5.md#intermediate-milestones),
a full [K3 audit coverage map](kernel_roadmap_v0.9.5.md#k3-audit-coverage-map),
and separate baseline/Gaia/positional-extension tracks. K3 is still partial;
PR #269 completes AX.12, not K3 or the kernel freeze. K3.07 is accepted through
PR #271. K3.08 observed stellar/figure/label routing is accepted through PR #272.
K3.09 shared-default correction is accepted through PR #273. Its remaining
[source assessment and agreed admission policy](kernel_migration_audit_v1.md#m5-source-assessment-and-proposed-admission-distinction-2026-10-19)
are documented; Fernando approved the lookup/physical-admission distinction
and PM-only policy on 2026-10-19. K3.09 explicit lookup admission is accepted through PR #274;
physical source gaps remain explicit. The measured-PM angular slice of AX.13 passed Mac acceptance for explicit
admission through PR #323; missing-PM approximation and Hip2
qualification remain pending. K3.10 galaxy routing closure
is accepted through PR #275. K3.12 generic nonstellar/Messier/Caldwell and
object-centre routing is accepted through PR #276. K3.13 globular routing is
accepted through PR #277. K3.14 PN routing is accepted through PR #278.
K3.15 SNR routing is accepted through PR #279. Fernando clarified and agreed the
[broader shared-service kernel](kernel_roadmap_v0.9.5.md#proposed-architecture),
including geometry/topology/projections, on 2026-10-19. The state SDK is one
component. K3.16’s default geometry-query extension proposal is withdrawn; its
[source assessment and resolution](kernel_migration_audit_v1.md#k316-diffuse-geometry-assessment-and-architectural-resolution)
retain M9 evidence and direct the work toward existing public geometry services.
PR #280 accepts the architecture documentation. Revision 32 now places
[KG.01–KG.07](kernel_roadmap_v0.9.5.md#kg-shared-geometry-services-and-completed-k-audit)
before K3.16: assess and migrate geometry services, audit completed K work,
then apply and verify demonstrated corrections. Previous receipts remain evidence
for their bounded claims; the audit determines whether implementations need changes.
Complete service-kernel closure remains open. The
[KG.01 assessment](kernel_migration_audit_v1.md#kg01-shared-geometry-service-inventory)
now maps existing services, 66 direct-import consumer modules, test owners and
five coupling/contract findings. KG.01 is accepted through PR #282. The
[KG.02 contracts and placement proposal](kernel_contract_k1.md#14-kg02-geometry-service-contracts-and-placement-plan)
are now delivered for review: explicit numerical kernel imports, legacy aliases,
ring/metadata/ownership rules and focused acceptance. KG.02 is accepted through PR #283. Fernando subsequently selected KG.03,
including that concrete placement and optional NumPy extra. Kernel dev9 now owns
pure CoordinateSpec vocabulary, spherical/projected records, frame/viewport and
the existing ring helper; Wenu aliases preserve class identity. KG.03 is accepted through PR #284. KG.04 now places projected clipping,
all three projections and cap/latitude/topology mathematics in kernel dev10;
legacy imports alias the same services. Appearance helpers remain in Wenu.
KG.04 is accepted through PR #285 (205 kernel, 8 tooling, 36 documentation and
295 focused Mac cases). KG.05 now verifies composed services and real atlas/polar
outputs. Its [evidence and equidistant input finding](kernel_migration_audit_v1.md#kg05-composed-geometry-acceptance)
are explicit; KG.06/KG.07 completed-K audit/corrections remain separate tasks.
The [KG.06 per-deliverable audit](kernel_migration_audit_v1.md#kg06-completed-k-service-boundary-audit)
now retains the accepted state/catalogue routes and identifies one demonstrated
point-projection correction for KG.07. Known partial K3 obligations remain open;
KG.06 changes documentation/evidence only and is accepted through PR #287.
KG.07 now implements that single correction in kernel dev11: point batches
retain missing-row slots while strict numerical operations receive finite
coordinates. The real polar tests require both projections to pass without
expected-failure markers; complete Mac acceptance is pending.
Extra scope or changed agreed order must be discussed with Fernando,
explicitly agreed and documented before implementation under the
[mandatory agent rule](assistant_instructions.md#roadmap-control-mandatory-before-implementation).

## Forward work

K1 and the K2 native-state/reuse and explicit time subsets are accepted
through PR #242, main `8fea897f`, including the shipped provider conformance kit.
The separate [kernel project](../../packages/wenu_kernel/README.md) owns
standard-library direction records, registration and synchronous sessions.
SI Cartesian states retain explicit optional velocity, independent error
channels and source-epoch availability. TimeService admits explicit offline
conversions, including bounded TT(TAI)/TAI. Native state queries still require
matching scales. Provider conformance uses factory-owned fixtures and
independent installed-consumer evidence. Minor-body request-resource rollback
is accepted through PR #243, main `f5a0abf3` (3,400 Mac integration tests passed).
PR #244, main `d36b1786`, scopes ordinary-request layer configuration to one
active build: original layer order/identities, horizon/disk aliases and point
label flags are restored on close/failure. PR #246, main `e5bd7c16`, extends
this owner to direct view/drawing and native atlas sheets, and makes
`wenu_chart atlas-sheet` the default producer route. Its 247-test Mac gate
passed, including real serial/spawn and cold/saved atlas equivalence.
PR #247, main `bf804cbb`, accepts native stellar realization through the real SDK
and `stellar_state.py`, including installation and native canvas isolation.
The accepted K3 stellar slice routes `Stars.position`, explicit HIP lookup through
`Stars.native_positions`, and native constellation endpoints through that adapter.
These routes declare source epoch J1991.25, preserve unpropagated Hipparcos
directions, IDs and display metadata, and do not add proper motion.
Native constellation-label anchors now consume full-source public kernel-backed
positions under accepted K3.07. K3.08 now feeds kernel-returned source directions
to the existing Skyfield star/figure and Astropy label observation methods
(accepted PR #272). Reports and other object families remain to migrate.
Catalogue ingestion now validates and preserves required source metadata in a
standard table/immutable metadata envelope; snapshot v3 carries it forward.
The [metadata audit](kernel_migration_audit_v1.md#catalogue-metadata-audit-2026-10-18)
records duplicated epochs, lost units/provenance and other source facts still
embedded in remaining providers, including the mixed-epoch open-cluster issue.
The open-cluster followup resolves that provider's epoch consumption: selected
geometry and snapshot v4 use preserved row epochs/source lineage, including
explicit unknowns, and retain catalogue metadata. Nonstellar normalization now
preserves source metadata/unconsumed fields and converts declared angular units,
with atomic reload and existing snapshot transport checks. A frozen nonstellar
record now validates declarations, exposes missing facts and controls geometry
specifications and snapshot v5 headers. Strict admission refuses remaining source
gaps; legacy charts retain explicitly unverified coordinate encoding. No automatic
J2000 measurement epoch remains in those provider/snapshot paths. Resource metadata
qualification remains open. Accepted K3.09 M4 removes shared implicit J2000
measurement epochs; missing source facts stay unknown and strict admission
continues to refuse them. Galaxies now use
an explicit static-direction admission policy: measurement epoch/scale are
optional provenance, while frame/origin/units/source identity remain required.
Requested epoch changes leave their native centres unchanged. The SDK now supports explicit `static_direction` admissions with optional source
epochs; native/epoch direction models retain their epoch requirement. Galaxy
centre routing now uses this capability for public positions, chart outlines and
observed centres. Missing source facts remain explicit legacy compatibility;
source frame/origin closure remains open. Production now pins the accepted dev8 SDK at main `9dd1909f`.
Shape parameters stay with the galaxy layer.
The SDK [selection manifest](../../packages/wenu_kernel/test_selection_v1.json)
keeps the independent core gate separate from existing Wenu tests. Current
products consume native stellar, static galaxy and open-cluster lookup adapters.
Open-cluster public/native centres and observer transformation inputs now use
`catalogue_lookup`, preserving per-row source labels, qualified numerical epochs,
motion fields/units/masks and immutable source-bound identity. Unqualified or
unknown epochs are never assigned a time scale. Saved skies restore the existing
manifest source digest and use the same adapter. Returned positions enter the
observer cache key; failures propagate even after cache fill. Cluster motion
propagation remains pending. The
[cluster motion audit](kernel_migration_audit_v1.md#open-cluster-motion-and-lookup-audit-2026-10-18)
records retained Dias motions and required provenance. A source-bound, versioned
Hunt astrometry companion now recovers 509 matching solutions (502 radial
velocities) for the existing 513 selected clusters. Four Dias-only solutions stay
unadopted. Offline attachment preserves all original fields; the default catalogue
and charts are unchanged. The raw ReadMe scale/origin gaps remain preserved. A separate
[source qualification and model contract](kernel_migration_audit_v1.md#cluster-propagation-qualification-and-model-contract)
now traces Hunt conventions to Gaia and the four Dias motions to D14. Centre
epoch lineage for the latter and cluster-mean covariance/model bounds remain
incomplete; default charts retain source lookup. See the
[ingestion API](implementation_reference.md#open-cluster-astrometry-ingestion).
The [shared astrometric engine](implementation_reference.md#shared-astrometric-engine)
now owns object-independent SI propagation, domain/numerical checks and angular
certificates. Cluster source admission/identity remains an adapter calling that
engine. Synthetic mixed star/cluster/PN/SNR use is verified; real adapters for
other families and reduced-input lookback policies remain planned.
The explicit [nominal cluster motion API](implementation_reference.md#nominal-cluster-motion-provider)
now implements source-bound immutable admission and finite-domain TCB rectilinear
direction evaluation through the accepted SDK. It retains all 513 IDs, advertises
502 full-input solutions and reports eleven unavailable rows. Existing chart and
saved-sky lookup routes are unchanged. Provider-owned angular certificates now
enable selective reuse in explicit interactive sessions; reproducible sessions
retain full-model evaluation. The numerical bound starts from admitted binary64
SI solutions; measurement, conversion and physical-model accuracy stay unknown.
Explicit native Python chart consumers now adopt the motion catalogue per call,
including restored source snapshots, with matching TCB context epochs and
source-digest/identity admission. Default lookup and snapshot v5 are unchanged;
explicit observed Python charts now use the shared finite-distance service. CLI/TOML
selection is now available for ordinary horizontal charts; persisted epoch states remain separate. See the
[consumer API](implementation_reference.md#explicit-native-cluster-motion-consumers).
The [observer-motion contract](scientific_contracts.md#cluster-observer-realization-contract)
now records the RA/Dec-only seam, required Cartesian/time/common-coordinate
prerequisites and correction/cache acceptance matrix. The explicit Python
consumer now admits a prepared reception receipt and the motion catalogue. Explicit
Cartesian SI output is now implemented in the core interface, preserving distance
and velocity through a separate admission with unknown error bounds; the separate shared observer service performs observer realization.
The explicit [TCB/TDB convention subset](implementation_reference.md#barycentric-time-and-coordinate-conventions)
now supplies time receipts and spatial scaling independently of object type.
An offline [reception context](implementation_reference.md#offline-reception-and-observer-input-context)
now retains explicit UTC/TT/TDB/TCB events and separately identified ERFA Earth/observer
PV with verified local leap/final EOP resources. The object-independent
[finite observer realizer](implementation_reference.md#finite-distance-nominal-observer-realization)
now returns range, parallax and corrected vacuum Alt/Az from actual kernel
Cartesian batches. Explicit observed Python chart and restored-source consumers
now call it through `LayerRealizationContext.from_reception`; Cartesian reuse
and remaining K3 routing are pending; this is not a completed kernel or frozen SDK.

[Roadmap to v0.9.5: kernel and loadable packages](kernel_roadmap_v0.9.5.md)
is the single active forward roadmap. Both architecture diagrams are in that
document and in the [diagram index](diagrams/README.md).
It starts with Gaia DR3, prepares a DR4 adapter, requires every existing
functionality to use the kernel, and then extracts one package at a time.
Kernel completion and Gaia integration remain planned; the implemented subset
is stated above.
The [K1 contract](kernel_contract_k1.md) is the accepted implementation target;
K5 remains the final usable SDK freeze after all consumers migrate.

The `v0.9.5` name is provisional. The old document with this version in its
title described the completed 49B/49C coordinate work, not this new kernel.
Its [original edition](archive/pre_kernel_20261017/docs/developer/target_architecture_v0.9.5.md)
is archived. Release naming must be confirmed before a tag is made. No release
tag is created by this roadmap; runtime migration status is stated above.

## Curation and unresolved science

The [stellar designation review](stellar_designation_review.md) and its
[ledger](data/stellar_designations_review.json) retain Fernando's review cells.
The [research dossier](data/stellar_designation_research/README.md) remains
available. Blank historical decisions do not block the accepted label policy.
Current source-data, selection and promotion workflows are in the
[curation guide](../user_guide/curation.md).

Minor-body automatic-name/provisional selection and satellite Moonlight,
brightness and detector science remain incomplete. They are paused behind the
kernel work; completed history is not an instruction to resume them.

## Archive

[Archive index](archive/README.md) preserves earlier architecture, proposals,
receipts and superseded instructions. The
[cleanup ledger](documentation_cleanup_v1.json) records exact original Git
blob identities and old-to-new paths. Read historical material only when its
scientific detail or provenance is needed; do not append milestone diaries to
the current architecture, coordinate guide, API reference or source map.

Explicit ordinary horizontal charts can select `nominal-observed` through
`astrometry.open_clusters` in schema-v2 TOML or `--open-cluster-model`, with
repeatable `--open-cluster-id` selection. Verified local leap/final EOP resources,
installed backend identity, finite TT/TCB domains and qualified WGS84 height are
required. See the [configuration contract](configuration_schema_v2.md#explicit-open-cluster-astrometry).
Other layers keep their existing scientific routes; no expansion is introduced.


K3.23 now verifies [ordinary observer-time sequences](kernel_migration_audit_v1.md#k323-observer-time-sequence-consumer-assessment)
through the canonical static generator. Planisphere viewport reuse fixes a
demonstrated same-chart composition refusal without changing its calculation.
Per-frame context/kernel-result, partial-progress/refusal and resume-identity
checks are accepted through PR #296 after 151 focused, 36 documentation and eight tooling Mac cases.

K3.24 now verifies [fixed-sky and rotating-horizon service consumers](kernel_migration_audit_v1.md#k324-fixed-sky-consumer-assessment)
and fixes observer cleanup during frame resolution. Anchor orientation and local
frame realization remain separate; cold/reuse geometry and graphical outputs are
checked. Accepted through PR #297 after 53 focused Mac cases.

K3.25 implements [major-planet and Moon state routing](kernel_migration_audit_v1.md#k325-major-planet-and-moon-state-assessment)
through the existing Cartesian SDK before the retained light-time/apparent chain.
Accepted through PR #298 after 83 focused, 36 documentation and eight tooling Mac
cases; clean synchronized main and branch cleanup confirmed. K3.26 is selected separately below.

K3.26 now routes [physical disk and sequence consumers](kernel_migration_audit_v1.md#k326-disk-and-sequence-consumer-assessment)
through the existing Cartesian adapter before retained appearance/geometry services.
Component sharing checks live observer resources and is scoped to one request context.
Accepted through PR #299 after 138 focused, 36 documentation and eight tooling Mac
cases; clean synchronized main/branch cleanup confirmed. K3.27 is selected separately below.

K3.27 now routes [natural-body track state samples](kernel_migration_audit_v1.md#k327-natural-body-track-consumer-assessment)
through the existing adapter, including known planetary bindings in mixed requests.
Sampling, fixed chart axes, temporal policy and annotations remain unchanged.
The `natural-body-track-routing` Mac gate is pending. Existing satellite-track
chart refusal remains; Moon sampling is scientific-API coverage, not a new CLI product.

K3.27 is accepted through PR #300 after 83 focused, 36 documentation and eight
tooling Mac cases, with clean main and branch cleanup confirmed. K3.28 now
accepts [asteroid state/offline resource routing](implementation_reference.md#asteroid-state-and-offline-resource-routing)
and manifest-backed Ceres solution facts through PR #301 after 211 focused,
36 documentation and eight tooling Mac cases, with cleanup confirmed. K3.29 now
implements [comet consumers and provider-record routing](implementation_reference.md#comet-consumers-and-provider-records)
through PR #302 after 273 focused, 36 documentation and eight tooling Mac cases;
cleanup is confirmed. K3.30 [antisolar reference routing](implementation_reference.md#antisolar-constructed-reference-routing)
is accepted through PR #303 after 117 focused, 36 documentation and eight tooling
Mac cases; clean main and cleanup confirmed. K3.31
[satellite state and observer services](implementation_reference.md#satellite-state-and-observer-services)
is accepted through PR #304 after 77 focused, 36 documentation and eight tooling
Mac cases; clean main and cleanup confirmed. K3.32 now verifies
[sampled satellite candidate consumers](implementation_reference.md#sampled-satellite-candidate-services)
without production changes, accepted through PR #305 after 61 focused,
36 documentation and eight tooling Mac cases; clean main and cleanup confirmed.
K3.33 now verifies [exact satellite service consumers](implementation_reference.md#exact-satellite-service-consumers)
without production changes, accepted through PR #306 after 86 focused,
36 documentation and eight tooling Mac cases; clean main and cleanup confirmed.
K3.34 verifies [satellite report consumers](implementation_reference.md#satellite-report-consumers)
without production changes, accepted through PR #307 after 68 focused,
36 documentation and eight tooling Mac cases; clean main and cleanup confirmed.
K3.35 routes [illumination and shadow Sun inputs](implementation_reference.md#satellite-illumination-and-shadow-services)
through the existing Cartesian adapter, retaining the physical models. Accepted
through PR #308 after 62 focused, 36 documentation and eight tooling Mac cases,
including offline DE440s parity; clean main and cleanup confirmed.
K3.36 now moves [TSIS resource facts into validated metadata](implementation_reference.md#solar-radiometry-resource-admission)
while retaining radiometry calculations. Accepted through PR #309 after 61 focused,
36 documentation and eight tooling Mac cases; clean main and cleanup confirmed.
K3.37 repairs [public teaching/installer consumers](implementation_reference.md#public-consumer-and-teaching-surfaces),
with the [public-surface-routing gate](testing_policy.md#public-surface-routing-gate).
K3.37 is accepted through PR #310 after 238 focused, 36 documentation and eight
tooling Mac cases, with clean main and branch cleanup confirmed.
K3.38 now verifies [maintenance/resource consumers](implementation_reference.md#maintenance-and-resource-consumers),
with the [maintenance-resource-routing gate](testing_policy.md#maintenance-resource-routing-gate).
K3.38 is accepted through PR #311 after 49 focused, 36 documentation and eight
tooling Mac cases, with clean main and branch cleanup confirmed.
K3.39 verifies [geometry and graphics boundaries](implementation_reference.md#geometry-and-graphics-consumer-boundary)
without production changes, using the [geometry-rendering-routing gate](testing_policy.md#geometry-rendering-routing-gate).
K3.39 is accepted through PR #312 at main `0deca8c3`: 247 focused,
36 documentation and eight tooling Mac cases; branch cleanup confirmed.
K3.40 delivers the [complete consumer reconciliation](implementation_reference.md#complete-consumer-reconciliation)
and [focused audit gate](testing_policy.md#consumer-reconciliation-gate).
K3.40 is accepted through PR #313 after 25 focused, 36 documentation and eight
tooling Mac cases. Fernando completed the six-product review and selected K4a.01;
SDK freeze and astronomical package extraction remain later.
