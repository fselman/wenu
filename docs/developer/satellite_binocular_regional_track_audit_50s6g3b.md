# 50S.6G.3B binocular and regional exact-track chart audit

**Status:** documentation-only candidate for Fernando's separate scientific and architectural acceptance
**Milestone:** 50S.6G.3B
**Baseline:** `ce6eea37e518f97c81e13d52a613e540b204c31b`
**Date:** 2026-09-19

## Decision sought

This audit proposes the smallest ordinary-chart integration that places accepted 50S.6G.3A exact local satellite tracks on binocular and regional products. It authorizes no implementation. Separate scientific and architectural acceptance is required before runtime, style, test, or specimen work.

## Bounded scope

50S.6G.3B is limited to:

- explicit immutable chart-display requests containing already-realized `ExactLocalSatelliteTrack` evidence;
- binocular and regional stereographic products in the existing horizontal product frame;
- installation and cleanup of accepted exact path and event layers through the ordinary chart-request lifecycle;
- independent path, event-marker, and event-label display controls;
- existing detail, style, projection, clipping, renderer, export, and semantic-SVG paths;
- PNG, PDF, and semantic-SVG acceptance specimens from the same prepared chart;
- focused request, lifecycle, geometry, semantics, export, and state-isolation tests.

It excludes crossing calculation, propagation, adaptive sampling, provider access, snapshot acquisition, report or CLI changes, candidate SatChecker tracks, all-sky/circumpolar products, planispheres, visibility, illumination, brightness, detector effects, scheduling integration, and unrelated refactoring.

## Existing authority

### Exact evidence is complete before chart construction

50S.6G.3A owns immutable snapshot-bound connected-visit evidence, exact entry/closest/exit anchors, deterministic sampling, failure semantics, track identity, coordinate provenance, and the output-neutral `SatelliteExactTrackLayer` and `SatelliteExactTrackEventsLayer`.

The chart path must consume that evidence unchanged. It must not call `LocalSatelliteCrossingOracle`, `Sgp4TemePropagator`, `SatelliteTopocentricTransformer`, `ExactLocalSatelliteTrackRealizer`, or the internal adaptive sampler.

### The ordinary chart pipeline already owns presentation

`ChartRequest`, request resolution, chart construction, `LayerRealizationContext`, `CelestialSphere.draw_chart()`, projection-domain guarding, stereographic projection, clipping, chart preparation, renderer selection, furniture, and export remain the canonical route.

The Solar-System track path is useful only as a lifecycle precedent: an explicit request installs temporary layers, shares one realized scientific result among views, and removes request-owned layers on close. Satellite exact tracks retain their own scientific and semantic types and do not become `SolarSystemTrackRequest` values.

## Proposed public request

A future frozen `SatelliteExactTrackDisplayRequest` contains:

- one `ExactLocalSatelliteTrack`;
- `draw_path: bool = True`;
- `draw_events: bool = True`;
- `label_events: bool = False`.

At least one of `draw_path` or `draw_events` must be true. `label_events` requires `draw_events`. The value contains no provider, snapshot path, tolerance, solver, realizer, style, projection, output path, or mutable cache option.

`ChartRequest` gains:

- `satellite_exact_tracks: tuple[SatelliteExactTrackDisplayRequest, ...] = ()`.

The tuple is explicit and default-empty. Entries are ordered as supplied. Duplicate `track_identity_sha256` values are rejected because one exact evidence realization must not be installed twice.

This is a Python request seam only. No CLI flag, JSON request-field change, report-bundle field, automatic discovery, or implicit use of previously calculated files is part of 50S.6G.3B.

## Admission and product restrictions

A request containing exact satellite tracks is valid only when all of the following hold:

- family is `regional` or `binocular`;
- projection is `stereographic`;
- coordinate frame is `horizontal`;
- every track's satellite-observer longitude, latitude, elevation, refraction policy, and Earth-orientation policy agree with the chart observer contract;
- the chart observer UTC instant equals the crossing field's declared coordinate reference instant;
- every crossing field specification remains geometric `gcrs-axes` / `topocentric-direction` with UTC reference identity as required by the accepted oracle;
- every evidence collection remains timeless and declares `sample_time_scale="utc"`;
- track identity, event roles, sample order, and evidence coordinate meaning pass the accepted 3A constructors.

Named-location and explicit-coordinate chart observers compare through their normalized scientific identity. Floating observer coordinates use the existing normalized values, not a new approximate matching policy.

Tracks from different field IDs may coexist only when they share the same admitted observer site and reference instant. The chart may frame a larger or differently shaped region than the circular crossing FoV; metadata and labels must describe each curve as only the accepted connected segment between its own entry and exit. No continuation outside that interval may be inferred.

## Fixed product-frame meaning

Every retained 3A sample is a geometric topocentric direction evaluated at its own UTC instant and expressed in fixed GCRS axes. During ordinary layer realization, the whole retained curve is transformed once into the chart's single horizontal product frame at the chart observer reference instant.

This creates a static chart of the time-varying line of sight against the sky and horizon at one declared reference instant. It does not reinterpret each vertex as simultaneous, recompute instantaneous AltAz per sample, rotate the chart during the visit, or claim one common physical observation instant for the samples.

The chart reference instant must equal the crossing FoV coordinate reference instant so field selection, horizon orientation, and product-frame meaning remain aligned.

## Request lifecycle and ownership

A future `charts/request_satellite_tracks.py` may own:

- validation of `SatelliteExactTrackDisplayRequest`;
- chart-request admission checks;
- installation of one accepted path layer and/or event layer per display request;
- event-label enablement on the event view;
- deterministic request-provenance summaries;
- removal of only the layers it installed.

The ordinary request build installs satellite layers after resolution and before canonical preparation. `ChartRequestBuild.close()` removes them even after export failure. Reusing a supplied maximal sphere leaves no satellite layers, selection, labels, styles, or evidence references behind.

The module performs no science. It receives immutable evidence and creates accepted layer views.

## Path, events, and labels

### Path

When enabled, one `SatelliteExactTrackLayer` supplies the accepted open connected-visit polyline or singleton point. Canonical projection-domain guarding and clipping own boundary intersections. The integration must not pre-clip, extrapolate, smooth, interpolate, close, or join distinct visits.

### Events

When enabled, one `SatelliteExactTrackEventsLayer` selects retained entry, closest-approach, and exit vertices. Coincident roles remain scientifically attached to one retained sample even if the event view carries multiple semantic event records at the same coordinate.

### Labels

Event labels are presentation annotations over the event view. With `label_events=False`, marker geometry remains and labels are absent. With `label_events=True`, the accepted English labels are:

- `entry`;
- `closest approach`;
- `exit`.

Spanish localization, timestamps, satellite-name labels, along-track tick marks, label collision optimization, and leader lines are deferred. Labels must use the existing chart annotation/preparation path and must not modify evidence geometry.

## Detail and style

Explicit satellite display requests are default-off content. When present and admitted, their layers participate in ordinary detail and style resolution without adding a renderer-specific draw route.

The future implementation may add narrowly scoped style roles for:

- exact satellite path;
- exact satellite event marker;
- exact satellite event label.

Style controls appearance only: color, line width, dash, marker, font, and annotation spacing. It cannot change samples, event selection, coordinates, clipping, visibility, or identity. Exact tracks must be visually and semantically distinguishable from SatChecker candidate evidence.

Product compositions may vary appearance through existing style overrides but may not enable, disable, or alter scientific track evidence independently of the request display controls.

## Stable semantic identity

The accepted 3A semantic family remains authoritative:

- `sky/artificial_satellites/exact_local_tracks/<visit_key>/track`;
- `sky/artificial_satellites/exact_local_tracks/<visit_key>/events`.

Projected path pieces retain the path identity through clipping. Event markers and labels remain descendants of the event identity and retain event roles. Multiple visits by the same NORAD object never collapse because the visit key binds the exact track digest.

SVG IDs must be deterministic, safe, unique within one product, and independent of output filename. PNG and PDF need not expose editable semantics but must use identical prepared geometry and appearance decisions.

## Provenance and export

The ordinary SVG provenance record must not recursively serialize the full exact evidence object. A deterministic request summary records, for each display request:

- `track_identity_sha256`;
- NORAD catalog ID and display name;
- field ID;
- entry, closest-approach, and exit instants;
- snapshot SHA-256;
- `draw_path`, `draw_events`, and `label_events`.

The summary preserves supplied order and is identical across PNG, PDF, and SVG generation from one prepared request. Scientific sample evidence remains in the immutable 3A object and is not duplicated into chart metadata or report files.

Export uses existing output destinations, atomicity, overwrite behavior, formats, and semantic-SVG backend. 3B adds no filename convention or filesystem protocol.

## Empty, multiple, and failure behavior

- An empty tuple installs no layer and produces the unchanged ordinary chart.
- One request may contain zero-duration evidence; path view becomes the accepted singleton and event roles remain explicit.
- Multiple satellites and multiple visits of one satellite are allowed when identities are unique and admission context matches.
- A failure in request validation installs nothing.
- A failure after installation triggers ordinary request-build cleanup.
- A failure in one requested export follows existing multi-output behavior; it does not mutate evidence or leave layers installed.
- No invalid or mismatched track is silently dropped.

## Acceptance specimens

A later implementation must create deterministic offline acceptance specimens from immutable synthetic or installed evidence:

1. one regional stereographic horizontal chart with an exact track crossing the viewport boundary, three event markers, and labels enabled;
2. one binocular stereographic horizontal chart using the same exact evidence, with path and markers but labels disabled;
3. PNG, PDF, and semantic SVG generated through the ordinary request/export route;
4. a semantic-SVG inspection demonstrating exact-local visit hierarchy, unique path/event identities, and preserved event roles;
5. a control chart with no satellite request demonstrating output neutrality outside the explicit feature.

The specimens must show that the same retained samples underlie both chart families and all formats. Scientific equality is tested from immutable geometry; visual review addresses clipping, line/marker balance, label readability, and distinction from candidate tracks. Golden raster bytes are not required.

## Required tests for a later implementation

A bounded implementation must test:

- frozen display-request validation and default values;
- rejection of unsupported families, projection/frame combinations, duplicate identities, observer mismatches, reference-instant mismatches, and invalid display-control combinations;
- empty request output neutrality;
- deterministic installation order and cleanup on success and failure;
- no calls to oracle, propagator, transformer, or track realizer during chart build or export;
- one shared evidence object across path and event views;
- singleton and multiple-visit behavior;
- canonical clipping of boundary-crossing paths without pre-clipping or extrapolation;
- independent path/event/label controls;
- fixed-product-frame coordinate meaning and unchanged sample metadata;
- style changes affecting appearance only;
- stable semantic paths, SVG IDs, visit distinction, and event roles;
- deterministic bounded provenance summaries rather than recursive evidence serialization;
- PNG/PDF/SVG generation through the same prepared chart;
- unchanged SatChecker candidate, Solar-System track, report, CLI, planisphere, and no-track chart behavior;
- state isolation when a reusable maximal sphere serves consecutive requests.

Focused tests may use deterministic constructed `ExactLocalSatelliteTrack` evidence. They must not access a provider or recompute crossing science.

## Rejected alternatives

- Passing a snapshot or crossing query into `ChartRequest` is rejected because chart construction must not perform science.
- Passing only a track digest is rejected because no authorized repository or file lookup exists in this milestone.
- Reusing `SolarSystemTrackRequest` is rejected because satellite evidence, time semantics, identity, and lifecycle differ.
- Installing layers directly outside the ordinary request lifecycle is rejected because cleanup and reproducible exports would become caller responsibilities.
- Transforming every vertex into its own instantaneous horizontal frame is rejected because a static chart requires one fixed product frame.
- Re-solving a larger chart footprint is rejected because it invents science outside the accepted evidence.
- Pre-clipping in the satellite integration is rejected because projection and clipping already have canonical owners.
- Serializing complete evidence into SVG provenance is rejected because it duplicates the scientific product and creates unbounded metadata.
- Adding planisphere support now is rejected because seam, face, horizon, mask, orientation, and labeling policies require 50S.6G.4A.
- Adding CLI or report support is rejected because their accepted schemas and file protocol require separate audits.

## Proposed implementation sequence after acceptance

1. Add the frozen display request and bounded provenance-summary contract.
2. Add request admission, deterministic installation, and cleanup ownership.
3. Register exact path/event/label detail and style roles through existing owners.
4. Connect only regional and binocular ordinary request preparation and export.
5. Add focused request, lifecycle, semantic, export, and isolation tests.
6. Generate and inspect the required PNG/PDF/semantic-SVG specimens.
7. Run the complete plugin-disabled suite and present the candidate for separate acceptance.

## Explicit authorization boundary

This candidate authorizes no implementation. Acceptance would authorize only the bounded 50S.6G.3B binocular/regional exact-track chart integration described here. It would not authorize 50S.6G.4A/B planisphere work, all-sky/circumpolar satellite tracks, provider access, snapshot acquisition, report or CLI changes, new execution science, visibility, illumination, brightness, detector effects, scheduling integration, or unrelated refactoring.
