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

This factory is the implemented intermediate boundary: it still receives an
observer and returns a `CelestialSphere` bound to that observer.  Milestone
46C.8 will preserve its behavior while moving the target maximal sphere to
observer-independent ownership.

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

- pause further example migrations after the binocular proof of the shared
  request scaffold;
- add a small ordinary Python interface that generates a celestial sphere,
  obtains a geometrical view, and draws that view;
- make the maximal sphere observer-independent and bind observer, instant,
  projection, framing, orientation, viewport, mask, and boundary in the view;
- distinguish configuring projection in the view from applying it lazily to
  render-selected observer-dependent spherical geometry during drawing;
- keep style and detail out of view geometry so one view can produce several
  products without geometrical reconstruction;
- retain the immutable request graph as the canonical advanced contract and
  translate the ordinary interface into it;
- centralize appropriate binocular, regional, planisphere, and circumpolar
  defaults while spelling the important defaults out in canonical examples;
- replace, rather than incrementally reproduce, the five canonical examples
  with declarations using few public imports and fewer than 70 lines each;
- permit a prebuilt compatible sphere to be supplied while retaining existing
  standalone `build_chart()` behavior;
- replace hard-coded binocular target dictionaries and regional-group
  construction procedures with packaged target/group declarations consumed by
  the common resolver;
- ensure that adding an ordinary binocular target or regional constellation
  set requires data or command arguments, not a new orchestration script;
- preserve documented CLI behavior, catalogue provenance, scientific
  geometry, and approved atlas-print output.

**Status:** Implemented through Milestone 46C.8F. The request facade accepts a
compatible caller-owned maximal sphere, verifies its normalized
observer/instant and declared load profile, and never closes or rebuilds it.
Family-specific coordinate-grid density now has one request-time configuration
boundary: only explicitly selected grids are installed, prior grids are
replaced, and maximal catalogue content remains untouched. Canonical example
declarations remain in this milestone. Exact products may now declare their
own detail policy and post-mode style overrides without mixing presentation
with chart geometry. Generic chart-center, active-grid, observer, date, and
time metadata may also be selected before chart construction and is realized
through the common furniture boundary afterward. The binocular example is the
first pending migration to these shared request facilities. A common
`build_chart_request()` boundary now prepares any family without export and
records whether it owns the observer, allowing every canonical `build_chart()`
compatibility wrapper to reuse identical construction and cleanup semantics.
The canonical binocular example is now a pure request adapter over those
facilities: it has no private target registry or construction/export pipeline,
accepts every packaged drawable target, preserves its documented controls and
compatibility builder, and keeps the installed resource byte-identical.  Its
size and remaining adapter ceremony establish that the shared scaffold is not
yet the intended ordinary interface.  Further example migrations are paused
until that interface is implemented and verified.

### Milestone 46C.8G — Specify observer-independent sphere ownership

- define the public generate-sphere, get-view, and draw operations before
  choosing final names in code;
- assign load-profile and native-content choices to sphere generation;
- assign observer, instant, projection, framing, orientation, viewport, mask,
  and boundary to the view;
- assign appearance, detail, grids, furniture, and output to drawing;
- define projection configuration as view state and projection execution as a
  lazy drawing-stage operation after render-local spherical selection;
- document ownership, cleanup, return values, supported projection names, and
  the boundary between friendly arguments and structured advanced options;
- require delegation to the existing maximal-sphere, request, composition,
  export, and `CelestialSphere.draw_chart()` pipeline.

### Milestone 46C.8H — Pass observer explicitly through canonical execution

- add an explicit observer to `CelestialSphere.draw_chart()` and the chart,
  masking, spatial-selection, context, and furniture paths that currently read
  `sky.observer`;
- preserve the existing bound-observer calls as a compatibility form during
  migration;
- keep `SkyLayer.spherical_geometry(observer)` as the sole observed-geometry
  contract and preserve complete observer/time/source cache keys;
- prove that explicit observers do not change approved atlas-print output.

**Status:** Implemented. `CelestialSphere.draw_chart()` and the canonical
chart render/export, masking, spatial-selection, label-placement, reference
furniture, request-furniture, and request preparation/export paths accept an
explicit observer. Omitting it preserves the observer-bound compatibility
form. Layer realization continues exclusively through
`SkyLayer.spherical_geometry(observer)`.

### Milestone 46C.8I — Decouple maximal-sphere construction

- expose a concise wrapper over `build_maximal_sphere()` that returns an
  observer-independent ordinary `CelestialSphere`;
- load catalogues, native geometry, load ceilings, source provenance, and
  caches without selecting one authoritative observer or instant;
- keep chart geometry, grids, selection, style, furniture, and output outside
  sphere construction;
- preserve the implemented observer-bound factory and request facade while
  callers migrate;
- make observer ownership and cleanup the responsibility of the caller or the
  request facade that created it.

**Status:** Implemented. `generate_celestial_sphere(profile=...)` is the
ordinary observer-independent loading operation. It returns the existing
`CelestialSphere` with the selected load profile and all canonical native
content registered, but with no sphere- or layer-bound observer. The existing
`build_maximal_sphere(observer, profile=...)` factory and request facade remain
available unchanged during migration.

### Milestone 46C.8J — Add the observer-bound geometrical view facade

- translate friendly observer, instant, family, subject, projection, framing,
  orientation, and mask arguments into the existing immutable request and
  resolver contracts;
- return a small immutable prepared-view value with resolved provenance and no
  style, renderer, Matplotlib, furniture, or output state;
- initially expose stereographic projection honestly and reject unsupported
  projection names rather than promising an unimplemented projection family;
- preserve packaged targets, arbitrary IAU sets, packaged groups, automatic
  framing, spatial selection, Serpens normalization, and supplied-sphere use.

**Status:** Implemented. `get_chart_view(sky, observer, ...)` translates the
ordinary family, subject, stereographic projection, framing, orientation, and
mask vocabulary into the established immutable request resolution and chart
preparation boundaries. It returns a frozen `ChartView` containing the
caller-owned observer, canonical chart geometry, projection identity, and
resolved target, constellation, and frame provenance. It owns no style,
renderer, furniture, language, title, output, or observer cleanup.

### Milestone 46C.8K — Centralize explicit family defaults

- define one public default policy for binocular, regional single, regional
  group, planisphere, and circumpolar views;
- keep concise omitted-default calls available while requiring canonical
  examples to show the scientifically and geometrically important values;
- exclude cache keys, catalogue joins, internal layer identifiers, and other
  implementation details from the ordinary vocabulary.

**Status:** Implemented. `CHART_VIEW_DEFAULTS` and
`chart_view_defaults()` define one immutable public geometrical policy.
Binocular views default to a 6.5-degree field, regional single views derive
their frame from constellation geometry, regional groups use packaged group
framing, planispheres use the visible hemisphere, and circumpolar views use
the south pole to declination -69.75 degrees. All default to stereographic
projection, zero position angle, and no mask. Explicit ordinary arguments
override the policy; advanced request validation remains compatible.

### Milestone 46C.8L — Add the ordinary drawing facade

- accept direct style, mode, detail, grid, furniture, title, language, and
  destination choices for one prepared view;
- translate those choices into existing detail, composition, style override,
  furniture, and export contracts;
- permit repeated atlas/cartoon and print/presentation drawings of one view
  without changing its geometry or leaking render-local state;
- retain structured options for advanced callers and export exactly once per
  selected product.

**Status:** Implemented. `draw_chart_view(view, destination, ...)` translates
one direct style, mode, detail policy, detail override, grid, furniture,
style-override, title, language, and output choice into a one-product immutable
request over the view's prepared geometry and content. It configures grids at
the established request-time boundary and delegates composition, rendering,
furniture, and the single save to `export_prepared_chart()`. It returns the
one `ChartExportResult`; repeated drawings reuse the same chart geometry and
replace request-time grids without leaking drawing state.

### Milestone 46C.8M — Add shared command-line adaptation

- map common CLI controls into the same three-stage Python interface;
- leave examples responsible only for explicit family defaults and genuinely
  family-specific arguments;
- preserve documented controls without making a script own catalogue,
  projection, renderer, furniture, or export procedure.

**Status:** Implemented. `add_chart_cli_arguments()` adds the complete common
product, content, style, legend, context, and credit contract.
`chart_cli_furniture()` translates shared furniture switches into immutable
options, including localizable reference and legend labels.
`draw_chart_view_from_arguments()` resolves the selected product matrix,
detail and style overrides, furniture, titles, language, and deterministic
destinations, then delegates each product to `draw_chart_view()`. Exact
product detail policies remain explicit family inputs. No canonical example
is replaced until Milestone 46C.8N.

### Milestone 46C.8N — Replace the five canonical examples

- replace binocular, regional single, regional group, planisphere, and
  circumpolar scripts with fewer-than-70-line declarative examples;
- use few public imports and show the important defaults explicitly;
- retain installed-example byte parity and `build_chart()` compatibility only
  through the common facade where that compatibility remains required;
- delete superseded example-only helpers rather than carrying both forms.

**Status:** Implemented. The binocular, regional-single, regional-group,
planisphere, and circumpolar examples now declare the ordinary three-stage
workflow and shared CLI in 56–69 lines each. Their installed resources remain
byte-identical. Packaged target and constellation-group data replace private
registries and curated construction procedures; the scripts retain explicit
observer/time, projection, framing, orientation, mask, family detail, title,
and family-specific arguments. Superseded `build_chart()`, `chart_request()`,
catalogue-loading, composition, Matplotlib, furniture-assembly, and export
helpers are removed. Exact rendered parity and migration closure remain for
Milestone 46C.8O.

### Milestone 46C.8O — Verify and close the example migration

#### Milestone 46C.8O.1 — Establish ordinary equatorial-grid defaults

- enable the labeled equatorial grid by default in the ordinary CLI while
  retaining an explicit suppression switch;
- derive 15-degree spacing for views smaller than 60 degrees and 30-degree
  spacing otherwise from the resolved geometrical frame;
- format equatorial right ascension labels as `hh:mm` and all other grid
  coordinates in degrees.

**Status:** Implemented.

#### Milestone 46C.8O.2 — Restore render-local atlas density defaults

- select the established `ol2` through `ol5` Milky Way levels by default at
  request resolution while retaining every loaded level in the maximal
  sphere and permitting explicit level selection;
- use the existing field-adaptive deep-sky thresholds in the regional,
  planisphere, and circumpolar atlas examples while preserving their explicit
  publication stellar limits;
- retain fixed binocular target detail and the separate sparse cartoon
  policies.

**Status:** Implemented.

#### Milestone 46C.8O.3 — Make constellation sets the regional-group primitive

- add one shared command-line subject adapter for comma-separated arbitrary
  IAU sets and optional packaged-group aliases;
- pass its typed result through the ordinary `get_chart_view()` subject
  boundary so validation, Serpens expansion, content selection, and automatic
  spherical framing remain resolver and chart responsibilities;
- make the canonical group example declare an adjacent constellation set
  rather than encode or require a packaged group.

**Status:** Implemented.

#### Milestone 46C.8O.4 — Add visible multi-patch planisphere masks

- interpret a possibly disjoint constellation set as official mask regions
  when requested by a stereographic observer-visible planisphere;
- discard selected regions wholly outside the visible hemisphere, retain and
  clip partially visible regions at the horizon and final chart boundary, and
  preserve separate visible patches;
- keep visibility and clipping in observer-bound chart preparation rather
  than the resolver, CLI adapter, or examples.

**Status:** Implemented.

#### Milestone 46C.8P — Add Galactic Mollweide all-sky views

##### Milestone 46C.8P.1 — Put projection geometry in the request

- make projection and spherical coordinate-frame identity immutable advanced
  request geometry rather than a view-only tag;
- expose both resolved identities from the ordinary chart view;
- retain explicit rejection of unimplemented combinations until their
  transformation, projection, and clipping stages exist.

**Status:** Implemented.

##### Milestone 46C.8P.2 — Add Galactic frame preparation

- transform canonical observer-bound AltAz spherical geometry to Galactic
  longitude and latitude before projection;
- keep the astronomical transformation outside the coordinate-neutral map
  projection;
- prove that resulting Galactic geometry is invariant within numerical
  tolerance across observer locations and instants.

**Status:** Implemented.

##### Milestone 46C.8P.3 — Add Mollweide projection and seam topology

- add Mollweide through the existing projection and chart pipeline only after
  regional sets and stereographic multi-patch masks are complete;
- center Galactic longitude zero and split curves, grids, and polygon rings
  correctly at the longitude-180-degree seam while retaining metadata;

**Status:** Implemented.

##### Milestone 46C.8P.4 — Add the elliptical all-sky chart

- reuse the same resolved constellation-set contract without observer-horizon
  rejection, clipping all-sky curves and patches at the elliptical boundary
  and preserving separate mask openings;
- make the Galactic grid the ordinary default and retain equatorial and
  ecliptic grids as optional transformed overlays.

**Status:** Implemented.

##### Milestone 46C.8P.5 — Add the canonical example and close visually

- verify Centaurus A, Omega Centauri, regional single and group charts,
  Serpens, masks, furniture, products, and all retained CLI controls;
- run focused, full, and mandatory atlas-print visual regressions;
- record the ordinary and advanced interfaces in architecture, implementation,
  source-tree, user-guide, and test-ownership documentation.

**Status:** Implemented.

#### Milestone 46C.8Q — Add optional observer-horizon presentation

##### Milestone 46C.8Q.1 — Establish horizon roles and mask policy

- retain the planisphere horizon as intrinsic chart boundary geometry rather
  than optional content;
- define `--horizon` as an independent unlabeled altitude-zero reference and
  `--horizon-mask` as an independent translucent below-horizon presentation
  mask for other chart families;
- make both controls idempotent no-ops for planispheres and keep both
  independent of AltAz-grid and `--grid-references` selection;
- require constellation and horizon openings to be composed before one
  effective outside mask is painted, preventing accumulated opacity;
- preserve the canonical spherical-geometry, frame-transformation,
  projection, preparation, clipping, rendering, and export pipeline.

**Status:** Implemented as architectural policy; runtime behavior remains in
Milestones 46C.8Q.2 through 46C.8Q.9.

##### Milestone 46C.8Q.2 — Add reusable horizon geometry

- expose one semantic observer-local altitude-zero curve without registering
  the complete AltAz grid;
- reuse that geometry for reference drawing and below-horizon mask
  preparation;
- preserve observer-independent maximal-sphere ownership and observer-bound
  realization.

**Status:** Implemented.

##### Milestone 46C.8Q.3 — Add shared request controls

- add independent `--horizon` and `--horizon-mask` switches to the common
  parser and immutable request adapters;
- expose equivalent ordinary Python drawing options;
- make all canonical and installed examples inherit both controls through the
  shared adapter without example-specific logic.

**Status:** Implemented as declaration and adapter plumbing; visible behavior
remains in Milestones 46C.8Q.4 through 46C.8Q.7.

##### Milestone 46C.8Q.4 — Configure reference lifecycle

- register the semantic horizon reference only when selected and never for a
  planisphere;
- keep `--horizon`, `--horizon-mask`, and `--altaz-grid` independent and avoid
  duplicate altitude-zero curves;
- remove prior request-time references so reused spheres cannot accumulate
  horizon layers.

**Status:** Implemented; reference appearance and mask behavior remain in
Milestones 46C.8Q.5 through 46C.8Q.7.

##### Milestone 46C.8Q.5 — Add below-horizon mask geometry

- derive below-horizon coverage from spherical altitude rather than projected
  line orientation;
- support wholly above, crossing, and wholly below regional, circumpolar, and
  binocular fields;
- transform and seam-split the all-sky horizon through the established
  horizontal-to-Galactic Mollweide pipeline.

**Status:** Implemented as mask-opening geometry preparation; composition and
painting remain in Milestones 46C.8Q.6 and 46C.8Q.7.

##### Milestone 46C.8Q.6 — Compose chart masks once

- generalize chart mask preparation so constellation and horizon restrictions
  define one final visible opening;
- paint the resolved translucent outside-mask style exactly once everywhere
  outside that opening;
- retain separate disjoint openings and horizon clipping without alpha
  accumulation.

**Status:** Implemented. Requests now carry horizon masking through the
shared export boundary, chart families prepare their applicable opening
groups, and the renderer paints one compound nonzero-winding mask. The
planisphere remains an idempotent no-op. Semantic horizon-reference and mask
appearance are finalized in Milestone 46C.8Q.7.

##### Milestone 46C.8Q.7 — Add semantic appearance

- give the horizon reference explicit style-owned color, linewidth,
  linestyle, alpha, and z-order;
- reuse the existing resolved mask style for `--horizon-mask` without adding
  a second opacity policy;
- keep styles and output modes from changing geometry.

**Status:** Implemented. The semantic horizon is configured through explicit
style fields, atlas/cartoon mode adapters change only its appearance, and all
chart families resolve horizon and constellation masks through the existing
single `MaskStyle` policy.

##### Milestone 46C.8Q.8 — Prove behavior and isolation

- test independent CLI and Python controls, geometry, Mollweide seam
  preparation, cross-family clipping, planisphere idempotence, mask
  intersection, and single-opacity rendering;
- prove request-order independence and no state leakage on one reusable
  maximal sphere.

**Status:** Implemented. The contract suite covers independent shared
controls, geometry and Mollweide seam preparation, chart-family boundaries,
planisphere idempotence, mask intersection and single-opacity rendering, and
forward/reverse horizon-state sequences on one reused sphere without layer
leakage.

##### Milestone 46C.8Q.9 — Close visually

- compare atlas-print all-sky, masked all-sky, regional horizon crossings,
  binocular and circumpolar intersections, combined Serpens/Ophiuchus masks,
  and planisphere no-op products;
- smoke-test cartoon presentation products;
- compile, run focused and full suites, and record the final ordinary and
  advanced interfaces.

**Status:** In progress. Milestone 46C.8Q.9.1 adds the one missing canonical
circumpolar framing control and records the public horizon interface. Its
visual handoff renders a fixed matrix through the six canonical examples:
unmasked and horizon-masked all-sky products; regional, binocular, and
circumpolar horizon crossings; combined Serpens/Ophiuchus masks; matching
planisphere no-op products; and a cartoon-presentation smoke product.
Milestone 46C.8Q.9.2 records approval or fixes only defects exposed by that
matrix, then marks the horizon work complete.

The first regional visual exposed incomplete endpoint-based framing.
Milestone 46C.8Q.9.1c moves automatic request framing to the complete official
IAU boundary geometry while retaining separate constellation-line identities
and explicit field overrides. The visual matrix must be rerun before closure.

**Final status:** Implemented and visually approved through Milestone
46C.8Q.9.2. Automatic regional framing now uses complete sampled official IAU
regions while retaining separate figure identities and explicit field
overrides. Focused and full suites and the fixed visual matrix pass.

## Milestone 46C.9 — Validate all chart families from one maximal sphere

- build one observer-independent canonical maximal sphere;
- exercise planisphere, regional single, regional group, circumpolar, and
  binocular chart views for the shared La Ligua observer and instant;
- exercise additional instants and observer locations against that same
  sphere without catalogue reconstruction;
- retain separate readable tests and one builder smoke contract per family;
- prove order independence, selection isolation, exact target and mask
  behavior, observer isolation, and deterministic cleanup;
- prove that changing observer, instant, or ephemeris selects a separately
  keyed observed realization while returning to an earlier state reuses its
  compatible cache;
- retain distinct maximal spheres only for genuinely different source or
  load-profile requests.

**Final status:** Implemented. A family-spanning integration contract prepares
planisphere, regional-single, regional-group, circumpolar, binocular, and
Galactic all-sky views from one actual observer-independent canonical sphere.
Forward and reverse requests preserve identical subjects, masks, frames, and
render-local selections without changing canonical layers. Additional La
Ligua instants and Papudo use separately keyed observed realizations, while
returning to an earlier compatible state reuses its immutable stellar AltAz
arrays. Existing family builder, cleanup, source, and load-profile contracts
remain authoritative.

## Milestone 46C.10 — Benchmark and close reusable observed-sky work

- report catalogue-loading, AltAz transformation, selection, projection,
  preparation, rendering, and export costs separately;
- verify that canonical catalogues are read once across several observers and
  instants and that compatible observed transformations are not repeated;
- run fast, integration, visual, and full suites;
- visually approve the mandatory atlas-print regression charts;
- update current architecture, implementation reference, source tree, and test
  audit to record the implemented result.

**Final status:** Implemented. The Mac closure run built one canonical sphere
in 4.530 seconds, prepared and exported 18 views across all six chart families
and three observer/instant identities, and completed its 37 reported
operations. Populated observed caches held three compatible identities while
optional unused outline caches remained empty; repeating the first stellar
AltAz request added no entry. Cumulative profiler
totals were 6.763 seconds for selection, 240.172 for projection, 124.118 for
preparation, 144.755 for rendering, and 277.339 for export. These diagnostic
categories overlap and are not an additive wall-time decomposition or release
threshold. Fast, integration, visual, and full suites passed. All 18
atlas-print products were visually approved, including the explicitly masked
regional-single and regional-group products; faint-star symbol saturation is
deferred to the later appearance-curation stage. Current architecture,
implementation reference, source tree, and test audit record this closure.

## Milestone 46D — Add one installed command and authoritative defaults

Milestone 46D begins only after Milestone 46C.9 validates all chart families
from one reusable observer-independent maximal sphere. It must preserve the
same request, view, drawing, `CelestialSphere.draw_chart()`, and single-export
pipeline.

### Milestone 46D.0.1 — Correct and freeze the configuration roadmap

- name the installed command `wenu_chart`, never `wenu-chart`;
- make the packaged, versioned, commented `defaults.toml` the authoritative
  declaration of all public configurable defaults rather than an overlay on
  duplicated Python literals;
- define deterministic precedence as
  `packaged defaults.toml < optional user TOML < explicit CLI arguments`;
- require comprehensive public appearance coverage, including backgrounds,
  fills, colors, line widths, `line_style`, symbol shapes and sizes, symbol
  edges, opacity, z-order, fonts, labels, grids, horizon, masks, furniture,
  and export appearance;
- retain validation, behavior, invariants, derived geometry, derived
  appearance, and catalogue operations in their existing Python owners;
- retain Milestone 46C.9 as the implementation prerequisite for all runtime
  configuration and command work.

**Status:** Implemented. This milestone changes documentation authority only;
it adds no configuration loader, command, or runtime behavior.

### Milestone 46D.1 — Audit every effective default

- inventory every effective default in the six canonical examples, shared
  argument adapters, view defaults, chart families, styles, output modes,
  detail policies, rendering symbols, grids and references, horizon and masks,
  furniture, and export workflow;
- classify each value by observer, subject, geometry, detail, style, mode,
  grid/reference, furniture, or export ownership;
- classify each as a public configurable default, derived value, invariant,
  or implementation detail;
- explicitly inventory every background, foreground, fill, line, label, and
  symbol color; line width and `line_style`; symbol shape, size, edge, and
  edge width; opacity, z-order, font, and label property;
- record every output-mode transformation and detect duplicated or conflicting
  literals before moving any value.

**Final status:** Implemented. Milestone 46D.1A records the exhaustive
responsibility map, classification boundary, appearance and source checklists,
output-mode transformations, and duplication/conflict register.
Milestone 46D.1B adds the exact ordered inventory for observer, subject,
family, product, export, detail, styles, modes, furniture, legends, grids, and
implementation constants. Schema design may now use that single audit without
introducing runtime configuration or a second default registry.

### Milestone 46D.2 — Specify the versioned TOML schema

- define responsibility-based sections for observer, subjects, family
  geometry, detail, styles, modes, grids and references, furniture, products,
  and export;
- require a schema version and deterministic section and key ordering;
- require every configurable line-bearing element to expose independent
  `color`, `line_width`, and `line_style` values;
- initially validate `solid`, `dashed`, `dotted`, `dash_dot`, and `none`;
- reject unknown sections and keys, wrong types, invalid colors and ranges,
  unsupported values and schema versions, and contradictory combinations with
  the complete configuration path in each diagnostic;
- prohibit executable expressions, Python class names, renderer operations,
  catalogue joins, imports, and arbitrary code.

**Status:** Implemented. `configuration_schema_v1.md` defines schema version
`1`, deterministic responsibility and key ordering, complete public namespace
boundaries, independent line color/width/style fields, closed vocabularies,
range and combination rules, full-path diagnostics, and the non-executable
data boundary. This milestone adds no parser, packaged `defaults.toml`, user
overlay, command, or runtime behavior; those remain in Milestones 46D.3–46D.6.

### Milestone 46D.3 — Add authoritative packaged defaults

- add one packaged, versioned, fully commented `defaults.toml` containing
  every public configurable built-in value;
- load it through package resources without relying on the current directory;
- translate its validated values into the existing immutable typed contracts
  while preserving their runtime owners;
- permit Python schema and validation types but do not duplicate public default
  literals in a second registry;
- retain mathematical constants, invariants, catalogue operations, derived
  geometry, and derived appearance computations in Python;
- prove the packaged document alone reproduces the established resolved
  request values and canonical appearance.

**Final status:** Implemented. Milestone 46D.3A adds the complete, versioned,
commented `wenu.configuration/defaults.toml` resource and characterizes its
deterministic order, schema coverage, line vocabulary, and audited baseline
values. Milestone 46D.3B adds resource-based loading and strict complete-
document validation for structure and ordering, types, finite values, colors,
ranges, vocabularies, schema version, and contradictory combinations. Every
failure names its complete configuration path. Milestone 46D.3C translates
the atlas/cartoon semantic bases, print/presentation modes, and mode palettes
into their existing immutable typed contracts and proves exact constructor
parity. Milestone 46D.3D translates family geometry, neutral/content/cartoon/
adaptive detail, canonical family ceilings, and binocular fixed detail and
stellar sizing into their existing immutable contracts, again with exact
parity. Request resolution and composition are deliberately not rewired.
Milestone 46D.3E translates furniture, family legends, magnitude-legend
appearance, product selection, and export options into their existing
immutable owners; public values without aggregate behavioral fields remain
frozen translation metadata. Exact packaged-default parity is now established
without changing request resolution, composition, rendering, path generation,
or export. Incremental runtime authority and visual closure belong to
Milestone 46D.4.

### Milestone 46D.4 — Migrate defaults by responsibility

- migrate chart backgrounds and boundaries, astronomical symbols,
  constellation figures and boundaries, grids and labels, horizon, extended
  objects, masks, furniture, fonts, family geometry, detail, products, and
  export defaults incrementally;
- remove each displaced Python public literal when its TOML value is connected
  to the existing typed runtime owner;
- include `line_style` wherever a configurable line is drawn;
- add focused characterization, schema, and validation tests at every step;
- accept no unexplained change to the atlas-print golden baseline.

**Final status:** Implemented. Milestone 46D.4A connects named atlas/cartoon and
print/presentation composition to one cached packaged style/mode translation.
The existing adapters receive the packaged palettes and cartoon label
transform values explicitly; custom style and mode objects retain final
precedence. Geometry, detail, furniture, products, and export are not rewired
in that slice. Milestone 46D.4B connects `chart_view_defaults()` and
neutral/cartoon named composition to one cached packaged geometry/detail
translation. Packaged content-layer sets travel with the policies; explicit
view arguments, detail policies, and detail overrides retain precedence.
Milestone 46D.4C connects one cached furniture/product/export translation to
neutral ordinary furniture, family legend plans, magnitude-legend appearance,
footer layout, shared product parser defaults, generated filename extensions,
and canonical base export options. Legends and context remain opt-in.
Explicit furniture, product arguments, output paths, and export options retain
precedence. Mode DPI/transparency,
circular transparency, and canvas face color remain derived; zero packaged
padding preserves the approved atlas-print crop.
Milestone 46D.4D removes the remaining ordinary drawing and request literals
for product style, mode, language, and title; omission resolves them from the
packaged `[products.default]` contract while explicit values retain
precedence. Explicit values retain precedence. Direct
typed-constructor defaults remain compatibility API signatures, not canonical
runtime authorities; they are not a second canonical runtime registry.
Focused and full tests plus the canonical atlas-print
regression matrix close the responsibility migration without an explained
visual change.

### Milestone 46D.5 — Load and validate user TOML overlays

- load an optional partial user TOML document over the packaged authority;
- merge recursively only through documented sections and keys without
  modifying the packaged defaults in memory;
- translate the validated result into existing immutable typed contracts;
- apply deterministic precedence:
  `packaged defaults.toml < optional user TOML < explicit CLI arguments`;
- distinguish omitted CLI values from explicit values so an argument-parser
  default cannot accidentally override TOML;
- prove sequential overlays do not leak mutable state.

**Status:** In progress. Milestone 46D.5A adds strict partial-overlay parsing,
schema-version and documented-path validation, recursive non-mutating merge,
complete effective-document validation, optional file loading, and aggregate
translation through the existing immutable typed owners. Sequential overlay
loads are isolated. Milestone 46D.5B remains responsible for threading the
resolved configuration through ordinary view/drawing and shared CLI adapters,
including omitted-versus-explicit argument precedence.

**Final status:** Implemented. Milestone 46D.5B threads one frozen effective
configuration through ordinary view geometry, composition, detail, footer and
magnitude-legend furniture, product naming, and export. The shared CLI exposes
`--config PATH`; configuration is validated before canonical sphere loading,
and product arguments retain `None` as the omission sentinel until the user
overlay is resolved. Explicit CLI style, mode, and all-product selections win
at the existing adapter boundary. Family field, angle, mask, and limiting
declination controls use the same omission rule, as do configurable furniture
switches. Direct Python values retain the same final precedence. Sequential
configured and packaged products remain isolated, and packaged-only behavior is unchanged.

### Milestone 46D.6 — Add the installed `wenu_chart` command

- add one installed command with `all-sky`, `planisphere`, `regional`,
  `circumpolar`, `binocular`, and `defaults` subcommands;
- make `regional` accept one or several constellations through the same
  constellation-subject parser, without separate single/group execution;
- retain shared observer, product, content, horizon, grid, furniture, style,
  mode, output, and configuration arguments;
- delegate to `generate_celestial_sphere()`, `get_chart_view()`, and the shared
  drawing adapter without importing or executing canonical example scripts;
- retain the six examples as short reproducible declarations and regression
  authorities.

**Final status:** Implemented. The installed `wenu_chart` entry point exposes
all five chart-family subcommands plus `defaults`. Each chart command loads
and validates the effective configuration before catalogue work, resolves
observer and subject omissions from that document, constructs one ordinary
observer-independent sphere and `ChartView`, delegates products to the shared
drawing adapter, and closes its observer on success or failure. The unified
`regional` path accepts either one or several IAU constellations or a packaged
group. The module does not import examples and owns no catalogue, projection,
rendering, furniture, or export procedure. `defaults` prints the packaged
authoritative TOML; deterministic `--write` output remains Milestone 46D.7.

### Milestone 46D.7 — Export a complete editable template

- add `wenu_chart defaults --write PATH` to write a complete, versioned,
  commented TOML document containing the effective packaged public defaults;
- make generated order, formatting, documentation, and schema version
  deterministic;
- document valid values, including the complete `line_style` vocabulary;
- document how to create named publication, presentation, outreach, location,
  and observing profiles without editing Wenu source;
- define whether a future profile-inheritance feature is justified only after
  ordinary single-file overlays are proven sufficient or insufficient.

**Final status:** Implemented. `wenu_chart defaults --write PATH` writes the
installed commented authority byte-for-byte as UTF-8, preserving its schema
version, deterministic order and formatting, documentation, value spelling,
and final newline. Repeating the command replaces the destination with the
same bytes; its parent directory must already exist. The user guide documents
the complete `solid`, `dashed`, `dotted`, `dash_dot`, and `none` line-style
vocabulary and separate publication, presentation, outreach, location, and
observing TOML profiles selected through `--config`. Version 1 retains one
overlay per invocation and no inheritance: composition is deferred until
actual single-file use proves that another schema feature is warranted.

### Milestone 46D.8 — Prove parity and close visually

**Status:** In progress. Milestone 46D.8A establishes executable
resolved-view parity between each of the six canonical examples and an
equivalent `wenu_chart` invocation. The contract compares observer identity,
family, subject, projection, coordinate frame, framing, orientation, pole,
declination limit, and mask only after omitted values have been resolved from
the same effective configuration. Drawing-request, overlay-isolation, failure
ordering, documentation, suite, and visual-matrix closure remain in 46D.8.

Milestone 46D.8B proves the installed command's downstream parity at the
shared drawing-adapter boundary without loading catalogues or rendering. One
combined contract resolves detail, all four semantic grids and labels, all
three reference planes, both horizon roles, constellation layers, poles,
legends, counts, context, credits, post-mode visual overrides, title,
language, style, mode, and an explicit output file. A separate contract proves
the deterministic atlas/cartoon and print/presentation output matrix. No
production behavior changes; configuration isolation and visual closure remain.

Milestone 46D.8C closes installed-command configuration precedence and state
isolation. Sequential commands apply two unrelated partial overlays and then
packaged defaults against one reused maximal-sphere identity; observer,
geometry, appearance, and product values remain local to their own immutable
configuration and each command owns a distinct observer. A conflicting
overlay proves explicit observer, subject, field, mask, product, title,
language, and output precedence. Invalid configuration raises
`ConfigurationError` before observer, sphere, view, or drawing work. Existing
integration contracts retain reused-sphere selection, grid, mask, observer,
and cache isolation ownership. Visual and documentation closure remain.

Milestone 46D.8D makes that visual closure reproducible. The command-driven
runner renders 18 products in fresh processes: both mandatory style/mode
baselines for all six families and six diagnostic atlas-print products that
exercise the remaining high-risk visual roles. A JSON manifest records the
exact commands, image metadata, checksums, and source revision. Structural
tests keep the matrix complete and cheap; generated images require explicit
human review on the Mac before this milestone can be marked approved.

Milestone 46D.8E records that review without treating every observation as a
renderer defect. Shared grid, detail, cartoon-content, mask, and binocular
policies become named remediation owners. The matrix separates constellation
mask openings from horizon openings, removes horizon claims from regional and
binocular fields that did not demonstrate a crossing, and retains the proven
circumpolar horizon diagnostic. No production behavior changes. Subsequent
46D.8 slices own implementation and final visual approval.

Milestone 46D.8F implements the common coordinate-grid remediation without
example overrides. Packaged semantic styles provide subdued grid weight,
opacity, color, and label scale. Request-time family policy supplies the
all-sky zero parallel, 15-degree regional sampling through 60-degree fields,
and two-hour circumpolar meridians. Shared formatting and boundary-aware
placement provide `hh:mm`, signed `dd:mm`, line clearance, one central
all-sky latitude-label meridian, and principal Mollweide longitude labels.
Visual rerendering remains required before acceptance.

Milestone 46D.8F.2 refines the Galactic all-sky grid after Mac review. It draws
30-degree latitude parallels from `-60` through `60`, draws longitude
meridians every 45 degrees, and labels only `0`, `90`, `180`, and `270`
degrees. Principal longitude labels sit below the Galactic equator and to the
right of their meridian; the seam label remains inside the Mollweide ellipse.
Other family and coordinate-grid policies remain unchanged.

Milestone 46D.8G activates the existing packaged family atlas policies at the
named composition boundary, closing the command/example density discrepancy
without adding example overrides. Large-area atlas charts now receive their
adaptive DSO magnitude, minimum-size, and enabled-layer policy by chart family.
The packaged cartoon policy adds the Milky Way, Magellanic Clouds, galaxies
through magnitude 8, and only large open and globular clusters; planetary
nebulae and remnants remain omitted. Explicit detail policies and overrides
retain final precedence. Visual rerendering remains required.

Milestone 46D.8H resolves the weak cartoon regional mask at the packaged style
owner. Cartoon mask opacity rises from `0.25` to `0.68`; its pale-grey color,
z-order, mask geometry, intersection semantics, and one-pass rendering remain
unchanged, as does the atlas mask. Visual rerendering remains required.

Milestone 46D.8H.1 corrects the cartoon mode boundary so it no longer replaces
the configured mask color with the canvas sky color. The translated packaged
or user-overlay mask now reaches cartoon print and presentation unchanged.
Atlas realization and all mask geometry and rendering behavior remain intact.

Milestone 46D.8H.2 promotes the visually selected cartoon mask defaults: warm
white `#fffdf5`, opacity `0.45`, and unchanged z-order `20.0`. Packaged TOML,
the compatibility preset, and translation contracts agree exactly; atlas and
all mask geometry and rendering behavior remain unchanged.

- generate every canonical family through both its example and `wenu_chart`
  with equivalent effective options;
- prove matching resolved observer, subject, geometry, detail, appearance,
  furniture, and export requests;
- test one- and multi-constellation regional subjects, packaged groups,
  explicit fields, targets, masks, horizon roles, grids, styles, modes,
  legends, and output paths;
- prove partial overlays change only requested values and sequential commands
  do not leak state into later products or a reused maximal sphere;
- prove invalid configuration fails before catalogue loading or rendering;
- run fast, integration, visual, and full suites and compare the mandatory
  atlas-print and cartoon-presentation regression matrix;
- update current architecture, source tree, implementation reference, user
  guide, README, migration status, and test audit;
- accept no unexplained change to the atlas-print golden baseline.

## Later dynamic-sky milestones

After 46C establishes correct static-data and observed-geometry ownership:

- **47A:** solar-system ephemeris layers for planets;
- **47B:** topocentric Moon position, phase, apparent size, and orientation;
- **47C:** artificial-satellite points and sampled tracks with explicit orbital
  source identity;
- **47D:** reproducible image-frame sequences that reuse static catalogues
  while producing correctly keyed observed states.  Initial demonstrations
  cover a rotating planisphere, a Hawaii-to-Tahiti location-and-time
  trajectory viewing the Southern Cross, and coordinate-epoch precession
  through an accepted astronomical model.

These layers must use the existing `SkyLayer.spherical_geometry()` contract
and canonical chart pipeline. They do not authorize a second projection,
clipping, rendering, legend, or export implementation.  Wenu exports
deterministically named static images and frame metadata only; movie encoding,
frame rate, transitions, and audio remain the responsibility of external
tools.
