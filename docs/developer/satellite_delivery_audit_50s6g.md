# 50S.6G representative delivery, report, file, and exact-track audit

**Status:** Accepted documentation-only architecture, API, performance,
interchange, CLI/file, and chart-delivery audit.

**Base:** accepted 50S.6F at merge commit `83a1018`.

**Runtime effect:** None. This audit changes no executable behavior, public
command, accepted snapshot domain, report output, or chart output.

## 1. Purpose

50S.6F answers one bounded scientific question: for one observer and an
ordered set of independently timed circular fields whose centres remain below
the configured airmass ceiling, which installed-snapshot satellites cross each
field? It deliberately remains inside the three-record synthetic snapshot and
60-second per-field domain.

50S.6G must deliver that exact geometric result beyond the developer API. It
must establish representative snapshot use, canonical machine-readable
reports, explicit CLI and file-input behavior, renderer-neutral exact track
evidence, and chart integration without creating a second propagation,
coordinate, projection, rendering, or export pipeline.

This audit decomposes that work into independently accepted slices.

## 2. As-is assessment

The accepted repository already provides:

- immutable canonical OMM records and digest-verified installed snapshot
  manifests in `satellites/snapshots.py`;
- the independently callable exhaustive 50S.5 oracle and the opt-in accepted
  50S.6D conservative coordinator;
- the accepted 50S.6F atomic same-observer multi-FoV coordinator, ordered
  failures, centre-only complete-interval airmass certification, and
  execution-only chunking;
- provider-neutral `SatelliteCrossingResult` values containing entry, closest
  approach, exit, minimum separation, range, angular rate, provenance, and
  warnings;
- a versioned deterministic JSON report for SatChecker sampled-candidate
  evidence in `satellite_presentations.py`;
- shared `SkyLayer` implementations for SatChecker sampled candidate tracks
  and points, with stable semantic SVG identity;
- the canonical spherical-geometry, projection, chart-preparation, renderer,
  semantic-SVG, and PNG/PDF/SVG export flow;
- one ordinary `ChartRequest` boundary that intentionally rejects artificial
  satellites from the Solar-System track contract.

The repository does not yet provide:

- an explicit external immutable satellite-snapshot directory loader;
- a policy-governed representative snapshot builder or admitted
  representative catalogue;
- a canonical exact-crossing report model or JSON/ECSV/VOTable encoders;
- a multi-FoV CLI or file-input schema;
- the accepted validation-output file and second-call workflow;
- drawable exact local crossing samples linked to exact crossing events;
- ordinary chart-request integration for artificial-satellite tracks;
- representative-scale equivalence, resource, or useful-speed evidence.

These absences are real responsibility seams. They must not be hidden inside
`crossing_batch.py`, `ChartRequest`, a renderer, or an exporter.

## 3. Scientific and product boundary

50S.6G retains every accepted 50S.6F invariant:

- one observer per batch;
- any non-empty ordered number of uniquely identified circular FoVs;
- independent inclusive UTC intervals and exact-solver tolerances;
- field-centre-only geometric vacuum airmass admission over each complete
  interval, with configurable `X_max` defaulting to 2;
- atomic validation before any crossing solve;
- exact equivalence to independent exhaustive 50S.5 results;
- full NORAD identifiers and immutable snapshot identity;
- geometric crossings retained independently of illumination or brightness.

The FoV radius still does not enter airmass admission. A geometric track does
not claim visibility. Horizon removal, Earth occultation, illumination,
apparent magnitude, detector contamination, scheduling decisions, and
observatory writes remain outside 50S.6G.

## 4. Representative snapshot admission

Representative scale must not mean implicit network access or an unverified
mutable catalogue. The runtime seam is an explicit caller-selected snapshot
directory containing one manifest and canonical OMM records. Loading must:

1. resolve no network resource;
2. validate schema, file names, record count, canonical bytes, digest, unique
   full NORAD identities, ordering, epochs, and supported SGP4 regimes;
3. retain source identity, source URL, acquisition instant, provider-policy
   URL and check instant, builder identity, warnings, and content digest;
4. publish no partially validated snapshot object;
5. leave the installed three-record snapshot as the fast deterministic test
   oracle rather than packaging a large mutable catalogue in Wenu.

Acquisition is a separate developer/CLI preflight. It may make at most one
supported bulk request, must inspect the provider policy before access, and
must validate and atomically publish an immutable directory before ordinary
offline calculation begins. No per-object requests, polling loop, parallel
downloads, automatic retry, credential capture, or runtime fallback is
accepted.

No public catalogue-size maximum is chosen by documentation. Admission must
be evidence-based. The representative matrix contains:

- catalogue tiers: synthetic three-record oracle, a policy-cleared medium
  specimen, and one policy-cleared full supported snapshot when practical;
- FoV counts: 1, 2, 5, 10, 20, and, when practical, 50;
- interval relationships: disjoint, partially overlapping, and identical;
- central, grazing, between-sample, near-zenith, boundary-time, seam, and
  no-crossing cases;
- cold and warm runs reported separately, with time, peak memory, evaluated
  records/states, fallback counts, and exact-result equality.

Useful-speed or shared-state-reuse claims require measured material benefit.
Chunk size remains an execution choice, not a public cardinality limit.

## 5. One canonical crossing information model

The canonical logical report is immutable, versioned, deterministic, and
independent of serialization. It contains:

- schema/product version and creation instant;
- Wenu version and implementation identities;
- complete observer and Earth-orientation identity;
- snapshot manifest identity and content digest;
- batch policy, `X_max`, chunk policy, and exact numerical tolerances;
- ordered field definitions, intervals, centre-airmass evidence, warnings,
  and zero-crossing summaries;
- for every visit: stable field identity, full NORAD identity, element epoch,
  entry, closest approach, exit, minimum separation, time in field, range,
  angular rate, convergence/acceleration evidence, warnings, and provenance;
- optional ordered exact-track samples with UTC instant, declared coordinate
  specification, direction, range, interpolation prohibition or policy, and
  sampling-tolerance evidence.

Missing future quantities are explicit `null`/masked unknowns, not zero,
false, or empty scientific claims. Illumination, flux, magnitude, detector
effect, and observatory scheduling fields are not invented in 50S.6G.

JSON is the canonical nested exchange and must ship with a versioned JSON
Schema. UTF-8, finite JSON numbers, stable ordering, deterministic formatting,
and atomic file publication are required.

Astropy ECSV is a lossless unit-aware tabular encoding of the same logical
model. One table uses an explicit record-kind discriminator for batch, field,
crossing, and optional sample rows so that fields with zero crossings remain
representable. Units, masks, schema version, provenance, and stable identifiers
are mandatory.

IVOA VOTable is a lossless astronomical interoperability encoding. It may use
one RESOURCE with separate field, crossing, and sample TABLE elements joined
by stable identifiers. FIELD units, datatypes, null behavior, TIMESYS, and
coordinate metadata must be explicit and round-trip validated.

Plain CSV is only an explicitly lossy convenience view. CCSDS OEM describes
orbit ephemerides rather than Wenu crossing semantics and is not a required
50S.6G deliverable. No encoder may recompute scientific results.

## 6. CLI and file-input failure contract

Python calls and direct CLI argument mode are atomic: validate the complete
batch, report every ordered field failure, return no partial crossing result,
and perform no crossing solve after any validation failure. CLI failure uses a
non-zero exit status and a concise diagnostic.

File mode is also atomic, but implements Fernando's accepted two-call
workflow:

1. An initial versioned JSON request file contains one observer, snapshot
   reference/digest, batch policy, and an ordered non-empty `fields` array.
2. Syntax, schema, path, snapshot, observer, interval, tolerance, unique-ID,
   coordinate, and complete-interval airmass validation run for every field
   before crossing work.
3. If every field is valid, calculation proceeds and no validation-output file
   is required.
4. If any field is invalid, no field is solved. Wenu atomically writes one
   separate versioned validation-output JSON file and exits non-zero.
5. That file preserves the source digest and field order, marks every invalid
   field with stable code and message, and embeds the ordered valid subset as a
   complete derived request.
6. Supplying the validation-output file in a second explicit invocation selects
   that embedded valid request, revalidates it against the current snapshot and
   policy, and calculates only those valid FoVs.

The validation-output file is therefore both an audit record and a valid
second-call envelope; it is not a crossing report. Its document kind prevents
confusion with an initial request or scientific result. If no valid fields
remain, the derived request is absent and the second call fails clearly.

No command silently drops fields, overwrites an input, chooses an output path
by destructive guess, or treats a stale validation file as pre-authorized.
Explicit output paths, no-clobber default, temporary sibling plus atomic
rename, and digest-bound revalidation are required.

ECSV and VOTable are output encodings, not initial request or validation-file
formats in the first CLI slice. JSON alone owns the nested request protocol.

## 7. Exact drawable track evidence

`SatelliteCrossingResult` defines an exact connected visit but contains only
entry, closest approach, and exit event values; those three values alone are
not a sufficiently controlled plotted curve. A separate immutable exact-track
evidence object must sample the accepted SGP4/TEME and topocentric route only
between the accepted entry and exit instants.

Sampling must be adaptive or conservatively bounded, retain every UTC sample
and coordinate specification, include entry and exit exactly, record angular
error/time tolerances and resource provenance, and fail closed when the curve
cannot be certified. Plotting must never linearly bridge separate visits,
field intervals, projection seams, or failed states.

The exact local track layer belongs beside the existing satellite candidate
layers and reuses their shared spherical-geometry and semantic-identity path.
It must retain a distinct status and SVG hierarchy:

- SatChecker sampled candidate evidence remains unverified candidate evidence;
- local exact crossing tracks identify exact connected visits and their
  snapshot/oracle provenance;
- later illumination and brightness metadata remain independent annotations.

No renderer may call SGP4, solve a crossing, interpolate an uncertified path,
or infer scientific visibility.

## 8. Ordinary chart integration

Artificial satellites remain distinct from natural satellites and from the
major/minor-body `SolarSystemTrackRequest`. `ChartRequest` may gain a separate
immutable artificial-satellite track selection, but it must consume already
validated exact-track evidence and must not own catalogue acquisition,
crossing solving, or report serialization.

Chart integration follows the canonical flow:

```text
exact crossing result + exact-track evidence
    -> shared satellite SkyLayer
    -> spherical geometry
    -> product-frame transformation
    -> projection-domain guard and projection
    -> chart preparation and clipping
    -> renderer
    -> PNG/PDF/semantic SVG export
```

Regional and binocular products are the first chart families because their
bounded viewports correspond directly to accepted circular-field queries.
Acceptance requires exact event-to-track identity, correct clipping, stable
labels/semantics, no geometry change across PNG/PDF/SVG, and visual specimens
covering central, grazing, clipped, multiple-track, and empty cases.

Stereographic planispheres require a separate audit before implementation.
That audit must define how circular crossing queries relate to the visible
hemisphere and rotating pouch/window; north/south face assignment; horizon and
mask meaning; seam splitting; clipping; east-west orientation; time labeling;
and SVG identity. A planisphere renderer must not become a crossing search
domain by accident.

All-sky, circumpolar, animation, interactive display, trail width, glow,
brightness-coded style, and detector footprints remain outside 50S.6G unless
separately audited.

## 9. Ownership

The anticipated stable responsibilities are:

- `satellites/snapshots.py`: installed and explicit-directory immutable
  snapshot loading and validation;
- a dedicated satellite snapshot acquisition/builder owner: policy-governed
  preflight and atomic publication, separate from runtime calculation;
- a dedicated exact-crossing presentation owner adjacent to
  `satellite_presentations.py`: canonical logical report plus pure encoders;
- `satellites/crossing_batch.py`: scientific batch validation and solving only,
  not CLI parsing, files, reports, or charts;
- a dedicated satellite CLI adapter under `cli/`: argument/file protocol and
  filesystem publication, composing domain services;
- the existing satellite layer owner: sampled-candidate and exact-local track
  layers with distinct scientific status;
- ordinary chart request/composition owners: declarative selection and layer
  registration only;
- existing projection, preparation, renderer, semantic identity, and exporter
  owners unchanged.

Final module names require each implementation slice's source-tree assessment.
This audit authorizes no production file.

## 10. Milestone sequence

50S.6G is decomposed as follows:

1. **50S.6G.1A — External immutable snapshot seam.** Add explicit-directory
   loading with complete manifest/digest validation and no acquisition.
2. **50S.6G.1B — Representative snapshot preflight and evidence.** Add one
   policy-governed bulk builder, representative specimens outside the package,
   and the declared scale/equivalence matrix.
3. **50S.6G.2A — Canonical exact-crossing report and JSON.** Add the immutable
   logical model, JSON Schema, deterministic JSON, and round trips.
4. **50S.6G.2B — Scientific table encodings.** Add lossless ECSV and VOTable
   encoders/decoders over the same model.
5. **50S.6G.2C — CLI and two-call file protocol.** Add direct atomic CLI mode,
   initial JSON requests, validation-output JSON, second-call valid-subset
   calculation, and atomic no-clobber publication.
6. **50S.6G.3A — Exact local track evidence and layer.** Add certified sampling,
   distinct exact semantics, and output-neutral shared-path geometry.
7. **50S.6G.3B — Binocular and regional chart products.** Connect exact tracks
   through ordinary requests and accept PNG/PDF/semantic-SVG specimens.
8. **50S.6G.4A — Stereographic planisphere audit.** Resolve domain, faces,
   horizon, masks, seams, orientation, labeling, and acceptance evidence.
9. **50S.6G.4B — Stereographic planisphere tracks.** Implement only the
   separately accepted 50S.6G.4A contract.

Every slice requires its own as-is assessment, focused gate, documentation
update, and Fernando's separate scientific and architectural acceptance. No
later slice is automatically authorized by accepting an earlier one.

## 11. Acceptance evidence

The documentation audit is acceptable when:

- every active authority and developer index agrees on scope and sequence;
- documentation tests protect the atomic direct mode, two-call file workflow,
  canonical report model, representative matrix, shared chart path, and
  explicit 50S.7/50S.8 exclusions;
- the coordinate guide records that no implemented coordinate meaning changes;
- `git diff --check` passes and the Mac documentation gate passes;
- Fernando reviews the scientific/product boundary and explicitly accepts or
  revises it.

Fernando scientifically and architecturally accepted this audit on 2026-09-17
after all 145 plugin-disabled current-documentation tests passed in 4.36
seconds. Only bounded 50S.6G.1A external immutable snapshot loading is
authorized next. Acceptance does not authorize acquisition, broader
runtime admission, reports, CLI/files, drawable tracks, chart integration,
illumination, brightness, detector effects, or observatory adapters.

## 12. Primary standards consulted

- RFC 8259, *The JavaScript Object Notation (JSON) Data Interchange Format*;
- JSON Schema Draft 2020-12;
- Astropy Enhanced CSV documentation and ECSV 1.0 header contract;
- IVOA VOTable Recommendation and VOUnits Recommendation;
- CCSDS 502.0 Orbit Data Messages, consulted to retain OEM as an orbit/state
  ephemeris option rather than a Wenu crossing-report substitute.

## 13. Accepted 50S.6G.1A implementation handoff

The accepted implementation adds only `load_snapshot_directory(directory)` in the
existing immutable snapshot owner. One explicit local non-symlink directory
must contain a non-symlink regular `manifest.json` and a non-symlink regular
records file named by that manifest. Directory names do not define snapshot
identity.

Both installed and explicit-directory routes construct the same immutable
snapshot through the accepted complete schema, canonical-byte, SHA-256,
record-count, full-NORAD identity/order, OMM semantics, epoch, provenance, and
warning validation. The focused tests extend the existing satellite-element
owner; no new production or test file is added.

This implementation performs no discovery, acquisition, provider access, network,
retry, fallback, cache write, atomic directory publication, representative
catalogue packaging, coordinator admission, benchmark, report, CLI/file,
track, chart, illumination, or later behavior. Fernando scientifically and
architecturally accepted 50S.6G.1A on 2026-09-17 after the 164-test focused
gate and all 2,583 plugin-disabled tests passed. Only a separately bounded
50S.6G.1B representative snapshot preflight and evidence audit is authorized
next, not its implementation.

## 14. Accepted 50S.6G.1B refinement

The dedicated `satellite_snapshot_preflight_audit_50s6g1b.md` refines the
representative-snapshot step without changing later report or chart contracts.
It separates a frozen official policy receipt and exact human digest
acknowledgement from one fixed CelesTrak Active-group CSV bulk request. All
responses stop on redirect or non-200 status and have no retry, fallback,
polling, per-object, parallel, or partial-success route.

Raw and canonical bytes, receipts, content-addressed publication, deterministic
medium selection, digest-bound evidence-only admission, exhaustive equality,
and the declared scale/resource matrix remain external artifacts. Active-group
scope is not full-population completeness. The candidate audit adds no runtime,
provider request, catalogue, benchmark result, report, CLI/file behavior,
track, or chart.

Fernando scientifically and architecturally accepted this refinement on
2026-09-17 after all 147 plugin-disabled current-documentation tests passed in
4.54 seconds. Only bounded fake-transport 50S.6G.1B.1 is authorized next; no
live CelesTrak access or representative admission/evidence is authorized.

## 15. Candidate 50S.6G.2A exact-report refinement

The dedicated `satellite_exact_crossing_report_audit_50s6g2a.md` refines
milestone 50S.6G.2A without changing the later ECSV/VOTable, CLI/file, track,
or chart contracts. It defines a distinct exact-local product, complete
immutable logical model, explicit creation instant, report identity digest,
closed Draft 2020-12 JSON Schema, deterministic UTF-8 JSON, strict semantic
decoder, and typed byte-identical round trips.

Validated zero-crossing fields remain explicit results. Version 1 requires
future illumination, magnitude, detector, and exact-track values to be null.
The audit changes no runtime and authorizes no implementation before Fernando's
separate acceptance.


## 16. Accepted 50S.6G.2A audit handoff

Fernando scientifically and architecturally accepted the exact-report audit on
2026-09-19 at `835ddfe`, after 175 documentation tests passed in 3.27 seconds
and clean repository checks. Only the bounded model, schema, deterministic
JSON encoder/decoder, and focused tests are authorized next. Later 50S.6G
delivery slices remain separately unauthorized.


## Candidate 50S.6G.2B refinement

The dedicated 50S.6G.2B audit refines this accepted delivery direction without
changing it. ECSV and VOTable are lossless alternate encodings of the accepted
exact-report model; canonical JSON-derived report identity remains
authoritative. One shared reusable format-neutral projection owns scientific
flattening, units, masks, joins, order, reconstruction, and limits, while thin
adapters own only ECSV or VOTable syntax.

The refinement remains candidate documentation. It authorizes no implementation
and does not pull 50S.6G.2C filesystem publication or any later science into
50S.6G.2B.

## 17. Candidate 50S.6G.2C refinement

The dedicated 50S.6G.2C audit refines the accepted two-call direction into one
offline CLI/filesystem boundary. Direct mode is wholly atomic. Initial JSON
file mode either calculates every valid field when the complete request passes
or solves none and atomically publishes deterministic validation-output JSON
containing every invalid FoV plus the ordered valid subset. A second explicit
call verifies the digest-bound validation record, retains invalid entries, and
revalidates and calculates only the valid subset.

Successful calculation publishes one explicit no-clobber directory containing
the accepted canonical JSON, ECSV, and VOTable bytes plus a digest manifest.
The candidate freezes symlink safety, filenames, exit statuses, and
interruption commit behavior. It authorizes no implementation or later track,
chart, provider, visibility, illumination, or brightness work.
