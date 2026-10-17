# 50S.6G.4A corrective AltAz stereographic planisphere exact-track audit

**Status:** scientifically and architecturally accepted corrective audit; bounded implementation authorized
**Milestone:** 50S.6G.4A corrective audit
**Baseline:** d8604fccc9a203d6fbc80c6f892dc3b9025a6f2e
**Date:** 2026-09-20

## Decision sought

This audit corrects the product identity selected by the accepted 2026-09-19
50S.6G.4A record. Fernando requires exact satellite tracks on Wenu's ordinary
observer-horizontal planisphere: ChartRequest(family="planisphere"), horizontal
AltAz coordinates, zenith-centred stereographic projection, and the horizon as
the chart boundary.

The earlier audit instead selected PolarPlanispherePairRequest, a different
product made from paired north and south equatorial celestial disks. That
accepted scope and its resulting unmerged implementation candidate do not
satisfy the requested product.

This corrective candidate authorizes no implementation. Fernando's separate
scientific and architectural acceptance is required before runtime, style,
test, or specimen-tool changes.

## Superseded authority and preserved evidence

The scientific and architectural acceptance recorded on 2026-09-19 at
c1d9015ab18153dc84aba1360edb29fa4f46bf4e applied to the wrong product
identity. Its authorization of paired equatorial polar-planisphere work is
superseded for 50S.6G.4B.

The rejected implementation branch
feature/50s6g4b-stereographic-planisphere-tracks at
7a00b15498ffef4a63e3babba433d380f333a94e remains isolated and unmerged. Its
test results and generated artifacts are historical diagnostic evidence only;
they do not establish acceptance of the requested AltAz product.

The accepted 50S.6G.3A exact connected-visit evidence and 50S.6G.3B ordinary
regional/binocular presentation remain valid. No satellite propagation,
topocentric transformation, crossing solution, adaptive sampling, identity,
semantic, style, provenance, renderer, or exporter result is revoked.

## As-is product identity

Wenu has two distinct products that have been called planispheres:

- ChartRequest(family="planisphere") resolves to one FullSkyChart in the
  horizontal coordinate frame with stereographic projection;
- PolarPlanispherePairRequest resolves to paired north and south equatorial
  celestial disks for a physical rotating planisphere.

The requested 50S.6G.4 product is only the first. It is an observer-local,
instant-specific visible-hemisphere chart, normally centred on altitude
90 degrees, bounded at altitude 0 degrees, with azimuth and altitude as its
pre-projection spherical coordinates.

FullSkyChart already owns the stereographic projection, horizon curve,
viewport, chart boundary, final clipping, preparation, renderer handoff, and
ordinary PNG, PDF, and semantic-SVG export. ChartRequest already owns a
default-empty satellite_exact_tracks tuple, request-level observer/time
identity, bounded provenance, request-owned layer installation, and cleanup.

The only intentional admission blocker is
validate_satellite_exact_track_requests(), which currently permits only the
regional and binocular families. No new chart type, projection, coordinate
service, layer, renderer, exporter, or parallel pipeline is required.
The only proposed runtime change is to widen exact-track family admission from
regional/binocular to planisphere.

## Bounded scope

A future corrected 50S.6G.4B may only:

- admit family="planisphere" in the existing exact-track request validator;
- preserve the existing stereographic and horizontal request requirements;
- reuse SatelliteExactTrackDisplayRequest and already-realized
  ExactLocalSatelliteTrack evidence without solving, propagating, or
  resampling;
- realize each complete retained track once into the chart's fixed AltAz
  product frame at the request reference instant;
- use FullSkyChart's existing horizon boundary, viewport preparation,
  projection, clipping, renderer, and exporters;
- preserve accepted exact-track path, event, label, semantic identity, style,
  bounded provenance, installation, cleanup, and state isolation;
- provide one deterministic physical AltAz planisphere specimen for La Ligua
  in PNG, PDF, and semantic SVG; and
- add only the focused planisphere admission, coordinate, boundary, lifecycle,
  semantic, export, and unchanged-output evidence required below.

It excludes paired polar disks, PolarPlanispherePairRequest,
PolarPlanisphereChart, polar page or pouch output, equatorial fixed-axis
presentation, circumpolar and Galactic all-sky products, CLI or report changes,
provider access, acquisition, new propagation or crossing science, visibility,
illumination, brightness, detector effects, scheduling adapters, and unrelated
refactoring.

## Coordinate contract

Every accepted exact-track sample is a geometric topocentric direction
evaluated at its own UTC instant and expressed in fixed GCRS axes. The retained
collection remains immutable and its ordered sample instants remain evidence.

The ordinary planisphere has one horizontal product frame resolved from the
chart observer and the crossing field's coordinate reference instant. The
existing LayerRealizationContext and CoordinateService transform the complete
track from its typed geometric topocentric GCRS-axis representation into that
one AltAz product frame before projection.

This is the accepted 50S.6G.3B fixed-product-frame rule applied to a wider
horizontal field. It does not reinterpret every sample as though the chart
frame changed at that sample's UTC instant. Per-sample UTC remains provenance
and event evidence; the chart reference instant owns the displayed AltAz axes.

The transformed chart geometry retains topocentric origin and the established
ordinary horizontal request status. It must not be routed through the
equatorial polar-face adapter, relabelled as an equatorial celestial track,
given a second light-time or apparent-place solution, or recomputed by the
chart.

## Admission and atomic failure

A non-empty planisphere exact-track request is valid only when:

- family is planisphere;
- projection is stereographic and coordinate_frame is horizontal;
- every display is a SatelliteExactTrackDisplayRequest;
- every display draws a path or events and labels require events;
- no track_identity_sha256 is repeated;
- each track retains the accepted geometric topocentric GCRS-axis coordinate
  contract and UTC samples;
- every track observer longitude, latitude, elevation, vacuum-refraction
  policy, and Earth-orientation policy matches the ChartRequest observer;
- every crossing field coordinate reference instant equals the ChartRequest
  observer instant; and
- multiple tracks share that same admitted chart context.

The complete tuple is validated before any request-owned layer is installed or
any output is written. No invalid or mismatched track is silently dropped.

All existing rejection remains: all_sky, circumpolar, non-stereographic, and
non-horizontal requests do not gain exact-track support from this milestone.

## Horizon boundary and scientific meaning

FullSkyChart's altitude-zero horizon is the ordinary chart's physical
presentation boundary. Existing spherical and viewport preparation may clip a
projected path at that boundary. Such clipping:

- does not create a crossing entry or exit event;
- does not change the accepted FoV visit interval;
- does not establish Earth occultation, illumination, or naked-eye
  visibility;
- does not alter retained evidence or track identity; and
- does not permit extrapolation, smoothing, closing, or joining visits.

The accepted multi-FoV admission already requires each field centre to remain
within its configured airmass bound over the complete interval. That field
admission is not replaced by chart-boundary clipping and is not a claim that
every satellite sample is illuminated or detectable.

A track point exactly on the closed horizon boundary may be drawn according to
the existing preparation tolerance. Tests must inspect retained scientific
event roles rather than infer events from graphical endpoints.

## Orientation, events, and presentation

The default planisphere is zenith-centred. FullSkyChart and
StereographicProjection own azimuth orientation, east-west display policy,
position angle, tangent point, and scale. The satellite layer must not mirror,
reverse, reorder, or recalculate samples.

Existing controls retain their meaning:

- draw_path shows the accepted open visit curve or zero-duration singleton;
- draw_events selects retained entry, closest-approach, and exit vertices;
- label_events enables the existing event labels without moving markers.

The physical specimen must make the event-specific context inspectable by
showing or accompanying the chart with the La Ligua site, chart reference UTC,
and complete entry-to-exit UTC interval. This is product validity information,
not new satellite evidence. General request provenance remains bounded and
must not serialize samples.

## Lifecycle, semantics, and output

configure_chart_request_satellite_tracks() remains the installation owner.
ChartRequestBuild remains the cleanup owner after success or any failure.
FullSkyChart continues through CelestialSphere.draw_chart(), ordinary
preparation, the existing renderer, and one final save per requested product.

The accepted semantic families remain:

- sky/artificial_satellites/exact_local_tracks/<visit_key>/track;
- sky/artificial_satellites/exact_local_tracks/<visit_key>/events.

PNG, PDF, and semantic SVG are three encodings of the same prepared
astronomical geometry. Semantic SVG and export provenance retain ordered
bounded summaries including track identity, NORAD identity, field ID, event
times, snapshot digest, and display controls. No full sample array or recursive
evidence object is serialized.

An empty satellite_exact_tracks tuple must remain byte-equivalent to the
ordinary planisphere baseline modulo no added provenance field, install no
layer, and change no title, legend, geometry, selection, style, or output.

## Test placement and acceptance evidence

The closest durable production owners are
charts/request_satellite_tracks.py, charts/request_generation.py,
charts/request_realization.py, charts/full_sky.py, and
sky/satellite_exact_track_layer.py. The corrected implementation should
normally require only the family-admission change plus specimen tooling;
existing owners already provide the other behavior.

The closest durable test owners are tests/test_satellite_exact_tracks.py for
admission and retained evidence, tests/test_request_generation.py for request
lifecycle and output, and tests/test_full_sky_chart.py for horizon projection
and clipping. No milestone-named runtime test file is justified.

Before implementation acceptance, corrected 50S.6G.4B must provide:

1. focused proof that planisphere is admitted while all_sky and circumpolar
   remain rejected;
2. exact observer/reference-instant and coordinate-policy rejection evidence;
3. fixed AltAz product-frame realization at the chart instant with sample UTC
   evidence preserved;
4. horizon clipping without synthetic scientific events;
5. request-owned cleanup after success and failure and no cross-render state
   leakage;
6. unchanged-output evidence for an empty tuple;
7. one physically propagated La Ligua visit rendered as a zenith-centred
   stereographic AltAz planisphere in PNG, PDF, and semantic SVG;
8. visual review of direction, horizon placement, markers, labels, context,
   legibility, and site/time validity;
9. semantic-SVG and bounded-provenance checks with no recursive samples;
10. the current documentation gate, relevant focused tests, and complete
    plugin-disabled suite; and
11. diff, whitespace, exact-head, branch-synchronization, and clean-tree
    checks.

The coordinate-system guide requires Fernando's scientific and pedagogical
review because this milestone extends an existing fixed AltAz presentation to
the full visible hemisphere.

## Proposed implementation placement

No production file is authorized by this corrective audit. If accepted, the
smallest implementation should keep responsibility with existing owners:

- charts/request_satellite_tracks.py: add planisphere to the admitted ordinary
  exact-track families and keep all validation and installation rules;
- charts/request_generation.py and charts/request_realization.py: unchanged
  canonical lifecycle and fixed horizontal product-frame ownership;
- charts/full_sky.py: unchanged stereographic projection, horizon boundary,
  clipping, renderer, and export ownership;
- sky/satellite_exact_track_layer.py: unchanged retained-evidence path and
  event views;
- existing style, semantic, provenance, and export owners: unchanged; and
- tools/: one deterministic physical acceptance specimen, not a user workflow.

No new production module, chart class, projection, coordinate adapter, layer,
renderer, exporter, provider, or report path is justified.

## Exclusions and next authority

This corrective candidate authorizes no implementation. The previously
accepted paired-equatorial authority is superseded and does not authorize
continued work on the rejected branch.

If Fernando accepts this corrective audit, only the bounded corrected
50S.6G.4B ordinary AltAz stereographic planisphere integration and the evidence
listed above become authorized. Merge, branch cleanup, program closure,
circumpolar tracks, Galactic all-sky tracks, paired polar disks, CLI/report
changes, visibility, illumination, brightness, detector effects, scheduling
adapters, 50S.7, 50S.8, and later work remain unauthorized.

## Acceptance and bounded corrected implementation authority

Fernando scientifically and architecturally accepted this corrective
documentation audit on 2026-09-20 at
80855938a8711b7cec05190b5c7d33557dace9a9. Verification comprised all 201
plugin-disabled current-documentation tests passing in 6.14 seconds, a clean
diff check against d8604fccc9a203d6fbc80c6f892dc3b9025a6f2e, exact local
and upstream head agreement, and a clean synchronized Mac working tree.

Implement only the bounded corrected 50S.6G.4B ordinary AltAz stereographic
planisphere integration specified above. The implementation may add
planisphere to the existing regional/binocular exact-track family admission,
extend the existing durable tests, and add one deterministic physical La Ligua
review tool producing PNG, PDF, and semantic SVG through the ordinary request
path.

Preserve the accepted fixed AltAz product-frame rule, exact observer and
reference-instant admission, horizon presentation boundary, no-synthetic-event
rule, request-owned installation and cleanup, unchanged empty-request output,
existing semantic identities, bounded provenance, canonical
CelestialSphere.draw_chart() path, and existing renderer/exporter ownership.

This acceptance does not authorize paired polar disks, circumpolar or Galactic
all-sky tracks, provider or acquisition changes, report or CLI changes, new
propagation or crossing science, visibility, sunlight, solar Earthshine,
moonlight, lunar Earthshine, brightness, detector effects, scheduling
adapters, 50S.7, 50S.8, merge of an implementation, or unrelated refactoring.
The corrected implementation remains a candidate until separately verified,
physically reviewed, and accepted.

## 50S.6G.4B verified candidate implementation record

Executable candidate `91eafff5ca7f0069806f7f059d19f7bb9ca123aa`
widens only `validate_satellite_exact_track_requests()` admission to the
ordinary `planisphere` family. It adds focused admission and empty-state
evidence plus one deterministic physical review tool; every existing
realization, lifecycle, projection, boundary, semantic, provenance, renderer,
and exporter owner remains unchanged.

The 252-test focused gate passed in 7.08 seconds and all 2,744
plugin-disabled repository tests passed in 220.63 seconds. One physically
propagated La Ligua visit produced PNG, PDF, and semantic SVG from 65 retained
samples with track digest
`3f526de147caae6832c7a56330d460948c4b8963c7cdbf753618682e70d4248a`.
Fernando reviewed the ordinary horizon-bounded chart and identified only a
non-blocking long specimen title; the companion manifest retains the reference
instant and complete event interval. Diff, exact-head, upstream, and clean-tree
checks passed. The candidate remains unaccepted and authorizes no merge or
later work.

## 50S.6G.4B final implementation acceptance

Fernando scientifically and architecturally accepted the corrected ordinary
AltAz planisphere implementation and explicitly authorized merge on
2026-09-20. PR 176 merged final candidate
`6bc623bbabb356b1481b6e5e06e855eb79a560b7` into
`program/50s-crossing-foundation` at
`f0730d80eb72c97837c75489a87d9faf1699e7d1`.

Acceptance evidence comprises 252 focused tests in 7.08 seconds, all 2,744
plugin-disabled repository tests in 220.63 seconds, 202 final documentation
tests in 5.19 seconds, the physically propagated 65-sample La Ligua
PNG/PDF/semantic-SVG specimen, and clean diff, exact-head, upstream, and
working-tree checks. The test-only long title was a non-blocking review
observation because the companion manifest retains the reference instant and
complete event interval.

Preserve ordinary `ChartRequest(family="planisphere")` admission, one fixed
AltAz chart-reference frame, per-sample UTC evidence, the horizon presentation
boundary without synthetic events, request-owned cleanup, stable exact-track
semantics, bounded provenance, and canonical rendering/export. 50S.6G delivery
is closed. Only a documentation-first 50S.6H observatory-planning adapter audit
is authorized next; no adapter runtime or 50S.7+ behavior is authorized.
