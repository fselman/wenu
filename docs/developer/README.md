# Wenu developer documentation

**Existing Wenu production baseline:** `6708f54a0d8984c0be348b2c8cb02b311646a02b`, 2026-10-17.
PR #234 is integrated. Its tree is identical to `ea8dc505`, which passed all
3,606 plugin-disabled Mac tests in 1,136.74 s; 16 overlay tests passed in 4.03 s.

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
Observed astrometry, native constellation-label anchors, reports and other
object families remain to migrate.
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
closure and shared helper defaults remain open audit findings. Galaxies now use
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
