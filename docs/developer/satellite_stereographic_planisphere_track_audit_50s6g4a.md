# 50S.6G.4A stereographic planisphere exact-track audit

**Status:** documentation-only candidate for Fernando's separate scientific and architectural acceptance
**Milestone:** 50S.6G.4A
**Baseline:** `00033b717e5b41471b618a0a2a87ec7dae65e7ac`
**Date:** 2026-09-19

## Decision sought

This audit proposes the smallest scientifically honest integration of accepted
50S.6G.3A exact local satellite-track evidence with Wenu's paired physical
polar planisphere when `projection_name="stereographic"`. It resolves the
coordinate domain, two-face placement, overlap, cap clipping, horizon and mask
separation, orientation, event labels, lifecycle, provenance, and acceptance
evidence before any runtime work.

This candidate authorizes no implementation. Fernando's separate scientific
and architectural acceptance is required before changing runtime, style,
tests, or specimen tools.

## As-is findings and product identity

Wenu currently has two different products that use the word planisphere:

- the ordinary `ChartRequest(family="planisphere")`, which constructs one
  observer-horizontal `FullSkyChart`; and
- `PolarPlanispherePairRequest`, which resolves matched north and south
  equatorial celestial disks and may select either polar azimuthal equidistant
  or stereographic projection.

50S.6G.4A concerns only the second product, with
`projection_name="stereographic"`. It does not authorize satellite tracks on
the ordinary horizontal full-sky planisphere, polar azimuthal equidistant
disks, `CircumpolarChart`, Galactic `AllSkyChart`, pouch-sheet compositions, or
other all-sky products.

The accepted physical pair owns opposite paper right-ascension direction,
matched declination limits, a forty-degree default overlap, exact circular
face boundaries, calendar and registration geometry, and independent
north/south exports. `PolarPlanisphereChart` already projects equatorial
geometry and clips curves to each face's declination cap. The page export owns
two canonical face exports and one final save per face.

The accepted 50S.6G.3B integration is not directly reusable as a coordinate
policy. Regional and binocular charts transform the complete time-varying
track into one horizontal product frame at the field reference instant. A
polar planisphere is instead an equatorial celestial disk. Reapplying the 3B
horizontal transformation would give the wrong product meaning.

## Bounded scope

50S.6G.4A is limited to a future implementation that:

- reuses `SatelliteExactTrackDisplayRequest` and already-realized
  `ExactLocalSatelliteTrack` evidence without solving, propagating, or
  resampling;
- admits only a resolved `PolarPlanispherePair` whose two faces use
  stereographic projection;
- installs accepted path and event views once for the paired export and removes
  them after both faces complete or any failure occurs;
- preserves each retained geometric topocentric direction in the fixed
  GCRS/ICRS axis orientation for equatorial-disk projection;
- projects the same immutable evidence independently through the accepted
  north and south face projections and cap clipping;
- reuses existing exact-track style roles, semantic identities, renderer, and
  PNG/PDF/semantic-SVG exporters;
- adds bounded event-specific site/time provenance to each face; and
- supplies focused coordinate, face, clipping, lifecycle, semantic, export,
  and state-isolation evidence plus physical visual specimens.

It excludes every new scientific evaluation, provider access, snapshot or
report/CLI change, ordinary full-sky/circumpolar tracks, visibility,
illumination, brightness, detector effects, scheduling integration, physical
horizon filtering, occultation, and unrelated refactoring.

## Scientific meaning: an event-specific overlay

An exact local track is observer-dependent and valid only between its declared
entry and exit UTC instants. A reusable polar planisphere normally represents
the celestial sphere for arbitrary rotations of date and time. Printing a
satellite track on that disk must not imply that the satellite repeats the
track on another day or whenever the disk is rotated to the same sidereal
orientation.

The future product is therefore an **event-specific planisphere overlay**. It
shows one solved local visit against the equatorial celestial disk and is valid
only for the stated site, coordinate-reference instant, and entry-to-exit UTC
interval. Each exported face must expose that limitation in bounded provenance
and in inspectable page text or accompanying specimen metadata. The product is
not an ephemeris, recurrence prediction, visibility forecast, or reusable
daily planisphere state.

## Coordinate contract

Every accepted 3A sample is a geometric topocentric direction evaluated at its
own UTC instant and expressed in fixed GCRS axes. The collection
`CoordinateSpec` is timeless; `sample_time_scale="utc"` and the ordered sample
instants carry time.

For a stereographic polar face, those fixed-axis longitudes and latitudes map
directly to equatorial right-ascension-axis orientation and declination. A
future integration must use the governed `CoordinateService` seam to express
`gcrs-axes` as `icrs` axes while preserving:

- `origin="topocentric-direction"`;
- `PositionStatus.GEOMETRIC`;
- timeless collection meaning;
- per-sample UTC instants in evidence metadata; and
- the original track identity and provenance.

It must not route the track through AltAz, recompute a direction at the chart
instant, apply apparent-place corrections, or relabel the geometric evidence
as astrometric, apparent, or observed.

The polar chart's projection adapter must make this decision from typed
coordinate meaning, not from a satellite-layer class check. Existing
observer-local sky layers retain their current observer-to-equatorial route;
already fixed equatorial-axis geometry retains its own origin and position
status. This is one canonical pre-projection boundary, not a satellite-specific
projection or a second rendering pipeline.

## Admission

A future paired exact-track export is valid only when all of the following
hold:

- the pair contains one south and one north `PolarPlanisphereChart`;
- both faces select `projection_name="stereographic"` and equatorial
  coordinate-frame geometry;
- the pair's limits, scale, handedness, boundary, and registration invariants
  already pass `PolarPlanispherePairRequest.resolve()`;
- every display value is a valid `SatelliteExactTrackDisplayRequest`, at least
  one of `draw_path` or `draw_events` is true, and `label_events` requires
  events;
- no `track_identity_sha256` occurs more than once;
- every track observer longitude, latitude, elevation, vacuum-refraction
  policy, and Earth-orientation policy match the supplied page observer;
- the page observer UTC instant equals every crossing field's declared
  coordinate reference instant;
- all tracks retain the accepted timeless `gcrs-axes` /
  `topocentric-direction` geometric collection and UTC sample contract; and
- multiple visits share the admitted observer and reference instant.

Validation of the complete tuple and both faces occurs before any layer is
installed or output path is written. No invalid or mismatched track is
silently dropped.

## Proposed request and lifecycle seam

`SatelliteExactTrackDisplayRequest` remains the sole display-control value;
50S.6G.4A proposes no competing polar-specific track request. A future bounded
API may add an explicit default-empty
`satellite_exact_tracks: tuple[SatelliteExactTrackDisplayRequest, ...] = ()`
keyword to `export_polar_planisphere_pages(...)`.

The paired export validates once, installs one path layer and/or event layer
per display in supplied order, exports both faces, and removes only those
layers in reverse installation order. Cleanup occurs after success, south-face
failure, north-face failure, furniture failure, or save failure. A supplied
maximal sphere retains no satellite layer, label state, style state, evidence
reference, or selection after return.

The implementation may extract a shared science-free layer installer from
`charts/request_satellite_tracks.py`, but regional/binocular admission and
paired-planisphere admission remain separate explicit validators. The export
must not construct a synthetic `ChartRequest` merely to reuse 3B validation.

## Faces, overlap, and cap boundaries

The same immutable path is projected independently on both faces. Existing
declination-cap clipping owns placement:

- geometry inside only one face appears only there;
- geometry in the configured overlap appears on both faces intentionally;
- a connected visit crossing a limiting declination is clipped at that face's
  exact circular boundary and continues on the other face where admitted; and
- an event marker appears on every face whose closed cap contains its retained
  event vertex.

Overlap duplication is not a second visit and must preserve the same
`track_identity_sha256`, UTC interval, and event role. Separate face documents
may retain identical semantic visit paths. Any later composition that places
both faces in one SVG document must qualify document-local SVG IDs by face
without changing scientific semantic identity; such a combined composition is
not implemented by 50S.6G.4B unless separately accepted.

Cap clipping may create a graphical path endpoint but never a scientific
entry or exit event. The integration must not synthesize an event, extrapolate,
interpolate, smooth, close, or join visits at a face boundary.

## Longitude continuity and orientation

A polar stereographic disk has no physical right-ascension cut from pole to
rim. A connected spherical curve crossing 0/360 degrees remains connected and
must not acquire a false long chord or split solely because longitude wraps.
Focused geometry evidence, rather than a distorted visual specimen, must
verify wrap continuity and declination-cap clipping.

The paired charts already own opposite paper right-ascension direction. The
track is not mirrored, reordered, or reversed before projection. Each face
projects the same ordered entry-to-exit evidence through its own accepted
handedness. Event roles and UTC ordering remain attached to retained samples
even when their paper direction differs between faces.

## Horizon, masks, and physical furniture

The physical horizon and pouch are observer-local moving furniture over an
observer-independent celestial disk. They do not own satellite science and
must not clip, mask, admit, reject, or reinterpret an exact track under this
milestone. The track remains a geometric result even where it would lie below
a chosen horizon setting. No horizon, Earth-occultation, illumination, or
visibility claim is added.

Constellation outside masks, catalogue detail selection, label curation,
calendar rings, cut lines, and page furniture also do not alter track evidence.
Only the face's accepted declination cap and final circular clip boundary may
clip path or event presentation. Page furniture remains drawn through the
existing additional-furniture stage before the single canonical save.

## Events and labels

The accepted display controls retain their 3B meaning:

- `draw_path` displays the accepted open connected-visit curve or singleton;
- `draw_events` selects exact entry, closest-approach, and exit vertices; and
- `label_events` enables the accepted English labels `entry`,
  `closest approach`, and `exit` without changing marker geometry.

Labels are presentation annotations. A label whose event lies outside one
face is absent from that face; a retained event in the overlap may be labeled
on both. The implementation may use the existing polar radial text-orientation
and interior-boundary preparation rules, but it must not move an event marker,
change a role, place text in the calendar ring, or infer a missing event at a
clip intersection. Timestamps on individual markers, collision optimization,
leader lines, Spanish event labels, and along-track ticks are deferred.

Each face must nevertheless carry a concise product-level validity statement
naming the site and complete UTC interval. This statement is page/provenance
furniture, not evidence geometry or an event label.

## Style, semantics, and provenance

Existing exact satellite path, event-marker, and event-label style roles
remain authoritative. Polar adaptation may change only appearance required for
legibility on the physical atlas palette. It cannot change samples, roles,
coordinates, face admission, clipping, identity, or product validity.

The accepted semantic family remains:

- `sky/artificial_satellites/exact_local_tracks/<visit_key>/track`;
- `sky/artificial_satellites/exact_local_tracks/<visit_key>/events`.

Projected pieces retain the visit identity after cap and viewport clipping.
Event markers and labels remain descendants of the event identity. Exact
tracks remain distinct from SatChecker sampled candidates and Solar-System
tracks.

Each face's semantic SVG and bounded export provenance records the supplied
order and, for every display:

- `track_identity_sha256`;
- NORAD catalog ID and display name;
- field ID;
- observer scientific identity;
- coordinate reference instant;
- entry, closest-approach, and exit UTC instants;
- snapshot SHA-256;
- face and limiting declination;
- `draw_path`, `draw_events`, and `label_events`; and
- the event-specific non-recurrence limitation.

The export must not recursively serialize samples or the full exact evidence
object. Filenames, page size, calendar layout, atomicity, overwrite behavior,
and existing PDF metadata remain owned by current exporters.

## Empty, multiple, and failure behavior

- An empty tuple produces byte-equivalent ordinary paired output modulo no new
  provenance field and installs no layer.
- A zero-duration exact visit remains a singleton with explicit coincident
  roles; no segment is invented.
- Multiple satellites and multiple visits of one satellite are allowed when
  identities are unique and the complete admission context matches.
- A validation failure produces no installation and no output.
- A failure after installation removes every request-owned layer.
- A south-face success followed by north-face failure follows existing paired
  export failure behavior; the integration adds no rollback claim for an
  already committed face.
- No face-selection, clipping, or label failure may mutate evidence.

## Acceptance evidence for a later implementation

50S.6G.4B must provide all of the following before implementation acceptance:

1. deterministic offline north and south stereographic polar-face specimens
   generated from one physically propagated accepted exact visit;
2. PNG, PDF, and semantic SVG for both faces through the canonical paired
   export and single-save paths;
3. visible site and complete UTC validity text and bounded semantic-SVG
   provenance on both faces;
4. physical visual review of track direction, handedness, overlap duplication,
   event markers, labels, celestial context, and calendar-ring clearance;
5. focused tests for complete pre-install validation, observer/reference
   admission, fixed-axis geometric status preservation, two-face projection,
   intentional overlap, limiting-declination clipping, 0/360-degree
   continuity, no synthetic boundary events, cleanup, state isolation,
   semantics, and bounded provenance;
6. unchanged-output evidence for an empty track tuple;
7. the current documentation gate, relevant polar/exact-track/export tests,
   and the complete plugin-disabled repository suite; and
8. diff, whitespace, exact-head, branch-synchronization, and clean-tree checks.

A physical short pass need not demonstrate every cap, overlap, and longitude
edge case in one image. Canonical synthetic geometry tests and physical visual
specimens are complementary evidence; the specimen must not distort accepted
track science merely to exercise a boundary.

The coordinate-system guide requires Fernando's scientific and pedagogical
review because this milestone adds a new equatorial presentation of existing
geometric topocentric directions, even though it adds no new coordinate
calculation.

## Proposed implementation placement

No production file is authorized by this audit. If accepted, the smallest
implementation should keep responsibility with existing owners:

- `charts/request_satellite_tracks.py`: reusable science-free display
  validation, layer installation, bounded summaries, and cleanup support;
- `charts/polar_planisphere.py`: typed equatorial pre-projection handling and
  existing cap clipping only;
- `charts/polar_page_export.py`: explicit paired admission, shared lifecycle,
  face provenance, and event-specific page validity text;
- `sky/satellite_exact_track_layer.py`: retained-evidence path/event views;
- existing style components, semantic identity, renderer, furniture, and
  exporters: unchanged ownership; and
- existing durable exact-track and polar chart/export test files, extended
  rather than replaced by milestone-named runtime tests.

No new projection, satellite science, renderer, exporter, report, CLI, or
provider module is justified.

## Exclusions and next authority

This candidate does not authorize 50S.6G.4B implementation. It also does not
authorize ordinary full-sky or circumpolar satellite tracks, polar azimuthal
equidistant satellite tracks, combined-face or pouch-sheet satellite output,
new report or CLI fields, provider access, another real catalogue execution,
visibility, sunlight, solar Earthshine, moonlight, lunar Earthshine,
photometry, brightness, detector effects, observatory scheduling adapters, or
50S.7/50S.8 work.

If Fernando accepts this audit, only the bounded 50S.6G.4B implementation and
the evidence listed above become authorized. Merge, later science, and program
closure still require separate decisions.
