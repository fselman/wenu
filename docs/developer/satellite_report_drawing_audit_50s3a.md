# 50S.3A satellite report and drawing contract audit

**Status:** Accepted by Fernando on 2026-09-15
**Audit date:** 2026-09-15
**Wenu baseline:** `9b751b9751b43cbf808158c86c2575b7872b1534`

## Purpose

This documentation-only audit freezes the smallest honest report and drawing
boundary for normalized SatChecker output before runtime work begins. It
changes no runtime code. The accepted 50S.2B adapter returns provider candidates
with ordered sampled directions; it deliberately does not construct an exact
`SatelliteCrossingResult`. Reporting and drawing must preserve that distinction.

## Admission and reuse review

No current production owner serializes satellite candidate evidence. The
Solar-System track pipeline is the nearest visual precedent, but
`SolarSystemTrackResult` represents ephemeris realization and must not be used
as a false type for provider samples.

50S.3B may add a small satellite presentation module and a satellite sky layer.
The layer must emit ordinary typed spherical geometry and then use the existing
coordinate service, projection, preparation, renderer, semantic SVG, and export
paths through `CelestialSphere.draw_chart()`. It must not add a chart-specific
projection, renderer, SVG writer, or export path.

## Scientific status of the input

A `SatCheckerCandidateEvidence` is provider-sampled candidate evidence, not a
verified connected FoV crossing. Reports and charts must say so explicitly.

The accepted samples are ordered geometric topocentric-direction ICRS
observations. They may be joined only in provider order to show the sampled
path. Joining samples is a display operation, not interpolation, propagation,
or an exact crossing solution. 50S.3B must not infer or label:

- FoV entry or exit;
- closest approach;
- boundary touch;
- continuous containment between samples;
- angular rate beyond the supplied sample evidence;
- illumination, visibility, magnitude, or detector contamination.

Provider illumination fields, when present, remain separate provider evidence.
They may be reported verbatim with provenance but must not control admission,
style, or crossing semantics.

## One normalized evidence source

Human-readable reports, deterministic JSON, and drawable layers must consume
the same immutable normalized evidence returned by `satchecker.py`. They must
not reparse provider JSON, reopen cache files, call the network, poll a task, or
perform propagation.

The presentation boundary accepts a completed `SatCheckerResult` in SUCCESS
state. PENDING and FAILURE remain explicit provider outcomes and may be
summarized, but they produce no candidate geometry.

## Deterministic report contract

The JSON product must be versioned and deterministic. It retains:

- product/schema identity and candidate-only scientific status;
- request observer, closed circular FoV, inclusive UTC interval, and source;
- terminal task state, task identifier, provider endpoint/version where known;
- exact response SHA-256 and cache provenance where available;
- ordered candidates using stable satellite identity;
- element epoch and orbit/snapshot evidence when present;
- ordered sample UTC instants and geometric topocentric-direction ICRS
  coordinates;
- provider evidence and warnings without scientific reinterpretation.

Candidate ordering is by NORAD catalogue identifier, with sample ordering by
observation instant. JSON keys and array order are stable. Unknown optional
values remain explicit nulls or are omitted according to one documented schema;
they are never guessed.

The human-readable product is a deterministic projection of that same report
model. It begins with the phrase **SatChecker sampled candidate evidence — not
verified crossings** and includes counts, query context, provenance, warnings,
and one candidate section or row per stable identity. Names are labels only;
NORAD catalogue identifiers are the durable keys.

## Drawing contract

The drawable layer consumes normalized candidate evidence directly.

- Two or more samples produce one open spherical polyline in supplied temporal
  order.
- One sample produces one point marker and no invented segment.
- Zero samples produce no geometry.
- No interpolation, extrapolation, smoothing, resampling, clipping-derived
  entry/exit event, or closest-approach event is created.
- Direction is conveyed only from sample order, using existing marker/style
  vocabulary where available.
- UTC labels identify supplied sample instants; they are not entry/exit labels.
- The requested closed FoV boundary may be drawn by the existing spherical
  geometry path, independently of candidate admission.

All sample geometry declares its accepted geometric topocentric-direction ICRS
coordinate identity and follows the canonical transformation and projection
path. Rendering performs no astronomy.

## Semantic identity and accessibility

Semantic identity must be stable under provider ordering and label changes.
The layer family is `artificial_satellites`; candidate components are keyed
by full NORAD catalogue identifier, never display name or sequence number. The
reserved path is:

`sky/artificial_satellites/satchecker_candidates/norad_<catalogue_id>/sampled_track`

Point samples and time labels use stable suffixes derived from their normalized
UTC instant. The exact spelling must be covered by semantic tests before
acceptance. SVG grouping and metadata must expose candidate-only status and
must not contain `entry`, `exit`, or `closest_approach` components for
SatChecker sampled evidence.

PNG, PDF, and SVG must all be produced by the same realized layer and shared
renderer/export system. SVG receives semantic structure; raster and PDF output
must remain visually equivalent within existing backend expectations.

## Ownership proposed for 50S.3B

- `src/wenu/satellite_presentations.py` owns the renderer-neutral report model,
  deterministic text/JSON serialization, and conversion of completed normalized
  provider evidence into presentation records.
- `src/wenu/sky/satellite_candidate_layer.py` owns only conversion of those
  records into typed spherical curves, points, labels, and semantic metadata.
- `src/wenu/satchecker.py` remains provider transport/cache/normalization.
- `src/wenu/satellite_crossings.py` remains the provider-neutral candidate and
  exact connected-visit domain.
- existing coordinate, projection, preparation, renderer, semantic, style,
  furniture, and export modules retain their responsibilities.

The final file names may change only if the implementation admission review
finds a closer existing owner; the scientific and dependency boundaries above
do not.

## Bounded implementation and gates

50S.3B is authorized to implement only renderer-neutral reports and a drawable
sampled-candidate layer from already-normalized evidence. It adds no CLI
acquisition workflow, waiter loop, provider retry, propagation, exact crossing
solver, local catalogue, illumination calculation, magnitude, or detector
model.

Ordinary tests use synthetic normalized evidence and remain network-free.
Focused gates cover report determinism, candidate-only wording, ordering,
singleton and empty geometry, coordinate identity, semantic stability, and
shared-backend drawing. Visual acceptance must include a compact synthetic FoV
chart in PNG, PDF, and SVG. The complete suite runs at the 50S.3B acceptance
boundary.

## Acceptance

Fernando accepted this scientific and architectural contract on 2026-09-15
after the focused documentation gate passed all 126 tests and the candidate
diff passed `git diff --check`. Acceptance closes 50S.3A and authorizes only
the bounded 50S.3B implementation. It does not authorize 50S.4 propagation or
snapshot work.
