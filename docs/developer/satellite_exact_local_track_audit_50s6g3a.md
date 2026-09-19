# 50S.6G.3A exact local track evidence and output-neutral layer audit

**Status:** documentation-only candidate for Fernando's separate scientific and architectural acceptance
**Milestone:** 50S.6G.3A
**Baseline:** `99631a08f5a2d28020f71b43f49f9fe94c261c3e`
**Date:** 2026-09-19

## Decision sought

This audit proposes the smallest exact-local-track boundary that can support later binocular and regional chart work without moving science into a renderer. It authorizes no implementation. Fernando's separate scientific and architectural acceptance is required before any production or test change.

## Bounded scope

50S.6G.3A is limited to:

- immutable exact local track evidence for one already accepted `SatelliteCrossingResult` connected visit;
- deterministic sampling only from entry through exit, inclusive;
- reuse of the accepted immutable snapshot, SGP4/TEME propagation, and geometric topocentric transformation;
- an output-neutral satellite layer that exposes retained evidence as ordinary spherical geometry;
- exact entry, closest-approach, and exit anchors, stable identity, coordinate metadata, provenance, explicit limits, and fail-closed behavior;
- focused scientific, identity, layer, and failure tests.

It excludes provider access, snapshot acquisition, a new crossing solve, report or CLI protocol changes, chart composition, style, projection, clipping, rendering, export, planispheres, all-sky products, visibility, illumination, brightness, detector effects, and tracks outside accepted connected visits.

## Existing authority

### Exact crossings are event truth

`SatelliteCrossingResult` already defines one normalized connected visit with `entry_instant <= closest_approach_instant <= exit_instant`. Its candidate binds the satellite, observer, closed circular field, inclusive query interval, source provider, orbit solution, immutable snapshot digest, and provenance.

The exact local oracle owns visit discovery and event refinement. Track construction consumes one accepted result; it must not rediscover entry, exit, closest approach, containment, or visit connectivity.

### The scientific route already exists

`Sgp4TemePropagator` owns successful geometric TEME states from the admitted immutable element record. `SatelliteTopocentricTransformer` owns the accepted observer and Earth-orientation transformation to geometric topocentric direction expressed in GCRS axes. 50S.6G.3A composes those owners and introduces no orbit interpolation, alternate propagation, provider coordinates, or apparent/refraction correction.

### Candidate display remains scientifically distinct

`SatelliteCandidateTrackLayer` and `SatelliteCandidateSamplesLayer` expose ordered provider samples with status `SatChecker sampled candidate evidence — not verified crossings`. They do not establish continuous containment or exact events. Their evidence classes, status, semantic paths, and provenance remain unchanged.

The Solar-System track work supplies a structural pattern: realize one immutable sample set and let views consume it without repeating science. Exact local satellite evidence must not reuse `SolarSystemTrackResult`, its ephemeris assumptions, or its cadence contract.

## Proposed evidence model

A future frozen `ExactLocalSatelliteTrack` represents exactly one accepted connected visit and retains:

- the original crossing result;
- an immutable ordered tuple of `ExactLocalSatelliteTrackSample` values;
- the declared track coordinate specification;
- requested angular chord-error tolerance and maximum sample interval;
- fixed recursion, evaluation, and retained-sample limits;
- algorithm and implementation identifiers;
- snapshot, orbit-solution, propagation, Earth-orientation, observer, and field provenance;
- deterministic `track_identity_sha256`;
- warnings only when they do not weaken correctness.

The product is not a multi-field or multi-satellite collection. Batch grouping, report attachment, and filesystem publication remain later concerns.

Each frozen sample retains at least one normalized UTC instant, one finite unit topocentric direction vector expressed in GCRS axes, longitude and latitude derived from that vector, positive topocentric range in kilometres, sufficient immutable propagation/transformation provenance, and zero or more roles from `entry`, `closest_approach`, and `exit`.

Sample order is strictly increasing by UTC instant. Coincident event instants create one sample with every applicable role. An ordinary adaptive sample has no event role.

## Coordinate meaning

The native collection coordinate identity is frame `gcrs-axes`, origin `topocentric-direction`, geometric position status, UTC time scale, and no collection-level instant because every vertex retains its own UTC instant.

This is a time-varying topocentric direction expressed in fixed GCRS axes. It is not a geocentric GCRS position, TEME-labelled sky coordinate, ICRS source direction, observed AltAz direction, or refracted apparent direction.

## Deterministic sampling and certification

Entry, closest-approach, and exit are mandatory evaluation instants and exact retained vertices. The realizer evaluates the admitted snapshot at those instants through the accepted propagation and topocentric owners. It does not copy crossing scalars as a substitute for direction evaluation.

Mandatory event anchors partition the interval. For every adjacent pair, the realizer evaluates the temporal midpoint through the same route and compares that direction with the normalized spherical chord midpoint of the endpoints. It subdivides when the midpoint angular deviation exceeds the requested chord-error tolerance or elapsed endpoint time exceeds the requested maximum sample interval. Subdivision is left before right for deterministic ordering.

The certificate is deliberately narrow: every accepted leaf passed the defined midpoint chord-deviation test and maximum-time-step rule. It is not a proof of a global continuous maximum error between evaluations, and metadata must not claim a stronger bound.

Inputs must be positive and finite. Fixed implementation limits bound recursion depth, propagation evaluations, and retained samples. Exhausting a limit, receiving failed propagation/transformation, producing invalid range/direction, or failing normalization raises one typed convergence/evaluation error and returns no partial track. Evaluation may be cached by normalized UTC instant within one realization without changing order, identity, or failure behavior.

When all three event instants coincide, evidence contains one sample with all roles. With two or more unique instants it contains an ordered track. No segment is invented for a singleton, and no propagation occurs outside the inclusive entry-to-exit interval.

## Identity and provenance

`track_identity_sha256` is the lowercase SHA-256 of a canonical versioned logical identity record binding at least:

- product and algorithm versions;
- NORAD identity fields;
- observer values and policies;
- field ID, center, radius, boundary, and coordinate identity;
- query interval and exact event values;
- source provider, orbit-solution ID, element epoch, and snapshot digest;
- tolerance, maximum step, and implementation limits;
- every ordered sample instant, vector, spherical values, range, and roles;
- propagator, gravity-model, Earth-orientation, and transformation provenance.

The digest identifies this evidence realization. It is not the report identity, snapshot digest, provider event ID, orbit-solution ID, or semantic entity key. Identical inputs under the same declared algorithm and dependencies reproduce equal evidence and digest. Changing tolerance, samples, snapshot, events, observer, coordinates, or implementation version changes identity.

## Output-neutral layer

A future `sky/satellite_exact_track_layer.py` may own only evidence validation, stable semantic metadata, ordinary spherical geometry construction, and transformation into a supplied `LayerRealizationContext`. It performs no propagation, crossing solve, adaptive sampling, provider call, report mutation, or filesystem work.

The layer consumes one exact evidence value and returns one open `SphericalCurves` for at least two unique samples or one `SphericalPoints` for a singleton. A separate event-point view may select existing retained sample indices. It must not propagate again or manufacture coordinates. The existing `CoordinateService` may transform native geometry into the product coordinate specification.

Metadata states `exact local connected-visit track` and never uses the SatChecker unverified-candidate status. Stable identity remains under `sky/artificial_satellites` and distinguishes exact local visits from provider candidate samples. A visit key binds satellite identity, field ID, ordered event instants, snapshot digest, and track identity so repeated visits do not collide.

The candidate family retains its sampled-track path. A future exact path is a sibling such as `sky/artificial_satellites/exact_local_tracks/<visit_key>/track`; final registered spelling is frozen and tested during implementation. This audit registers no chart layer.

## Reports and CLI remain unchanged

The accepted JSON/ECSV/VOTable report and CLI bundle remain unchanged. Track evidence references the accepted crossing and identities in memory; it is not inserted into `report.json`, `report.ecsv`, `report.vot`, or `manifest.json`.

A serialized track extension requires a separate schema, round-trip, digest, resource-limit, and compatibility audit. A CLI option or bundle filename likewise requires separate authorization.

## Later implementation acceptance tests

A bounded implementation must test:

- exact inclusion and combined roles for entry, closest, and exit;
- deterministic left-before-right ordering and digest identity;
- no propagation outside the connected visit;
- midpoint-deviation and maximum-step subdivision;
- cached reuse without scientific change;
- identity changes for tolerance, snapshot, observer, event, or sample changes;
- typed fail-closed propagation, transformation, recursion, evaluation, and sample-limit behavior;
- one all-role point for a zero-duration visit and one open curve otherwise;
- event views selecting retained samples without recomputation;
- coordinate identity and per-sample UTC metadata through layer realization;
- stable non-colliding exact-visit semantics;
- unchanged explicitly unverified SatChecker layers;
- no report, CLI, provider, chart, renderer, or exporter change.

Tests use deterministic fake evaluators for convergence edges and accepted local services for parity cases. They require no network or current provider data.

## Rejected alternatives

- Three event points alone do not control the intervening curve.
- Provider samples are candidate evidence, not snapshot-bound exact visits.
- Uniform cadence alone provides no declared curvature check.
- Calling the crossing oracle again creates a second event truth.
- `SolarSystemTrackResult` has different science and identity.
- Sampling inside the layer moves science into presentation.
- Silent truncation publishes uncertified partial evidence.
- Adding tracks to report bundles changes accepted schemas and protocol.

## Proposed sequence after acceptance

1. Add frozen sample, evidence, policy, typed-error, and realizer contracts adjacent to local satellite science.
2. Implement deterministic anchored adaptive sampling by composing accepted propagation and topocentric owners.
3. Add evidence-only exact-track and event views with stable semantics.
4. Add focused offline tests and documentation.
5. Run focused and full plugin-disabled suites plus clean diff and tree checks.
6. Present the candidate for separate scientific and architectural acceptance.

## Explicit authorization boundary

This candidate authorizes no implementation. Acceptance would authorize only the bounded 50S.6G.3A exact local track evidence and output-neutral layer described here. It would not authorize 50S.6G.3B chart integration, 50S.6G.4A/B planisphere work, provider access, report or CLI changes, new crossing science, visibility, illumination, brightness, or unrelated refactoring.

## Acceptance and bounded implementation authority

Fernando scientifically and architecturally accepted this documentation-only audit on 2026-09-19 at `ce549715889c135e17b87749f3860855b1b54447`. Verification comprised 193 plugin-disabled current-documentation tests passing in 5.73 seconds, a clean diff check against `99631a08f5a2d28020f71b43f49f9fe94c261c3e`, and a clean synchronized Mac working tree.

Implement only the bounded 50S.6G.3A exact local track evidence and output-neutral layer specified above. Preserve the accepted connected crossing as event truth; compose the accepted immutable snapshot, SGP4/TEME, and geometric topocentric route; retain exact event anchors; use deterministic fail-closed sampling; and keep candidate and exact scientific status distinct.

This acceptance does not authorize 50S.6G.3B chart integration, 50S.6G.4A/B planisphere work, report or CLI protocol changes, provider access, new crossing science, visibility, illumination, brightness, detector effects, or unrelated refactoring. The implementation remains a candidate until separately verified and accepted.
