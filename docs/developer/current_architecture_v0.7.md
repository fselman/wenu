# Wenu current architecture v0.7

**Status:** Implemented baseline for the v0.8 migration
**Baseline commit:** `b72eef8`
**Date:** 2026-08-05

Wenu v0.7 implements independently selectable equatorial, ecliptic, and
Galactic coordinate-grid layers. It does not implement an observer-local
AltAz grid, although horizontal coordinates are already the canonical
spherical geometry used by projection and rendering. The horizon remains
chart-owned boundary geometry and is not optional reference content.

The canonical flow, ownership boundaries, declarative examples, render-local
detail policy, style ownership, and packaged-example parity documented by
`target_architecture_v0.7.md` remain in force.

The permanent test suite is organized by these current responsibilities rather
than by completed milestone history. Fast unit, integration, visual, and full
commands are recorded in `source_tree.md`; the full suite remains the release
authority and atlas print remains the visual reference baseline.

The v0.8 migration now provides one immutable canonical load profile and one
maximal-sphere factory. It loads complete reusable astronomical content for an
observer and returns the existing `CelestialSphere`; chart geometry,
coordinate-grid spacing, detail, presentation, and export remain downstream
request concerns.

Stellar AltAz realization is cached per loaded `Stars` layer using observer
location, instant, ephemeris identity, data directory, catalogue identity,
and source revision. Render-local magnitude and identifier selections mask
that immutable maximal realization, and constellation figures reuse it.
Vectorized point catalogues use the same key identity: open-cluster and
planetary-nebula selections index immutable maximal AltAz center arrays.
Milky Way and Magellanic Cloud level selections likewise index immutable
maximal observed ring arrays. Official constellation boundaries cache their
complete sampled B1875 realization; the native source revision and sampling
step are part of the cache identity, while the requested constellation set
remains render-local.
Extended-object layers cache complete observed outline catalogues at each
requested geometry quality. Sample count and minimum displayed angular size
belong to the cache identity; magnitude and identifier subsets are applied
afterward. Galaxies, Messier-style objects, globular clusters, and supernova
remnants share this policy through `NonStellar`.

Milestone 46C.7A adds an immutable public chart-request graph. It separates
the scientific observer and instant, subject identity, optional framing,
content, detail, furniture, product, language, title, and output. It is a
declarative contract only: resolution and generation continue to be added
incrementally over the canonical sphere and chart pipeline.

Milestone 46C.7B adds an offline packaged target cross-identification
resolver. A resolved target preserves its display identity and ICRS center
while separately naming every catalogue family and identifier required to
draw it. Unknown and ambiguous aliases raise explicit user-facing errors;
explicit coordinates retain user provenance and need no packaged component.

Milestone 46C.7C adds the corresponding offline constellation-subject
resolver. It accepts arbitrary IAU abbreviation sets and packaged teaching
groups, and resolves their public region identities into the distinct line,
boundary, and label identifiers required internally. In particular, a public
`Ser` request consistently expands to `Ser1`/`Ser2` figures and
`SerCap`/`SerCau` labels while retaining one official boundary identity.
Teaching-group framing and curated legacy-example content are packaged data,
not example-script globals.

Milestone 46C.7D adds one request-resolution boundary before construction.
It resolves targets or constellation subjects, unions the central target and
packaged group content into an immutable render-local selection, and rejects
detail ceilings that exceed the chosen maximal-sphere load profile. The
original request remains unchanged; no chart, renderer, or export work occurs
in this phase.

Milestone 46C.7E resolves family framing defaults without constructing chart
geometry. Binocular requests receive the established 6.5-degree field unless
overridden; packaged groups provide their recorded width and height; arbitrary
IAU sets explicitly defer automatic framing to their authoritative geometry.

Milestone 46C.7F completes that operation in the existing
`RegionalChart.from_constellations()` constructor. With no explicit field it
derives a spherical center and maximum great-circle extent from all unique
loaded figure endpoints, then applies configurable padding and a minimum
field. Explicit-radius calls retain their previous result.

Milestone 46C.7G adds render-local spatial catalogue selection after a chart
field exists. Catalogue centers reuse the observer/time point cache, are
projected through the selected chart, and are tested against its viewport and
circular field stop where present. Visible identifiers are unioned with
explicit selections and the already retained central target.

Milestone 46C.7H adds immutable catalogue exclusions to the chart request.
They are applied after packaged, explicit, and automatic field selection.
Contradictory explicit inclusion is rejected, and a resolved central target
cannot be excluded silently.

Milestone 46C.7I adds one chart-construction boundary over resolved requests.
It constructs the established full-sky, regional, circumpolar, or binocular
chart, then applies spatial content selection. `FullSkyChart` now owns the
same official-boundary outside-mask operation already used by regional charts;
its horizon also bounds spatial catalogue selection. No request facade
subclass or private example pipeline is required.

Milestone 46C.7J closes the ordinary declarative facade. Public
`generate_chart_request()` owns one observer and canonical maximal sphere,
resolves and prepares the request, composes each requested product through
the established composition API, exports each product exactly once, and
closes its observer even after failure. `export_prepared_chart()` exposes the
same final composition/export boundary for a caller that already owns a
compatible prepared sphere and chart request. Named targets without a
drawable packaged catalogue component are rejected before construction.

Milestone 46C.8A allows that same facade to receive a compatible prebuilt
maximal sphere. `ChartObserverRequest` normalizes its scientific location and
UTC instant without constructing an observer or loading an ephemeris; the
facade compares that identity and the sphere's declared load profile before
resolution. A supplied sphere remains caller-owned and is never closed or
rebuilt. Omitting it retains the standalone owned-sphere behavior.

Milestone 46C.8B moves canonical coordinate-grid density into one request-time
configuration boundary. Only grids explicitly selected by detail or label
options are registered. Before each request, previously registered semantic
grids are removed and the selected planisphere, regional, circumpolar, or
binocular configuration is installed in canonical drawing order. Astronomical
catalogue layers are untouched, the maximal load profile remains grid-free,
and repeated requests cannot accumulate duplicate grid layers.

Milestone 46C.8C adds immutable product-specific composition options to the
chart-request graph. An exact atlas/cartoon and print/presentation product may
select its detail policy and post-mode style overrides without changing the
request's family, frame, projection, mask, or other chart geometry. The
generation facade applies those options at the established composition
boundary; products without an explicit entry retain their previous defaults.

Milestone 46C.8D adds one family-neutral late context-furniture boundary.
`ChartContextOptions` records chart-center, active-grid, observer-location,
date, and local-time selections without requiring a constructed chart or sky.
The request exporter realizes those selections only after chart construction,
then supplies immutable context lines to the established legend furniture.
The same contract applies to all canonical chart families and contains no
target, framing, projection, or example-specific policy.

Milestone 46C.8E exposes the request facade's existing construction phase as
`build_chart_request()`. It resolves and prepares any chart family without
rendering or exporting, using either an owned canonical maximal sphere or a
compatible caller-owned sphere. Its `ChartRequestBuild` records resource
ownership, exposes the prepared chart, supports deterministic context-manager
cleanup, closes an owned observer at most once, and never closes a supplied
sphere. `generate_chart_request()` now delegates to this same preparation
boundary before the established single export.

Milestone 46C.8F migrates the canonical binocular example to that shared
request scaffold. The script declares its observer, packaged target, field,
content, products, detail, style overrides, furniture, and title; the common
facades own maximal content, target/component resolution, chart preparation,
composition, rendering, and single export. `TARGETS`, manual catalogue and
grid registration, Matplotlib orchestration, and repeated saving are removed.
Its compatibility `build_chart()` uses `build_chart_request()` and accepts a
caller-owned sphere. Any packaged drawable target is accepted without a script
change, while Centaurus A and Omega Centauri retain their approved fields and
publication identities.

Milestone 46C.8H introduces the execution seam required by the target
observer-independent sphere. `CelestialSphere.draw_chart()` accepts an
explicit observer, which overrides its compatibility bound observer, and the
canonical chart, masking, spatial-selection, label-placement, context, and
reference-furniture paths carry that observer without changing the layer
contract. Existing calls that omit it retain their v0.7 behavior.

Milestone 46C.8I adds `generate_celestial_sphere()` as the first ordinary
three-stage operation. It loads the canonical native catalogues and geometry
under an explicit load profile into an ordinary `CelestialSphere` whose
observer is `None`; its canonical layers are likewise unbound. The established
observer-bound `build_maximal_sphere()` and request facade remain compatible
until observer-bound views become the ordinary construction boundary.

Milestone 46C.8J adds `get_chart_view()` as the second ordinary operation. It
binds a caller-owned scientific observer to an observer-independent sphere,
resolves the friendly subject and frame vocabulary through the advanced
request graph, and prepares the established canonical chart geometry. The
returned frozen `ChartView` exposes geometry and resolved provenance but no
appearance, drawing, furniture, language, title, output, or cleanup state.
Only the implemented stereographic projection is accepted.
