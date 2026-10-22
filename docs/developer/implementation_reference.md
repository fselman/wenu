# Wenu implementation reference

## Finite constellation segments in regional products

Product-review correction PR.03 marks constellation endpoint curves with
`segment_geometry = "minor_great_circle"`. Kernel dev12's existing
`project_geometry_for_viewport` boundary clips those explicitly declared
segments to the safe spherical cap before projection. Wholly interior
segments retain their exact endpoint chords; distant antipodal chords cannot
cross the visible field. Both-outside arcs that enter the cap are retained,
and per-edge IDs, names and HIP metadata follow the surviving geometry.
Sampled curves and grids retain their existing projection path. No source
topology, observer transformation, renderer, cluster sizing or label placement
is changed. Source-free restored constellations acquire the same declaration
when realized. The focused gate is `finite-constellation-segments`; final Mac
visual acceptance remains the reported Sco/Lib/Sgr/Oph replot.

**Implemented baseline:** `6708f54a`. This is an entry-point reference, not a
forward API specification. [Source map](source_tree.md) and
[scientific contracts](scientific_contracts.md) supply the detailed owners.

The [agreed service-kernel boundary](kernel_roadmap_v0.9.5.md#proposed-architecture)
includes the existing geometry/topology/projection interfaces as shared services.
The state SDK is one component. Product/domain consumers call the service needed;
source contours need no artificial ObjectRecords or universal state-query wrapper.
KG.03 keeps existing Wenu API names as same-object kernel aliases. Numerical
algorithms remain unchanged; explicit canonical geometry imports no longer
require importing the Wenu application.

## Constructed reference service routes

K3.17 verifies the existing implementations: grids and planes construct typed
source curves then use `CoordinateService`; poles/keypoints preserve their
defining frame before native/observer transformation. IAU boundaries sample and
test membership in FK4/B1875. Horizon/visibility remain observer-local, using
shared geometry/domain/projection services for chart masks. Existing saved skies
restore those same classes through the layer registry. No new algorithm or API
is introduced. See the [routing assessment](kernel_migration_audit_v1.md#k317-constructed-reference-service-routing-assessment)
for ownership, returned-value/refusal evidence and remaining limits.

## Diffuse contour source admission and saved skies

K3.16 uses `sky/isophote_sources.py` for immutable, byte-bound source receipts.
Each level retains original GeoJSON document/feature properties and IDs, the
loaded document SHA-256 and a normalized geometry digest covering compounds,
ring order, holes and original longitude encodings. Captured packaged provenance
is retained with its checksum. Milky Way split contours are checked against the
hash-verified canonical D3 source; Cloud product digests must match their sidecar.
Custom sources retain their own declarations without acquiring packaged provenance.

Milky Way source frame/epoch declarations are absent. ICRS/degree rendering remains
an explicit compatibility interpretation. Cloud products declare ICRS/degree axes;
the Gaia DR3 release and proper-motion selection describe derivation, not a contour
measurement epoch or motion model. Physical origin, distance and morphology epoch
remain unqualified. The native CoordinateSpec retains the existing ICRS chart
encoding convention, not a newly measured physical origin. Unsupported explicit
frame/units/epoch/origin declarations refuse rather than being silently transformed.

Loaders validate before publishing new data. Native and observed realization check
metadata, geometry and Cloud fractions before cache lookup. Public kernel spherical
records and existing topology/domain/projection services carry the same vertices;
source interpretation stays in Wenu. Geometry metadata exposes the source envelope
as `source_metadata`; layer `catalogue_metadata` owns the immutable record.

New saved skies use **v6** (`wenu-fixed-sky-records-v6`) and require these envelopes.
Admission checks their level coverage, geometry and manifest source digests before
restoration. v1–v5 remain readable without original source/provenance files, but
receive explicit legacy receipts with unavailable original properties and no
captured provenance envelope. Existing source digests remain useful integrity
facts; they do not recover discarded declarations. Older readers reject v6.
No observer state, morphology evolution, new SDK API or kernel release is added.


## Shared kernel geometry records

`StereographicProjection.project_points` (also used by the equidistant subclass)
preserves the collection length and IDs/names/labels/metadata. It projects finite
coordinate rows; missing input rows produce NaN x/y slots. Entirely finite input
uses the unchanged numerical call, and empty collections retain their existing
behavior. Direct `project_spherical` validation is unchanged; missing rows cannot
hide a finite invalid latitude or opposite-pole coordinate elsewhere in a batch.
Source tables and missing-state admission are unaffected by this geometry repair.


Kernel dev11 exposes CoordinateSpec, PositionStatus and GENERIC_SPHERICAL_SPEC
from `wenu_kernel.coordinates` without NumPy or Wenu. Explicit
`wenu_kernel.geometry` imports provide SphericalPoints/Curves/Polygons/Grid,
ProjectedPoint(s)/Curve(s)/Polygon(s)/Grid, SphericalFrame,
SphericalCoordinates and Viewport using the optional NumPy geometry extra.
The existing leaf namespaces remain available under both canonical and legacy
names, with identical class objects. Source/observer factories and
ObservationContext remain in `wenu.coordinates`.

`wenu_kernel.geometry.topology.ring_interior(coordinates, pole_winding)`
retains the existing degree-input north-pole outline convention and returns the
filled-side boolean and area in steradians. The source adapter still chooses
the winding interpretation. Writable-array and shallow-metadata semantics remain
unchanged; these values are not immutable SDK state batches.

Kernel implementation commit: `ba591f156573324c3e08f9fb4d7bf626e2197f9c`.
Root packaging selects its `geometry` extra. State SDK imports stay stdlib-only;
geometry imports require no Wenu/Astropy/Skyfield/Matplotlib. KG.04 additionally exports StereographicProjection,
PolarAzimuthalEquidistantProjection and MollweideProjection through
`wenu_kernel.projections` and their existing leaf modules.
`wenu_kernel.geometry.clipping` owns existing projected viewport/convex clipping
and centroid functions; `wenu_kernel.geometry.domain` owns the six public
latitude/cap/viewport-projection operations specified in the
[geometry contract](kernel_contract_k1.md#14-kg02-geometry-service-contracts-and-placement-plan).
Existing Wenu projection classes and mathematical preparation functions are
identical aliases. The demonstrated private `_clip_polyline_to_viewport`
legacy test seam also forwards without becoming a public API. Projection
formulas, capability differences and failure behavior are unchanged.
`wenu.rendering.preparation` retains magnitude/diameter sizing, point styles,
marker-margin culling and radial label offsets. No kernel rendering dependency
or automatic object-state query is introduced.

## Canonical public imports

```python
from wenu import (
    AdaptiveDetailPolicy,
    AllSkyChart,
    AtlasChartStyle,
    BinocularChart,
    CartoonDetailPolicy,
    CelestialSphere,
    ChartContentOptions,
    ChartLegendSelection,
    ChartStyleOverrides,
    CircumpolarChart,
    DetailOverrides,
    FixedDetailPolicy,
    FullSkyChart,
    LegendOptions,
    MatplotlibRenderer,
    Observer,
    PresentationMode,
    PrintMode,
    RegionalChart,
    ResolvedDetail,
    SkyContentSelection,
    add_chart_arguments,
    chart_detail_overrides,
    compose_chart,
)
```

Keep compatibility exports in `wenu.__init__`; do not infer that a future
provider package may depend on this broad product-level facade.
`Observer` owns its loaded ephemeris: use it as a context manager or call
`close()` when its lifetime ends.

### Observer resource lifetime and geometry cache identity

`Observer.geometry_resource_identity()` checks the live owned SPK descriptor.
It hashes its bytes on first geometry admission and guards device/inode, size,
mtime and ctime thereafter. A closed, replaced or modified admitted handle refuses
before warm-cache lookup. Closing stays idempotent; create a new Observer to adopt
a different ephemeris. A filename/model guess is not source qualification (M10).

`observer_geometry_key` is process-local, not a serialized scientific receipt.
It conservatively binds active EOP columns, units, masks and metadata, IERS policy,
ERFA leaps, backend versions, Astropy ephemeris selection/kernel and live Skyfield
observer/time/Timescale inputs. Point/polygon helpers and `Stars.observed_altaz`
share it. Existing provider admission still precedes geometry reuse. Unchanged
inputs retain maximal-selection reuse; changed resources recompute or propagate
refusal. Duck-typed test/legacy observers keep their existing compatibility route;
this does not qualify unknown resources or establish apparent-place accuracy.
The legacy Astropy resource-loading policy is unchanged; the explicit offline
reception backend remains the separate strict admitted path. No observer/resource
handles or process-local keys are persisted in native snapshot v6.

### Application sky assembly

`wenu.sky.assembly.SkyAssembly` contains the existing construction bodies.
`CelestialSphere(observer, assembly=None)` continues to accept arbitrary
`SkyLayer` instances through `add`/`extend`; convenience `add_*` calls delegate
to the supplied assembly (or lazily selected stateless default). Construction
arguments/defaults, source loading, registration order and compatibility aliases
are retained. Failures propagate without substituting a default implementation.

`build_maximal_sphere`, `generate_celestial_sphere`,
`generate_native_icrs_sphere` and `NativeSkySnapshot.make_sky` also accept the
optional per-call `assembly=`. A build delegates to its corresponding assembly
method; the default binds itself to the resulting sky. Saved reconstruction
uses `restore_snapshot(snapshot)` and the existing validated records. Snapshot
codec/source checks remain in `native_snapshot.py`; no data/schema or original
source-loading behavior changes. Workers use this same restoration entry point.
No global plugin registration/discovery or new package protocol is introduced.

## 3. Canonical composition and export

```python
composition = compose_chart(
    chart,
    style="atlas",
    mode="print",
    detail=FixedDetailPolicy(
        ResolvedDetail(star_magnitude_limit=6.0)
    ),
    legends=LegendOptions(
        objects=True,
        stellar_magnitudes=True,
        context=True,
    ),
)

result = chart.export(
    sky,
    MatplotlibRenderer(ax),
    "chart.png",
    composition=composition,
)
```

`chart.export()` resolves render-local layer options, invokes the existing
chart renderer, draws requested legends, and saves exactly once. It returns a
`ChartExportResult`; established two-value unpacking remains supported:

```python
rendering, saved = result
```

Compatibility `style=` and `layer_options=` arguments remain available for
existing callers.

Canonical examples may add the complete shared command-line contract with:

```python
add_chart_arguments(parser, default_output="output/example")
```

The parsed request separates product selection, astronomical content,
appearance, and legends. Content and legend switches are opt-in. Explicit
visual overrides are immutable and apply after style/mode resolution:

```python
composition = compose_chart(
    chart,
    style="cartoon",
    mode="presentation",
    style_overrides=ChartStyleOverrides(
        constellation_linewidth=2.0,
        constellation_line_color="white",
    ),
)
```

Omitting `style_overrides` preserves the resolved style and mode defaults.
`chart_detail_overrides(arguments)` applies the caller magnitude limit and
the explicitly selected constellation and coordinate-grid layers relative to
the selected detail policy. Constellation lines, labels, and boundaries are
independent opt-in requests. It retains cartoon constellation-vertex
selection even when line figures are hidden.

Each canonical example exposes independent equatorial, ecliptic, and Galactic
grid and grid-label switches. A `*-grid-labels` switch enables only its own
grid. The grid systems use black, orange, and blue respectively for both
their default lines and numeric labels. The principal equator, ecliptic, and
Galactic plane remain separate furniture selected with
`--grid-references SELECTION`.

Cartoon presentation resolves a trichromatic palette: deep-blue background,
yellow stars/lines/boundaries/context, and white footer credits. Cartoon print
uses white paper with black structure, context, and credits. Circular chart
boundaries obtain their appearance from the resolved cartoon mode without
changing their chart-owned geometry. When Milky Way or Magellanic Cloud
isophotes are selected as cartoon content, they use unshaded dotted contours:
yellow in presentation and black in print.



## Existing product entry points

| Entry point | Purpose | Current owner |
|---|---|---|
| `compose_chart` | Resolve independent content/detail/style/mode/furniture | `charts/composition.py` |
| `CelestialSphere.draw_chart` | Canonical layer-to-projection-to-renderer execution | `sky/celestial_sphere.py` |
| `generate_chart_request` | Ordinary and atlas request dispatch/lifecycle | `charts/request_generation.py` |
| `wenu_chart` | Installed ordinary-chart CLI | `cli/chart.py` |
| `wenu_design_atlas` | Resolve/validate atlas geometry | `cli/atlas.py`, `atlas_design.py` |
| `wenu_plot_atlas` | Standalone atlas index | `cli/atlas.py`, `charts/atlas_index.py` |
| `wenu_create_atlas` | Sheet rendering and book assembly | `cli/atlas.py`, `charts/atlas_publication.py` |
| `wenu_retrieve_comets` | Explicit SBDB comet discovery | `cli/comets.py` |
| `wenu_satellite_crossings` | Exact local satellite-crossing file workflow | `cli/satellite_crossings.py` |

Ordinary families are `AllSkyChart`, `FullSkyChart`, `RegionalChart`,
`CircumpolarChart` and `BinocularChart`. Product commands delegate to the
existing request/composition owners, not to new copies of their algorithms.

## Explicit nonstellar catalogue-lookup admission

`NonStellar.require_catalogue_lookup_metadata()` validates the existing immutable
record for baseline chart lookup. `missing_fields_for("catalogue-lookup")` and
`require_complete(position_model="catalogue-lookup")` require catalogue identity,
edition, byte binding, provenance and declared source angular units. Missing
frame/origin or measurement epoch/scale remain in the record; they do not block
this explicitly selected lookup capability. Conflicting/unsupported declarations
still fail during ingestion. `require_complete_metadata()` retains the original
strict physical/source-model requirements and is not relaxed by a lookup call.

An explicit `metadata.coordinate_spec(provider, position_model="catalogue-lookup")`
uses model `catalogue-lookup` for a qualified reference, or
`catalogue-lookup-legacy-unverified-encoding` for incomplete reference evidence.
Missing origin is `legacy-unverified-origin`, never an invented barycentre.
The existing ICRS chart interpretation is not promoted into a verified source
frame. No evaluation instant or zero motion is asserted. Existing public position
and observed/native geometry policies stay unchanged; this admission API does not
perform another family's kernel routing or add angular propagation. Its source
record and known/unknown fields survive existing snapshot transport unchanged.

## Shared ICRS coordinate defaults

`ICRS_ASTROMETRIC_SPEC.epoch` and `icrs_catalogue_spec(provider, epoch=None)`
represent an unspecified measurement epoch. ICRS orientation does not establish
that epoch. Callers with validated catalogue epochs continue to pass them
explicitly; `epoch="J2000.0"` remains supported when it is an actual source fact.
The helper signature remains compatible with callers that omit the argument.
Constructed celestial references, raw observation-helper inputs and transformed
boundary outputs gain no fabricated J2000 epoch. FK4/FK5/ecliptic defining
equinoxes remain separate and unchanged. The coordinate service's numerical
frame transformations, snapshot schemas and original source records are unchanged.
This does not qualify missing nonstellar frame/origin or measurement metadata;
`require_complete_metadata` still refuses those gaps.

## Offline Gaia candidate audit

[`tools/gaia_crossmatch_audit.py`](../../tools/gaia_crossmatch_audit.py) is the
K4a.03 maintenance owner for the versioned external downloader cache. It validates
manifest identity, policy/source/membership digests, all product and completed
raw-query bytes, integer IDs, ECSV angular/motion/epoch units and actual candidate
sets/counts. It loads the full original Wenu source through `Stars.source_catalog`;
chart magnitude selection never defines the audit population.

Exact HIP identifiers link ESA-1997-I/239 entries to Gaia's published Hipparcos-2
crossmatch. Fernando explicitly accepts `gaiadr3.hipparcos2_best_neighbour` as the
association authority. For each HIP, retain exactly that published best-neighbour
source ID and original evidence in `published_association`; zero best rows means
no published association. Multiple contradictory best rows stop integrity admission;
never choose a neighbourhood alternative by proximity or score. Retain all
neighbourhood alternatives, source fields, masks, flags, errors/correlations and
foreign photometry. Original multiple-system/shared-source/consistency annotations
and poor/missing astrometric inputs do not revoke the published association.
This does not adopt an astrometric solution/model or component-specific RV.

No 2007 positions/proper-motion catalogue is downloaded or reprocessed. The
[source profile](data/gaia_dr3_audit_reference_v1.json) declares the Gaia reference
conventions used only by optional `--diagnostics`. That flag adds the old nominal
1997/Gaia tangent-linear comparisons; it is off by default. Diagnostic failures,
large separations, missing PM or unexpected numerical epochs are annotations,
never association acceptance gates. This independent source diagnostic is not
production propagation or AX.13. Its model omits distance, perspective, binaries
and covariance and uses no separation threshold. The coordinate guide remains
current; production geometry and scientific policies are unchanged.

Explicit `--cache` and `--output` arguments are required. Use a new output version;
existing output refuses overwrite. V2 products are `summary_v2.json`,
`hip_review_v2.jsonl` (all HIP rows), `candidate_evidence_v2.jsonl`,
`published_associations_v2.jsonl` (one retained published best link per associated
HIP), `candidate_separations_v2.csv` and `audit_manifest_v2.json`. The last is the
completion marker, published last. Exceptions remove partial output. Provenance
binds input bytes, source/membership/visual-photometry identities, tool/profile and
software versions; the summary declares the exact association-policy version.
The original cache and v1 report remain untouched. The v1 Mac receipt is accepted;
the association-preserving v2 Mac report remains pending. Association count is
reported separately from `adopted_astrometric_solutions`, which remains zero.
Source publication and production/model admission are separate later work.

## Kervella published association supplement

K4a.03S1 adds the source-bound published Kervella et al. 2022 CDS J/A+A/657/A7
Table A.1 supplement to the same offline audit owner. The
[source profile](data/kervella_association_source_v1.json) binds exact original
ReadMe/compressed/expanded bytes, record count/length and selected field slices.
The current CDS table has 116,017 rows, distinct from the paper's 116,343 PMa
catalogue count; no number from the paper is used as a promised EDR3-link total.
Missing/duplicate/float identifiers, changed bytes/layout or incomplete receipts
refuse source admission. IDs are parsed directly from ASCII decimal fields into
strings; no binary64 conversion. Original source rows remain recoverable through
the raw resource digest, row number and row digest.

[`tools/fetch_kervella_catalogue.py`](../../tools/fetch_kervella_catalogue.py) is
the explicit acquisition owner, separate from the offline audit. It reads only
the profile's two advertised CDS HTTPS static resources, sequentially, with
100 MiB transport/expanded caps, no redirect/retry/mirror/account fallback or
per-star query. It validates original/expanded hashes before publishing the last
completion receipt and reuses an existing verified capture without network.
Unknown/partial directories refuse overwrite. No network occurs on import or
inside tests/rendering. Raw source files are external, not vendored.

`gaia_crossmatch_audit.py --kervella-source DIRECTORY` validates that capture and
joins exact HIP keys. Existing published primary associations remain byte-for-byte
equal on agreement or disagreement. For previously unassociated HIP entries only,
a published non-null `GaiaEDR3` value supplies the supplemental identity; no cone
search, magnitude/quality threshold, component rematching or motion calculation is
performed. DR2-only values are preserved as evidence and never cast into DR3.
New associations retain their EDR3 edition and the explicit profile-bound ESA
statement that the EDR3/DR3 source list is identical. That bridge does not extend
to DR2, DR4 or arbitrary releases. Companion tables A.2/A.3 are excluded.

The v3 report preserves all original HIP rows/order/photometry and primary
candidate evidence, annotates Kervella agreements/conflicts/missing rows and IDs,
and writes the combined published-association ledger. Shared sources are annotated,
not used to erase a published association. It reports newly associated and still
unassociated counts plus original-V half-magnitude histograms before/added/after,
including missing magnitudes separately. Primary Gaia source-parameter/candidate
counts remain those of the original raw cache; the supplement adds identities,
not Gaia astrometric rows or Kervella corrected/derived astrometry. Adopted
astrometric solutions stay zero. The cache and older v1/v2 reports are read-only;
v3 filenames/manifest and a new output directory prevent overwrites.

The actual source assessment is in the
[dated receipt](data/kervella_assessment_v1.json). Its real source counts must not
be confused with the combined Mac result, which remains pending until executed
against Fernando's original full source/cache. No production provider, model,
photometry/name selection, renderer, SDK or saved-sky format changes. The
coordinate guide remains current; no numerical coordinate/model policy changes.

## Astrometric input acquisition and coverage

K4a.03S2 separates explicit source acquisition from the existing offline audit.
[`tools/fetch_stellar_astrometry.py`](../../tools/fetch_stellar_astrometry.py)
accepts `--cache`, `--association-report` (the verified v3 report), and a new
`--output` capture directory. It verifies the original raw cache, report products,
original membership/V identity and published ledger before deriving sorted unique
missing DR3 IDs. Already cached Gaia rows are reused. The original explicit source
column selection includes errors/correlations, auxiliary parameters and quality/RV
fields; raw returned VOTables retain all units, masks and field metadata.

The [source profile](data/stellar_astrometry_acquisition_v1.json) records the dated
provider review and exact corrected CDS I/311 ReadMe/compressed/expanded identities.
The explicit client makes sequential anonymous synchronous TAP requests with at
most 500 source IDs and MAXREC=batch+1, validates QUERY_STATUS including trailing
overflow, exact integer ID reconciliation, source units and reference epoch, and
captures TAP_SCHEMA datatype/unit/UCD/description metadata. VOTable parsing uses
FIELD names rather than XML IDs: ESA supplies uppercase SOURCE_ID/DESIGNATION
IDs with lowercase ADQL names. Exact requested names remain mandatory; no blanket
case folding or unknown-column admission is used. Raw response bytes stay intact.
Requests have bounded
bytes/timeouts, no redirects, automatic retries, mirrors or account fallback.
Failures stop the invocation. A manual rerun of the same command reuses only
completed digest-verified source/query batches with the identical input plan;
changed inputs or corrupted completed products refuse. The completion manifest
is published last. Partial batches are never admitted as empty results.

The Hipparcos-2 parser validates pinned bytes, 117,955 unique 276-byte records and
ReadMe field slices. It retains native radians, original PM/parallax, formal errors,
Sn/component flags, all 15 upper-triangular weights and the full original row.
The captured ReadMe does not state the epoch time scale or explicitly qualify the
RA differential convention: those remain unresolved before model admission. No
covariance is constructed and acceleration/VIM/stochastic/orbital models are not
adopted merely because their measurement fields exist.

`gaia_crossmatch_audit.py --cache CACHE --kervella-source KERVELLA
--astrometry-source CAPTURE --output NEW_REPORT` recomputes and preserves the
published ledger, verifies the capture against exactly those associations and the
original cache, and writes version-4 products. Per-HIP `astrometric_coverage`
distinguishes five-parameter (31), six-parameter (95), position-only (3), incomplete,
unknown and unassociated Gaia records. Five/six-parameter rows require available
position/epoch/parallax/both PM values; this does not require positive parallax or
RV and makes no physical distance/error claim. Otherwise complete Hip2 measurement
inputs are inventoried as fallback; missing/incomplete Hip2 keeps original 1997
lookup visible. Original associations, membership/order, names and V stay intact.
`preferred_available_input` records source availability, not runtime adoption;
`adopted_astrometric_solutions` stays zero. Quality flags never erase identities.

The summary counts original versus additional cached Gaia rows separately, and
reports source/fallback availability and missing Hip2 membership. Every raw cache,
v1/v2/v3 report and production module remains unchanged. Companion parallaxes,
component RV borrowing, source distribution and production propagation remain
separate. The coordinate guide remains current: no mathematical model is changed.

## Local stellar enrichment snapshot

[`stellar_enrichment.py`](../../src/wenu/stellar_enrichment.py) is the data-only
multi-edition snapshot codec. It is separate from `stellar_catalogue.py` because
that native-direction owner requires one qualified source epoch; the linked
snapshot must preserve different editions/epochs and explicitly unknown Hip2
conventions without asserting a model. It imports only the standard library and
has no acquisition, observer, kernel, catalogue-loader or renderer dependency.

`StellarEnrichmentSnapshot(products, manifest)` admits immutable byte tuples only.
The fixed product set is metadata, per-HIP enrichment rows, Gaia sources, Hip2
sources and candidate evidence. The version-1 completion manifest binds each
exact byte payload. Admission checks strict JSON (duplicate fields and non-finite
numbers refuse), edition-qualified decimal-string primary IDs, original source
identity, membership/order/V digests, complete original column preservation,
original-field and published-ledger digests, source references, parameter units,
epochs, raw Hip2 field/weight agreement, candidate/source reconciliation and
availability counts. Five-/six-parameter measurements do not imply valid distance
or full physical motion. Every `adopted_solution` remains null.

`load_stellar_enrichment(directory, expected_manifest_sha256=None)` reads the fixed
filenames only and validates before returning. Supply the published manifest hash
to bind a particular source identity. `snapshot.metadata` and
`snapshot.records(product='stars_v1.jsonl')` return detached decoded values;
underlying data remain immutable bytes. Source masks/unknowns are null, designation
dataclass fields are JSON objects and tuples become arrays; their source edition
and digest remain metadata. All loaded original columns, including unused fields,
are retained. Gaia original values/errors/correlations/quality/photometry live in
one source product with exact-ID references; Hip2 retains original 276-byte row
text and all 15 weights. Covariance and distance are not constructed.

The existing offline command accepts an optional `--source-output NEW_DIRECTORY`
alongside `--astrometry-source` and the required new audit `--output` directory.
It normalizes only already verified caches and the current full original source,
validates the snapshot, stages it, reloads/compares every byte and publishes its
completion manifest last with no-clobber semantics. Failure removes only the owned
staging/new incomplete directory. Existing caches/reports remain read-only.
Candidate Gaia parameters are referenced rather than duplicated inside evidence.
The output is a local external source, not data bundled in Git, a wheel or a
saved sky. Original defaults, propagation/model and redistribution admission are
unchanged. The coordinate guide remains current; no coordinate model changes.

## Explicit full-input stellar motion

`stellar_state.admit_stellar_motion(source, *, coverage, distance_policy,
radial_velocity_policy)` derives an immutable `StellarMotionCatalogue` from a
validated `StellarEnrichmentSnapshot`. The source remains verbatim and its
`model_admission=none` and null adopted-solution fields are not rewritten.
The distinct admission record binds its manifest, original membership/V identity,
association ledger, source reference facts, SI solution digest, finite TCB domain
and explicit model policies. `to_record()` returns a detached record; `rows`
contains all original HIP entries in source order, including unavailable rows.

The supported explicit policy strings are `positive-parallax-reciprocal` and
`spectroscopic-proxy`. Linked DR3 five-/six-parameter rows require finite position,
both proper motions, positive parallax and measured radial velocity. The sixth
Gaia astrometric parameter is not an RV. A reciprocal positive parallax supplies
a nominal distance; no distance posterior, parallax zero-point or binary/systemic
RV correction is inferred. Six-parameter solutions with RV may be admitted.
RUWE, duplicated-source and component flags do not veto published identities.
Negative/zero parallax, absent measurements and unknown solution codes remain
explicit unavailable reasons; no neighbourhood alternative or different source
is silently selected. Hip2/original fallback records remain in the source but
are not promoted through their unresolved conventions or invented RVs.

The adapter reads declared Gaia reference/units, converts its Julian-year TCB
epoch and spherical differentials once into immutable SI position/velocity, then
`StellarMotionProvider(catalogue, representation='direction')` or the explicit
`representation='cartesian'` delegates to `RectilinearAstrometricProvider`.
These are distinct SDK models/resources/references. `describe()`, `catalogue()`,
`supports()`, `evaluate()`, `certify()` and `close()` retain the existing provider
protocol/lifecycle. Objects use original catalogue/HIP keys; external IDs preserve
original catalogue/edition and published Gaia edition plus the explicitly bridged
DR3 identity. Query objects must be available model objects; unknown/unavailable
objects refuse rather than falling back. Register the provider and its exact
reference with the SDK, then query through an owned session.

Direction results retain source/evaluation/anchor times and the shared core's
`2**-40` rad numerical bound relative to the admitted binary64 SI trajectory.
The core owns its existing angular reuse certificates. This bound excludes
source-to-SI conversion, measurement, distance/RV-estimator and physical-model
errors, which remain unknown. Cartesian results retain SI PV with separate
unknown position/velocity error channels and no temporal certificate. Supplied
source errors/correlations remain available verbatim; covariance propagation is
not implemented. No extra light-time, observer parallax, apparent correction,
frame precession, binary orbit or historical-date accuracy is introduced.
The caller's finite TCB domain is a nominal computational admission, not a claim
of physical validity or absolute angular accuracy.

The source codec, original/native facade and ordinary `Stars`/figure/label/chart
consumers remain unchanged. No automatic source replacement, top-level export,
CLI option, dependency, SDK or saved-sky format change accompanies this API.
The closest gate is `stellar-motion-provider`, followed by documentation and
source-audit/tooling integrity. Actual real-source Mac acceptance is separate
from constructed offline tests.

## Native stellar kernel adapter

The [K4a.02 acquisition/matching policy review](scientific_contracts.md#gaia-dr3-acquisition-and-matching-policy-review)
and [dated audit](data/gaia_dr3_acquisition_policy_v1.json) are design documents.
No production Gaia TAP client or automatic consumer adoption is implemented;
the separate explicit full-input provider above uses only a validated local source.
Current terms/usage and service preflight remain unresolved; proposed local
workload caps are not provider quotas or execution authority.

K4a.01 now specifies the [stellar membership and enrichment contract](scientific_contracts.md#stellar-membership-and-enrichment-contract)
and [source-bound census/logical schema](data/stellar_enrichment_contract_v1.json).
It remains a logical enrichment design: the separate maintenance report now
retains the accepted published associations. The separate explicit full-input adapter consumes the local enrichment snapshot;
there is no default Gaia loader or saved-sky codec change. Existing
`source_catalog` owns the full retained population; `catalog` and `hip_df` are
selected/observed views. The contract keeps foreign astrometry and photometry
separate from those baseline rows and reserves explicit release-qualified
identities and component/match evidence in the admitted local source snapshot.

`stellar_catalogue.StellarCatalogueMetadata` is an immutable mirror of a
`wenu-stellar-catalogue/1` document. The document declares catalogue/edition,
frame/origin, epoch value/format/time scale, column units, source digest,
provenance and preserved original source metadata. Extra source fields survive
round trips. `ingest_stellar_catalogue(table, metadata)` validates coordinates,
units, identity uniqueness and row/reference-epoch agreement, copies all input
columns, and returns a `StellarCatalogue(table, metadata)` envelope. Legacy table
access remains available, with the same metadata preserved in table attributes.
`Stars.catalogue_metadata` exposes the immutable runtime record.

`Stars.load(..., metadata=None)` validates source identity before parsing and
publishes a table only after ingestion. The packaged Hipparcos document is
`wenu/data/catalogs/hipparcos/metadata.json`, derived from its retained ReadMe.
A custom source requires a matching supplied document or adjacent
`<filename>.metadata.json`; byte-identical packaged input can use its packaged
profile. There is no inferred epoch/edition fallback for unidentified bytes.
Constructed tables must also be explicitly ingested before native use.

`stellar_state.LegacyNativeStellarProvider(rows, *, namespace, source_epoch,
provenance, catalogue_edition=...)` copies identifier/longitude/latitude rows.
It advertises `native_direction` and `batch_evaluation` only. A digest binds
materialized binary inputs, source epoch, edition and provenance; it is not an
asserted digest of the original catalogue file. `native_stellar_states(...)`
registers an owned provider, queries at its source epoch and closes its local
session/kernel. Published immutable states survive close. Empty tables avoid
a query; failed registration retains caller cleanup. There is no global cache.

`Stars.realize(native_context, None)` uses this service after existing stellar
selection. Finite returned vectors are converted to geometry. Exact source coordinate
encoding is retained only when its canonical vector equals the returned kernel
vector; altered results determine the output. This preserves existing exact
native-value assertions without bypassing the query. Source tables,
IDs, photometry, designation metadata and missing-row behavior remain owned
by `Stars`. `_SnapshotStars` inherits this path. No public facade export is
added. Snapshot schema v3 preserves the complete metadata envelope. Readers
admit v1/v2 through an explicit source-digest-bound legacy profile; they refuse
legacy sources that cannot be identified. New snapshots restore metadata
without consulting the original catalogue or its packaged profile.

`Stars.position(instant=None)` uses the same kernel-backed helper for the stable
marker selection. `instant` is retained for compatibility and ignored: the result
is explicitly source-native at the admitted catalogue epoch, not a propagated
position at that instant. No catalogue-specific epoch, edition or provenance
literal is supplied by the stellar geometry or kernel bridge.
`Stars.native_positions(identifiers=None)` queries explicit HIP IDs from the full
source table (or the stable table for constructed legacy objects without one).
Available rows retain source order, IDs, photometry, designations and NaNs;
absent IDs are omitted for the consumer's missing-ID policy. `None` requests the
complete source, independently of marker selection; an explicit empty iterable
still requests no rows. Empty selections
avoid a query. Both APIs prefer authoritative `ra_degrees`, with hours × 15
only for hours-only constructed inputs, avoiding a redundant floating-point
round trip. Neither mutates active marker selection.

Native `ConstellationLines.realize` requests the loaded graph's vertex IDs
through `native_positions`, then joins returned IDs to the original edge order.
This preserves faint endpoints, warning/gap policy and global resolvability
metadata without evaluating unrelated catalogue stars. Returned kernel vectors
control endpoints; refusal is not replaced by raw catalogue coordinates.
Native `ConstellationLabels.realize` requests all source positions through
`native_positions()` once and uses those returned angles for constellation
membership, Serpens splitting and the existing spherical mean. Faint source
stars remain included independently of marker selection. Empty/all-invalid
inputs preserve the returned coordinate specification without a second query.
Kernel refusal propagates; there is no raw-table fallback. Snapshot label
instances inherit this path. Observed labels now use the same public source
positions, then retain their existing Astropy transformation and spherical mean.
The returned source specification travels into CoordinateService; the shared
helper’s compatibility default remains unchanged for other callers.
No claim of all-consumer kernel closure follows.

`Stars.observed_altaz(observer)` now queries the admitted kernel-backed source
angles before every observed-cache lookup. Its cache identity includes source
IDs, the effective RA-hour encoding and returned declinations alongside existing
observer/resource/revision keys. A changed state misses the cache; a failed query
propagates even after cache fill. For unchanged directions, existing source
RA-hour encoding and prebuilt stable-table representation are retained to avoid
an unnecessary numerical round trip. Changed returned longitudes determine new
RA hours. `observed_cache.skyfield_stellar_altaz` owns the existing
`at(...).observe(...).apparent(deflectors=[]).altaz()` boundary. It adds no
motion, distance, light-time iteration or corrections of its own.

`compute_altaz` uses this same maximal observation boundary, then selects from
the stable catalogue and updates only its historical `hip_df` result. Render-local
stars and constellation figures reuse the boundary without mutating selection.
Figure availability/topology remains tied to the active catalogue as before;
label means still include the complete source. The retained Skyfield and Astropy
methods are distinct compatibility paths, not a new unified apparent-place
science model. Shared resource/cache checks are described below; solar-system
model/source qualification remains K3.25.

The `native-catalogue` reference explicitly means an unpropagated lookup.
Unbounded lookup availability is not astrometric validity at arbitrary epochs;
all uncertainty channels are `not_evaluated`. Epoch propagation, accuracy bounds,
velocity and reuse certification are refused. The helper queries J1991.25(TT)
for current Hipparcos rows; it never relabels them as propagated J2025.0 states.

Until SDK publication, root metadata uses an immutable VCS dependency pinned
to SDK source commit `4add1447d0db5598c1b2ff7f3c231d465b2c63f0`, subdirectory
`packages/wenu_kernel`. This is a separate distribution, not vendored code.
A normal install resolves that dependency at installation time; rendering does
not acquire software or catalogue data. For a synchronized development checkout:

```bash
python -m pip install --no-deps --no-build-isolation ./packages/wenu_kernel
python -m pip install --no-deps --no-build-isolation -e .
```

The SDK is not yet frozen or published on PyPI. Replacing this provisional pin
requires a reviewed compatible release and installation gate. The new
`kernel-native-stars` gate checks separate wheel/sdist/editable consumption,
native selection/saved-worker behavior and a legacy-versus-kernel page image.
PR #247 passed its final Mac followup at `8e4be740` (identical merge `bf804cbb`):
eight tooling, 36 documentation and seven native-output cases, including actual
wheel/sdist/editable consumption. The new public-position/endpoint slice uses
the narrower `native-stellar-routing` gate; it does not change installation.

## Coordinate and state entry points

`NonStellar.load` stages reading, normalization and magnitude selection before
publishing the new catalogue name/source/table/revision or clearing caches.
Rejected angular units leave the prior loaded catalogue usable. The common
normalizer copies the source table, preserving unconsumed fields, masks,
descriptors and an independent `Table.meta`; canonical fields retain their
established names. Declared RA/Dec/position-angle units convert to degrees;
declared diameter/dimension units convert to arcminutes. Incompatible units
raise before publication. Unitless inputs retain the legacy column encoding,
explicitly a compatibility policy rather than recovered source metadata.
Globular core/half-light radii likewise convert to arcminutes before computing
the half-light diameter. Numerical extra columns retain their declared units
and descriptions. Native positions and native/observed shape/symbol metadata
include an independent `catalogue_metadata` mirror. The snapshot table transport
preserves retained fields/units/descriptions and table metadata;
the record described below adds the source admission boundary; no new kernel routing follows.

`NonStellarCatalogueMetadata` (in `objects/nonstellar.py`) is a frozen mirror
of `wenu-nonstellar-catalogue/1`. It retains original table metadata, original
angular units, normalized units, input-byte SHA256, catalogue/edition and source
URLs, plus explicitly nullable frame/origin/epoch/time scale. Source declarations
are validated before publication, including supported frame/origin, ICRS equinox
refusal and epoch syntax/scale. No source edition or epoch is inferred from a
name, file path, release date or `ICRS/J2000` frame description. The source digest
is checked before/after reading. `catalogue_metadata.to_record()` returns a copy;
`missing_fields` reports gaps for the default source-epoch model and
`require_complete()` refuses them. `missing_fields_for(position_model)` and
`require_complete(position_model=...)` apply an explicit model-specific policy.
The supported `static-direction` model does not require a measurement epoch or
its scale. It still requires frame, origin, source identity, units, edition and
provenance. Supplied epoch declarations remain validated and preserved.

`load(..., require_complete_metadata=True)` requires the facts needed by the
provider's `position_model` before replacing a catalogue. The provider also
exposes `admission_missing_fields` and `require_complete_metadata()` using that
same policy. `Galaxies.position_model` is `static-direction`: source epoch is
provenance, and changing a requested epoch does not update its native centres.
Other nonstellar providers retain the default `source-epoch` policy.
Geometry carries `catalogue_position_model` separately from the source record;
a fully admitted static direction has `CoordinateSpec.model='static-direction'`.
The default load preserves legacy chart compatibility:
missing source facts remain null, and geometry explicitly carries the model
`legacy-unverified-catalogue-encoding`. Its ICRS/barycentre chart interpretation
is software compatibility policy, not evidence for missing source facts.
The inspected packaged tables all lack a measurement epoch; several also lack
a declared frame/origin. Missing epoch is not a galaxy admission failure, but
the packaged galaxy frame/origin gaps still prevent strict admission. Existing
chart output is retained without claiming that adopting a record closes a provider.

`native_coordinate_spec(table=None)` supplies native positions/outlines/symbols;
`observed_coordinate_spec(observer)` supplies observer metadata from the same
record while retaining the existing transform and observer instant. Provider
identity/provenance is read from that record, including PN source identity.
Geometry includes its `catalogue_admission` document separately from the unchanged
raw `catalogue_metadata`. Unknown epochs produce `epoch=None`; declared source
epochs are retained. No coordinate, motion, frame-transform or render algorithm
is changed by this metadata boundary.

Snapshot v5 stores the admission record with each nonstellar fixed table,
binds it to the manifest's source digest, checks table metadata/units and derives
the header from its native specification. The existing open-cluster row contract
remains separate. Readers admit v1-v4 using their historical formats; old J2000
headers are not promoted to source facts, original source units/digests are not
fabricated, and restored geometry derives its meaning from preserved metadata.

`OpenClusters.native_coordinate_spec(table=None)` mirrors coordinate epochs from
the selected table's `position_epoch` column, or an explicitly declared global
`coordinate_epoch` when that column is absent. Only a uniformly known selection
has a scalar epoch. Mixed, masked, unknown and empty selections use `epoch=None`;
row epoch/source declarations and masks remain aligned in geometry metadata.
An ICRS/J2000 frame description is never parsed as a measurement epoch.
Native and observed geometry also retain an independent copy of `Table.meta`.
Invalid epoch declarations are refused before replacing the loaded table/source.

Snapshot v4 introduced the open-cluster coordinate header from this interface;
v5 retains it and validates it against the preserved rows. Legacy v2/v3 J2000 headers are admitted
as historical format claims only; restored cluster geometry uses the preserved
row facts. The v1 compatibility path has no fixed catalogue layer. Nonstellar
resource metadata gaps remain explicit audit findings. K3.09 removes shared
implicit J2000 measurement epochs without relaxing nonstellar admission.

The separate candidate `wenu_kernel` package provides `Kernel`, `KernelSession`
and `StateProvider` plus typed direction/Cartesian records in `wenu_kernel.records`. See its
[implemented subset and independent gate](../../packages/wenu_kernel/README.md).
Native stellar realization/public positions/constellation endpoints, static
galaxy centres and open-cluster source lookups have production adapters. Preserve
other existing imports until their own K3 public-path gate is implemented. No common observer adapter is supplied by the foundation.

`wenu_kernel.time.TimeService(adapters=(), admissions=())` admits one explicit
`TimeAdapter` per directed scale pair. `convert(time, target_scale,
maximum_error_s=None)` returns an immutable `TimeConversion` containing source,
target, model/resource identity, provenance and introduced numerical error in
seconds. `admissions` and `maximum_error_s` are keyword-only. Same-scale identity
is exact; absent conversions fail `TimeConversionUnavailable`. There is no
implicit session conversion, chaining or resource download.
`wenu_kernel.time_adapters.TaiTtAdapter(validity)` supplies TT(TAI)/TAI with a
finite source-scale `TimeSpan`; it is not a TDB/TCB or civil/calendar adapter.
Callers retain conversion receipts and separately account for input/physical
time uncertainty. The coordinate guide's existing observer parser remains current.

`CartesianState` uses `position_m`, optional `velocity_m_s`, explicit
`velocity_available` and separate position/velocity evidence. Native Cartesian
references use representation `cartesian`, units `m,m/s` and an explicitly
admitted frame/origin. Query with `AccuracyRequest(metric="euclidean_norm",
position_m=..., velocity_m_s=...)`; `require_velocity=True` requests velocity
without imposing a numerical bound. Unknown velocity remains `None`. An absent
declared source epoch is also explicit `None`, not a fabricated resource epoch.
Only full-model Cartesian evaluation and identical-query reuse are available;
temporal certificates remain direction-only. No frame or unit conversion is
performed by the kernel.

`wenu_kernel.reuse.ReuseCertificate` and the typed provider `certify` operation
cover scalar original direction anchors. `StateBatch.reuse_certificates` lists
their immutable envelopes; reused rows carry `certificate_id`, original
`anchor_time`, requested `time` and retained `source_epoch`. The default
`SessionPolicy.reproducibility="reproducible"` uses provider-planned canonical
anchors when supported, otherwise full-model evaluation.
Explicit `interactive_bounded` sessions may reuse admitted certificates for
`bounded_reuse` queries with a positive angular tolerance. `query.coverage`
requires a certificate covering the whole interval. No arbitrary cached anchor
is admitted as a reproducible atlas result. Optional
`wenu_kernel.providers.CanonicalDirectionProvider.plan_reuse` returns an immutable
`DirectionReusePlan` of `AnchorSelection` records, constructed with
`wenu_kernel.reuse.make_reuse_plan`. The returned `StateBatch.reuse_plan` records
that schedule. Only providers advertising `canonical_direction_reuse` need
this method; existing non-planning providers retain their original protocol.

- `coordinates.py`: `CoordinateSpec`, `ObservationContext` and scientific
  enum/value vocabulary. Frame, origin, status, epoch, equinox and instant
  are distinct.
- `positions.py`: current small `PositionProvider` protocol. Its existence
  does not imply that every production path consumes it uniformly.
- `coordinate_service.py`: `CoordinateService.transform()` changes reference
  representation while preserving geometry kind, topology, IDs and metadata.
  It is not a universal orbit or stellar-space-motion propagator.
- `ephemeris.py`, `skyfield_ephemeris.py`, `solar_system_directions.py`:
  resource-bound Cartesian state, observer state, astrometric light-time and
  apparent-place boundaries.
- `sky/realization.py`: layer realization context; `sky/solar_system_points.py`
  supplies the shared descriptor-driven moving-body point route.
- `sky/native_snapshot.py`: current native catalogue snapshot and reuse facade.
  Preserve coverage, resource and design binding; do not relabel it as the new kernel.

## Request resource lifetime

`build_chart_request()` returns `ChartRequestBuild`; use its context manager or
call `close()`. Request-added minor-body layers, registry entries and entity
aliases are scoped to that build. Existing registry entries/aliases and a
supplied observer retain their original ownership. Resolver rebinding is atomic
and visits each distinct layer once, including a separately registered Moon.
`prior_minor_body_attributes` retains request-owned alias restoration metadata;
it is not a catalogue/snapshot persistence format.

Minor-body lifetime rollback is accepted in PR #243. PR #244
also journals ordinary request configuration inside `_prepare_with_sphere()`.
Use `with build_chart_request(...) as build:` or explicitly close the build:
its sky is the supplied object, its requested configuration remains active while
open, and close restores the original layer objects/order and remembered
horizon/disk aliases and point-label flags. Preparing another build on that
same sky before close raises `RuntimeError`; separate skies remain independent.

Horizon/disk/track configuration helpers accept an optional keyword-only `state`
used by this owner to remember an attribute before its first write. Omitting
`state` preserves standalone persistent configuration. The journal uses the
sky's existing public clear/extend (or add/remove) registry operations and does
not copy catalogues/resources or rewind scientific caches. It covers canonical
configuration writes, not arbitrary caller edits while a build is active.
Restoration attempts continue after an error; failed cleanup keeps the sky
leased. A returned build can retry `close()` after the cause is resolved. Failed
preparation with failed cleanup leaves the supplied sky unavailable for another
request; it is not silently treated as restored. This synchronous lease is not a
thread/process concurrency contract. Observer/resource ownership remains
separate, including its explicit cleanup failure semantics.

`open_chart_request_scope(sky, *, request=None, observer=None)` is the common
entry used by ordinary generation, view/drawing and native atlas sheets. It
returns a `ChartRequestBuild` with `prepared=None` until ordinary preparation
attaches a chart. Accessing `chart` before that raises `RuntimeError`. Use its
context manager for drawing/native execution; ordinary generation transfers the
scope to the returned prepared build. Configuration helpers receive the scope
as `state` and call `remember_attribute(owner, name)` before writing.

The opener never creates or owns an observer. A completed ordinary build adopts
its newly created observer only after preparation succeeds; failure stays under
the original observer creator. Supplied drawing/native resources remain borrowed.
Setup, export and close use the same restoration and lease-retention logic;
cleanup failures preserve the original failure as context. The native route
omits `request` and does not configure observer-dependent layers. Every atlas
producer route uses its injected command or defaults to `wenu_chart atlas-sheet`.

Native sheet export creates an owned `Figure`/`FigureCanvasAgg` with explicit
100-dpi layout resolution, retaining the existing standard layout metrics.
Interactive figure/display scaling cannot enter grid-label measurement. The
requested `presentation.dpi` still controls raster export; no global Matplotlib
backend is forced. The existing canonical composition/renderer/export chain
and frame/grid geometry remain the owners of page content. Regression checks
compare actual SVG label coordinates and PNG pixels at ambient 100/200 dpi
for polar, regional and hemispheric pages.

No state query is routed through the kernel by this lifecycle work. The
coordinate guide remains current; no astronomical algorithm, catalogue, frame,
time or rendering style changes.

## Static kernel directions

The candidate SDK adds `static_direction` as an explicit direction capability.
Its admissions cannot also claim `native_direction` or `epoch_direction`.
`DirectionState.source_epoch` accepts `None`; the session permits this only for
static admissions whose catalogue has no declared source epoch. Declared epochs
remain mandatory provenance. `ObjectRecord` retains the existing native/epoch
source-epoch requirement. Evaluation/anchor times remain required; other record
fields and query/result variants are unchanged.

Static providers retain explicit model/resource coverage, references, accuracy
and existing certificate admission. Static does not imply zero physical error,
new observer transformations, infinite coverage or implicit caching. The root
production dependency now pins accepted dev7 at the immutable commit above.
Galaxy directions consume the new capability; native stellar semantics remain
unchanged and share only the table/provider mechanics.

## Galaxy kernel adapter and shape ownership

`objects/galaxies.py::_native_centres` validates preserved catalogue metadata,
constructs a `static_direction` provider and consumes kernel-returned vectors.
It backs inherited public `position`, native chart outline/label construction,
observed outline centres and observed centre-table inputs. Refused/failed queries
propagate; there is no direct-source recovery route. Empty/missing coordinates
remain empty/missing rather than fabricated states. Exact source angle encoding
is retained only when the returned vector is identical; changed vectors control
all downstream geometry.

`catalogue_state.py` owns copied immutable rows, content-bound identities,
standard provider protocol, vector decoding and owned kernel/session lifetime.
The native facade in `stellar_state.py` retains its descriptor/resource
identities, required source epochs and returned states; its separate explicit
stellar motion adapter uses the shared astrometric engine. Galaxies
do not import a concrete stellar provider.

The galaxy model keeps fixed native directions. Full source metadata and digest
are bound into the derived resource identity. A source epoch with an admitted
explicit scale is retained as a TimePoint; an unqualified date is preserved in
metadata but not published as a numerical SDK source epoch, never assigned a
scale. It does not prevent the explicitly static lookup from running.
An undated `position()` uses JD 0 TT as a deterministic internal evaluation
anchor, not a source measurement date. Explicit requested instants retain their
actual evaluation meaning; supported Astropy/date inputs are decoded to TT.
Unbounded availability is the declared static chart model policy, not a bound
on physical accuracy. No numerical or physical precision is claimed.

Legacy source gaps remain in the admission record and reference policy. A missing
origin becomes `legacy-unverified-origin` in the SDK reference; no barycentric
source origin is inferred. Strict catalogue admission still rejects missing
frame/origin/units/provenance. Existing public coordinate metadata retains its
marked compatibility interpretation.

K3.10 applies `require_catalogue_lookup_metadata()` before each galaxy provider
query when the source record has the required identity/edition/provenance/units
and byte binding. Packaged sources meet this lookup policy without qualifying
their missing physical frame/origin. Existing constructed/unitless legacy sources
retain explicit compatibility status with their missing lookup facts included
in the kernel reference/provenance; errors are never caught and replaced with
source coordinates. Strict physical admission remains unchanged.

For galaxy outlines the shared owner calls `_outline_state` before cache access;
its returned centre arrays, ordered IDs and immutable metadata enter cache identity.
`_transform_outline_table(..., centres=...)` uses that batch without a second query.
Galaxy `_observed_point_source_key` similarly binds the already-queried centre
values. Changed kernel states invalidate a warm observation cache, and failed
admission/query propagates even after cache fill. The generic NonStellar owner now opts into these hooks under K3.12;
K3.13–K3.15 add globular, PN and SNR facades to the same mechanics with their
own source/provider identities. No transformation or ellipse mathematics
changes. Cold and restored galaxies use these same methods without a schema change.

Centre, angular semiaxes and PA form the domain shape description. Catalogue
major/minor diameters are converted to semiaxes by existing outline geometry;
PA retains its defining celestial frame. Shape parameters and outline sampling
stay above the kernel. Curves are constructed only for requested chart geometry;
LMC/SMC keep their separate isophote treatment. The existing observed path still
transforms sampled vertices as a frame transformation. Replacing that with a
centre/local-orientation construction is a separately validated geometry change;
no physical propagation of a galaxy curve is introduced here. The one-outline
case now uses its existing coordinate array directly, avoiding an unnecessary
concatenation that failed for a single synthetic galaxy.

## Open-cluster kernel lookup

`OpenClusters.position(instant=None)` and native `realize` consume
`_native_centres(table, instant)`. Observer `spherical_geometry` queries the
maximal catalogue through the same boundary before calling the unchanged
`catalogue_point_altaz` transform/cache. Selected rows retain their IDs/order,
including repeated requests. Missing coordinates remain missing. Returned kernel
vectors control the coordinates; failures propagate without raw-source recovery,
even when an observer cache already exists. The cache key binds the returned
centre arrays as well as the source revision.

`OpenClusterCatalogueMetadata.from_table` mirrors preserved row position sources,
epoch labels, explicit epoch scales, frame/origin declarations and all column
units into an immutable record. `to_record()` returns an independent JSON copy.
`catalogue_metadata_for(table)` binds this to the source byte digest (when known)
and a canonical derived-table ECSV digest. Canonical metadata key ordering makes
cold/restored identities equal. The derived digest is not called an original
catalogue digest. All retained columns, masks, descriptions and metadata enter
that binding; motion fields remain uninterpreted source data. Geometry adds the
record as `catalogue_admission` and `catalogue_position_model='catalogue_lookup'`;
source arrays and raw `catalogue_metadata` remain independently copied.

Per-row `position_epoch_scale` or an explicitly declared source-profile/global
`coordinate_epoch_scale` permits numerical epoch admission. A valid epoch label
without a scale remains preserved text and yields no invented SDK source epoch.
The curated `RA_source` field selects its declared source profile under
`input_catalogue_metadata`; it never supplies an epoch from a catalogue name.
Known unsupported frames/origins/coordinate units or invalid epoch declarations
are refused before replacing a loaded source. Missing declarations retain the
explicit legacy ICRS encoding; the SDK origin is `legacy-unverified-origin` unless
every admitted row declares a barycentric origin. This is not strict physical
source-metadata closure.

The shared `CatalogueDirectionProvider` accepts optional aligned `source_epochs`
without changing existing scalar-epoch stellar/galaxy resource identities. Source
lookup uses `catalogue_lookup`, unknown physical/numerical errors, ordered batch
queries and the existing owned kernel/session scope. Undated lookup uses an
internal JD 0 TT request anchor, never a measurement date; explicit `TimePoint`
queries retain their scale, while supported Astropy/date inputs are decoded to
TT. Unbounded lookup availability is software policy, not ancient-date accuracy.

Snapshot v5 already preserves cluster tables, masks, units, source metadata and
source digests. Restoration now forwards that existing source digest into the
same record; no schema field or source file access is added. Older supported
snapshots retain their previous coverage/admission. Production pins accepted SDK
dev8 at `9dd1909f`. The provider performs no acquisition, motion propagation,
source combination or morphology calculation. The ingestion companion below recovers omitted
Hunt fields without changing default routing. Resolve remaining epoch/origin
facts and admit a physical model before any propagation claim.


## Open-cluster astrometry ingestion

`tools/hunt_reffert_catalogue.py` owns offline `read_cluster_astrometry`,
`build_astrometry_companion`, `publish_astrometry_companion` and
`attach_cluster_astrometry`. The reader verifies local source/ReadMe byte counts
and digests against a versioned data specification, then uses Astropy's CDS reader
for ranges, units, descriptions and missing values. No new byte offsets, source
epochs or units are embedded in software. Changed meanings/units, duplicate IDs,
non-finite unmasked measurements, negative uncertainties and unordered distance
percentiles fail before publication. Publication uses a fresh directory and
refuses existing versions. Acquisition is separate and never implicit.

`data/catalogs/open_clusters/open_clusters_hunt_astrometry_v1.ecsv` is a companion
bound to the exact accepted `wenu_open_clusters_v0.2.ecsv` SHA-256. Its 513 rows
retain selected IDs/order: 509 matching Hunt solutions, including 502 available
radial velocities, and four fully masked Hunt rows for Dias-only centres. Source
IDs, names and coordinates must match exactly; no positional crossmatch or Dias
motion substitution is performed. The original 132 columns and metadata remain
untouched. The complete source schema/evidence is preserved in the ECSV metadata
and `open_clusters_hunt_astrometry_source_v1.json`; a separate receipt binds the
product bytes. Old full/photometric v1 derivatives and the active selector retain
their exact bytes and selection-criteria bindings.

`attach_cluster_astrometry(selected_path, companion_path, receipt_path)` verifies
both products and returns an independent table with `hunt_astrometry_*` original
CDS fields. It does not install this table as the default. The existing
`OpenClusterCatalogueMetadata.from_table` mirrors its source envelope, fields,
units and masks without a new runtime adapter. Source `e_*` standard errors and
`s_*` dispersions, distance percentiles, flags, heliocentric Galactic XYZ and
radial-velocity availability remain separate. ICRS densest-point centres and mean
cluster motions retain their different roles. The RA motion is explicitly
`mu_alpha_star` from the ReadMe's cos(dec) statement. The literal source epoch
label `2016.0` is retained without inventing its scale or origin. Cluster-mean
covariances are unavailable; individual-star covariances are not substituted.
This is ingestion, not a propagated or zero-motion model. Rendering, kernel,
snapshot schema and normal catalogue loading are unchanged.

Regenerate from verified local `clusters.dat.gz` and `ReadMe` using
`python tools/hunt_reffert_catalogue.py --help`. Only the small aggregate file is
needed; there is no need to fetch the large member table again. The adjacent
catalogue README provides a complete offline command. Cite Hunt & Reffert (2024),
A&A 686 A42, DOI 10.1051/0004-6361/202348662, CDS/VizieR and Gaia/DPAC. The source
specification records the acquisition and policy checks on 2026-10-19. Frozen
tests preserve four complete original records and the exact original ReadMe,
with hashes and original row indices; constructed mutations are labelled faults.


## Shared astrometric engine

`astrometric_state.SpaceMotionRow` copies an identifier, source `TimePoint`, SI
position/velocity triples or an explicit unavailable reason. It does not encode
an object family. `RectilinearAstrometricProvider(rows, *, descriptor, catalogue,
admission, evidence, reuse_method=None, velocity_evidence=None)` consumes copied typed key/row pairs and
immutable SDK bindings supplied by a source adapter. It validates full identity
sets, supported direction capabilities, numerical evidence, source scale/epoch
and finite model domains. The engine owns full nominal rectilinear evaluation,
normalization, exact-rational numerical verification and conservative angular
reuse certification. Semantic object types remain in ObjectRecords and never
select numerical branches. It imports only the standard library and accepted SDK.
No observer, projection, source loading or implicit time conversion occurs.

`cluster_state.ClusterMotionProvider` is the cluster-specific facade over this
single engine. Cluster admission retains qualification, source bytes/units,
distance estimator, systemic-RV proxy, density-mode/core-mean policy and all
existing catalogue/model/reference/resource identities and uncertainty meanings.
Its existing public constructors, row name and source-table API remain available.
`ClusterMotionRow` aliases the shared SI row type. Cluster spherical differential
conversion remains source ingestion through Astropy; numerical time propagation
and domain/reuse algorithms have one object-independent owner.

One constructed provider containing star, cluster, PN and SNR semantic records
is exercised through the real SDK and portable conformance kit. An isolated
stdlib/SDK subprocess also evaluates that module with Wenu/Astropy/NumPy absent.
This proves engine reuse, not independent installation of all of Wenu or
production stellar/PN/SNR catalogue admission. The installed-wheel cluster test
checks that both facade and engine ship and execute together.

The engine still requires complete admitted SI space-motion solutions. Explicit
Cartesian output and the separate nominal finite observer service are now implemented as described below; explicit observed Python chart/saved adoption is implemented. The requested configurable
200-year no-PM and 1,000-year PM-only lookback policies, measured from source
reference epochs, remain planned reduced-model admission policies, not enabled
models or absolute accuracy guarantees. Expansion and morphology evolution are
excluded. Future object adapters qualify centres/systemic motions and call this
engine; they must not copy its propagation or certificate implementation.

## Nominal cluster motion provider

`cluster_state.load_cluster_motion(companion_path, metadata_path, *, coverage)`
verifies the explicit companion bytes before parsing, admits qualified source
facts/units/policies and returns a frozen `ClusterMotionCatalogue`. Its rows copy
source-epoch `TimePoint`, SI position/velocity triples and explicit unavailable
reasons. The original ECSV and copied JSON evidence remain immutable strings;
`source_table()` and `to_record()` return independent copies. Original input-byte
hashes and derived-table hashes are separate. `admit_cluster_motion(table,
metadata, *, coverage)` is the corresponding explicit in-memory boundary,
including constructed fixtures whose provenance must be labelled as such.

`open_clusters_hunt_motion_admission_v1.json` is the versioned runtime adoption
metadata. It binds the existing Hunt companion/selected catalogue, canonical
source specification and accepted qualification record; the primary-source chain
is retained. Epoch J2016.0(TCB), barycentric ICRS, mu_alpha_star, source identity
and column mappings come from this document. No catalogue epoch or field-value
default is embedded in the provider. `distance` is mapped explicitly to published
`dist50`; using that estimator rather than inverse parallax is recorded policy.
The spectroscopic RV proxy, density-mode/core-mean approximation and omission of
an additional light-time correction are explicit model choices.

`ClusterMotionProvider(catalogue)` implements the existing SDK protocol and
advertises `epoch_direction`, batch evaluation and `direction_reuse_bound`, with a separate model/reference
identity. Object keys retain the existing `wenu_open_clusters` namespace and
selected IDs across source lookup and motion models. Astropy owns the spherical
position/differential conversion, including
mu_alpha_star at the poles. SI rectilinear propagation applies to an elapsed TCB
coordinate-time interval, then normalizes the resulting direction. This is the
accepted nominal centre model, not an ERFA/SOFA relativistic star-catalogue
propagation or a historical membership/density reconstruction. No observer,
precession, projection, rendering, download or implicit time conversion occurs.
Backend versions, source/qualification/policies and the explicit model domain enter
identity. Fractional-day epochs use the SDK's canonical split without losing
subday time differences.

Admission requires an explicit finite `TimeSpan` in TCB containing the source
epoch. This is a caller-declared nominal model domain, not certified physical
validity. A domain numerically intersecting a zero-distance trajectory is refused.
There is no default interval promising ancient-date accuracy. All 513 selected
IDs remain in the catalogue; 502 have full nominal inputs. Seven missing-RV rows
and four unqualified Dias-only rows remain explicit unavailable records; they
cannot enter the advertised full-model subset. Mixed unsupported requests refuse
without omission, invented zero RV or source-coordinate fallback.

Query the provider through `Kernel`/`KernelSession` using its advertised catalogue,
model and reference, selected admitted keys and explicit TCB `TimePoint` values.
`DirectionState.time` is the requested instant; `anchor_time` identifies the
original full-model computation and `source_epoch` retains the admitted source
epoch. Measurement and centre/model bounds remain `not_evaluated`. Numerical
evidence now bounds evaluation of the admitted binary64 SI solution; it excludes
source measurement, spherical-input conversion and physical-model uncertainty.
Velocity-output and subfloor accuracy requests are refused. Unknown errors are
never zero. The provider owns no catalogue acquisition or implicit
registration and respects the existing owned/borrowed close contract.

Source lookup remains the default for `OpenClusters.position`, charts and saved
skies. Explicit native motion consumption is described below; the active v0.2
selector and saved source records are unchanged. The independent numerical oracle uses scalar-trig
initial conditions and ERFA PV updates, plus an analytic perspective case, rather
than calling the production differential conversion to construct expected data.
The installed-wheel test exercises the actual provider/kernel while checking that
importing it does not change the fixture's default cluster lookup.

### Explicit native cluster motion consumers

`OpenClusters.position(instant, *, motion=catalogue)` selects the admitted nominal
model for that call. `instant` must be a matching-scale SDK `TimePoint` inside
the finite domain. The companion's selected-source digest must equal the loaded
or restored layer's source digest, and complete identity sets must match. The
kernel receives each distinct selected key once; returned vectors are joined
back to the original order, including duplicates. An unavailable selected row
refuses the whole query. There is no implicit omission, zero RV or lookup fallback.
Empty selections return empty geometry after source/time admission.

Native chart layers consume the same boundary via geometry option `motion` and
an explicit `LayerRealizationContext` evaluation instant/scale. The context's
native ICRS axes may now carry an epoch; this does not propagate static neighbours.
The chart guard permits an epoch-bearing layer only when its returned instant
and scale match that context. Frame, origin and astrometric status checks remain.
The nominal reference, immutable original states, source epochs, evaluation and
anchor times, model/resource identity and separate error channels accompany the
geometry. The source table/selection is not changed. The coordinate specification
has no common source `epoch`; its `instant` is the model evaluation time.

For an already admitted `motion`, a cold or restored `sky` uses the same public
pipeline (the date is illustrative and must lie inside the supplied domain):

```python
from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC

context = LayerRealizationContext(
    NATIVE_ICRS_SPEC,
    evaluation_instant="J2050.0",
    evaluation_time_scale="tcb",
)
options = {layer: {"enabled": False} for layer in sky.layers}
options[sky.open_clusters] = {
    "geometry": {"selected": selected_cluster_ids, "motion": motion},
}
result = sky.draw_chart(
    projection=projection,
    renderer=renderer,
    realization_context=context,
    layer_options=options,
)
```

`read_native_sky_snapshot(...).make_sky()` restores the same source-backed
`OpenClusters` facade. Supply `motion` and the context at consumption; neither is
installed in shared layer state or persisted as an evaluated snapshot. Snapshot
v5/legacy readers and default charts keep their existing semantics. No original
selected catalogue is reloaded, and a new restored facade still defaults to lookup.
The caller explicitly loads/adopts the motion companion separately.

This bounded integration supplies observer-free native Python chart consumers.
Observer-dependent motion is refused: this direction provider does not supply
the Cartesian observation/error-realization contract. CLI/TOML model selection,
persisted epoch states and observer adoption remain future work. Chart calls use
reproducible full-model sessions; interactive provider reuse remains available
through the separate SDK API and is not a projection/paper accuracy promise.

### Explicit Cartesian astrometric output

`ClusterMotionProvider(catalogue, representation="cartesian")` supplies an explicit
Cartesian admission to the same object-independent `RectilinearAstrometricProvider`.
The default `representation="direction"` retains its accepted descriptor, model,
reference, resource identities, numerical/reuse behavior and chart consumers.
Cartesian output uses a distinct provider/model/reference binding, preserving
object keys and source-resource provenance. Both representations can coexist in
one kernel/session without sharing query/cache identities or evaluating one
another. Cartesian source records advertise `cartesian_state` and batch evaluation;
there is no direction-reuse capability on that admission.

Query its advertised admission through the existing SDK, for example after
explicitly loading/admitting `motion_catalogue` and choosing a covered TCB instant:

```python
from wenu.cluster_state import ClusterMotionProvider
from wenu_kernel import Kernel
from wenu_kernel.records import AccuracyRequest, SessionPolicy, StateQuery

provider = ClusterMotionProvider(motion_catalogue, representation="cartesian")
admission = provider.describe().admissions[0]
with Kernel(references=(admission.reference,)) as kernel:
    kernel.register(provider, ownership="owned")
    with kernel.open_session(SessionPolicy((admission.catalogue,))) as session:
        result = session.evaluate(StateQuery(
            admission.catalogue, admission.model, selected_keys,
            (evaluation_time,), admission.reference,
            AccuracyRequest(metric="euclidean_norm"), require_velocity=True,
        ))
```

`CartesianState.position_m` retains the unnormalized nominal barycentric SI
position; its norm carries distance. `velocity_m_s` retains the full admitted
constant space velocity and `velocity_available` is true. Source reference epoch,
requested evaluation/anchor time and explicit scale are independent fields.
The core evaluates exact rational arithmetic on the admitted binary64 SI PV
and split-JD elapsed time, rounding only final position coordinates. It applies
no additional light-time, observer translation, parallax, aberration or frame
transformation. This is the existing nominal catalogue model, not a qualified
geometric emission worldline or historical cluster reconstruction.

Position and velocity have separate SI uncertainty evidence. Measurement,
physical model and numerical bounds remain `not_evaluated`; independent
numerical tests are not a universal error certificate. The direction's angular
bound is not copied into metres or metres/second. Requests for Cartesian accuracy
bounds, angular accuracy, temporal certificates or interval coverage are refused.
Identical requests may use the SDK's exact cache; different times use full PV
evaluation. A required velocity is supported for full-input solutions only.
Unqualified/missing-input rows remain visible but unavailable; mixed selected
queries refuse completely. The 513-row cluster source still admits 502 solutions
and retains eleven unavailable rows. There is no source/zero-velocity fallback.

This adds explicit state output only. Existing native/observed lookup, explicit
native motion charts, snapshot formats and observer resources are unchanged.
The [observer contract](scientific_contracts.md#cluster-observer-realization-contract)
now has implemented time/common-coordinate and nominal finite-observer services;
observed chart/saved adoption remains separate.

### Barycentric time and coordinate conventions

`astrometric_coordinates.TcbTdbAdapter(validity)` accepts a finite SDK `TimeSpan`
on either TCB or TDB. Register the adapter and `adapter.describe()` explicitly
with SDK `TimeService`; no automatic chain/session conversion is introduced.
`TimeService.convert(time, target_scale)` returns its original input event,
canonical split-JD target, exact model identity, provenance and a numerical
rounding bound. Identity remains owned by the SDK. Other scale pairs refuse.

The implementation evaluates the exact decimal defining constants of IAU 2006 B3
using rational arithmetic: `L_B=1.550519768e-8`, `T_0=2443144.5003725`,
`TDB_0=-0.0000655 s`. Only the final small date part is rounded to binary64.
The exact rounding discrepancy is rounded upward in the receipt; the adapter's
maximum numerical error is `2**-36 s` (the canonical half-day fraction has
absolute rounding error at most `2**-55 day`). This bounds this coordinate
operation on admitted input numbers, not reception-date uncertainty or a clock
realization. The chosen finite domain is a caller policy, not an ephemeris or
historical-observation coverage claim. No resource bytes, network or backend
version enter this resource-free algebraic model.

`convert_barycentric_batch(batch, admission=..., source_coordinate_scale=...,
time_admission=..., conversions=...)` consumes a complete actual SDK `StateBatch`. Callers explicitly
supply the expected `ModelAdmission`, the spatial convention (`"tcb"` or `"tdb"`),
the explicit time-adapter admission with its independent finite coverage,
and one matching adapter receipt per query time. It checks catalogue/model/resource,
frame/origin/status/units, source/model coverage, full-model evaluation, ordered
object/time completeness, source epochs and full velocity. Wrong bindings,
missing states, reuse or altered receipts refuse the whole conversion. The SDK
already requires unique requested object/time keys; their order is preserved.

The returned immutable `BarycentricBatchConversion` is a derived convention
view, not a replacement SDK admission or observed state. It retains the original
batch, state and time admissions, states, epochs and uncertainty evidence. Each state view has
`original`, `conversion`, scaled `position_m`, operation-only component
`position_rounding_m`, unchanged `velocity_m_s`, target `time` and
`coordinate_scale`. Scaling uses exact rational `1-L_B` (or its reciprocal),
then rounds final components once. IERS Conventions (2010) section 1.2 scales
TCB-compatible length and elapsed time by the same factor; coordinate velocity
therefore remains unchanged. There is no second propagation, origin translation,
observer subtraction, apparent correction or additional stellar light time.
Scaling-rounding bounds do not certify total Cartesian uncertainty or a temporal
interval. Time-conversion rounding is retained separately and is not folded into
a claimed position bound. Original unknown channels stay unknown.

Authorities reviewed 2026-10-19:
[IAU 2006 B3](https://iau-a3.gitlab.io/res.html) and
[IERS Conventions (2010), section 1.2](https://iers-conventions.obspm.fr/content/tn36.pdf#page=17).
No source code or tabulation from those authorities is bundled.
Independent Decimal/ERFA time references, Decimal position scaling, synthetic
mixed-family real kernel queries, isolation and an installed real-cluster
consumer validate this subset. This does not prove that a selected observer
backend supplies the declared convention. The following offline reception
context now supplies one explicit nominal backend/input subset, consumed by
the separately admitted finite observer service below.

### Offline reception and observer input context

`astrometric_observation.ErfaReceptionBackend` prepares one event independently
of object type. Construct it with explicit `leap_seconds_path`,
`leap_seconds_sha256`, `eop_path`, `eop_sha256`, finite TT `coverage`, and
`backend_identity`. `reception_backend_identity()` inspects the installed
Astropy/PyERFA/ERFA versions and compiled ERFA SHA-256 for caller admission.
No new files, backend version pins or source downloads are installed implicitly.

Only local IERS Leap_Second.dat and final IERS-B formats are read. Their bytes
are checked before/after parsing; data are copied into the service. Every
resource has its own TT coverage retained in `model.dependencies`. The caller
span must fit the intersection of final EOP support, leap expiry and the
conservative 1950--2050 model interval. Leap expiry is interpreted using its
actual Astropy TAI convention, never relabelled UTC. The installed ERFA leap
rows from 1972 onward must equal the admitted IERS rows before and after a
call. The service does not update them, modify global Astropy settings or use
IERS_Auto, predictions, extrapolation, network acquisition or Observer handles.

`prepare(reception, longitude_deg=..., latitude_deg=..., height_m=...)` accepts
an ISO UTC string ending in Z (including valid leap seconds), or an SDK TT
`TimePoint`. Local timezone/DST resolution remains a caller responsibility.
Site coordinates explicitly mean WGS84 east-positive longitude, geodetic
latitude and ellipsoid height in -1000..10000 m. No legacy Observer elevation
is silently treated as a qualified ellipsoid height.

The frozen `ReceptionContext` (backend model version 2) additionally retains
the complete numeric ERFA astrometry tuple, nominal Sun position, UTC label and
an integrity digest over all its content. These fields bind the subsequent
realizer to the actual prepared site/event/resources and prevent silent context
replacement. They are not serialized into existing sky snapshots.
It retains the original input; split UTC, TAI, TT,
UT1, TDB and TCB dates; WGS84 site; model/resource/code identities; final
UT1-UTC, polar motion and CIP dX/dY values; the explicit SDK TDB/TCB admission
and receipt; nominal Earth and observer position/velocity in TDB-compatible
BCRS SI coordinates; operations and unapplied target corrections. TT/TDB uses
ERFA DTDB's topocentric approximation with UT1 and the WGS84 site. EPV00 supplies
analytic Earth heliocentric/barycentric PV; measured final CIP offsets augment
the IAU 2006/2000A orientation before APCO prepares terrestrial observer PV.
The fixed IAU au and SI speed of light perform unit conversions. This is not
the legacy Observer's Skyfield SPK and carries no DE440 resource claim.

All total numerical/physical time and PV error fields remain `None` (unknown).
The final addition of the returned DTDB offset has its own rationally checked
rounding bound; that is not a DTDB/clock/EOP accuracy bound. The SDK's exact
TDB/TCB receipt remains separate. A finite-bound TT/TDB TimeService adapter is
not published while its total numerical bound is unqualified. ERFA's published
model comparisons (DTDB versus DE405 time integrations; EPV00 versus DE405
positions/velocities) are reference comparisons, not a complete bound for a
particular observer or a promise outside admitted coverage.

No target state is propagated or translated, and no apparent/horizontal
direction is returned by preparation. The finite-range realizer below consumes
that frozen context without rebuilding Earth/site states or adding a second
space-motion or stellar light-time step.
Independent analytic leap/TT checks, a published ERFA observer reference with
explicitly synthetic EOP inputs, site/range checks, corruption/refusal recovery
and actual installed cluster queries at the returned TCB event validate this
input boundary. The finite observer gate below adds target correction checks;
physical-error bounds remain unknown.

Primary authorities reviewed 2026-10-19:
[ERFA DTDB](https://github.com/liberfa/erfa/blob/master/src/dtdb.c),
[EPV00](https://github.com/liberfa/erfa/blob/master/src/epv00.c),
[APCO](https://github.com/liberfa/erfa/blob/master/src/apco.c),
[published numerical checks](https://github.com/liberfa/erfa/blob/master/src/t_erfa_c.c),
and [Astropy IERS data handling](https://docs.astropy.org/en/stable/utils/iers.html).
No authority implementation or data file is copied into Wenu.

### Finite-distance nominal observer realization

`NominalObservationAdmission(state_admission, reception_model)` explicitly binds
one full nominal Cartesian source admission to the prepared backend model.
The first policy is `light_time="no-additional-correction"` and
`corrections="solar-monopole-aberration-vacuum/1"`; unsupported policies refuse.
Source coordinates must be TCB-compatible nominal barycentric ICRS Cartesian
states, qualified by their source adapter. This is not a retarded geometric
Solar-System model. Source/centre qualification remains outside the realizer.

`realize_astrometric_batch(batch, reception, admission=...)` consumes actual
SDK results for exactly one reception TCB event. It checks full query/model/
resource/reference bindings, ordered completeness, velocity availability,
reception integrity/backend identity and the exact time receipt. It preserves
the original batch and its source/evaluation epochs. It does no provider lookup
or second propagation. Wrong time, changed context, partial/reordered state
arrays and singular observer/source or Sun/source geometry refuse atomically.
Requested apparent bounds (`maximum_error_rad`) and native accuracy requests
cannot be promoted to observer bounds and are refused. Native temporal/reuse
certificates do not qualify observer directions.

The fixed sequence is explicit convention scaling; one observer subtraction;
finite-source solar-monopole LD; AB with combined annual/diurnal velocity and
its solar-potential term; final-CIP CIRS rotation; vacuum ATIOQ. The latter's
`diurab`, `refa` and `refb` must be zero to prevent double aberration/refraction.
The Sun is evaluated at reception. Its conventional ERFA limiter is retained;
deflector retardation, planetary/multipole deflection, extra target light time,
refraction and solar occultation/visibility are not modelled. No `atciq`,
`pmpx`, `apply_space_motion`, `observe()` or retarded-time solver is called.

The frozen `ObservedAstrometricBatch` retains original and convention-converted
states, reception/context identity, explicit admission and a separate observer
`ModelRef` with source and backend resources. It returns ordered
`ObservedAstrometricState` records: object key, synchronous nominal `range_m`,
observer-origin BCRS-oriented `geometric_vector`, solar-deflected
`natural_vector`, `proper_bcrs_vector`, topocentric `apparent_cirs_vector`, and
vacuum `azimuth_rad` (north through east)/`altitude_rad`. The `CoordinateSpec`
states observer-origin observed Alt/Az, radians and the retained UTC reception
label. No chart geometry or projection is constructed by this service.

Angular/range error fields and emission time remain `None`. Original source
measurement/model/numerical evidence, approximate reception uncertainty,
operation-only scaling/addition rounding and exact time receipts retain separate
meanings. No total apparent/range bound is inferred. The inverse TCB/TDB view
may differ from the retained reception TDB split by round-trip rounding; both
receipts are retained and no extra propagation is applied to conceal it.

The service has no observation cache or handles. Exact repeats recompute each
correction per object; the upstream SDK may still cache exact source requests.
A future observation cache must bind full state content, reception identity,
source/backend model/resources and correction policy, including distance.
There is no fallback from a failed source query or partially realized batch.

The `astrometric-observer` gate retains reception/installed checks and adds
independent analytic parallax/range at several distances, the distant-source
limit, independent Lorentz aberration, a separate Astropy finite-distance
AltAz comparison, exact correction counts, no-second-motion spies, changed
range and warm refusal tests. Deliberate double translation and double
aberration must fail those same numerical oracles. A real installed cluster
query exercises this exact public function. These are model/composition tests,
not independent physical ephemeris or universal ancient-date accuracy proofs.
Default lookup charts and native snapshots retain their existing semantics.
Explicit observed Python consumers now adopt this service as described below.

Primary correction authorities reviewed 2026-10-19:
[ERFA LD](https://github.com/liberfa/erfa/blob/master/src/ld.c),
[solar limiter](https://github.com/liberfa/erfa/blob/master/src/ldsun.c),
[AB](https://github.com/liberfa/erfa/blob/master/src/ab.c), and
[ATIOQ](https://github.com/liberfa/erfa/blob/master/src/atioq.c).
Wenu calls the installed library; it does not copy these implementations.

### Observer motion: current boundary and proposed handoff

Explicit observed cluster chart adoption is implemented through the same
`OpenClusters.realize` owner as native motion. The existing observed lookup
calls `catalogue_point_altaz` and `CoordinateService` with RA/Dec only. No distance
or velocity enters that transform, so replacing those angles with propagated
ones would not implement the finite-distance observer contract.

The SDK already supports `CartesianState`/`cartesian_state`, explicit velocity
availability and separate position/velocity evidence. The explicit cluster Cartesian representation now adopts that SDK interface. TimeService has explicit admission/receipts,
and the separate offline reception context now maps UTC/TT explicitly. It
retains unknown approximate-conversion error rather than advertising an
unqualified bounded TT/TDB SDK adapter. Default Observer/chart time handling
is unchanged.
Solar-System `AstrometricDirection` requires retarded geometric target/emission
semantics, which the nominal cluster model does not supply. These existing types
are not permission for a consumer to read private cluster PV or relabel states.

The [scientific contract](scientific_contracts.md#cluster-observer-realization-contract)
owns the proposed handoff, correction/time/resource requirements, output evidence,
failure and reuse policy. The [roadmap](kernel_roadmap_v0.9.5.md#cluster-observer-implementation-order)
separates Cartesian, time/common-convention, observer and product adoption.
The offline input context and nominal finite observer service above are
implemented. Cold/saved/fresh-process Python chart and actual SVG output gates
cover consumer adoption. Total physical-error qualification remains pending.

### Explicit observed cluster Python consumers

Prepare a `ReceptionContext` through the offline backend above, using explicit
local leap/final EOP bytes, digests, installed backend identity, finite TT domain
and caller-qualified WGS84 site. Then construct
`LayerRealizationContext.from_reception(reception)` and call:

```python
context = LayerRealizationContext.from_reception(reception)
geometry = sky.open_clusters.realize(
    context, None, motion=motion, selected=selected_ids,
)
options = {layer: {"enabled": False} for layer in sky.layers}
options[sky.open_clusters] = {
    "geometry": {"motion": motion, "selected": selected_ids},
}
result = sky.draw_chart(
    projection=projection, renderer=renderer,
    realization_context=context, layer_options=options,
)
```

The snippet assumes the explicitly prepared receipt, admitted motion catalogue,
existing sky, projection and renderer. Import `LayerRealizationContext` from
`wenu.sky.realization`. This is the existing canonical Python drawing API;
ordinary horizontal request/CLI/TOML model selection is now implemented as
described in the configuration contract.
Unmigrated layers must be disabled for this reception-context chart: their base
adapter refuses the new request. The chart guard also rejects overridden layers
that return a mismatched frame/status/event/units/corrections or omit the reception
identity, before projection. A legacy Observer, if present, is not the authority
for this explicit receipt's site/time/resources.

`OpenClusters.position(reception.tcb, motion=motion, reception=reception)` supplies
the same observed centre data without drawing. Both paths require non-empty
selection, the matching TCB instant and the unchanged complete source binding.
Selected order and duplicates survive a unique-key full Cartesian SDK query
with SI Euclidean error meaning and required velocity. No native angular
certificate is reused. The result converts radians to degrees only at the
`SphericalPoints` boundary and retains `astrometric_observation` (the complete
immutable batch/receipt) and ordered `observed_states` in metadata. Existing
source fields/epochs remain distinct from evaluation and reception events.
All selected rows must be usable; unavailable inputs, source/domain/context
mismatch and query refusal fail completely, including after a prior good call.

Source snapshot v5 is unchanged. A restored sky receives the motion catalogue
and newly prepared reception context per call; no evaluated states, local
resource handles or observation receipt are persisted. Cold, restored and fresh
processes use the same public route without reloading source catalogues.
Default lookup, explicit native motion and existing appearance remain available.

### Cluster direction reuse bound

The model version is now `cluster-centre-rectilinear/2`; source resources and
object identities are unchanged. The provider verifies every computed direction
against exact rational arithmetic on its admitted binary64 SI position/velocity
and the exact split-JD TCB input. Python `Fraction(float)` preserves that binary
value exactly ([Python 3.11 documentation](https://docs.python.org/3.11/library/fractions.html)).
A fixed algorithm budget of `2**-40` radians is checked, not assumed; a numerical
failure refuses publication. This budget is part of model identity. It starts
after the Astropy spherical-to-Cartesian admission conversion. It is neither a
bound on that conversion nor on the original astrometric data/model.

For a stored anchor vector w and exact model position p(t), the sufficient test is
positive w dot p and

\[
4\lVert w\times p\rVert^2
\le \epsilon^2\lVert w\rVert^2\lVert p\rVert^2,
\qquad 0 < \epsilon \le 1\ {\rm rad}.
\]

The angle is acute and its sine is at most epsilon/2. Since angle is at most
twice its sine on this range, the angular separation is at most epsilon.
All comparisons use rational operations, without inverse-trig rounding. The
corresponding circular cone has half-angle below pi/2 and is convex. The exact
rectilinear p(t) is a line segment, so admission of both endpoints proves the
bound everywhere between them, including fast perspective changes and the
original anchor approximation. Interior test samples supplement this proof;
they do not define it. Missing motion never becomes a zero-speed certificate.

`certify(query, anchor)` accepts only a scalar original full-model anchor with
matching source/model/reference/evidence. It verifies that actual stored vector
at the anchor, then halves each model-domain endpoint toward the anchor until
the cone test succeeds. The returned interval is conservative, clipped to finite
source/model coverage, and need not be the longest possible one. Halving and
rounding a candidate time never authorize an unchecked endpoint. A requested
whole interval is checked explicitly at its endpoints and anchor hull; an
unprovable interval is refused. Larger requested tolerances use at most one
radian for this proof. No catalogue-specific time step is embedded in software.

Use a `bounded_reuse` query with positive `AccuracyRequest.angular_rad` through
an explicit `interactive_bounded` kernel session. The unchanged SDK selects
eligible original anchors per object, rejects looser old certificates for tighter
requests and evaluates only missing objects. Reused rows carry the actual
requested time, original anchor time and certificate identity. Source epoch is
unchanged and reuse never creates a new anchor. The certificate method and
identity bind source, model, reference, coverage, vector and bound. No provider
global cache or hidden propagation in `describe`, `catalogue` or `supports` is
introduced. Exact rational endpoint arithmetic is proof work, not another full
normalized-direction result.

No canonical schedule is advertised. Default `reproducible` sessions therefore
use full-model evaluation, as required by the existing SDK, independent of cache
warmness and request order. This slice neither changes that contract nor adds
chart/snapshot integration. Bounds concern computation within the nominal model;
physical ancient-date validity remains unevaluated.

## Independent provider verification

`wenu_kernel.conformance.provider_suite(factory, name=...)` returns a standard
`unittest.TestSuite`. The factory creates a fresh `ProviderCase` containing
the provider, supported full-model `query`, a distinct-time `probe`, activity
and buffer-mutation hooks, and `reuse_query` when direction reuse is advertised.
`ProviderActivity` records full-model work, certifications and close calls.
Run one case per admitted catalogue/model/reference/subset. The same checks
support direction and SI Cartesian providers; optional canonical reuse must be
exercised by a supplied sample, while unrelated providers need no planner.
See the [kit contract and limitations](../../packages/wenu_kernel/README.md#provider-conformance).
The provider owns its science/failure tests and fixtures; the SDK module ships
no concrete provider and does not import the legacy Wenu package.

## Configuration, presentation and curation

Use [schema v2](configuration_schema_v2.md) for ordinary chart configuration.
`configuration/` validates partial overlays and translates them into existing
typed owner records. Unknown fields fail instead of creating hidden behavior.
Installed atlas layout, full style and index style have different protocols;
`resources.py` owns discovery. Adding one preset must not make another
preset's test require it to be the sole registry entry.

`star_designations.py` supplies names and Bayer/Flamsteed identity independently
of astrometry. `StarDesignations.curated_names` is the accepted presentation
overlay; source `record.names` and the Wikidata snapshot remain unchanged.
Explicit inclusion, labels and symbol eligibility are separate decisions.

Catalogue maintenance, exact input/output identities, active selectors and
criteria publication are documented in the [curation guide](../user_guide/curation.md).
`resources.py::curated_catalogue_bundle()` resolves verified installed defaults;
original scientific snapshots remain explicitly accessible.

## Fixed celestial scenes and temporal products

`charts/fixed_sky_sequence.py` owns `FixedSkyRotatingHorizonSequenceRequest`
and `generate_fixed_sky_rotating_horizon_sequence`. The renderer-neutral
`fixed_sky_circumpolar_orientation` in `charts/fixed_sky_orientation.py`
resolves the circumpolar anchor rotation through the canonical chart request.
`charts/fixed_sky_baseline.py` owns
`generate_fixed_sky_complete_render_baseline` and `PngFrameComparisonTolerance`;
the complete-render baseline is distinct from the fixed-scene reference route.
Keep both routes and ordinary observer-time sequences during migration.

The installed `wenu_examples` and `wenu_notebooks` commands copy the packaged
examples and bilingual notebooks. Their resource/install contracts remain
part of release acceptance even though copying does not query sky state.

## Existing advanced areas

Solar-System points, tracks, resolved disks and sequences use descriptors,
shared spherical geometry and the canonical exporters. Symbol display scale
does not change physical angular size metadata or catalogue membership.

Satellite domain APIs live under `satellites/`; presentation and report
adapters consume their immutable scientific results. Exact reports are not
sampled-provider candidate reports. Read [satellite science](satellite_guide.md)
and [scientific contracts](scientific_contracts.md) before changing those routes.

For a detailed old API explanation not reproduced here, consult the
[complete baseline reference](archive/pre_kernel_20261017/docs/developer/implementation_reference.md)
and verify names/signatures against the current source before using them.
Historical candidate or authorization language in that edition is not current status.

## Extension procedure

1. Identify the current owner, public seam and actual signature in source.
2. Preserve the canonical pipeline and independent product concerns.
3. Verify the owning responsibility and immediate contracts only during iteration.
4. Follow the [kernel roadmap](kernel_roadmap_v0.9.5.md) for state-provider
   migration; do not introduce an alternate position route.
5. Update this reference and the source map only when responsibility changes.

The existing [user examples](../user_guide/chart_examples.md),
[configuration guide](../user_guide/configuration.md) and
[SVG guide](../user_guide/svg_output.md) remain operational documentation.


## Ordinary request cluster astrometry selection

`ClusterMotionRequest` is imported from `wenu.charts.request`, without a new
top-level export. `ChartRequest.cluster_motion` defaults to lookup. An active
request selects the accepted `nominal-observed` model, ordered `identifiers`,
local leap/EOP paths and SHA256 digests, four-part installed `backend_identity`,
increasing finite `start_jd_tt`/`stop_jd_tt` and `start_jd_tcb`/`stop_jd_tcb`, and
explicit `height_wgs84_m`. Paths are interpreted from the process working
directory; absolute paths are preferable. JD bounds are user domain endpoints,
not a high-precision reception timestamp or a physical error certificate.

The configuration translator maps `astrometry.open_clusters` into this immutable
contract. `get_chart_view` carries it into the ordinary drawing request. The CLI
`--open-cluster-model lookup|nominal-observed` overrides TOML model selection;
repeatable `--open-cluster-id` replaces its identifier list. `lookup` does not
open the extra resources. The admitted model is currently limited to horizontal
ordinary charts; unsupported frames fail instead of changing frame semantics.

`chart_cluster_motion_options(request, observer)` composes public source/backend
services and returns per-layer motion/reception/selection geometry options.
Caller-qualified WGS84 ellipsoid height must equal the ordinary observer's
height; it is never inferred from an unqualified legacy elevation. Source and
reception coverage remain independent, local resource hashes and code identity
are checked, and each requested cluster must have usable admitted inputs.
The cluster adapter checks the receipt against the chart site/time/vacuum frame,
then performs a full Cartesian query and the accepted shared observer realization.
There is no fallback or shared layer mutation. Lookup spatial pre-culling is
skipped for this explicit source model; projection/viewport clipping occurs on
realized geometry. Other families keep their existing scientific routes.

Model choice does not override layer enabling, symbol style or minimum-size
filtering. Explicit chart cluster membership intersects the admitted identifier
list; exclusions apply too, and an empty effective membership disables that layer.
View centres and target-resolution definitions retain their existing meaning. Wide-field adaptive detail can hide open clusters; configure that
appearance independently. Active model parameters remain in SVG provenance and
sequence identity; lookup retains its former identity. Snapshot v5 and native
atlas workers are unchanged. See the complete
[configuration fields](configuration_schema_v2.md#explicit-open-cluster-astrometry).

## Generic nonstellar and named-target kernel lookup

K3.12 uses NonStellar._kernel_centres and _catalogue_direction_provider for the
generic owner, including Messier and Caldwell. The galaxy facade shares these
mechanics with its accepted static model identifiers/reference semantics retained.
Generic lookup uses catalogue_lookup, copied source rows and full immutable source
metadata identity. Qualified numerical epochs are retained; unknown/unqualified
dates remain provenance. No requested-time propagation occurs. The deterministic
undated evaluation anchor is JD 0 TT, not a measurement epoch. Missing source
facts stay explicit; legacy constructed/unitless inputs remain disclosed.

The generic _state_table and _outline_state query before observation cache access;
returned positions, ordered IDs and metadata govern cache identity. Outlines use
that same batch. position, realize (including label-only), spherical_centers and
spherical_geometry preserve source order, catalogue membership, semantic identity,
selection and geometry mathematics. Dedicated subclass routes are not activated
by this generic-owner opt-in.

ResolvedTarget.coordinate queries an immutable copied target direction through
the same table-provider protocol before returning SkyCoord. The record identity
binds key, coordinates, provenance and components; it does not claim a digest of
original source bytes. Unknown physical reference/epoch facts remain explicit in
the provider reference. Explicit-coordinate subjects keep their constructed route.
get_object_center and binocular request preparation consume this public property,
so refused target queries propagate through both consumers. No hidden target cache
or catalogue cross-identification replacement is introduced.

## Globular-cluster kernel lookup

K3.13 enables GlobularClusters._uses_catalogue_lookup and supplies a globular
_direction_provider facade to the accepted shared catalogue lookup owner. The
semantic type is globular-cluster; provider/model/resource IDs are globular-owned.
Source metadata admission, copied rows/identity, nullable or qualified source
epochs, evaluation anchor, vector decoding, observation inputs and returned-state
cache identities use the accepted NonStellar mechanics. No source fact is inferred.

Public position, native outline and label realization, observed centres/outlines
and restored sources all query the provider. Failed source admission or state
evaluation propagates after cache fill; source coordinates are not a recovery
route. Harris half-light diameters, structural metadata, source/active selection,
common-name policy, sampling and glyph/observer mathematics stay with their existing
owners. PN and SNR routes are described below; physical motion remains separate pending work.

## Planetary-nebula kernel lookup

K3.14 enables PlanetaryNebulae._uses_catalogue_lookup and a PN-owned provider
facade to the shared NonStellar catalogue lookup owner. Source admission, copied
rows/identity, unknown/qualified epochs, deterministic evaluation anchor and vector
decoding retain their accepted mechanics. Unknown physical facts stay explicit.

PlanetaryNebulae.realize constructs the existing SphericalPoints from returned
_native_centres after the existing native selection/size filter. Its observed
spherical_geometry queries _state_table on the full source before cache access
and supplies _observed_point_source_key(state_table). The shared observation
cache transforms the returned centres, then applies existing requested-row order.
position and spherical_centers inherit the shared provider boundary. Source
records, membership/flux/diameter metadata, native catalogue order, observed request
order/duplicates and empty-symbol behavior remain unchanged. No labels-only flag
or outline sampling is added to the PN API: symbols already carry their labels.
Failed admission/state queries propagate even after cache fill; no direct-source
fallback. Snapshot transport and renderer symbol scaling are unchanged.

## Supernova-remnant kernel lookup

K3.15 enables SupernovaRemnants._uses_catalogue_lookup and supplies an SNR-owned
_direction_provider facade to the shared NonStellar lookup owner. The semantic
type is supernova-remnant; provider/model/resource IDs are SNR-owned. Source-bound
admission, copied rows and metadata identity, optional source epochs, evaluation
anchor and vector decoding use accepted shared mechanics. Physical source gaps
remain explicit; no source frame/origin/epoch is inferred.

position, native realize (including labels_only), spherical_centers and observed
spherical_geometry query returned centres. The inherited state-table and outline
hooks query before observed cache access and bind state values/IDs/metadata into
cache identity. The outline builder consumes the same queried batch without a
second lookup. Constructor/per-call selection and signed semantic keys are
unchanged. Green radio axes/flux, unknown PA circle policy, morphology, sampling
and renderer appearance remain with existing owners. Restored source snapshots
use the same adapter without schema changes or hidden state/fallback.



## Public atlas sheet contract

`charts.atlas_sheet.AtlasSheetChartRequest(sheet, page, presentation,
output_dir)` owns the existing validated immutable sheet request.
`charts.atlas_publication.AtlasSheetChartRequest` and
`charts.request_generation.AtlasSheetChartRequest` remain aliases of the same class
for existing imports and old pickle GLOBAL paths. Validation, defaults
and normalized Path output directory are unchanged. The chart CLI and atlas
workers use the sheet-service contract. Existing publication imports of
AtlasSheetChart, AtlasChartPresentation and private sheet helpers remain aliases.

`charts.atlas_sheet.render_atlas_sheet(request, sky)` renders one
observer-free prepared sky into the supplied directory and returns the existing
`ChartExportResult`. Its `output` is the first requested format; `report_outputs`
contains remaining chart formats and report files in the established order.
This is the sheet rendering service, not the atomic publication entry point:
call `generate_chart_request(request, sky=sky)` for request scope, safe staging,
no-clobber publication and cleanup. The renderer uses the unchanged native-ICRS
realization, composition, grid/furniture/report policies and one offscreen Agg
figure. Exceptions still close that figure and reach the request executor.

`catalogue_star_counts(stars, magnitude_limit)` now obtains full-source geometry
through `stars.native_positions()`, including its HIP IDs and magnitude metadata.
It retains first-HIP/source order, finite position/photometry filtering and
cumulative counts; unavailable or refused native states cannot fall back to
raw RA/Dec. This is source-native catalogue availability, not propagation or a
new epoch/observer model. Per-sheet report statistics still consume completed
rendered geometry. Atlas design remains geometry-only and the standalone index
continues through canonical polar/layer/coordinate/domain/projection services.

## Physical polar product service boundary

`PolarPlanispherePairRequest.resolve()` retains both equidistant and stereographic
faces, handedness and registration. `PolarPlanisphereChart.render()` delegates
to the canonical sky/layer pipeline; observed inputs use `CoordinateService`
before public kernel projection/domain services through the existing aliases.
Native ICRS rendering retains its explicit realization context.

`CommonYearCalendarRequest` retains its existing Astropy mean-sidereal calibration
at standard-time local midnight and its deterministic 365-day ring. This is
product calibration, not a new universal kernel calendar/time API. Calendar
furniture uses each face's returned projection directions.
`PolarHorizonOverlayRequest` uses canonical horizon/coordinate results before
projection and millimetre placement; resolved horizons feed
`PolarPouchFurnitureRequest` and `PolarPouchSheetRequest`.

`export_polar_planisphere_pages` uses the existing chart composition/export
boundary and closes each face figure even on failure. The pouch face/sheet
exporters save resolved physical furniture with existing `ExportOptions`.
Page dimensions, duplex alignment, fonts, windows, folds, previews and assembly
remain Wenu policy. K3.22 changes verification only; public APIs and production
implementations are unchanged.

## Observer-time sequence generation and resume

`ObserverTimeChartSequenceRequest.frames` retains chart semantics and effective
configuration while substituting each UTC simulation instant and deterministic
frame output. `generate_observer_time_chart_sequence` delegates each uncached
frame to `generate_chart_request`; it does not implement a second scientific
rendering route. The static generator owns context construction, request leases,
owned observer cleanup and canonical export.

`TemporalTimeline` separates UTC instants from civil display times;
`PlaybackSpec` supplies a presentation cadence with matching frame count.
`ObserverTimeSequenceManifest` schema 1 preserves request/configuration,
timeline/display/playback identity and per-output byte count/SHA-256. Completion
records are written after successful static generation. Resume refuses a
changed declared plan before rendering, regenerates missing or altered files,
and does not claim new generation for reused frames. Output-directory
portability and the legacy lookup identity remain intact.

The existing planisphere viewport calculation now runs once per frozen chart
and returns its existing immutable kernel `Viewport`; callers replacing chart
parameters receive a fresh calculation. This prevents numerical refitting from
making a valid composition appear to belong to another chart. Strict composition
mismatch refusal remains unchanged. No timeline, manifest or snapshot schema
changes, new propagation, or fixed-sky/rotating-horizon adoption occur here.

## Fixed-sky service consumers and observer ownership

`resolve_fixed_sky_rotating_horizon_frame` constructs anchor and local observers
under one cleanup scope. Both are released if construction, orientation or
cleanup fails. Returned `FixedSkyCircumpolarOrientation` is retained as provenance
and supplies the canonical request position angle; the request observer uses the
local frame instant. Source catalogue epoch is not replaced by the anchor.

`generate_fixed_sky_rotating_horizon_sequence` retains explicit `cold` and
`reuse_loaded_sphere` modes. Both call the same static generator and effective
configuration. Reuse keeps an unbound catalogue container and closes the
per-frame observer; it claims no evaluated-state reuse or temporal certificate.
The independently generated complete-render baseline remains an ordinary
observer-time sequence with its own output directory and resume contract.

Existing reference geometry and numerical tolerances are preserved. The anchor
corrects a reference orientation; this is not a new physically frozen stellar
model or a guarantee of exact all-object invariance. K3.24 changes only observer
cleanup and verification of service consumers, source/projected geometry and
actual PNG/SVG/rendered-PDF cold/reuse equivalence.

## Major-planet and Moon point states

`ephemeris_state.KernelEphemerisStateSource` adapts the existing
`EphemerisStateSource` protocol to the existing Cartesian kernel records. Each
geometric request gets a borrowed, request-scoped registration/session; returned
SI position/velocity are converted to the protocol's AU/AU-day output. The original
backend evaluates the original request once. No cache, light-time solver or
physical uncertainty bound is added. Kernel failures propagate without raw fallback.

Default major-planet/Moon point assembly opts into this adapter. The raw Skyfield
source remains the reception-observer/apparent backend. Custom source injections,
tracks, resolved disks and minor-body bindings retain their existing routes pending
their separate milestones. The existing direction solver remains the sole
light-time authority; apparent correction constructs Skyfield Astrometric directly
and never calls observe a second time. Descriptor targets (including planetary
barycentres) remain distinct from physical body IDs.

`resolve_skyfield_resource_identity` hashes exact bytes and retains segment coverage.
It now reports `unqualified SPK model` without an explicit model argument. An explicit
argument is labelled caller-declared, not independently qualified. Renaming a BSP
cannot qualify its physical model; a verified acquisition/model receipt remains
necessary for such a claim. No source bytes or numerical formula changed.

## Resolved-disk and sequence state routing

Default `SolarSystemDiskRealization`, `ObservedSolarSystemDiskSequenceRealizer`
and `FrozenEarthDiskSequenceRealizer` now reuse `KernelEphemerisStateSource`.
Constructors accept `source_factory=None` for that default assembly. Explicit
injected factories retain their existing EphemerisStateSource compatibility;
they remain caller-owned protocol boundaries. The default observed paths use
the adapted source for target/Sun light-time queries and the appearance service's
reception-Sun state. The raw Skyfield source still supplies reception observer PV
and apparent corrections. The frozen construction adapts its one initial
Earth-relative-to-Sun query and each same-epoch target-relative-to-Sun query.
It remains geometric and does not call the observed light-time/apparent services.

Single/observed display owners check `observer_geometry_key` before sharing a
component result. Frozen geometric display checks only the existing live SPK
identity hook; it does not acquire or require observer EOP data. They retain one coherent result for the same context object,
observer and resource key, rather than treating equal-valued separate request
contexts as one admission. Resource changes rebuild; closed/changed resources
refuse before reuse. A fresh request retries source/kernel admission and cannot
return a previous request's geometry after refusal. Within one admitted context,
face, limb, terminator and date components continue sharing their exact result.
This is request component sharing, not a persisted/evaluated-state cache.

Radius, angular diameter, phase, illuminated fraction, bright-limb orientation,
physical disk sampling and sample chronology retain their existing owners and
formulas. Magnification remains post-projection preparation. No capability is
expanded: current single/observed Venus and Moon and frozen Venus/Mercury policies
remain as before; custom generic protocol seams do not admit new public products.

## Natural-body track state routing

`SolarSystemTrackRealizer.curve` adapts known `SkyfieldEphemerisStateSource`
planet/natural-satellite target bindings to `KernelEphemerisStateSource` after
binding resolution. This covers default binding and the planetary source returned
by `MinorBodyResourceSession.source_binding` in a mixed request. The observer and
apparent roles retain their raw source. An already-adapted or explicit generic
protocol source is preserved; minor-body session assembly is described below.
No minor-body resource acquisition or numerical model is moved here.

Sampling and major tick insertion are unchanged. Every sample keeps its observer,
reception instant, retarded target direction and source identity. The assembled
curve transforms once into the request's fixed product axes; per-vertex times stay
in metadata rather than being collapsed into one physical epoch. Path and major
symbols consume the same returned samples. Temporal path/tick/symbol/date choices
change presentation only. The shared component owner checks live observer inputs
before reusing a result within the same context object; separate requests re-admit,
and closed resources or a failed fresh query cannot return previous geometry.

Public chart admission is unchanged: existing planetary chart families and
natural-satellite track refusal remain. Moon tests cover the existing scientific
sampler API, not a newly admitted chart/CLI capability.

## Asteroid state and offline resource routing

`MinorBodyResourceSession.source_binding()` wraps known asteroid
`SkyfieldMinorBodyStateSource` targets with the existing
`KernelEphemerisStateSource`; its observer/apparent source remains raw planetary
science. Ceres and manifest-derived numbered objects use this same assembly.
Comet bindings now use this same session route. Explicit generic protocol injection remains
compatible; it does not claim the default offline-session route.

The Cartesian adapter accepts an `EphemerisResourceChain`, registers every
ordered resource/digest/coverage and admits only their coverage intersection.
The original backend still selects exact segments and performs the existing
small-body-plus-planetary composition. Returned SI position/velocity replace
those fields on the original state record, retaining `MinorBodyEphemerisState`,
solution, segment, chain and provider IDs. Registration borrows resources;
the resource session remains their owner. No new light-time solver is added.

`sky.ceres.CERES_SOLUTION` remains import-compatible and loads the complete
unchanged facts from `wenu.data/ceres_solution_v1.json`. Schema and descriptor
identity are checked before publication; the offline session retains acquisition
receipt, SPK digest/target/frame checks. The packaged manifest does not qualify
new physical accuracy or replace an installed acquisition receipt.

Warm asteroid track components recheck their resolver/session before reuse;
changed binding identities require fresh realization and closed sessions refuse.
The observer key alone cannot establish the lifetime of a separately owned SPK.

## Comet consumers and provider records

`MinorBodyResourceSession` adapts all known `SkyfieldMinorBodyStateSource`
targets, including manifest-derived periodic and installed provisional comets.
It preserves the raw planetary observer/apparent binding. Existing model
parameters, quality fields, exact solution/segment selection and both resource
identities remain on the returned minor-body state. No numerical backend or
light-time implementation is replaced.

`KernelEphemerisStateSource.apparent_gas_tail_position_angle_deg` forwards the
optional source-owned sample using the original request and observer state.
An absent sample remains `None`; provider refusal propagates. Existing point
and track-symbol consumers validate/use it or retain their original apparent
Sun fallback. This transport is not K3.30 antisolar-reference migration.
Warm components now recheck both asteroid and comet resource sessions before
sharing, while retaining one target trajectory for path and major symbols.

`comet_discovery` and `comet_photometry` retain their existing validated provider
result records. `cli.comets.table_text`, `json_text` and `main` consume those
returned rows, missing values, sampled extrema, epochs and provenance. Magnitude
samples are provider model values, not position queries, continuous minima or
visibility predictions. Existing explicit acquisition, bounded sequential
workload, validated raw-response cache and report failure behavior are unchanged.
Automatic/provisional selection limits remain as documented.

## Antisolar constructed-reference routing

`AntisolarReferenceProvenance` in the existing `wenu.antisolar` owner is an
immutable construction receipt: kind, method, observation, source coordinate
specification, optional source/observer resource identities, availability and
provenance text. It holds no live observer/backend. The numerical functions in
that module are unchanged.

`SolarSystemPointLayer` and `CometTrackSymbolLayer` share the point owner's
private apparent-Sun realization. Known Skyfield Sun inputs use
`KernelEphemerisStateSource`; custom protocol injections remain compatible.
Raw observer/apparent sources and the existing single light-time calculation
retain ownership. Provider PsAng wins without a Sun query. Returned Sun values
control the fallback tangent; refusal propagates after prior success.
`antisolar_reference_provenance` records the actual reception/sample instant
and source frame/resource before fixed-axis projection. A suppressed tangent
retains its receipt with `available=False` and the existing head-only geometry.

`CelestialPoints.add_antisolar_point()` retains Astropy `get_sun`, the existing
unit-direction conversion through `CoordinateService`, and the same antipode.
`constructed_reference_provenance` is a row-aligned tuple on native and observed
geometry; ordinary rows contain `None`. The antisolar row records construction
observation and the original geocentric GCRS Sun convention. Rebinding for later
display transforms the stored point; it does not recompute the Sun. No new public
argument, physical pseudo-body, SDK contract or saved-snapshot schema is added.

## Satellite state and observer services

`Sgp4TemePropagator.propagate()` and `propagate_many()` retain their signatures and
`SatelliteTemeState` results. Private numerical methods contain the original
scalar/accelerated-array calculation bodies; public calls admit their returned
PV through a borrowed, request-scoped Cartesian SDK registration in the same
existing module. The original SGP4 nonzero-status exception retains its code,
NORAD identifier and evaluation instant across the adapter.

The reference is geometric Earth-centred TEME in SI units. Complete canonical
record content, the separately retained source-record digest, optional caller
snapshot digest and SGP4 implementation/version/model bind identity. The SDK
query uses explicit TAI labels converted offline from the original UTC strings;
source epoch and installed ERFA leap-table identity are retained. The orbital
calculation still receives the unchanged split UTC JD. Registration admits only
the exact finite batch. Duplicate samples share transport rows and are restored
in their original order; the backend retains its original scalar/array route.
No physical validity interval, covariance, evaluated-state cache or reuse
certificate is inferred.

`SatelliteGeocentricItrsTransformer` and `SatelliteTopocentricTransformer` consume
the returned typed TEME state through their existing Astropy/EOP chain. Earth
orientation is re-read/admitted by the existing service; no warm transformation
cache is introduced. TEME, ITRS, topocentric GCRS-axis directions and vacuum AltAz
retain their distinct meanings. A constructed typed TEME input remains compatible;
it is not retroactively labelled as a kernel-evaluated state.

Snapshot loading, canonical source-content validation, immutable element records
and external admission tokens remain their existing owners. Direct hand-authored
records are not promoted to independently validated captured provider evidence.
No new module, public export, SDK/dependency pin or serialized schema is added.

## Sampled satellite candidate services

`SatCheckerQuery`, `submit()` and `poll()` retain the existing provider boundary:
one explicit request per call, no polling loop or automatic retry. Exact receipt
bytes and request/EOP identity remain in `SatCheckerCache`. Replaying a cached
receipt explicitly calls the same `parse_response()` normalizer; no new replay
API or serialized schema is added.

`SatCheckerPresentation` consumes normalized immutable evidence for deterministic
text/JSON reports. `SatelliteCandidateTrackLayer` and
`SatelliteCandidateSamplesLayer` use `CoordinateService.transform()` and public
kernel spherical records, then `CelestialSphere.draw_chart()` supplies the
canonical domain/projection/rendering route. Returned coordinates and service
refusal reach drawing even after successful use; there is no transformed-state
cache in these owners.

Response digest/version, full NORAD identity, source-inferred geometric
ICRF/ICRS-oriented topocentric convention, provider sample order, UTC labels,
UT1 Julian dates, nullable provider illumination and candidate warnings are
retained. Per-sample times remain metadata rather than a fictitious single
track epoch. A singleton has no invented segment. Supplied records are neither
new SGP4 evaluations nor exact crossing events. Loading or drawing them requires
no positional SDK query and cannot establish provider-data redistribution
permission, physical accuracy or continuous coverage.

## Exact satellite service consumers

`LocalSatelliteCrossingOracle.solve()` retains the adaptive complete-scan owner.
`ConservativeConeShellSelector.select()` uses the same default SGP4/observer
services for its initial state and returns ordered retain/reject/indeterminate
evidence. State-evaluation refusal becomes indeterminate, never a false negative.
`AcceleratedLocalSatelliteCrossingOracle` validates complete selection identity,
uses the shared exact-record solver for every non-rejected record, and preserves
its explicit selector-failure fallback policy.

`MultiFieldSatelliteCrossingCoordinator` obtains current field-altitude service
values through `FieldAirmassCertifier`. Request/domain and whole-interval airmass
validation precede every solve, including reuse of a coordinator after success.
Failures remain atomic and ordered; independent intervals and processing chunks
retain their existing meaning.

`ExactLocalSatelliteTrackRealizer.realize()` validates snapshot/object/model/epoch
bindings and uses the same default state/observer chain at retained event anchors
and adaptive vertices. `SatelliteExactTrackLayer` and
`SatelliteExactTrackEventsLayer` consume that immutable evidence through existing
coordinate and kernel geometry services. A singleton has no invented segment;
event labels/path controls do not alter sampling. Drawing never repropagates a
solved track. Equal native/product specifications retain the existing identity
path; changed representations consume the returned coordinate result/refusal.

`FreshSubprocessMatrixExecutor` reconstructs a validated offline snapshot/query
and uses the existing exhaustive or accelerated owner in a fresh process. Strict
request/result/evidence hashes and publication contracts remain unchanged. The
small synthetic snapshot worker test does not execute the historical medium
production benchmark or renew consumed execution authority. No new public API,
serialized schema, numerical model or package is added.

## Satellite report consumers

`ExactSatelliteCrossingReport.from_results()` accepts ordered immutable
`MultiFieldCrossingResult` values and the explicit batch policy, creation time
and implementation identities. It validates snapshot/element, observer, field,
interval, airmass and acceleration context, then stores canonical compact JSON.
`document` returns a detached copy. `to_json`/`from_json`, `to_ecsv`/`from_ecsv`
and `to_votable`/`from_votable` preserve the same logical identity. The private
`_satellite_tabular_reports` owner derives the fixed columns from the existing
schema; ECSV masks and VOTable Unicode null indicators retain explicit nulls.
These interfaces consume solved records; they do not query physical states.

`cli.satellite_crossings.run()` loads and validates the selected local snapshot,
constructs typed queries and the existing `MultiFieldSatelliteCrossingCoordinator`,
and runs complete current validation before solving. `main()` exposes direct,
initial-request and validated-request modes with the retained status mapping.
An invalid initial file request publishes an ordered validation partition and
explicit derived subset; it never silently executes that subset. A separate
validated-request call checks its signed content and current validation again.
The existing report bundle includes JSON, ECSV, VOTable and a digest-bound file
manifest. Round trips precede staged writes and the no-replace rename; failure
cleanup removes only the owned staging directory.

`SatellitePlanningAdvisory.from_report()` takes a validated report and an
`ObservatoryPlanningContext` of `PlanningObservationUnit` values. It preserves
planning-unit/report visit order and exact report/snapshot/field identities,
computes the retained half-open interval intersection and emits detached,
canonical advisory JSON. Only the existing general profile version 1 is
supported. Illumination, brightness, detector effect and operational disposition
remain unknown; no facility system is contacted or modified.

K3.34 adds service-value/refusal and actual bundle/interchange/advisory evidence
in the existing test owners. No API, numerical model, schema or production
module changes. The [satellite guide](satellite_guide.md#17-exact-crossing-reports)
retains the scientific report contract.

## Satellite illumination and shadow services

`SatelliteIlluminationGeometryEvaluator(source, policy=None)` retains its typed
`SatelliteTopocentricState` input and same-instant geometric Earth-to-Sun request.
`SatelliteShadowTransitionFinder(source).find(query)` retains its observer-free
`SatelliteShadowTransitionQuery` and directed resource-bound event records.
Both constructors adapt known resolved Skyfield Sun sources with the existing
`KernelEphemerisStateSource`. Injected custom protocols and existing adapters
remain supported; no new public interface or wrapper protocol is added.

The adapter supplies returned geometric ICRF/Earth-centred Cartesian values,
converted through the existing AU protocol and accepted ITRS/EOP orientation.
It introduces neither light time nor apparent corrections. Each Sun request
retains exact UTC input, source/resource identity, target/centre IDs and the
adapter's existing provenance. The adapter borrows the source and never closes
its owner. Changed borrowed source identity or failed evaluation refuses; no
cross-call state cache suppresses the current query.

The finder uses public SGP4 propagation at every evaluated instant. Both original
SGP4 status failures and kernel failures are exposed through
`SatelliteIlluminationGeometryError` with `PROPAGATION_FAILURE`, preserving the
cause. Existing Sun-source and EOP error codes remain authoritative. Finite
visible-disk quadrature and continuous contact-margin root search retain their
separate algorithms and original tolerances. Event completeness remains bounded
by the existing admitted envelope and fail-closed search limits.

No report schema, renderer, public export or resource bytes change. The focused
gate retains analytic overlap/contact, independent observer altitude and
adversarial transition tests, and requires a real offline Sun-source parity case
on the Mac. Source-free custom-protocol geometry remains compatible. Radiometry
resource metadata, reflected light and paused Moonlight work remain separate.

## Solar radiometry resource admission

`DirectSolarIrradianceEvaluator` and `DirectSolarSpectralIrradianceEvaluator`
consume the existing `SatelliteIlluminationGeometry`. Accepted distance and
uniform-disk visible fraction control the retained scalar/array scaling. No
state query is needed for these already evaluated values. The nominal
bolometric 1361 W/m² at 1 au remains separate from the TSIS native spectral
integral and its finite wavelength coverage.

`data/solar_spectral_resource_tsis1_hsrs_v2.json` owns the existing edition label,
DOI/product/source URL, historical access date, byte count/SHA-256, exact header,
units, count/endpoints/spacing/resolution, audit integral and unresolved
redistribution status. The current radiometry owner decodes a closed version-1
metadata object, rejects duplicate/non-finite/malformed facts and validates the
supported units and consistent grid before creating a private frozen record.
The existing `TSIS1_HSRS_V2_*` names remain value-compatible aliases, and
`SolarSpectralIrradianceResourceIdentity` retains its public fields/signature.
Its defaults mirror the admitted record. Source-derived provenance text remains
unchanged in meaning and output.

`load_solar_spectral_irradiance_resource(path)` still admits only the exact
external CSV bytes and then invokes the unchanged parser. Native-grid energy
integration, explicit off-grid refusal, pointwise uncertainty scaling and
`not_evaluated` integrated uncertainty remain unchanged. The metadata file is
packaged using existing JSON build rules; wheel/sdist and isolated import tests
verify its exact bytes and fail if it is absent. There is no fallback resource,
CSV vendoring, acquisition, new source edition or kernel/SDK API.

## Public consumer and teaching surfaces

The existing `wenu.__all__` facade resolves all 290 declared exports; shared
geometry/projection aliases remain the same kernel class objects. This does not
make astronomical directories independently installable or freeze the facade.

| Installed command | Existing application owner | K3.37 acceptance route |
|---|---|---|
| `wenu_chart` | `cli/chart.py`, public view/request composition | Installed help, existing three-stage delegate/configuration tests |
| `wenu_design_atlas` | `cli/atlas.py::design_main` | Installed help; retain K3.21 design/publication receipt |
| `wenu_plot_atlas` | `cli/atlas.py::plot_main` | Installed help; retain K3.21 sheet/output receipt |
| `wenu_create_atlas` | `cli/atlas.py::create_main` | Installed help; retain K3.21 batch/worker/output receipt |
| `wenu_retrieve_comets` | `cli/comets.py` | Installed help only; retain K3.29 provider/CLI receipt, no acquisition |
| `wenu_satellite_crossings` | `cli/satellite_crossings.py` | Installed help; retain K3.34 direct/two-call report receipt |
| `wenu_examples` | `cli/examples.py` | Actual installed copy/skip/force and six script help paths |
| `wenu_notebooks` | `cli/notebooks.py` | Actual installed copy/skip/force, five relative paths/bytes |

Six examples keep their accepted requests and public service delegation. View
construction now releases its observer on refusal; callers still own observers
after successful `chart_view()`. `generate()` releases it after product setup or
drawing. Packaged example copies remain byte-identical.

Five notebooks retain filenames and intended La Ligua/local date (2026-08-15
21:00), stereographic east-west reversal, magnitude 5.5 for first-chart or 6 for
publication, and constellation/reference requests. First-chart notebooks explicitly retain
`of_date` references; publication notebooks use the canonical J2000 default.
Retired renderer recipes are
replaced by explicit atlas/print requests through `get_chart_view()` and
`draw_chart_view_from_arguments()`. Current canonical style/export replaces
manual artist styling, hard-coded projection radius, debug introspection and
repeated save calls. This is a runnable teaching migration, not pixel parity
with a broken historical notebook. English/Spanish folders now select their
respective language. Cells ship without stale outputs and release observers on
failure. Open the reported PNG; rerun from the first cell after editing settings.

Existing strict configuration overlays, named preset protocols, family/CLI
precedence, style/detail/product translation and immutable generated-label
dictionary remain unchanged. The installed-resource test compares exact bytes,
builds a wheel from the sdist and runs generated scripts under `-I -S` without
checkout access or network. Numerical/product receipts remain with their owners.

## Maintenance and resource consumers

The migration inventory explicitly classifies all 93 K3.38 paths:
86 operational Python tools and seven resource/acquisition/build
owners. The classification records responsibility, not blanket run authority.

| Responsibility | Existing examples | Boundary |
|---|---|---|
| Source maintenance | Hunt/Dias union, observing membership, Wikidata compilation, curation and criteria pages | Source metadata, IDs, masks, selection and exact bytes; source-native crossmatch/layout stays here |
| Explicit acquisition/preflight | `minor_body_acquisition`, snapshot acquisition, SatChecker, query/acquire/install tools | Existing provider policy, receipts, byte/identity admission and offline cache boundaries; no rendering-time acquisition added |
| Build/resource | `resources.py`, `curated_catalogue_packaging.py` | Same admitted manifest drives copying; build source loader avoids application/numerical imports |
| Application review | Zodiac/polar/atlas rendering adapters and report tools | Existing public composition, coordinate/state or kernel geometry services |
| Independent validation/fixtures | `validate_*`, captured or constructed fixture builders | Preserve raw/reference comparison legs and original evidence domains |
| Manual benchmarks/development | Benchmark scripts, OpenAI diagnostic/translation utilities | Explicit standalone work; no historical execution authority revived |

Zodiac pole/centre transformations use `CoordinateService.transform_skycoord()`
with the original mean-ecliptic J2000 pole, vacuum AltAz observer and FK5 J2000
centre label. Returned typed longitudes/latitudes control the retained SkyCoord
compatibility result, target-up angle and formatted Spanish title. Refusal is
propagated through the review request, with observer cleanup. No transform
formula, source reference, output style or selection changes.

`benchmark_reusable_sphere.py` now registers observer close callbacks as each
construction succeeds. Later construction/view failure releases all prior
resources; one failed close does not prevent other cleanup attempts. Timing,
view matrix, export and cache-report computations are unchanged. Tests exercise
synthetic failures only, not the production benchmark.

Build admission remains a direct source load of stdlib-only `resources.py`.
The returned manifest selects the exact files copied, and source corruption
must refuse before replacing a prior publication. This resource contract does
not interpret catalogue rows or claim physical precision. Existing installed
wheel/sdist acceptance from K3.37 remains applicable to unchanged build rules.
`openai_model.py` performs a remote model-list request if imported; it is an
external development utility, not imported or executed by this audit/gate.
No provider acquisition or present-day permission is certified here.

## Geometry and graphics consumer boundary

K3.39 inspects 48 unchanged source owners, pinned under
`geometry_rendering_routing.owners` in the migration inventory. No new API or
implementation is introduced. The existing boundary is:

| Responsibility | Existing owner / public route |
|---|---|
| Records, alignment, topology, domain and clipping | `wenu_kernel.geometry`; identical `wenu.geometry` and preparation mathematical aliases |
| Stereographic, polar equidistant, Mollweide | `wenu_kernel.projections`; identical Wenu public classes |
| Guarded chart orchestration | Regional/full-sky viewport guard, all-sky coordinate/map route, polar face-cap/latitude route, then `CelestialSphere.draw_chart` |
| Appearance preparation | `wenu.rendering.preparation`: supplied magnitudes/diameters, viewport marker margin, style and label offsets |
| Graphics | `MatplotlibRenderer` and helper leaves consume projected records, with backend clipping/label layout |
| Furniture | Application reference grids use appropriate coordinate/projection services; legends reuse rendered geometry; footer uses resolved strings |
| Export | `export_composed_chart` / `ExportOptions.save`, chart/SVG semantic documents and one save per output |

New seams force altered guard/projection returns and failure after success, so
recomputation, bypass or stale first-draw reuse fails. Three explicitly synthetic
prepared scenes use each real projection and produce PNG/PDF/SVG, preserving
point IDs/missing rows, label text, areas, viewport and physical page size.
After projection, coordinate transforms, kernel state evaluation and further
projection calls are forbidden during renderer/footer/semantic/export execution.
These scenes verify graphics composition, not source or observational accuracy.
Existing numerical/topology, physical label/tick/band, legend single-save and
semantic-vector contracts remain in their original test owners. Coordinate
meaning is unchanged; the coordinate guide remains current. No new geometry
query, renderer algorithm, schema, dependency or astronomical package is added.

## Complete consumer reconciliation

`consumer_reconciliation` in the migration inventory is the current K3.40 view.
Its per-file source blobs and source/import/call review map the complete present
census to accepted service routes and bounded receipt IDs. It supersedes stale
current-status wording in historical per-slice records without erasing those
original results, failed runs, retries or limitations.

| Surface | Reconciled evidence |
|---|---|
| 274 production + 22 kernel + 86 tools + six source examples | 388 exact source identities, purpose, responsibility and appropriate route; packaged copies counted within production |
| 290 root Python exports and 20 declared export modules | Exact declared names, owning modules and runtime identity/resolution |
| Eight commands and five notebooks | Current pyproject target/owner and exact notebook identities; retain accepted installed-command/resource/cell evidence |
| K3.01–K3.39 | Original bounded records, delivery PR/head/merge and retained Mac acceptance, with KG/AX service evidence only where already adopted |
| 21 sensitive scientific call expressions | Raw provider/state/coordinate ownership or explicit public delegation; import adjacency alone is not numerical proof |

Source processing, build copying, independent numerical oracles and explicit
acquisition remain distinct from application state consumers. Geometry services
do not query fictitious physical objects. Custom injected protocols and the
legacy geometry fallback remain their existing documented compatibility routes.
The audit found no production correction to implement.

The original KG.07 full Mac gate total is not present in the persistent record.
The ledger preserves that distinction: original local component/isolation and
unchanged core receipts, accepted K3.16 real atlas/four-polar cold/restored
outputs, and K3.39 missing-row/strict-domain/alias checks supply the affected
scopes. It does not assert an unobserved 103-case Mac run.

Unqualified physical source/model facts, unpropagated stellar lookup, honest
legacy snapshot interpretation, satellite exact-versus-candidate/visibility
domains, synchronous ownership, unknown errors and bounded reuse remain explicit.
No SDK freeze, new acquisition/model, astronomical package extraction or Gaia
activation follows from K3.40. The separate six-product review is the agreed
next acceptance step before Gaia; exact requests/resources are resolved then.

The consumer-reconciliation Mac gate also retains the original LMC boundary
composition case that was locally blocked by missing DE440s in KG.07. It uses
the already installed offline resource; no acquisition or full lower-level
gate repeat is part of this reconciliation.

