# Wenu current architecture

## Saved epoch position consumption

`stellar_epoch_consumer.py` owns captured query-input admission and the lifecycle
of the data-backed stellar position view. It calls immutable bundle validation
and the accepted query service upstream; it contains no propagation or renderer.
`Stars.realized()` chooses the live or data-backed adapter. Existing sky assembly
then lends the same replacement stars to lines and labels. Atlas sheets,
publication counts and reports consume that shared view through existing owners.
Publication workers receive a small digest-bound descriptor, verify source-sky
and design identity and admit their own input once. Codecs, strict saved-product
compatibility, source/model mathematics and observer ownership remain unchanged.
The candidate passed 50 stellar/publication, 17 atlas and 36 documentation Mac
cases at `9f7b2e9a`, then actual J-2000 preparation and saved/live/serial/spawn
geometry/product checks with Polaris drawn in both north caps. User visual
acceptance and merge are confirmed through #361/main f72a2055 after #362;
clean Mac synchronization and cleanup are confirmed. No companion runtime follows.



## Exact-event ephemeris companion lifecycle

The selected K4b.07.C2 candidate extends existing ephemeris request/adapter owners
for native split-JD TDB input and pinned offline DE440/DE441 resource ownership.
Selection remains in `skyfield_ephemeris.py`; the existing `ephemeris_state.py`
returned Cartesian SDK path remains authoritative for transported PV.
The separate `ephemeris_companion.py` module owns immutable derived-product
validation/preparation/publication/reload, not a second numerical engine.
It stores Earth-centre/Sun simultaneous geometric ICRF/TDB-compatible states,
not stellar nominal-astrometric states or terrestrial observations.
Optional stellar-manifest linkage verifies explicit common-event receipts.
No chart, renderer, observer, original stellar codec/model/core or modern
default changes. Mac/runtime/actual-cache acceptance is pending.
See the [API](implementation_reference.md#exact-event-ephemeris-companions).

## Stellar epoch query lifetime

`stellar_epoch_query.py` owns explicit in-memory reuse policy, detached resolution
and receipt, and short-lived SDK composition. It consumes an already validated
immutable epoch catalogue. Reuse returns saved positions without reconstruction;
advancement calls existing public source admissions and selection/providers,
verifies original coefficients/references and closes SDK resources before return.
It does not own a numerical engine, product codec, source cache or chart observer.
The immutable codec's strict watched code files remain unchanged so old accepted
products keep their original compatibility binding. At `350de788`, 20 focused
Mac runtime and 36 documentation cases passed. Both original retained products
passed unchanged reuse and reciprocal all-row target-hash verification; user
acceptance/merge are confirmed through #359/#360 at d4fb035d. Consumer
adoption is accepted above; companion/observer runtime remains separate.


## Exact-event stellar persistence candidate

`stellar_epoch.py` owns the derived immutable epoch-product schema, preparation,
strict reader and completion-last publication lifecycle. It is separate from
`stellar_enrichment.py`'s original source schema and `sky/native_snapshot.py`'s
source-only sky reconstruction. `stellar_state.py::stellar_model_selection`
shares ordered first-available admission between live stellar views and epoch
preparation; query failure still cannot select a fallback. Preparation uses
existing typed SDK direction/Cartesian providers. The reader performs no model
evaluation or provider/session construction. No kernel/numerical, chart,
renderer, observer, installed command, dependency or collection change occurs.
The maintenance command delegates to this owner; later consumers will use their
public stellar/state interfaces, not implement astrometry in rendering code.

**As-is baseline:** `6708f54a0d8984c0be348b2c8cb02b311646a02b` (2026-10-17).
This document describes implemented behavior. The proposed kernel and package
architecture lives separately in the [roadmap](kernel_roadmap_v0.9.5.md).

The separate [K2 kernel project](../../packages/wenu_kernel/README.md)
implements immutable direction records, explicit registration and synchronous
sessions, reproducible certified direction reuse and SI Cartesian full-model
states with optional velocity and separate uncertainty channels. Explicit
time-adapter admission, conversion receipts and bounded TT(TAI)/TAI conversion
remain separate from same-scale native state queries. A reusable stdlib
provider conformance kit verifies an external consumer with no repository fixtures.
The base state SDK has no runtime dependencies; explicit numerical geometry
imports use the optional NumPy geometry extra. Accepted PR #247 makes it a
separate Wenu dependency and routes native stellar realization through it.
The existing state/geometry consumer routes are now reconciled for K3.40
acceptance; the final SDK freeze remains pending. The canonical projection and
rendering pipeline is retained.

The agreed target service kernel also includes generic spherical geometry/topology,
domain guards, projections/projected geometry and coordinate/observer realization
services. KG.03 now places the pure CoordinateSpec/PositionStatus vocabulary,
spherical/projected records, SphericalFrame/Viewport and the existing numerical
ring helper in kernel dev9. Legacy Wenu imports alias the same classes; the
Milky Way layer retains source policy and delegates the unchanged ring math.
KG.04 now places the three projection implementations, projected clipping and
spherical domain/latitude/cap topology in kernel dev11. Wenu projection/clipping
modules and mathematical preparation names delegate to those same services.
Magnitude/diameter sizing, marker-margin culling, label offsets and chart/render
policy remain at Wenu owners. Base kernel imports remain stdlib-only; explicit
geometry/projection imports use the existing optional NumPy extra. The installed state SDK is one
component, and its accepted subset does not establish the full kernel boundary.
See the [agreed target and accepted-work disposition](kernel_roadmap_v0.9.5.md#proposed-architecture).
Geometry consumers can call public geometry services directly. There is no accepted
new SDK geometry-query capability from K3.16’s
initial assessment. The subsequently agreed K3.16 metadata/v6 transport now supplies source envelopes and explicit legacy admission.


K3.07 routes native constellation-label anchors through the full-source public
stellar query. Membership, Serpens splitting, source-order grouping and spherical
means retain their existing rules. Labels inherit the returned coordinate spec;
K3.07 is accepted through PR #271. K3.08 now routes observed stellar/figure
inputs through kernel lookup before the retained Skyfield observation boundary,
and observed label inputs through the public full-source lookup before the
retained Astropy boundary. K3.08 is accepted through PR #272 and does not close K3.

Accepted K3.09 M4 removes implicit J2000 measurement epochs from the shared
ICRS specification and helper. Unknown source epochs remain None; explicitly
admitted stellar/cluster epochs and numerical frame transforms are unchanged.
Nonstellar strict admission still refuses absent frame/origin and model-required
epoch/scale declarations. No source qualification follows from the default fix.

K3.09 now has explicit nonstellar catalogue-lookup validation separate from strict
physical admission. Lookup requires preserved identity/provenance/units/byte
binding while retaining absent physical reference/epoch facts. The explicit
lookup spec discloses unverified reference interpretation and unknown origin.
Existing chart geometry and strict physical admission remain unchanged. K3.09 baseline admission is accepted through PR #274; reduced-input PM algorithms
remain AX.13, under the approved no-universal-PM-cutoff policy.

Accepted K3.10 galaxy routing applies the shared source-bound lookup validation
when its required source evidence is present, while preserving explicitly
unqualified constructed/unitless legacy sources. Unqualified source dates stay
provenance and do not block static lookup. Galaxy outline state is queried before
cache access, and returned centres enter outline/point cache identity. The same
queried centres construct outlines once; unchanged returned states still reuse
their observer transformation. Later K3.12–K3.15 adapters reuse these returned-state cache hooks;
source ownership remains with each catalogue family.
This is accepted through PR #275 and does not qualify absent physical source facts.

K3.16 admits diffuse source declarations in the Wenu-owned immutable
`sky/isophote_sources.py` envelope before shared kernel spherical/topology services.
Saved-sky v6 preserves it; v1–v5 use explicit source-free legacy receipts. Source
properties absent in older files remain unavailable. Observation/projection/render
science and the kernel distribution are unchanged; K3.16 is accepted through PR #289.
See [diffuse admission](implementation_reference.md#diffuse-contour-source-admission-and-saved-skies).

K3.17’s constructed-reference assessment retains existing grid, pole/keypoint,
FK4/B1875 boundary, horizon/mask and furniture implementations: they already use
the shared coordinate/geometry/domain/projection services. Source-free restored
references use those same owners. New closure tests verify returned values and
refusal; there is no new production route or numerical algorithm. Complete
observer resource/cache checks are accepted under K3.18/PR #291 after the
402-case focused Mac gate. See the
[routing ledger](kernel_migration_audit_v1.md#k317-constructed-reference-service-routing-assessment).

## Completed-K service-boundary audit

At main 52c8315c, [KG.06](kernel_migration_audit_v1.md#kg06-completed-k-service-boundary-audit)
finds no need to redo accepted state/catalogue routing. Source adapters call the
state SDK; geometry consumers use canonical mathematical services through public
compatibility aliases. Kernel imports no application/catalogue/backend/renderer.
KG.07 implements G06.C1 in the shared point-projection adapter: missing-coordinate
rows retain NaN projected slots and entity metadata; only finite coordinate rows
enter strict numerical operations. Direct invalid numerical inputs, finite
invalid latitudes and the opposite-pole domain still refuse. No catalogue rows
are dropped and no missing direction is published as a state. The real equidistant
polar specimens now require success without expected-failure markers. The
correction is merged through PR #288. K3.16 subsequently accepted all four real
cold/restored polar outputs; K3.39 accepted point-row/domain compatibility.
The original 103-case KG.07 Mac total is not persisted and is not invented here;
the reconciliation records the applicable original/component and later evidence.
Observer/cache identity and application assembly are accepted through K3.18/K3.19.
K3.21's lower-level public atlas sheet contract is accepted through PR #294.
K3.22 physical polar product service consumers are accepted through PR #295.
K3.23 ordinary temporal sequence consumers are accepted through PR #296.
K3.24 fixed-sky consumer verification and observer cleanup are accepted through
PR #297 after 53 focused Mac cases. No K3/K5 freeze is claimed.

## Canonical pipeline

Catalogue/provider → spherical geometry → projection-domain guard → projection
→ projected geometry → preparation → renderer → furniture/export.
`sky/celestial_sphere.py::CelestialSphere.draw_chart()` is the existing core.
There must be no second scientific or rendering pipeline during migration.
`geometry/frame.py::SphericalFrame` aligns a projection; it is not an
astronomical frame transformation.

## Responsibility map

| Area | Existing owner | Boundary |
|---|---|---|
| Catalogue objects | `objects/` | Centres, source tables and extended morphology |
| Sky layers | `sky/` | Spherical content and observer-dependent realization |
| Coordinate meaning | `coordinates.py`, `coordinate_service.py` | Explicit frame/origin/status/time and transformations |
| Solar-System states | `ephemeris.py`, `skyfield_ephemeris.py`, `solar_system_directions.py` | Resource-bound states, light time and apparent directions |
| Minor bodies | `minor_body_*.py`, shared Solar-System layers | Explicit resource admission and descriptor-based point/track routes |
| Artificial satellites | `satellites/`, satellite report and presentation adapters | Snapshot, propagation, crossings, illumination and reports |
| Pure geometry | `geometry/` | Spherical/projected values, topology and clipping |
| Projection | `projections/` | Stereographic and Mollweide mapping |
| Products | `charts/`, `cli/` | Requests, framing, composition, atlas publication |
| Graphics | `rendering/`, `chart_document.py` | Preparation, Matplotlib and semantic SVG/PDF/PNG |

The [source map](source_tree.md) lists every production Python file.
Wenu now depends on the separate `wenu-kernel` distribution. The astronomical
directories inside Wenu are not yet independent loadable packages.

## Implemented products and independent concerns

Ordinary charts include Galactic all-sky, observer-visible planisphere,
regional, circumpolar and binocular products. Physical polar-planisphere and
time-sequence products retain their separate product contracts while sharing
geometry, projection, preparation and export. The physical pair, common-year
calendar, A4 page, pouch and imposed sheet remain Wenu product owners. Their
existing coordinate-service and kernel projection/domain calls are retained;
K3.22 adds consumer/refusal and fabrication-output evidence, not a new numerical
implementation or a product move into the kernel.

Chart family owns projection/framing/boundary. Detail owns selection. Style
owns appearance. Output mode owns physical display adaptation. Furniture and
legends have their own controls. Drawing selectors never supply a center;
centering is explicit. These concerns must not silently modify one another.

Atlas design, index and publication commands are implemented. Installed
layouts are 34-chart landscape, 36-chart portrait and two hemispheres.
Layout, full chart presentation and index presentation are separate inputs.
`atlas-v6` and `atlas-hemispheres-v2` are data presets, not scientific engines.
Their names do not freeze the set of styles that may be installed.
Publication realizes source content natively and supports selected sheets,
explicit saved-sky reuse, facing reports and criteria appendices. Accepted
K4b.06 slices (#346/#348/#350) add explicit stellar-owned nominal TCB motion
to Python sheets, the installed sheet command and serial/spawn publication.
Accepted #354 adds independent finite TT mean-equatorial/ecliptic view axes,
derived target-axis layouts, dated references and matching report furniture.
The common geometry orientation precedes domain/projection/preparation, including
secondary label regions; original source/design identities remain intact.
See the [acceptance receipt](kernel_migration_audit_v1.md#accepted-dated-axis-atlas-result).
Ordinary chart requests still lack this stellar-motion binding, and a realized
stellar view refuses observer routes. Persistence and ancient/future Earth-bound
observers remain separate K4b.07/K4b.08 work. See the
[atlas guide](../user_guide/atlas.md) for current commands and limitations.

## Scientific state as implemented

`CoordinateSpec` and `ObservationContext` are immutable metadata contracts.
`CoordinateService` owns standards-based astronomical transformations;
provider-specific position generation remains separate.

The stellar catalogue is Hipparcos. Unbound `Stars.position(instant)` returns
the catalogue directions and ignores `instant`; the explicit realized view
instead exposes its admitted model/event positions through that public interface.
Default Skyfield `Star` construction
currently supplies only right ascension and declination: no catalogue
proper motions, parallax or radial velocity. The observed route does compute
apparent AltAz for the requested observer/date; lack of stellar space-motion
propagation does not mean Earth orientation is omitted. Native ICRS axes do
not precess. The native position/realization routes now consistently declare
source epoch J1991.25; the former default J2000.0 metadata was incorrect.
An explicit Gaia full-input nominal provider now exists separately; the default
`Stars` lookup/observed routes do not adopt it.

The [K4a.01 enrichment contract](scientific_contracts.md#stellar-membership-and-enrichment-contract)
now records the complete 118,218-row source population, its visual-photometry
identity and the logical edition/component/matching schema. This design does
not alter the runtime table, source bytes or native/observed routes. Current
chart selections remain independent of future enrichment membership; current
saved-sky v6 does not carry Gaia solutions. The external Gaia acquisition has
completed on Mac; the separate [offline candidate audit](implementation_reference.md#offline-gaia-candidate-audit)
checks cached bytes and retains published Hipparcos-2 Gaia best-neighbour links
through exact HIP keys. Optional 1997-motion diagnostics cannot veto links.
Its same offline owner now optionally supplements missing identities from the
published Kervella Table A.1 through exact HIP keys, preserving primary links and
EDR3/DR2 provenance. A separate explicit bounded static-file acquisition tool
captures that publication; no production provider/network path is added.
The explicit astrometric-input capture now reuses existing Gaia rows, requests only
missing published IDs and captures the corrected Hipparcos-2 table. The same
offline audit can produce a v4 measurement-coverage/fallback inventory. It keeps
position-only and incomplete Gaia solutions distinct, retains original 1997 lookup
where Hip2 is absent/incomplete, and does not activate any production provider.
The independent data-only `stellar_enrichment.py` codec now admits an immutable
local linked-source snapshot, preserving original loaded fields/designations,
Gaia and Hip2 source records and association/availability evidence. The offline
audit owns explicit normalization and no-clobber publication; source-free reload
validates bytes, references, units and membership. Native ingestion and production
providers do not consume the snapshot automatically.
Association retention and measurement availability are distinct
from physical-model admission. The explicit `stellar_state.StellarMotionCatalogue`
now consumes that immutable source and retains every original object, recording
unavailable reasons for missing/unqualified inputs. `StellarMotionProvider`
extends the existing `RectilinearAstrometricProvider`; it does not duplicate its
numerical engine. Explicit source-unit/TCB conversion, reciprocal positive-parallax
distance and spectroscopic RV proxy policies qualify nominal direction/Cartesian
queries through the SDK. Measurement/input-conversion/physical errors remain
unknown. No default star/figure/label/chart/saved-sky or observer path changes;
reduced-input and historical-model admission remain separate.

Native `Stars.realize()` now selects rows with the existing policy and obtains
finite directions from `stellar_state.LegacyNativeStellarProvider` through
`KernelSession.evaluate`. Returned kernel vectors supply the geometry; kernel
failures propagate. Cold skies and saved `_SnapshotStars` inherit this route.
The adapter is a source-native lookup, with J1991.25(TT) source epoch and
explicitly unknown errors, not a proper-motion or zero-motion model.
Missing-coordinate rows retain their legacy metadata/NaNs outside kernel
states for downstream filtering. No acquisition occurs during evaluation.
`Stars.position()` uses the same helper. `Stars.native_positions(identifiers)`
looks up explicit HIP identities in source order, independently of marker
magnitude selection. Native constellation lines consume only that public
interface and join returned IDs to their curated topology, including faint
vertices; they no longer read catalogue coordinates themselves. Saved stars
inherit both APIs. `stellar_catalogue.py` validates source metadata before
publication and mirrors it in an immutable record. Epoch/edition/provenance come
from the data document; native labels inherit the stellar specification too.
Snapshot v3 preserves that metadata; source-bound legacy v1/v2 admission remains
explicit. The metadata audit records remaining nonstellar and resource defects.
Open-cluster geometry now mirrors preserved row epochs/source lineage and source
metadata; a selected uniformly known epoch is scalar, otherwise it is explicitly
unknown at collection level. Snapshot v4 validates that header and restores older
bundles from their row facts. Nonstellar ingestion now preserves source table
metadata/unconsumed columns and converts declared angular units before atomic
publication. Geometry mirrors catalogue metadata; the existing snapshot table
transport retains it. Unitless inputs remain a legacy compatibility path;
A frozen `NonStellarCatalogueMetadata` record now mirrors source facts/units and
source digest. Native and observed specifications consume that record. Unknown
epochs are explicit; snapshot v5 preserves these records and validates its headers
without automatic J2000 stamps. Strict admission refuses missing declarations;
existing charts retain an explicitly marked legacy encoding. Several resources
still lack a declared frame, and all inspected nonstellar tables lack measurement
epochs. Admission is model-specific: `Galaxies` uses `static-direction` and does
not require a source epoch/scale. It keeps native ICRS directions fixed while
retaining any source epoch as provenance. Other providers keep the default
source-epoch policy. Frame/origin/units/provenance remain required for strict
galaxy admission. The SDK now admits explicit `static_direction` states with
optional source epochs and unchanged coverage/error checks. Galaxy public/native
centres, chart-outline centres and observed centre inputs now use a real kernel
session. Missing source origins are explicitly `legacy-unverified-origin` in
that reference; source records and public legacy specifications remain truthful.
Strict metadata closure is still open. Shape dimensions/PA and outline sampling
remain galaxy/domain geometry above the kernel, with the existing observer and
projection services retained.
Open-cluster centres now use the accepted dev8 `catalogue_lookup` capability
for public/native geometry and the maximal table passed into the existing
observer transform/cache. Metadata mirrors row source/epoch labels, explicit
scales, frame/origin gaps and all column units. A canonical derived-table digest
binds every retained field/mask, including uninterpreted motions, into the
provider identity; loaded bytes and saved manifest source digests remain separate
provenance. The source lookup neither propagates nor asserts zero physical motion.
Observed cache keys include returned centre arrays; even a warm cache cannot
suppress a failed kernel query. Selected order, duplicate requests and empty
selections retain their behavior. Snapshot schema v5 is unchanged.
Observed stellar/figure/label input routing is accepted through K3.08. Other families and remaining resource/adapter closure remain open. See the
[adapter contract](implementation_reference.md#native-stellar-kernel-adapter).
Solar-System Cartesian resources, state requests and astrometric/apparent
direction realizers have stronger typed contracts. They solve light time
separately from apparent corrections. These facilities must be reused rather
than reimplemented in a new kernel.

## Explicit stellar angular approximation

`stellar_state.admit_stellar_angular_motion` now admits linked Gaia position,
source TCB epoch and both PMs without distance/RV. It retains every original
object and unchanged source facts, including missing/nonpositive parallax and
missing RV. The catalogue records the normalized tangent approximation and
unavailable rows separately from the accepted full-input model. The shared core's
new `AngularMotionRow` carries unit direction/transverse derivative, with no
physical PV. It uses the existing affine numerical/reuse implementation and a
distinct provider/model/reference/resource binding; Cartesian/velocity/observer
capabilities are refused. Original source epoch remains the extrapolation anchor.
Finite caller coverage is required without a universal short PM cutoff; unknown
source/physical/perspective errors remain unknown. Default star/figure/label/
chart/saved consumers, full-input SI/model identities and cluster adapters are
unchanged. The separately explicit Hip2 fallback is described below; no-PM,
original Hip2 time-scale qualification and product adoption remain pending.

## Explicit long-term frame orientation

The existing `astrometric_coordinates.py` owner exposes LongTermFrame and
`orient_direction_batch`, using corrected ERFA ltpb/ltecm only when explicitly
requested. Finite caller TT validity is bounded to J2000 +/-200000 Julian years;
the TT frame equinox remains independent of each native stellar TCB epoch.
A derived direction-batch view retains the original SDK batch, native source/
evaluation/anchor epochs and uncertainty. Model identity binds exact TT input,
backend versions, actual matrix and domain. No converted SDK state or reuse
certificate is issued. Module import and native propagation remain ERFA-free;
explicit orientation requires the existing ERFA dependency, no observer/EOP.
CoordinateService's current Astropy/default/chart routes remain unchanged.
Physical and total numerical orientation errors stay unqualified; published
qualitative accuracy is not a certified bound. Complete Mac acceptance at
`97921fe8`, PR #328, passed 311 focused, 125 source-audit, 36 documentation and
eight tooling cases, plus 48 actual derived directions. Accepted native stellar
digests remain unchanged; Mac frame model IDs/backend/poles are recorded in the
inventory without requiring cross-platform last-bit matrix identity.

## Historical calendar boundary

The existing `astrometric_coordinates.py` owner provides immutable HistoricalDate
and HistoricalEpoch records and `resolve_historical_date`. Explicit proleptic
calendar/year/continuous-scale input is normalized without large summed-JD
rounding, then passed to the unchanged SDK TimeService for an admitted TCB
conversion. Original date labels and source-date uncertainty remain alongside
separate numerical calendar/conversion receipts. TCB identity and existing
TDB/TCB admission require no observer or acquisition; unsupported conversion
refuses. The isolated native stellar path accepts ancient dates without EOP,
Earth ephemerides or scientific imports. This adds no historical observer,
precession or physical/date-error propagation. Complete Mac acceptance at
`ceeb894b`, PR #327, passed all focused/audit/documentation/tooling gates and
24 actual historical states. All accepted Gaia/Hip2 digests are unchanged;
source-date uncertainty remains separately retained, not propagated into a
total angular/physical accuracy claim.

## Explicit Hipparcos-2 angular fallback

The same stellar owner now exposes `admit_stellar_hipparcos2_motion` with an
explicit `nominal-tcb-deferred-qualification` epoch policy. It admits only
position/both-PM Hip2 rows where Gaia angular inputs are unavailable, then uses
the unchanged shared angular engine. The original unknown source scale and
all raw source evidence stay intact; nominal TCB interpretation is separately
bound in the model identity, with unknown convention error and
[issue #326](https://github.com/fselman/wenu/issues/326) for later qualification.
No actual time conversion, distance/velocity inference, component correction or
automatic consumer adoption occurs. Existing Gaia admission bindings and all HIP
objects remain. Complete Mac acceptance at `d71ee8da` in PR #325 passed:
2,850 Hip2 fallback models plus 115,105 Gaia angular models, with 263 original
lookup entries retained. Both Gaia digests are unchanged; 24 sampled directions
passed the independent Decimal arithmetic check. Physical/time-convention
accuracy remains unevaluated. See the
[API](implementation_reference.md#explicit-hipparcos-2-angular-fallback).

## Explicit nominal cluster motion API

The `cluster_state.py` source adapter now admits immutable qualified cluster
solutions and supplies its compatibility facade over the shared
`astrometric_state.RectilinearAstrometricProvider`. The object-independent core
owns separately typed SI/angular rows, domain checks, affine evaluation, numerical
verification and angular certificates. Object types and source facts enter through explicit SDK bindings;
the core imports no catalogue/observer/graphics or astronomy dependencies.
The facade supplies the same real SDK `epoch_direction` admission. It converts source
spherical differentials through Astropy and evaluates the declared SI rectilinear
centre model at explicit TCB instants within a required finite nominal domain.
The runtime metadata resource binds the accepted source companion and its
qualification; unsupported rows and unevaluated physical errors remain explicit.
The actual 513-row source has 502 full-input solutions, seven missing RVs and four
unqualified Dias-only epochs. Provider-owned exact-rational cone certificates
now bound numerical direction reuse within that declared domain. Only explicit
interactive sessions reuse prior anchors; reproducible sessions evaluate the full
model. The bound starts from admitted binary64 SI states and does not certify
source conversion, measurement or physical accuracy. Velocity output on the direction admission remains
unsupported. Explicit Cartesian admission now supplies SI position/velocity through
the same core with separate unknown error evidence and no Cartesian bounds/reuse. Default chart/observed/saved consumers continue to use source
lookup. Explicit native chart calls now accept the admitted motion catalogue and
an explicit TCB context epoch, query a reproducible kernel session and consume
its returned vectors. Restored v5 skies use that same inherited facade without
reloading source catalogues or persisting evaluated states. The native chart
guard checks returned epoch/scale against the request; unchanged static layers
retain source epochs. Explicit observed Python charts now call the shared realizer through a prepared
reception context. Ordinary horizontal request/CLI/TOML selection now composes the
same service through layer-local motion/reception geometry options. See the [API and limits](implementation_reference.md#nominal-cluster-motion-provider).

## Observer motion prerequisite assessment

The default cluster observer seam discards distance/velocity: lookup RA/Dec enters
`catalogue_point_altaz` and `CoordinateService`. The cluster catalogue contains SI
PV internally, and its provider now offers explicit direction or Cartesian output. The SDK already
supports a separate Cartesian admission; adopting it does not itself solve observer
time/common-coordinate conventions or apparent-place realization. Existing
Solar-System light-time realization has incompatible geometric emission semantics.
The [observer contract](scientific_contracts.md#cluster-observer-realization-contract)
and [ordered gates](kernel_roadmap_v0.9.5.md#cluster-observer-implementation-order)
now specify those prerequisites. The explicit Cartesian prerequisite is implemented with the accepted SDK.
`astrometric_coordinates` additionally supplies a resource-free TCB/TDB adapter
for explicit SDK TimeService registration and a complete-batch spatial scaling
view. `astrometric_observation` separately prepares UTC/TT reception events,
TDB/TCB receipts and a nominal ERFA EPV00/APCO terrestrial observer context from
explicit local leap/final IERS-B resources. It records installed code identity and
independent coverage, never borrowing the Observer Skyfield SPK identity. Total
errors remain unknown. The same observation owner now realizes full nominal
Cartesian batches into finite-range observer directions and vacuum Alt/Az.
It preserves source states and a frozen, integrity-bound ERFA reception context;
observer subtraction, finite-source solar deflection and annual/diurnal
aberration each have one owner. No second propagation or target light time is
applied. `LayerRealizationContext.from_reception` carries this event into the
canonical chart pipeline. Explicit cluster motion uses actual Cartesian SDK
states, converts the service's radians to degree geometry and preserves the full
observation receipt. No legacy Observer is needed for this route; unmigrated
layers refuse reception realization rather than silently ignoring its resources.
The chart guard checks vacuum AltAz/site-event binding before projection.

## Abstraction barriers that remain incomplete

The following are retained compatibility properties or later K5/extraction
obligations, not unresolved baseline routing bypasses. K3.40's current ledger
supersedes the earlier partial-consumer status.

1. Application `sky/assembly.py` owns concrete layer construction; central sky,
   factory and snapshot APIs delegate to it. Astronomical packages are not yet
   independently extracted or discovered through a plugin registry.
2. `SkyLayer.realize()` retains its documented legacy fallback to
   `spherical_geometry(observer)` for compatible geometry layers. Applicable
   physical/catalogue consumers use their admitted state/observation routes;
   constructed geometry need not become an object-state query. Final uniform
   facade/lifecycle placement is a K5 review, not a new capability claim.
3. Frozen coordinate metadata does not make every geometry result immutable:
   general arrays, dictionaries and layer collections retain their documented
   mutability/aliasing contract. This does not imply general thread safety.
4. Request preparation temporarily installs layers and rebinds resolvers.
   Minor-body registration/alias and atomic resolver rollback is accepted in
   PR #243. PR #244 adds a synchronous request-state journal
   around ordinary request preparation. It restores original layer identities
   and order, horizon/disk aliases and point-label flags on close or failure;
   overlapping builds on one mutable sky fail before configuration. Failed cleanup
   retains the lease; a returned build can retry close before another request. Configuration
   owners explicitly remember their writes; direct standalone configuration
   calls retain their persistent semantics. Catalogues/resources/scientific
   caches are not cloned or rewound. This is isolation of canonical request
   configuration, not thread safety, arbitrary caller mutations or kernel routing.
   `open_chart_request_scope()` now gives ordinary generation, direct
   `charts/drawing.py` execution and native atlas sheets the same entry/cleanup
   owner. The view path preserves its prepared geometry and helper order while
   journaling writes through `ChartRequestBuild.remember_attribute`. Native
   sheets acquire the lease without an observer or ordinary configuration.
   Their export pages use an owned offscreen Agg canvas at fixed 100-dpi layout
   resolution. This isolates grid-label measurements from GUI/display scaling;
   the requested raster export dpi remains a separate output setting.
   Atlas API/worker execution defaults to `wenu_chart atlas-sheet`, removing
   the direct-generator fallback. This accepted lifecycle change is distinct
   from the current native stellar kernel adapter.
5. `charts/atlas_sheet.py` owns the validated public sheet request,
   presentation, chart adapter, rendering, furniture and report service.
   Both batch publication and generic request execution depend on that leaf. Generic request
   execution consumes that public result while retaining scope/staging and
   atomic publication. The former private furniture/report-helper cycle is
   removed. Publication workers use the public chart command and the same
   request type; the old request-generation import remains an identical alias.
   Whole-catalogue count appendices now consume full-source native stellar
   geometry and its photometry, retaining unique-HIP/source-order counts.
6. Native snapshots are existing transport/reuse objects, not a universal
   physical-state store. A saved design-bound snapshot is not interchangeable
   with an arbitrary epoch/observer request.

Existing package-boundary tests protect the broad geometry/projection/domain
separation, but do not enforce all these semantic or internal product barriers.
See the [as-is diagram](kernel_roadmap_v0.9.5.md#current-architecture).

## Current incomplete science and compatibility

Keep implemented planet, Moon, minor-body and satellite functionality during
migration. Incomplete capability is not enabled merely by registering a package.
See [scientific contracts](scientific_contracts.md) for retained resource,
time, provenance, uncertainty, photometry and satellite limitations.
Ancient-calendar input and long-baseline stellar propagation are not currently
supported by the ordinary observer parser.

## Verification and history

Baseline production content passed all 3,606 plugin-disabled Mac tests at
`ea8dc505` before merge; the merge has the identical Git tree. Follow the
[testing policy](testing_policy.md) for subsequent changes. Numerical, visual
and print evidence are different obligations; one does not substitute for another.
Full historical text is retained in the
[baseline archive](archive/pre_kernel_20261017/INDEX.md).


## Ordinary request cluster model selection

`charts.request.ClusterMotionRequest` is the immutable user input contract.
Schema-v2 translation and the installed CLI supply it to `ChartRequest` through
the existing view/drawing path. `charts.request_realization` composes the accepted
packaged source admission and explicit offline reception backend once per export
request; it adds no propagation or observer mathematics. Only the cluster layer
receives its motion/reception options. Its adapter checks chart site/time/vacuum
meaning, then calls the same Cartesian/observer route as standalone Python use.
Other layers retain their existing observer resources and scientific models;
this does not claim a common new backend for every family.

Spatial catalogue selection skips lookup pre-culling for this explicit model,
retains requested cluster membership/exclusions and lets canonical projection clip
realized positions. Model selection remains separate from style/content enabling
and minimum angular-size filters. Request state is not installed on shared sky
layers. Output provenance and sequence identity include active model admission;
lookup omits the added field to retain its existing identity. Native atlas-sheet
requests and non-horizontal chart frames do not adopt this opt-in.

## Generic nonstellar and target lookup routing

Accepted K3.12 (PR #276) opts the generic NonStellar owner into catalogue lookup for
public points, native outlines/labels and observed centre/outline inputs. Galaxy
and generic lookup share metadata admission, epoch handling and vector decoding
mechanics while retaining distinct model/resource identities. The dedicated SNR owner opts into the same mechanics under K3.15 below.
K3.13 now opts the globular owner into the same source-bound lookup/cache mechanics
with its own globular semantic type and model/provider/resource identity. Half-light
diameter construction, structural metadata, common names and selection are unchanged.
Globular routing is accepted through PR #277.
Returned generic states enter both observation cache identities before reuse.
Named ResolvedTarget coordinates similarly query immutable copied target records;
object-centre and binocular preparation consume that public coordinate. Explicit
user coordinates remain constructed references. Target provenance/components are
preserved without claiming source epoch or physical origin qualification. No
source membership, aliases, selection, observer mathematics or rendering changes.

## Planetary-nebula kernel lookup

Accepted K3.14 (PR #278) opts PlanetaryNebulae into the accepted shared lookup/cache
mechanics with its own PN centre/provider identity. Its native point-symbol route
uses returned centres rather than reading raw coordinates; its observed-symbol
route queries a returned state table before cache access and includes that state
in cache identity. Inherited public position and observed centre APIs use the same
lookup. Empty observed selections remain empty without a query.

Native catalogue order and observed requested order/duplicates retain their prior
behavior. True/probable catalogue inclusion, curated criteria, minimum-size
filtering, diameter/flux metadata and fixed display symbols are unchanged. No
central-star position/motion substitutes for the nebular centre, and no motion or
expansion is introduced. Cold/restored skies share these methods.

## Supernova-remnant kernel lookup

The K3.15 candidate opts SupernovaRemnants into accepted source-bound catalogue
lookup and returned-state cache hooks with its own SNR provider/model/resource
identity. Public centres, native outlines/labels, observed centre/outline inputs
and restored sources consume returned directions. Queries precede cache access;
changed states invalidate reuse and refusal propagates after warm results.

Green radio major/minor diameters, missing PA and existing equal-area circle
interpretation remain unchanged. Signed Galactic designations, selection, radio
flux metadata and appearance are preserved. No associated compact-object position
or motion substitutes for the radio-centre source, and no expansion or propagation
is added. K3.15 is accepted through PR #279; physical source qualification remains explicit.


## Observer resources and observed caches

`Observer` still owns one Skyfield ephemeris; existing request owners close only
resources they own. Its geometry-resource check binds the loaded SPK bytes and
open file descriptor, refuses closed/changed resources and does not reload a
replacement pathname. Shared point/polygon caches and the stellar maximal cache
now include effective EOP data/masks/units, leap data, installed backend versions,
Astropy ephemeris selection and live Skyfield time/backend inputs. Resource changes
cannot reuse an old geometry entry merely because site/time/name/path match.

`CoordinateService` retains Astropy transformations. `skyfield_stellar_altaz`
retains the no-deflectors stellar calculation; the explicit nominal observer
service retains verified offline reception receipts and full recomputation.
These backend adapters remain transitional Wenu owners with the accepted SDK and
kernel geometry dependencies; K5.02 reviews final facade/packaging placement.
No reverse dependency into Wenu is introduced in the standalone kernel.

## Application sky assembly

`sky/assembly.py::SkyAssembly` owns the existing concrete layer construction and
source-free reconstruction bodies. `CelestialSphere` owns ordered `SkyLayer`
registration and chart orchestration; its `add_*` methods are compatibility
delegates. `maximal_sphere.py` keeps the immutable load profile and public factory
entry points, delegating builds to application assembly. `NativeSkySnapshot`
keeps verified data/codec admission and delegates facade reconstruction.

The ordinary factory, native factory and snapshot reconstruction accept a local
`assembly=` override. The default is stateless and selected lazily. Existing
atlas worker initialization already calls `snapshot.make_sky()`, so cold, saved
and spawned construction reach the same owner without passing live sky objects
between processes. No executable factory or assembly object is stored in v6.
Layer order, compatibility attributes and existing observer ownership remain.

This is application composition, not a new kernel service or independently
installed module. The broad Wenu package facade still exports concrete families;
package isolation/extraction and remaining chart/private-helper work retain
their later roadmap milestones. No numerical or rendering algorithm moves here.


## Ordinary chart consumer boundary

The five ordinary chart families share request preparation and render-local
composition. Targets enter through admitted lookup and CoordinateService;
group framing and automatic catalogue selection consume public returned layer
geometry. Masks use the existing coordinate/domain services. Styles, detail,
mode and furniture keep their separate policy roles; rendered magnitude counts
read projected output. The [K3.20 assessment](kernel_migration_audit_v1.md#k320-ordinary-chart-consumer-assessment)
records these actual seams and their verification without changing production
mathematics. The chart/atlas helper boundary remains K3.21; no full K3/K5 or
independent astronomical-package closure is implied.

## Ordinary temporal sequence consumers

`charts/sequence.py` replaces only the observer instant and deterministic
output path in each immutable chart request, then calls the ordinary static
generator with the same effective configuration. That generator owns
observer/resource cleanup and constructs the frame's realization context.
Timeline UTC sampling, civil display time and playback cadence remain distinct.

Schema-v1 manifests retain declared request/configuration, physical/display
instants and playback identity, plus completed output sizes/hashes. Resume
checks compatibility before generation and reuses only verified files;
a failed frame cannot acquire a completion record. This verifies a declared
plan and saved bytes, not a certificate of current external source/backend
accuracy or identity. Later moving-body models remain separate.

A frozen `FullSkyChart` now retains the immutable viewport produced by its
existing circle fit. Recomputing that fit could differ numerically and trigger
the strict same-chart composition guard. The formula, guard, horizon arrays,
projection and renderer algorithms are unchanged.

## Fixed-sky and rotating-horizon consumers

The fixed-sky sequence retains two observer instants: the celestial anchor
determines the reference orientation; each frame's local observer supplies the
ordinary realization, horizon, visibility and furniture time. CoordinateService
transforms the constructed FK5/J2000 reference independently at both instants.
The established signed angle correction is consumed by the canonical request.

Cold execution builds each frame independently. Loaded-sphere execution reuses
only the unbound catalogue container, with a fresh local observer, request lease,
realization, projection and export per frame. It does not cache evaluated
celestial states or introduce proper motion. The independent complete-render
baseline remains an ordinary observer-time sequence, without inheriting the
anchor-relative rotation. Its graphical comparison helpers are unchanged.

Frame resolution now registers each successfully created observer for cleanup
immediately. A failed second construction or one failing close cannot leave
the other observer open. No orientation, provider or rendering formula changes.

K3.25 adds a Wenu ephemeris-to-Cartesian-SDK adapter for default major-planet
and Moon point assembly. Ephemeris backend/model knowledge remains outside the
generic kernel. Request-scoped borrowed sessions return SI states to the retained
light-time and apparent services through the existing AU protocol. Tracks/disks
and minor-body adoption remain separate. Filename-based DE-model inference is
removed; unknown models remain explicitly unqualified. K3.25 is accepted through PR #298 after 83 focused Mac cases; this does not close K3/K5.

K3.26 extends the existing adapter at default single-disk, observed-sequence and
frozen-Earth sequence assembly. Target/Sun states and the initial frozen Earth
vector feed the unchanged appearance/disk algorithms; raw reception/apparent
backends retain their separate role. Component owners check live resources (SPK only for the frozen geometric path)
before reuse and share only within the same context object. Equal
values in a separate request context trigger fresh admission. No long-lived
evaluated-state cache or new astronomical model is added. K3.26 is accepted through
PR #299 after 138 focused Mac cases.

K3.27 adapts known Skyfield planet/natural-satellite target bindings inside the
existing track realizer, covering both default assembly and the planetary binding
returned by a mixed minor-body resource session. Observer/apparent sources remain
raw; custom protocol and asteroid/comet state routes retain compatibility. The
track component owner checks the existing observer-resource key before same-context
sharing; an equal-valued separate context performs fresh admission. Exact sampling,
tick insertion, one fixed-product-axis transformation and temporal/annotation
algorithms are retained. Accepted through PR #300 after 83 focused Mac cases; K3/K5 remain partial.

Asteroid offline sessions now supply kernel-backed geometric target bindings to
the existing point and sampled-track consumers. The common Cartesian adapter
retains both small-body and planetary resource identities and the original
minor-body solution/segment record. Numerical composition, apparent corrections,
projection and renderer remain their existing owners. Ceres solution facts live
in a versioned packaged manifest, with the legacy constant retained. Warm track
sharing checks the asteroid resolver's lifetime as well as the observer key.
Comet offline sessions now use the same target adapter, preserving their original
solution/non-gravitational parameters, segment and resource chain. The adapter
forwards the existing optional provider tail-angle sample; point and sampled
symbols keep their existing orientation/fallback algorithms. Warm track reuse
re-admits either asteroid or comet sessions. Discovery and model photometry retain
validated provider records, which the existing CLI/report owners consume directly;
they do not invent positional states for scalar magnitudes. Acquisition stays
outside deterministic rendering. Comet routing is accepted through PR #302 after 273 focused Mac cases.
Astronomical package extraction remains pending.

Antisolar references remain constructed geometry. The existing shared point
owner supplies apparent Sun fallback geometry to both comet points and sampled
symbols. Known Skyfield Sun states use the existing Cartesian adapter; observer
and apparent-correction backends retain raw ownership. Optional provider PsAng
continues to take precedence and does not trigger a fallback Sun query. Immutable
construction receipts retain the source frame/resource and actual sample
observation before transformation into fixed product axes. Explicit Astropy
antisolar points retain their construction-time antipodes and receipt when
later displayed with another observer; they are not physical SDK objects.

## Satellite state and observer boundary

The existing `Sgp4TemePropagator` now transports scalar and array results through
the existing Cartesian SDK in its current owner. The retained SGP4 backend still
receives the original split UTC Julian dates and produces geometric Earth-centred
TEME, never ICRF. The adapter returns admitted SI PV through the original typed
kilometre API, preserving source/snapshot identity, epoch/age and status errors.

Request-scoped borrowed registration binds the complete canonical element record,
optional caller snapshot digest, propagator implementation and installed leap-table
identity. UTC-to-TAI conversion labels the SDK query only; it changes no SGP4
input. Admission is limited to the exact finite request, with unknown uncertainty
and no temporal reuse or invented prediction-validity interval.

The existing Astropy TEME-to-ITRS and observer-subtraction services retain their
formulas, installed EOP evidence, WGS-84 site and geometric vacuum policy.
Snapshot validation/external admission remains upstream; acquisition remains
separate from evaluation. Later candidate/crossing/report/illumination/radiometry
migration and astronomical package extraction remain pending.

## Sampled satellite candidate boundary

SatChecker maintenance explicitly submits or polls once and retains local exact
receipts. Its existing parser publishes immutable typed candidate/sample evidence.
Presentations consume those records; candidate track/sample layers call the shared
`CoordinateService` and kernel spherical geometry before the canonical domain,
projection and renderer pipeline. These routes already meet their service boundary
and require no production rewrite.

Supplied samples keep their individual UTC/UT1 times, response digest, provider
version, warnings and candidate-only semantics. Track geometry is an open sampled
polyline; a singleton remains one point. No interpolation, propagated state,
continuous containment, entry/exit event or new physical accuracy is inferred.
Rendering does not acquire data or invoke SGP4. Existing source-inferred frame
meaning and provider licensing/coverage limitations remain explicit.

## Exact satellite consumers

Exhaustive solving, conservative cone/shell selection and default exact-track
realization use the accepted `Sgp4TemePropagator` Cartesian-kernel route and
existing topocentric observer service. Their numerical algorithms remain their
existing owners. The selector's retain/indeterminate outcomes reach exact solving;
only admitted rejection evidence can omit a record. Existing explicit exhaustive
fallback or fail-closed policy remains authoritative.

Multi-field coordination validates the complete request and current whole-interval
airmass admission before any solve, preserving input order and chunking. Strict
matrix evidence and fresh-process execution use the same scientific services.
Historical production-matrix receipts retain their pinned provenance; the small
synthetic worker check is not a new production performance/capacity qualification.

Solved-track path/event layers consume immutable retained samples, then shared
coordinate/kernel geometry and canonical drawing services. Event views select
existing sample anchors without propagation or resampling. Same-spec native
geometry remains a valid identity path. Exact events, bounded sampling tests and
the absence of a global continuous-error proof remain distinct metadata claims.

## Satellite report consumer boundary

Exact reports are immutable scientific evidence, built from the coordinator's
ordered `MultiFieldCrossingResult` values. The report owner validates source,
observer, field, interval, airmass and acceleration identity before publishing a
canonical payload. It performs no orbit or coordinate evaluation. The private
tabular owner projects that same payload to ECSV/VOTable and reconstructs the
same validated report; these are interchange views, not alternate science.

The satellite CLI assembles the existing snapshot admission, typed requests and
multi-field coordinator, then calls the report owner. Direct, initial-file and
validated-subset modes use the same services. Validation is current on each call;
a prior validation file is not permission to bypass changed resource/domain
refusal. Report bundles are staged and round-trip checked before atomic
no-clobber publication. A failed write or competing publisher leaves no partial
Wenu bundle and preserves the other writer.

Planning advisories consume only validated exact reports and caller-owned
planning contexts. Existing half-open interval overlap, labels and scientific
status remain in the advisory owner. They neither propagate satellites nor
contact observatory systems. K3.34 verifies these existing boundaries without
production changes; package extraction and K3/K5 closure remain separate.

## Satellite illumination and shadow boundary

The existing illumination owner composes typed satellite states, geometric
Earth-to-Sun ephemeris and installed-EOP orientation in ITRS. Known
`SkyfieldEphemerisStateSource` inputs now use the existing request-scoped
`KernelEphemerisStateSource` before the retained geometry. Already adapted
sources are not wrapped twice; custom injected state protocols retain their
existing path. Source/model knowledge remains in Wenu, not the generic kernel.
The borrowed ephemeris remains caller-owned; this adds no source cache or
resource acquisition.

The observer-independent shadow finder already obtains satellite states from
the accepted SGP4 Cartesian route. Kernel failures there now map to its existing
typed propagation-failure code, retaining the original exception as cause.
Illumination and transitions use the same Sun assembly boundary. The original
finite-Sun/WGS-84 quadrature, twilight mathematics, continuous limb margins,
contact subdivision/bracketing and physical domains remain unchanged. This is
K3.35 routing, not new illumination, radiometry, brightness or visibility science.

## Solar radiometry resource boundary

Bolometric and spectral radiometry consume accepted immutable illumination
geometry; they do not re-query or propagate physical states. K3.36 retains those
calculation owners. TSIS edition facts now live in packaged
`data/solar_spectral_resource_tsis1_hsrs_v2.json`, validated into a private frozen
record in `satellites/radiometry.py` before compatibility constants and the
existing public resource identity defaults are published. Mathematical models,
integration/error policies and unit support remain software contracts.

The external spectrum is still loaded only from an explicit caller path after
exact byte-count/digest admission. Metadata is shipped; the spectrum is not.
The parser, native grid, inverse-square/visible-fraction scaling and native
energy integration retain their algorithms and original tolerances. Missing or
invalid packaged metadata fails rather than reconstructing embedded source
facts. Public identity fields and constant values remain compatible. No
redistribution permission or current source acquisition follows from this move.

## Public consumer and teaching boundary

K3.37 retains the existing public Python facade, eight command entry points,
configuration schema/precedence and translations. The six canonical examples and
their packaged copies still delegate to public sky/view/drawing services. They
now close the owned observer when view preparation fails, as well as during
product setup/drawing failures; no accepted example request changes.

All five shipped notebooks had retired imports and low-level render calls.
They now declare their existing La Ligua date, stereographic east-west reversal,
magnitude limit and references through current atlas composition and canonical
export. They do not reproduce the obsolete manual renderer's pixel layout.
Notebook data are explicitly included in both source and wheel distributions.
No astronomical calculation, shared service, dependency or public API changes.
K3.37 is accepted through PR #310; subsequent K3.38/K3.39 acceptance is recorded in the current reconciliation. K5 remains separate.

## Maintenance and resource consumer boundary

K3.38 distinguishes application consumers from source-maintenance, explicit
acquisition, independent validation and build-only publication. Raw source-table
normalization/crossmatch and separately expressed scientific oracles retain
their existing owners; wrapping them as application state queries would alter
responsibilities or invalidate comparison independence.

The zodiac review adapter now obtains its mean-ecliptic J2000 pole and FK5 J2000
centre label through CoordinateService, keeping the same Astropy transforms,
vacuum observer context, orientation formula and title formatting. Its private
helpers still return SkyCoord compatibility values. The reusable-sphere manual
benchmark registers each successfully constructed observer for cleanup before
the next acquisition; all cleanup callbacks run even if one close fails.

Resources/build adapters retain digest-bound admission and pure copying. No
runtime provider, source catalogue, dependency or build-rule changes occur.
Explicit provider policy/preflight tests use synthetic transport; they establish
mechanism, not renewed provider permission. No external workload is executed.

## Geometry and graphics consumer boundary

K3.39 retains the existing kernel geometry/topology/domain/clipping and three
projection implementations. Wenu compatibility imports remain identical aliases.
Regional/full-sky charts pass spherical geometry through the canonical viewport
guard before preparation; Mollweide owns map seams and polar products use their
existing face-cap/latitude paths. Equidistant numerical curves remain strictly
finite; separate components express disconnected curves. Missing point rows
retain their accepted NaN slots and entity metadata.

Preparation owns marker sizing, culling and label offsets; Matplotlib consumes
projected records. Graphics helpers and SVG serialization have no astronomical
provider role. Application reference furniture may construct/transform coordinate
grids through CoordinateService and shared projections before drawing; it is not
part of the generic renderer. Legends consume returned rendering/metadata and
footers consume resolved text. No production correction was demonstrated in this
bounded audit. Existing dependency direction, scientific meaning and physical
appearance are retained. K3.40 reconciliation and K3/K5 closure remain separate.

## Complete consumer reconciliation

K3.40 pins the current source/public/operational census at main `0deca8c3`:
274 root production Python files, 22 kernel files, 86 operational tools and six
source examples (388 files total); the six packaged example copies are already
within production. It also records all 290 root exports, 20 modules declaring
`__all__`, eight installed commands and five packaged notebooks. Historical
inventory counts and per-slice receipts remain historical, rather than being
silently relabelled as a new full census.

Each path has an exact source blob, responsibility group, appropriate route and
accepted evidence IDs. All 39 preceding K3 obligations are reconciled; raw state
and coordinate calls remain in the appropriate provider/shared-service owners.
No new applicable baseline bypass was demonstrated. No production implementation
changes are needed. The candidate closure is routing/compatibility acceptance,
not complete physical source qualification, Gaia propagation or SDK freeze.
The source namespace includes a legacy explicit Hipparcos ReadMe downloader
with import-time network/write effects; it is source-inspected only, outside
deterministic import/test/render routes. This is not new acquisition authority.

Complete Mac audit/documentation acceptance is pending. After acceptance,
Fernando's six-product review precedes Gaia. K5 final contract review/freeze and
independent astronomical package extraction remain separate.
