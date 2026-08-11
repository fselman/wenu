# Wenu migration roadmap: v0.7 to v0.8

**Status:** Active
**Source:** `current_architecture_v0.7.md`
**Target:** `target_architecture_v0.8.md`
**Base commit:** `b72eef8`

## Milestone 46A — Add the semantic AltAz grid

- add native observer-local `AltAzGrid` geometry;
- add `CelestialSphere.add_altaz_grid()` and public exports;
- add independent `altaz_grid` detail and label selection;
- add `--altaz-grid` and `--altaz-grid-labels`;
- retain black semantic AltAz colors and adapt print lines and labels to
  gray `#707070`;
- keep the horizon excluded and chart-owned by default;
- configure all canonical and packaged examples declaratively;
- test geometry, identity, opt-in controls, styling, isolation, and parity;
- compile, run focused and full suites, and visually approve affected charts.

The milestone must preserve `CelestialSphere.draw_chart()` and every v0.7
ownership boundary.

## Milestone 46B — Rationalize permanent test ownership

- organize permanent tests by current responsibility rather than completed
  milestone history;
- consolidate duplicated documentation, example, legend, furniture, style,
  detail, label, geometry, catalogue, pipeline, and regression contracts;
- retain focused scientific coverage and the full suite as release authority;
- define fast, integration, visual, and full validation tiers.

**Status:** Implemented through Milestone 46B.10.

## Milestone 46C.1 — Reuse identical canonical integration builds

- introduce a session-scoped canonical build registry;
- reuse only builds with identical example, observer, catalogue depth,
  selection, target, mask, and framing requests;
- retain independent builder smoke coverage;
- close every registry-owned observer at session teardown.

**Status:** Implemented.

## Milestone 46C.2 — Record maximal-sphere ownership and selection gaps

- record observer-independent catalogue ownership separately from
  observer/time-dependent AltAz geometry;
- preserve AltAz as the canonical spherical geometry entering projection;
- distinguish load ceilings and sampling quality from render-local selection;
- inventory every construction-time restriction and every existing
  `spherical_geometry()` selection option;
- define the maximal canonical content profile needed by all supported chart
  families;
- reserve the same layer contract for future planets, Moon, artificial
  satellites, tracks, and time sequences;
- record the regional, binocular, and masked-planisphere adaptation evidence
  in `wenu_chart_request_audit_20260810.md` and derive the declarative request
  requirements from actual usage;
- add characterization tests only where the implemented boundary is not
  already enforced.

This milestone changes architectural authority and records the as-is gaps. It
must not prematurely change public behavior or introduce a parallel pipeline.

## Milestone 46C.3 — Add an immutable render-local content selection

- introduce one immutable detail-owned selection contract;
- express constellation figures, boundaries, labels, catalogue identifiers,
  isophote levels, and Cloud choices independently of style and chart type;
- translate the selection through `apply_resolved_detail()` into structured
  layer geometry options;
- preserve existing `ResolvedDetail`, explicit layer-option, and example APIs;
- make the selection contract suitable for both Python and command-line chart
  requests rather than coupling it to test fixtures or example globals;
- prove that sequential selections on one sphere do not leak state.

## Milestone 46C.4 — Complete late selection in every canonical layer

- load complete constellation-line and boundary data and filter named subsets
  during spherical-geometry production;
- connect existing render-local object-selection capabilities to resolved
  detail for open and globular clusters, planetary nebulae, supernova
  remnants, galaxies, and other registered catalogues;
- make Milky Way and Magellanic Cloud isophote levels render-local;
- separate maximum sampling quality from requested grid and content density
  where scientific accuracy permits;
- preserve catalogue provenance, authoritative native coordinates, Serpens
  boundary behavior, and atlas-print appearance.

**Status:** Implemented through Milestone 46C.4B.

## Milestone 46C.5 — Add one canonical maximal-sphere factory

- define an immutable, comparable load profile containing catalogue ceilings,
  data sources, and maximum sampling quality;
- add one factory that registers complete canonical content for an observer;
- return an ordinary `CelestialSphere` and retain
  `CelestialSphere.draw_chart()` as the execution core;
- keep chart projection, framing, masks, detail, style, legends, and export
  outside the factory;
- reject requests that exceed the declared available content instead of
  silently returning an incomplete chart.

Coordinate grids remain request-time semantic geometry rather than loaded
catalogue content: their spacing and extent vary by chart family and must not
be frozen into the reusable sphere.

**Status:** Implemented.

## Milestone 46C.6 — Cache observer-dependent spherical realizations

- cache expensive native-coordinate to AltAz transformations under complete
  observer, instant, source, and geometry-quality keys;
- transform maximal vectorized catalogue coordinates once before applying
  repeated render-local subsets where this preserves results;
- keep cached geometry immutable and prevent rendering state from entering
  cache keys;
- invalidate or select a distinct cache entry when observer location, time,
  ephemeris, orbital source, or native data changes;
- measure catalogue reads and coordinate transformations directly rather than
  enforcing fragile wall-clock thresholds.

**Status:** Implemented. Milestones 46C.6A–46C.6D cover the maximal stellar
transformation shared by stars and constellation figures, vectorized point
catalogues, Milky Way and Magellanic Cloud isophotes, sampled B1875
constellation boundaries, and quality-keyed extended-object outlines.

## Milestone 46C.7 — Add a declarative user chart-request facade

- introduce one immutable request contract shared by Python and command-line
  entry points;
- express observer location/time, chart family, target or constellation set,
  optional framing, mask, content, product, furniture, language, title, and
  output without exposing construction orchestration;
- resolve packaged common names and catalogue identifiers offline with
  explicit provenance, unknown-name, and ambiguity diagnostics;
- accept explicit coordinates for targets not present in packaged catalogues;
- automatically request the catalogue families required to represent the
  resolved target and reject incompatible load profiles;
- select ordinary field objects spatially so users do not have to curate every
  object identifier, while retaining explicit inclusion and exclusion;
- retain the resolved central target independently of general magnitude or
  size thresholds and diagnose a target with no drawable representation;
- provide automatic regional framing and sensible family defaults while
  retaining explicit field and position-angle overrides;
- normalize constellation line, boundary, and label identities internally,
  including the two parts of Serpens;
- accept actual observer location/time inputs independently of switches that
  request their display in chart furniture;
- delegate to the maximal-sphere factory, canonical composition, renderer,
  and single export rather than implementing a convenience pipeline;
- retain all established lower-level APIs for advanced callers.

**Status:** Implemented. Milestones 46C.7A–46C.7J cover the immutable request,
offline target and constellation/group resolution, load-profile validation,
automatic framing and spatial content, explicit exclusions, all four chart
families, and the ordinary one-call generation facade. The facade owns and
closes its observer and canonical maximal sphere, delegates composition and
single export to the established pipeline, exposes results and output paths,
and rejects named targets without drawable packaged components. A separate
prepared-request export entry point preserves an advanced sphere-reuse path.

## Milestone 46C.8 — Make canonical examples pure chart requests

- migrate the five canonical examples to obtain content from the shared
  declarative request facade;
- express their differences through chart definitions, resolved detail, and
  immutable content selections;
- permit a prebuilt compatible sphere to be supplied while retaining existing
  standalone `build_chart()` behavior;
- replace hard-coded binocular target dictionaries and regional-group
  construction procedures with packaged target/group declarations consumed by
  the common resolver;
- ensure that adding an ordinary binocular target or regional constellation
  set requires data or command arguments, not a new orchestration script;
- preserve documented CLI behavior, catalogue provenance, scientific
  geometry, and approved atlas-print output.

## Milestone 46C.9 — Validate all chart families from one maximal sphere

- build one canonical sphere for the shared La Ligua observer and instant;
- exercise planisphere, regional single, regional group, circumpolar, and
  binocular chart requests against it;
- retain separate readable tests and one builder smoke contract per family;
- prove order independence, selection isolation, exact target and mask
  behavior, and deterministic cleanup;
- retain distinct builds for genuinely different observer, time, ephemeris,
  source, or load-profile requests.

## Milestone 46C.10 — Benchmark and close reusable observed-sky work

- report catalogue-loading, AltAz transformation, selection, projection,
  preparation, rendering, and export costs separately;
- verify that canonical catalogues are read once and reusable transformations
  are not repeated;
- run fast, integration, visual, and full suites;
- visually approve the mandatory atlas-print regression charts;
- update current architecture, implementation reference, source tree, and test
  audit to record the implemented result.

## Later dynamic-sky milestones

After 46C establishes correct static-data and observed-geometry ownership:

- **47A:** solar-system ephemeris layers for planets;
- **47B:** topocentric Moon position, phase, apparent size, and orientation;
- **47C:** artificial-satellite points and sampled tracks with explicit orbital
  source identity;
- **47D:** time sequences and animation that reuse static catalogues while
  producing correctly keyed observed states.

These layers must use the existing `SkyLayer.spherical_geometry()` contract
and canonical chart pipeline. They do not authorize a second projection,
clipping, rendering, legend, or export implementation.
