# Wenu implementation reference

**Implemented baseline:** `6708f54a`. This is an entry-point reference, not a
forward API specification. [Source map](source_tree.md) and
[scientific contracts](scientific_contracts.md) supply the detailed owners.

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

## Native stellar kernel adapter

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
`Stars.native_positions(identifiers)` queries explicit HIP IDs from the full
source table (or the stable table for constructed legacy objects without one).
Available rows retain source order, IDs, photometry, designations and NaNs;
absent IDs are omitted for the consumer's missing-ID policy. Empty selections
avoid a query. Both APIs prefer authoritative `ra_degrees`, with hours × 15
only for hours-only constructed inputs, avoiding a redundant floating-point
round trip. Neither mutates active marker selection.

Native `ConstellationLines.realize` requests the loaded graph's vertex IDs
through `native_positions`, then joins returned IDs to the original edge order.
This preserves faint endpoints, warning/gap policy and global resolvability
metadata without evaluating unrelated catalogue stars. Returned kernel vectors
control endpoints; refusal is not replaced by raw catalogue coordinates.
Observed astrometry and native constellation-label anchor calculation remain
legacy consumers. No claim of all-consumer kernel closure follows.

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
resource metadata gaps and shared helper defaults remain explicit audit findings.

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
`stellar_state.py` remains a native stellar facade; its descriptor/resource
identities, required source epochs and returned states are preserved. Galaxies
do not import a concrete stellar provider.

The galaxy model keeps fixed native directions. Full source metadata and digest
are bound into the derived resource identity. A source epoch with an admitted
explicit scale is retained as a TimePoint; an unqualified date is preserved in
metadata but refused for numerical kernel admission, never assigned a scale.
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

This API is explicit and additive. `OpenClusters.position`, native/observed chart
routes, saved skies and the active v0.2 selector still use accepted source lookup.
Chart/snapshot adoption remains a separate next slice with its own
consumer/failure gates. The independent numerical oracle uses scalar-trig
initial conditions and ERFA PV updates, plus an analytic perspective case, rather
than calling the production differential conversion to construct expected data.
The installed-wheel test exercises the actual provider/kernel while checking that
importing it does not change the fixture's default cluster lookup.

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
