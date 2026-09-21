# Wenu current architecture v0.9

**Status:** Implemented current architecture
**Previous baseline:** `archive/architecture_history/current_architecture_v0.8.md`
**Completed migration:** `archive/migration_history/wenu_migration_0.8_to_0.9.md`
**Accepted design:** `archive/architecture_history/target_architecture_v0.9.md`
**Baseline commit:** `5da93cc`
**Closure date:** 2026-08-28

## Purpose

This document is the current architectural authority for Wenu v0.9. It
records the implemented physical-planisphere baseline and the responsibility
boundaries that current and post-v0.9 work must preserve. Detailed public APIs
and file ownership remain in `implementation_reference.md` and
`source_tree.md`. The reviewable as-is structure and coordinate-rationalization
seams are rendered in `diagrams/current_architecture_v0.9_overview.svg` and
`diagrams/coordinate_transformation_as_is_v0.9.svg`. The intended result after
49B/49C is rendered separately in
`diagrams/coordinate_transformation_target_49bc.svg`. Source-level as-is and
proposed structures plus the target runtime call sequence are indexed in
`diagrams/README.md`.

The v0.9 architecture is closed around the accepted canonical physical
polar-planisphere product: paired celestial disks, civil calendar and page
furniture, the latitude-specific folded horizon pouch, reviewed physical
appearance, curated bright and deep-sky content, and shared localization.
The optional night edition remains a later appearance experiment and is not a
condition of the canonical v0.9 architecture.

This closure records architecture and implementation state. It does not claim
that a `v0.9.0` Git tag or distribution release exists; package versions
remain governed by Git tags and setuptools-scm.

## Canonical pipeline

Wenu retains one astronomical and rendering flow:

```text
catalogues or provider state
    -> observer-independent celestial content
    -> explicitly framed spherical geometry
    -> projection-domain guard
    -> coordinate-neutral projection
    -> projected geometry and clipping
    -> chart preparation
    -> canonical renderer
    -> resolved furniture and export
```

Examples, command adapters, physical furniture, and renderers do not acquire
catalogue loading, astronomical transformation, projection selection, or chart
policy. Style and output mode change appearance, not astronomical geometry.

## Ordinary chart architecture

The implemented ordinary workflow separates:

- chart type: projection, framing, viewport, and final boundary;
- style: semantic visual appearance;
- output mode: medium, dimensions, DPI, and presentation scaling;
- detail policy: astronomical selection and density;
- observer: site and observation-time context;
- renderer: realization of prepared graphical records;
- export: one final save per declared product.

One observer-independent `CelestialSphere` may serve multiple chart families,
observers, and instants. Observer-bound realizations use explicit immutable
keys; render-local requests and configuration overlays do not leak state
between commands or products.

Regional, full-sky, all-sky, circumpolar, binocular, and polar-planisphere
products share this pipeline. PNG, PDF, and semantic SVG are output products
of the same resolved geometry and preparation path.

## Physical polar-planisphere product

The canonical v0.9 physical product contains:

- matched north and south celestial disks with independently declared
  declination limits and validated common physical scale;
- opposite face handedness implemented in geometry, never by mirroring a
  finished image or reversing text;
- a 365-day standard-time civil calendar with immutable daily, monthly, and
  label furniture;
- actual-size A4 disk pages with centre, registration, scale, face, and
  assembly records;
- a separate latitude-specific altitude-zero horizon pair;
- an accepted folded A4 pouch with cut window, cardinal furniture, hour scale,
  registration, and assembly geometry;
- deterministic page, pouch, preview, manifest, and command/export ownership.

The celestial disks remain observer-independent. Site and standard UTC offset
calibrate the civil-time relationship and the separate horizon product.
Daylight-saving behavior is instruction policy, not a second astronomical
scale.

Polar projection, calendar geometry, page furniture, horizon transformation,
pouch furniture, rendering, preview, and export remain distinct owners.
Physical millimetre geometry is resolved before Matplotlib realization and is
not inferred from display pixels.

## Content, appearance, and localization

One packaged polar detail policy owns the reviewed stellar, constellation,
Milky Way, Magellanic Cloud, and curated binocular/deep-sky selection. The
canonical physical appearance uses the accepted white-background palette and
reviewed magnitude mapping, including its configured bright-star treatment.

Semantic label keys and packaged language catalogues provide shared English
and Spanish generated text across chart families. Unknown caller text remains
unchanged, and unsupported language identifiers fail explicitly. Localization
does not own geometry, catalogue identifiers, or caller titles.

The optional dark night edition remains deferred until it receives physical
review under red observing light. It must reuse the same geometry and product
pipeline when undertaken.

## Coordinate and temporal boundaries

Every astronomical value must retain explicit frame, origin, epoch, observation
instant, time scale, observer, and apparent/geometric status where applicable.
Projection code remains coordinate-neutral and may not select or relabel an
astronomical frame.

Milestone 49D.2 adds an optional immutable `LayerRealizationContext` before
projection. It can carry product coordinate identity, observation context,
provider evaluation instant/time scale, and resolved reference equinox.
`SkyLayer.realize()` adapts that input to the existing
`spherical_geometry(observer, ...)` contract. Ordinary requests do not yet
supply the context and follow the exact legacy branch; no current astronomical
layer, numerical geometry, or public product changes in this milestone.

Future Sun, Moon, and planet layers must preserve the same output-neutral
boundary. They acquire provider states, transform exactly once into the
requested spherical product frame, and declare Wenu semantic identity before
projection. PNG, PDF, and SVG then share the existing projection, preparation,
Matplotlib rendering, and single export path. SVG annotation may expose the
reserved `solar-system/sun`, `solar-system/moon`, and
`solar-system/planets` hierarchy, but it must not infer astronomical identity,
recompute coordinates, add a post-export overlay, or invoke a separate SVG
generator.

The 49D.2 handoff and this output-neutral moving-object boundary were
scientifically, pedagogically, and technically accepted by Fernando on
2026-08-29. They remain review-branch additions until merged.

The proposed 49E.1 ephemeris boundary distinguishes a Cartesian state source
from observer-relative direction realization. A source state must preserve
its target, centre, frame, instant/time scale, position/velocity units, kernel
identity, coverage, and provenance. Light-time and apparent-place physics are
resolved before the result becomes spherical chart geometry; a raw
barycentric vector must never be relabelled as an ICRS sky direction. This is
a design candidate only and changes no installed runtime path.

The accepted 49E.1 decisions require complete position-velocity states,
provider/model plus filename/SHA-256/coverage kernel identity, and a shared
request/session ephemeris resource. Because Wenu is unreleased and the as-is
runtime has only one helper default plus two tests using it,
`PositionStatus.TOPOCENTRIC` is removed atomically in 49E.2;
observer-centred origin and physical correction status remain separate. Venus
is the first planned 49I.1 body, followed by the Moon.

49E.2 installs only renderer-neutral Cartesian boundary types in
`ephemeris.py`: resolved resource identity, geometric state request, complete
position-velocity state, and structural state source. The types own no kernel
I/O, observer-relative direction realization, coordinate transformation,
chart, or output policy. A deterministic source exists only in tests. `observer_altaz_spec()` has no status default:
observer-transformed celestial directions explicitly use `APPARENT`, native
observer-local references use `GEOMETRIC`, and `OBSERVED` remains reserved for
future atmospheric realization.

49E.3 installs `SkyfieldEphemerisStateSource` as a borrowed-resource adapter.
It hashes the exact already-open BSP file once, records conservative common
segment coverage in TDB, and returns simultaneous geometric target-minus-centre
ICRF states in AU and AU/day. It owns no observer-relative direction physics,
moving-object layer, projection, renderer, or output path.

The accepted 49E.4 audit defines the next boundary without changing runtime
code. Astrometric direction realization combines the observer's barycentric
state at reception with iterated target states at retarded emission times and
retains distance, one-way light time, both instants, convergence policy, and
resource provenance. Apparent-place realization is a later explicit step that
adds gravitational deflection and aberration. Neither step selects an equinox:
native spherical directions use fixed ICRS axes before `CoordinateService`
performs any requested product-frame transformation.

Fernando scientifically accepted that boundary on 2026-08-30 after all 45
current-documentation tests passed in 2.03 seconds. Runtime realization remains
49E.5 and is not part of the implemented as-is architecture yet.

The accepted 49E.5 implementation supplies the renderer-neutral astrometric stage.
One typed observer barycentric state at reception and repeated typed target
states at retarded emission times produce an observer-origin ICRS
`SphericalPoints` value plus retained distance, light-time, emission-time,
iteration, target, observer, and exact resource evidence. The candidate is not
connected to a production sky layer and changes no chart or output.

Fernando scientifically accepted the implementation and installed-DE440 Venus
comparison on 2026-08-30 after 111 focused tests, 1,848 routine tests with 30
deselected, and all 1,878 tests passed. Apparent place remains 49E.6; drawable
Venus remains 49I.1.

The accepted 49E.6 implementation adds the renderer-neutral apparent stage. It
consumes the accepted 49E.5 astrometric result, including retained relative
velocity, and uses Skyfield `apparent()` for explicit gravitational deflection
and aberration without invoking `observe()` again. Same-kernel, same-resource,
same-observer-state, and same-reception-instant checks protect the handoff.

The result is an observer-origin apparent direction on fixed ICRS-oriented
axes. Apparent is a physical correction status, not a reference frame or an
equinox-of-date selection. No sky layer or output path consumes the candidate;
future Venus geometry must still pass once through the product-frame,
projection, renderer, and shared PNG/PDF/SVG pipeline.

Fernando scientifically accepted 49E.6 and its installed-DE440 Venus
comparison on 2026-08-30 after 95 focused tests and all 1,883 tests passed.
Residuals from direct Skyfield were `3.152e-11` degree in right ascension and
`1.544e-12` degree in declination. Drawable Venus remains 49I.1.

The 49I.1 audit identifies one remaining chart-side prerequisite. Although
`LayerRealizationContext` and `SkyLayer.realize()` exist, ordinary chart
facades do not yet construct and pass the product-frame context. The proposed
49I.1A closes that output-neutral handoff; 49I.1B then adds one opt-in Venus
layer using the accepted provider, astrometric, apparent, transformation,
projection, renderer, and shared-export sequence. No 49I.1 runtime or visible
planet is part of the implemented architecture yet.

Fernando scientifically and architecturally accepted the 49I.1 audit on
2026-08-30 after all 48 current-documentation tests passed in 3.30 seconds.
The accepted audit changes no runtime type or output; 49I.1A remains the next
implementation milestone.

The accepted 49I.1A implementation closes the ordinary request-to-layer context
handoff. One request-derived `LayerRealizationContext` reaches every canonical
chart facade before `CelestialSphere.draw_chart()`. Existing layers ignore it
through the concrete compatibility adapter and retain their established
geometry. Ordinary pre-projection products are currently horizontal for
planisphere, regional, circumpolar, and binocular, and Galactic for all-sky;
the reference equinox remains a separate field. No Venus layer or visible
output is installed by 49I.1A.

Fernando scientifically and architecturally accepted 49I.1A on 2026-08-30
after 166 focused tests, 1,859 routine tests with 30 deselected, and all 1,890
tests passed. The full suite also verified UTC-datetime normalization for the
ordinary chart-view observer contract. 49I.1B is the next bounded slice.

The accepted 49I.1B implementation installs one dormant `VenusLayer` in the canonical
sphere. `--planet venus` enables it; the layer borrows the observer kernel,
uses the accepted astrometric/apparent chain, and transforms once into the
49I.1A product coordinate specification before ordinary projection. It adds
no physical disk or alternative SVG path and is scientifically and visually
accepted. Fernando's installed-DE440 comparison placed Venus at the
Stellarium position for the declared La Ligua instant; PNG, PDF, and semantic
SVG looked the same. Acceptance passed the 148-test implementation review, 35
focused post-correction tests, and all 1,898 tests in 82.01 seconds.

The proposed 49I.2 audit now distinguishes the common moving-body chart
pipeline from its interchangeable state-source and appearance policies.
Current code proves one installed JPL/Skyfield Venus route only. The Moon is
the next proposed body because strong topocentric parallax tests observer
ownership; its correction policy must be compared with direct Skyfield rather
than inherited from Venus by assumption. No Moon or generic body layer is part
of the implemented architecture yet.

Fernando scientifically and architecturally accepted the 49I.2 audit on
2026-08-30 after all 51 current-documentation tests passed in 1.88 seconds.
The accepted audit changes no runtime type or output. 49I.2A Moon numerical
direction validation is the next bounded implementation.

Fernando scientifically accepted 49I.2A on 2026-08-30 after 102 focused tests
passed in 1.99 seconds and the installed-DE440 validator agreed with direct
Skyfield to 0.1503 mas in right ascension and 0.0624 mas in declination. The
accepted validation measured 0.9500231004-degree topocentric-geocentric
parallax and a 27.91-mas 52 m minus 0 m observer-height displacement. The
complete suite then passed all 1,902 tests in 89.59 seconds. It adds no runtime
production type or chart content.

The accepted 49I.2B implementation extracts the shared renderer-neutral
symbolic-point orchestration into `sky/solar_system_points.py`. A frozen descriptor owns body
identity, declared centre, selection key, and explicit correction policy.
`VenusLayer` is now a thin specialization with unchanged downstream ownership;
a test-only Moon descriptor proves reuse without installing Moon content.
Verification passed all 1,912 tests, and main-versus-branch Venus products
were identical at the PNG, rendered-PDF, and normalized semantic-SVG levels.
Fernando scientifically and architecturally accepted 49I.2B on 2026-08-30.

The accepted 49I.2C implementation installs a thin default-off Moon
specialization and
replaces planet-only internal selection with one request-owned
`solar_system_objects` set. Class-aware `--planet venus` and `--moon` inputs
therefore converge before detail application. The Moon retains natural-
satellite semantics and the ordinary style, projection, renderer, and exporter
owners; physical disk and phase remain deferred. Fernando scientifically,
architecturally, and visually accepted this symbolic Moon slice on 2026-08-30
after all 1,917 tests and the PNG/PDF/SVG comparison passed.

The accepted 49I.2D audit places a shared Solar-System trajectory contract
before physical-disk work. It distinguishes each body's sample reception
instants from the single fixed chart-frame instant, assembles accepted apparent
directions as one typed spherical curve, and reuses the existing vectorized
coordinate, projection, clipping, renderer, and export path. Major-time anchors
remain scientific metadata; visible perpendicular ticks and the starting-date
label are projected annotations. Fernando scientifically and architecturally
accepted the audit on 2026-08-31 after 55 documentation tests, 1,889 routine
tests with 30 deselected, and all 1,919 tests passed. The audit changes no
runtime source, public interface, numerical geometry, or output.

The accepted 49I.2D.1 implementation adds the renderer-neutral
scientific curve only. One frozen request merges regular samples and exact
major-time anchors. The accepted scalar observer-state, astrometric, and
apparent chain is reevaluated at every vertex using one borrowed ephemeris
resource. Complete apparent directions are assembled as one open
`SphericalCurves`, then transformed exactly once into the fixed product
frame. The installed-DE440 validator agreed with direct Skyfield to
`4.293e-10` degree in right ascension and `8.471e-11` degree in
declination. Fernando accepted the slice after all 1,929 tests passed. It adds
no registered layer, public option, projected annotation, style, renderer, or
output change.

The implemented temporal sequence contracts distinguish physical instants,
civil/display time, sampling cadence, and playback cadence. The accepted
fixed-sky reference keeps the celestial scene and equatorial grid anchored
while the observer-local horizon and AltAz grid rotate. Complete independent
renders remain the correctness oracle for later reuse optimization.

Implemented `CoordinateSpec` and coordinate-service ownership plus future
provider, moving-object, public-coordinate, and reuse work are governed by
`post_v0.9_architecture_roadmap.md` and must preserve this v0.9 pipeline.

## Configuration and public boundaries

Packaged defaults and schema-version-2 configuration resolve into immutable
typed contracts. User overlays merge non-mutatingly; explicit command values
override overlays; sequential invocations share no active configuration
singleton.

The installed `wenu_chart` interface and canonical examples are adapters over
the same public drawing and export workflow. They do not import one another or
create alternative astronomical, rendering, or physical-product paths.

## Acceptance and regression authority

Automated tests protect scientific geometry, ownership, configuration,
localization, output, and physical-size contracts. Atlas-print remains the
visual regression baseline for ordinary pre-v0.9 families. The accepted
white-background polar disks and folded pouch are the physical v0.9 baseline.

Human inspection remains authoritative for paper scale, readability,
registration, cutting, assembly, classroom use, and appearance. The accepted
49H.3 reference additionally establishes the fixed-celestial-scene and
rotating-observer-horizon behavior.

The routine regression gate is expected to complete in less than 30 seconds on
Fernando's Intel Mac. The complete suite plus any milestone-specific
scientific, SVG, visual, print, sequence, or classroom acceptance remains
mandatory before milestone closure.

## Active authority after v0.9

Current work reads this document together with:

- `implementation_reference.md` for public and advanced API contracts;
- `source_tree.md` for responsibility ownership;
- `post_v0.9_architecture_roadmap.md` for active milestone sequencing;
- `target_architecture_v0.9.5.md` for the proposed coordinate-rationalization
  target and minimal 49B/49C roadmap;
- `coordinate_system_guide_v0.9.5.md` for living equations, coordinate
  conventions, code ownership, object inventory, and provenance;
- `archive/audits/coordinate_transformation_audit_09a2afd.md` for scientific coordinate
  evidence;
- `archive/audits/public_interface_audit_v0.9.5.md` for the accepted executable inventory and
  public system, frame, equinox, and epoch boundary;
- `archive/milestone_history/49d_scene/celestial_scene_dependency_audit_49d1.md` and
  `archive/milestone_history/49d_scene/layer_realization_context_49d2.md` for scene dependencies and the minimal
  pre-projection realization handoff;
- `archive/milestone_history/49f_svg/svg_output_audit_and_plan.md` for SVG product evidence.

The v0.8 architecture, v0.9 target, and v0.8-to-v0.9 migration documents are
provenance. They do not override this implemented baseline.

## Accepted drawable Solar-System trajectory

Milestone 49I.2D.2 installs the first visible Venus trajectory in regional and
binocular charts. The scientific `SolarSystemTrackLayer` remains in
`wenu.sky`; projected ticks and two-pass perpendicular date placement belong
to `wenu.charts.solar_system_track_annotations`. Style owns the accepted
amber-orange appearance. The same prepared geometry reaches PNG, PDF, and
semantic SVG at `sky/solar_system/planets/venus/track`.


## Deferred physical Solar-System appearance

Milestone 49I.3A is an accepted contract audit, not implemented architecture.
The current runtime still realizes Venus and the Moon as apparent centre
points and style still draws provisional fixed hollow symbols. No current
record carries physical angular diameter, illuminated fraction, bright-limb
orientation, body orientation, photometry, or display magnification.

The accepted boundary keeps a future physical-appearance state renderer-neutral
and keeps object-specific display magnification outside that scientific state.
Any resolved disk must become ordinary semantic geometry before the existing
projection, clipping, renderer, and shared exporter.


## Accepted Venus physical-appearance state

Milestone 49I.3B installs `wenu.solar_system_appearance` as a
renderer-neutral numerical boundary. `SolarSystemApparentDisk` accompanies
the accepted Venus direction with physical radius, angular diameter, phase,
illuminated fraction, and apparent-ICRS bright-limb position angle. It carries
no display magnification or chart/output policy.

No production layer consumes the state yet. Current Venus and Moon chart
appearance remains the existing symbolic points. There is no resolved disk,
request, style, renderer, or output change in 49I.3B.


## Accepted resolved Venus disk boundary

Milestone 49I.3C accepts an illuminated `SphericalPolygons` layer plus limb
and terminator `SphericalCurves` layers sampled at the physical angular radius.
After ordinary projection, chart preparation applies Venus-specific display
magnification about the projected physical centre. This avoids forcing mixed
geometry into the curve-only `SphericalGrid` contract and avoids
renderer-specific disk artists.

The accepted future capability includes several independently realized Venus
disks in one fixed chart frame. Milestone 49I.3C.1 now installs the
output-neutral physical centre, limb, visible terminator, and illuminated-face
spherical geometry bundle. No sky layer, chart request, magnification, style,
renderer, or output behavior consumes it yet. Current symbolic Venus output
remains authoritative.


## Drawable resolved Venus disk

Milestone 49I.3C.2 installs one opt-in resolved Venus disk for regional and
binocular charts. Three sky layers share one physical appearance realization:
an illuminated polygon, a closed limb curve, and a visible terminator curve.
The ordinary projection pipeline projects each component and the physical
centre; chart preparation then scales projected offsets by the Venus-specific
display magnification about that exact projected centre.

Symbolic Venus remains the default. A request cannot select symbolic and
resolved Venus simultaneously. Magnification alone cannot enable the disk,
factor 1 retains physical angular scale, and planisphere/all-sky products
retain symbolic representation. Direct Python chart requests and the CLI
install the same request-owned layers.


## Accepted multi-epoch resolved planet-disk boundary

Milestone 49I.3C.3 audits two distinct static sequence products. Observed
sequences independently realize the topocentric observer and planet appearance
at every sample before transformation into one fixed chart frame. Frozen-Earth
ecliptic sequences instead freeze Earth's heliocentric position at the start,
advance the planet geometrically, and permit only the planet disks, a central
six-point Sun symbol, and the equatorial grid in the fixed ecliptic frame.

Every accepted sample retains full physical distance, origin, unit, instant,
and provider provenance for possible future independently governed 3D
Solar-System visualization. No 3D runtime is installed.

Both policies reuse the accepted per-epoch spherical disk geometry and
object-specific post-projection magnification around each separately projected
centre. The frozen construction is not apparent sky and must retain that status
in labels and metadata. Fernando accepted the audit on 2026-08-31 after all 63
current-documentation tests passed in 2.04 seconds. It changes no implemented
runtime or output.


## Accepted output-neutral observed Venus disk sequence

Milestone 49I.3C.3.1A adds immutable start-inclusive major sampling and
independently realizes the observer, apparent Venus and Sun directions,
physical appearance, and spherical disk geometry at every epoch. The result
retains full observer/AU distances with provider and instant evidence for
possible future independently governed 3D use.

The native physical geometries deliberately remain per epoch because their
apparent coordinate identities carry different instants. A later drawable
slice must transform each independently into one fixed product frame before
aggregation. No request option, registered layer, chart transformation,
projection, magnification, renderer, or visible output is installed.


## Drawable observed Venus disk sequence

Milestone 49I.3C.3.1B installs the accepted observed sequence in regional and
binocular charts. Each physical epoch is transformed independently into the
fixed product frame before illuminated faces, limbs, terminators, and optional
date centres are aggregated. Chart preparation magnifies each projected
component around its own projected physical centre.

Combined geometry retains exact instants, time scale, observer/AU distances,
and provenance. Symbolic Venus, one resolved Venus disk, and a resolved Venus
sequence are mutually exclusive. Frozen-Earth mode, Mercury, and 3D
visualization remain unimplemented.


## Accepted output-neutral frozen-Earth Venus sequence

Milestone 49I.3C.3.2A freezes Earth's heliocentric ICRF vector at the start
and evaluates Venus heliocentrically at exact major epochs. Each result retains
the frozen Earth vector, relative target vector, frozen-earth/AU distance,
physical diameter, phase, illuminated fraction, and fixed-ecliptic limb
orientation. Target and fixed-Sun directions are geometric in J2000
mean-ecliptic axes and must never be described as apparent sky.

This state remains output-neutral. Public request integration, resolved disk
adaptation, per-centre projected magnification, central six-point Sun,
equatorial grid, restricted scene, semantics, and rendering remain
49I.3C.3.2B. Mercury remains 49I.3C.3.3; no 3D visualizer is installed.


## Drawable frozen-Earth Venus disk sequence

Milestone 49I.3C.3.2B installs the accepted frozen construction in regional
charts. Exact start-inclusive Venus states share ordinary illuminated, limb,
terminator, optional-label, and central fixed-Sun spherical layers. Each Venus
disk is magnified after projection about its own physical centre.

The restricted scene permits only those sequence layers, the fixed Sun, an
optional equatorial grid, and an explicitly requested ecliptic reference. The
ecliptic is latitude zero in the fixed product frame; the equatorial grid is
transformed directly from FK5 into those same J2000 mean-ecliptic axes. Neither
reference depends on observer AltAz geometry. Automatic English and Spanish
titles and reference labels use the resolved chart language.

All retained directions remain frozen-observer geometric, not apparent sky.
Mercury remains 49I.3C.3.3; no 3D visualizer is installed.


## Mercury generalization audit boundary

The accepted Milestone 49I.3C.3.3 audit governs, but does not implement,
Mercury reuse. The
accepted sequence request/result and physical spherical disk geometry are
already target-parameterized. CLI selection, body constants, drawable layers,
style lookup, cleanup, semantic roots, localization, and installed-kernel
evidence remain Venus-specific.

The authorized first runtime slice is output-neutral Mercury descriptor/radius
state plus an installed-DE440 frozen-Earth comparison. Only a separately
accepted second slice may generalize the drawable frozen sequence. No Mercury
runtime, public request, style, semantic output, or chart is currently
installed.


## Output-neutral lunar physical appearance

Milestone 49I.3E.1 registers one immutable Moon body descriptor with physical
body ID `301`, Earth parent relationship, JPL equal-volume mean radius
`1737.4 km`, localization, symbolic compatibility, and an output-neutral
spherical-appearance capability. A non-drawable Earth descriptor with body ID
`399` completes the catalog relationship without exposing Earth as a chart
target.

The generic `SolarSystemAppearanceRealizer` produces the lunar
`SolarSystemApparentDisk` from accepted topocentric Moon and Sun directions.
The physical state remains renderer-neutral and contains no magnification or
page policy. Resolved geometry, public Moon appearance controls, sequences,
styles, rendering, and visible output remain later 49I.3E slices.


## Drawable resolved single-epoch Moon

Milestone 49I.3E.2 adapts the accepted lunar physical appearance into the
generic resolved-disk layers. Bare `--moon` selects the resolved disk at
physical scale; `--moon-appearance symbolic` preserves the compatibility
point. Moon-specific magnification is display-only, post-projection, bounded
from 1 through 1000, and independent of output mode.

The Moon descriptor authorizes its disk in regional, binocular, circumpolar,
planisphere, and Mollweide all-sky products without broadening Venus support.
Generic 720-sample geometry, transformation, preparation, rendering,
semantics, and exporters own the output. Multi-epoch Moon behavior remains
unimplemented under 49I.3E.3. Fernando accepted the single-epoch scientific,
architectural, visual, operational, and regression result on 2026-09-02.


## Observed multi-epoch Moon sequence

Milestone 49I.3E.3 adapts `--moon-disk-sequence` into the generic
`ObservedSolarSystemDiskSequenceRequest`. Every sample independently realizes
the topocentric Moon and its physical appearance, then transforms complete
spherical disk geometry into the one product frame fixed at the chart epoch.
The background, horizon, projection, and furniture therefore do not rotate
between samples.

Descriptor policy authorizes observed Moon sequences in all five chart
families while preserving Venus's regional/binocular boundary. Shared labels,
per-centre post-projection magnification, semantics, clipping, and PNG/PDF/SVG
export remain generic. Frozen-Earth lunar sequences remain unimplemented.



## Completed resolved Moon capability (Milestone 49I.3E)

Milestones 49I.3E.0 through 49I.3E.3 are closed. The implemented architecture
has one catalog Moon identity and Earth relationship, one renderer-neutral
physical appearance state, shared illuminated spherical-disk geometry, a
resolved single-epoch request, symbolic compatibility, and an observed
multi-epoch request. Single disks and independently realized sequence samples
use ordinary transformation, projection, per-centre post-projection
magnification, rendering, semantic SVG, and export owners in all five ordinary
chart families.

The sequence preserves one chart-epoch product frame while each sample retains
its own apparent centre, distance, diameter, phase, illuminated fraction, and
complete tangent geometry. No Moon-specific projection, renderer, or exporter
exists. Parent closure adds no runtime behavior; Frozen-Earth lunar sequences,
interpolation, animation, texture, libration, eclipses, disk refraction, and
occultation prediction remain unimplemented.


## Performance closure boundary (Milestone 49J)

The current complete-frame authority remains `generate_chart_request()`;
fixed-sky and observer-time sequences call that static path for every frame.
`tools/benchmark_reusable_sphere.py` is a separate shared-sphere diagnostic
whose overlapping profiler categories are non-additive. It is not a cold
independent-frame oracle.

The accepted historical audit at
`archive/milestone_history/49j_performance/performance_and_closure_audit_49j0.md`
freezes exclusive stage timing and the first fixed-sky circumpolar reuse
candidate. `post_v0.9_architecture_roadmap.md` records the accepted
test-practice, measurement, and optimization sequence and governs the current
minor-body and publication programs. Planning adds no instrumentation, cache,
optimization, test reclassification, or runtime/output change.

The accepted 49J.1 evidence is recorded in
`archive/milestone_history/49j_performance/test_architecture_and_accepted_practice_audit_49j1.md`.
Static inspection
found no session-scoped fixture or `tests/conftest.py`, despite the older
source-tree description of a session-scoped canonical build registry; 49J.2
corrected that description. Repeated Mac evidence found 27.16-second routine
and 85.49-second complete medians. The accepted policy is archived at
`archive/milestone_history/49j_performance/test_practice_decisions_49j2.md`.
`archive/milestone_history/49j_performance/test_entry_and_admission_49j3a.md`
implements reproducible documented test entry and admission rules without
changing tests or runtime architecture.
`archive/milestone_history/49j_performance/marker_truthfulness_49j3b.md` records
the completed marker audit and gate-membership correction.
`archive/milestone_history/49j_performance/repository_source_index_49j3c.md`
records the completed test-only immutable source inventory and lazy
parsed-source index.
`archive/milestone_history/49j_performance/immutable_catalogue_fixture_49j3d.md`
records the accepted catalogue-summary fixture and rejection of session-scoped
canonical-sphere reuse.
`archive/milestone_history/49j_performance/cold_builder_kernel_oracles_49j3e.md`
records the accepted preservation of distinct cold builders and independently
recomputed installed-kernel scientific validators.
`archive/milestone_history/49j_performance/calendar_layout_cost_49j3f.md`
records the accepted removal of redundant test-only canvas redraws while
retaining physical text-containment measurement.
`archive/milestone_history/49j_performance/observer_time_sequence_oracle_49j3g.md`
records the accepted decision to retain the cold two-frame canonical
observer-time route unchanged.
`archive/milestone_history/49j_performance/test_suite_optimization_closure_49j3h.md`
records the accepted 49J.3 fault-model and test-file-growth closure.
`archive/milestone_history/49j_performance/cold_frame_performance_baseline_49j4.md`
records the accepted diagnostic harness:
three fresh circumpolar frames traverse `generate_chart_request()`, while
exclusive nanosecond spans and residual are observed without changing an
installed interface, runtime owner, cache, or chart output.
`archive/milestone_history/49j_performance/loaded_sphere_reuse_49j5a.md` owns
the accepted opt-in execution seam. The accepted comparison in
`archive/milestone_history/49j_performance/fixed_sky_reuse_equivalence_49j5b.md`
matches it exactly with the cold oracle, and
`archive/milestone_history/49j_performance/performance_closure_49j6.md` closes
49J.
The fixed-sky orchestrator may reuse one observer-independent canonical sphere,
but each frame supplies a fresh observer to the unchanged complete request
route. The cold independent-frame execution remains the default oracle.

## Minor-body provider boundary (accepted Milestone 50A.0)

`archive/milestone_history/50a_minor_bodies/minor_body_scientific_provider_audit_50a0.md`
accepts the provider boundary without changing implemented architecture.
Asteroids and comets must still produce the existing geometric
`EphemerisState`, then use the accepted astrometric/apparent realization and
descriptor-driven moving-body pipeline. The first source is a bounded local
Horizons small-body SPK with an explicit companion planetary-resource chain;
rendering remains offline and no two-body element propagator is an implicit
fallback. The next authorized implementation is the 50A.1 provider/resource
seam only.

## Minor-body state-provider seam (Milestone 50A.1 accepted)

`ephemeris.py` now admits either one `EphemerisResourceIdentity` or an explicit
`EphemerisResourceChain` on a geometric state. Existing planetary states retain
their original single-resource identity. `minor_body_ephemeris.py` adds a
frozen Horizons solution identity and an unconnected
`SkyfieldMinorBodyStateSource` that borrows a small-body kernel, a planetary
state source, and a timescale.
Its frozen `MinorBodyEphemerisState` remains an `EphemerisState` while retaining
the typed orbit solution and selected SPK segment on each result.

The small-body segment supplies target relative to its declared centre. The
planetary source supplies that numeric centre relative to the requested centre
at the same TDB instant. Their positions and velocities are composed only after
the dependency request, resource, frame, and AU/AU-day units are validated.
No observer, light-time, apparent-place, spherical-geometry, catalog, chart, or
output owner consumes this provider yet.

Milestone 50A.2 adds `SpiceMinorBodyKernel` as the explicit owner of one local
Horizons DAF/SPK handle. It evaluates a selected type-21 descriptor through
CSPICE `spkpvn()` without furnishing a global kernel or allowing hidden SPICE
composition. The existing astrometric realizer now accepts a target resource
chain only when it explicitly contains the observer's planetary resource;
Skyfield remains the DE440, observer-state, and apparent-place owner. This seam
is exercised only by the validator and remains unconnected to a body or chart.

## Drawable Ceres point and track (Milestone 50A.3B accepted)

`archive/milestone_history/50a_minor_bodies/drawable_ceres_50a3b.md` records the accepted bounded
Ceres connection. `CERES_BODY` joins the descriptor catalog with a stable
minor-body identity and symbolic-point plus apparent-track capabilities.
`MinorBodyResourceSession` validates an explicit local acquisition manifest,
opens the declared SPK once per chart build, and supplies a descriptor-aware
`EphemerisSourceBinding`: the Ceres provider owns the target state, while the
existing DE440/Skyfield provider continues to own observer state and apparent
corrections. The shared point and track realizers, fixed product frame,
projection, preparation, semantic SVG, renderers, and exporters remain the
ordinary route. Fernando accepted the macOS PNG and semantic SVG; 50A.3 is
closed. Milestone 50A.3G now verifies the merged explicit CLI contract visually
before 50A.4 comet numerical validation begins.

## Object-centered regional framing and explicit CLI semantics

Explicit point-center identity is resolved before regional chart construction.
`get_object_center()` overloads fixed `ResolvedTarget` values and
descriptor-driven Solar-System bodies into the same apparent observer-
horizontal point contract. Regional framing consumes that result while the
ordinary detail, spatial-selection, projection, preparation, renderer, and
export owners remain unchanged. Drawing selectors never supply a center.
Planets, the Moon, installed asteroids, packaged stellar and deep-sky targets,
and explicit ICRS or horizontal coordinates use the same chart family only
through an explicit CLI or effective-configuration center.
Constellation geometry remains the independent extended-region framing case.

## Installed-CLI moving-object preflight

For exact numbered asteroids, `wenu_chart` resolves data before building the
chart. `minor_body_acquisition.py` is the sole network and immutable-cache
owner; it returns a verified local manifest-backed directory. The request,
coordinate, projection, rendering, and export pipeline remains offline. Public
policies are `acquire-if-missing` (default), `offline`, and `refresh`; an
explicit resource directory is authoritative and read-only.

## Provider-neutral satellite crossing domain (Milestone 50S.1 accepted)

The dormant `satellite_crossings.py` domain boundary defines immutable
satellite identity, terrestrial observer/site, explicitly framed closed
circular field, inclusive UTC interval, provider candidate, and normalized
connected-visit result contracts. It reuses `CoordinateSpec` and is not
exported through the public package facade or consumed by the canonical chart
pipeline. No satellite acquisition, orbit solution, propagation, coordinate
transformation, exact crossing solver, report, drawing, or output changes in
this accepted milestone. Fernando accepted the implementation on 2026-09-15
after all 2,428 tests passed; PR #123 merged it as `23b851b`.


## 50S.2B SatChecker adapter boundary (accepted)

The dedicated 50S.2B milestone branch adds a dormant `satchecker.py` provider
boundary. It maps only geometric topocentric-direction ICRS circular fields to
the versioned asynchronous SatChecker endpoint, performs explicit UTC-to-UT1
conversion with Astropy automatic IERS download disabled, and exposes one-shot
`submit()` and `poll()` operations. There is no retry, concurrency, hidden
wait loop, import-time access, chart-construction access, or ordinary-test
network dependency.

Exact response bytes become immutable SHA-256-addressed local receipts.
`SatCheckerCache` keys the complete Wenu request, transmitted parameters,
resolved endpoint, Earth-orientation identity, and adapter schema, and validates
both response bytes and stored normalized interpretation on reuse. Successful
provider output becomes `SatelliteCrossingCandidate` with ordered
`SatCheckerSample` evidence. The adapter does not create
`SatelliteCrossingResult`, exact crossing events, satellite states,
illumination physics, reports, tracks, projection, rendering, or export. Fernando scientifically and architecturally accepted this implementation on
2026-09-15. The focused provider/domain gate passed all 45 tests in 1.79
seconds, the expanded focused gate passed all 168 tests in 3.89 seconds, and
the complete plugin-disabled suite passed all 2,457 tests in 88.48 seconds.
Only 50S.3 reporting and drawing is authorized next.


## 50S.3B sampled-candidate presentation boundary (accepted)

Candidate 50S.3B adds a dormant renderer-neutral
`satellite_presentations.py` boundary and two ordinary sky layers in
`sky/satellite_candidate_layer.py`. A `SatCheckerPresentation` accepts one
terminal `SatCheckerResponse`, retains its exact receipt digest and normalized
query/evidence, sorts candidates by full NORAD catalogue identifier, and emits
deterministic human-readable and versioned JSON products.

`SatelliteCandidateTrackLayer` realizes two or more ordered samples as one
open spherical curve and realizes a singleton as one point.
`SatelliteCandidateSamplesLayer` exposes only supplied points with optional
UTC labels. Both consume `SatCheckerCandidateEvidence`, transform through
`CoordinateService` into the request product frame, and then use
`CelestialSphere.draw_chart()`, projection, preparation, renderer, semantic
SVG, and PNG/PDF/SVG export unchanged.

The stable semantic roots are
`sky/artificial_satellites/satchecker_candidates/norad_<id>/sampled_track`
and `.../samples`. No entry, exit, closest approach, interpolation,
propagation, provider access, illumination calculation, magnitude, or detector
claim is introduced. Fernando visually accepted the network-free synthetic text report and centered
FoV chart on 2026-09-15 after matching PNG, PDF, and semantic SVG inspection.
The final focused boundary passed all 217 tests, and the complete plugin-disabled
suite passed all 2,473 tests in 83.98 seconds. Fernando accepted the implementation and its scientific boundaries on
2026-09-15. This closes 50S.3B; only 50S.4 snapshot, propagation, and specimen
builder work is authorized next.


## Accepted 50S.4A snapshot and propagation audit

The as-is review finds no production owner for canonical OMM/GP records,
immutable satellite element snapshots, geometric TEME propagation receipts, or
the TEME/Earth-orientation/topocentric state chain. The accepted SatChecker,
provider-neutral crossing, presentation, generic Cartesian-state, coordinate,
chart, and renderer modules do not own those responsibilities.

Fernando accepted the documentation-only contract audit on 2026-09-15 after
the focused gate passed all 128 tests and the branch diff check was clean. The
accepted contract defines five bounded stages:
50S.4A contract acceptance; 50S.4B synthetic installed snapshot and element
domain; 50S.4C direct `sgp4>=2.25,<3` WGS-72 propagation into typed geometric
TEME state; 50S.4D no-download independently validated topocentric
transformation; and 50S.4E propagated sampled-specimen construction and
closure. 50S.4A added no runtime behavior, dependency, package data,
propagation, transformation, or crossing result. Acceptance closes 50S.4A and
authorizes only 50S.4B immutable OMM element and snapshot work.


## Accepted 50S.4B immutable element snapshot

The dedicated milestone branch adds the first bounded
`src/wenu/satellites/` package. `elements.py` owns immutable, fail-closed
canonical OMM/GP records; `snapshots.py` owns manifest validation,
canonical-byte and record-level SHA-256 verification, deterministic full-NORAD
ordering, duplicate rejection, immutable lookup, and installed-resource
loading.

The packaged `synthetic_50s4b_v1` snapshot contains exactly three
hand-authored non-operational LEO-like, MEO-like, and geosynchronous-like
records with six-digit synthetic identifiers. No provider response or tracked
object was copied. `sgp4>=2.25,<3` is now a direct dependency, but this
candidate adds no propagator construction, TEME state, Earth-orientation
transform, observer direction, crossing result, acquisition, or rendering.

At production commit `d3cb597`, the expanded focused gate passed all 158
tests and the complete plugin-disabled suite passed all 2,483 tests in 87.11
seconds. A wheel built from that commit was installed into an isolated virtual
environment; `load_snapshot()` loaded from `site-packages`, verified
`b6ab95df3eb180b07694b1b9bafd47c2805b6cc7ebea8636490beec03cd71457`,
and returned the ordered identifiers 900001, 900002, and 900003. Fernando
accepted the implementation and its bounded scientific ownership on
2026-09-15. This closes 50S.4B and authorizes only 50S.4C validated SGP4/TEME
propagation.


## Accepted 50S.4C validated SGP4/TEME propagation

`satellites/sgp4.py` now owns the bounded mapping from one accepted
`SatelliteElementRecord` to the upstream `Satrec` API. Initialization passes
WGS-72 explicitly, retains improved operation mode, supplies evaluation time as
separate Julian-day and fractional-day values, raises every non-zero SGP4
status explicitly, and returns immutable `SatelliteTemeState` values with
geocentric geometric TEME position in kilometres and velocity in kilometres
per second.

The wrapper records complete satellite/source/snapshot identity, canonical UTC,
both Julian-date components, element age, SGP4 package version, implementation
backend, WGS-72, operation mode, status, provenance, and warnings. Scalar and
array routes share the same state construction; the array route uses upstream
acceleration when available and otherwise preserves the scalar contract.

The admission review found that the first synthetic IDs 900001–900003 exceeded
the upstream `Satrec` maximum 339999. The snapshot was transparently corrected
to valid six-digit synthetic IDs 300001–300003 and every affected digest was
regenerated. Wenu does not pass a hidden surrogate identity to SGP4.

Pinned Vallado verification cases cover near-Earth satellite 5 and deep-space
satellite 4632 at epoch, while the upstream published terminal-error case
44160 verifies explicit failure. The candidate adds no ITRS, observer,
topocentric direction, crossing solver, acquisition, presentation, or
rendering behavior.

At production commit `e0d7c78`, the expanded focused gate passed all 167
tests and the complete plugin-disabled suite passed all 2,492 tests in 86.88
seconds. An isolated wheel installation then loaded Wenu from `site-packages`,
verified corrected snapshot digest
`2e5288a6aad9fbe29cfe6d9a60e0045be28501859d8c739135fd302460ece5fe`,
and propagated all three identifiers with TEME/WGS-72/status zero.


Fernando scientifically and architecturally accepted 50S.4C on 2026-09-15 after the 15-test initial gate, 167-test expanded gate, all 2,492 tests, the 132-test documentation gate, and installed-wheel propagation evidence. This closes 50S.4C and authorizes only 50S.4D Earth-orientation and topocentric state work.


## Accepted 50S.4D Earth-orientation and topocentric state

The accepted implementation adds `satellites/topocentric.py` as the owner of the
Cartesian TEME → geocentric ITRS → observer-subtracted topocentric ITRS chain.
It consumes an accepted `SatelliteTemeState` and `SatelliteObserver`, selects
the installed bundled IERS-A file explicitly with automatic download disabled,
and records the file SHA-256, installed package versions, coverage, UT1−UTC,
polar motion, and interpolation statuses. Instants outside the installed table
coverage fail closed.

The immutable `SatelliteTopocentricState` retains satellite, observer, TEME,
ITRS, topocentric Cartesian, range, vacuum AltAz, and coordinate/provenance
evidence. Its celestial values are a topocentric geometric vector expressed in
GCRS axes; they are deliberately not labelled ICRS, a GCRS coordinate,
astrometric, apparent, or observed. The generic `CoordinateService` remains
unchanged because it transforms already represented spherical geometry rather
than satellite Cartesian state.

The initial 17-test topocentric gate, 89-test expanded satellite/coordinate
gate, 133-test documentation gate, and complete plugin-disabled suite of 2,511
tests in 95.10 seconds pass on Fernando's Mac. The final diff check is clean.
Fernando scientifically and architecturally accepted 50S.4D on 2026-09-15.
Acceptance closes the Earth-orientation/topocentric boundary and authorizes
only bounded 50S.4E propagated-specimen builder work. No crossing, field
intersection, illumination, photometry, CLI, chart, or specimen behavior is
added by 50S.4D.

### Accepted 50S.4E propagated sampled specimens

`tools/build_50s4_satellite_specimens.py` is the candidate developer-only
50S.4E composition boundary. It loads the installed
`synthetic_50s4b_v1` snapshot, propagates its ordered records through the
accepted SGP4/TEME and topocentric chains, and writes one deterministic JSON
document only beneath a caller-selected output directory.

The document records the snapshot digest and record identity, evaluation grid,
observer, exact Earth-orientation resource, propagator identity, software
version, sampled TEME states, sampled topocentric states, and bounded query
inputs. It is labelled **propagated sampled specimens — not verified
crossings**. It has no network client, does not construct
`SatelliteCrossingResult`, does not find entry/exit or closest approach, and
does not define production solver tolerances or implement 50S.5.

#### Accepted 50S.4E gate evidence

On macOS with Python 3.11.7, the dedicated builder gate passed all 10 tests in
10.58 seconds, the expanded satellite/coordinate gate passed all 99 tests in
18.07 seconds, the documentation gate passed all 134 tests in 2.45 seconds,
and the complete plugin-disabled suite passed all 2,522 tests in 105.38
seconds. The generated JSON had SHA-256
`16137e9380404dca03789532ab029c4159755c69dd2ab0ca5990a82cd9c42374`.
The branch was clean and `git diff --check 243b75c...HEAD` passed. Fernando scientifically and architecturally accepted 50S.4E on 2026-09-15.

Acceptance closes 50S.4. The next authorized boundary is only bounded 50S.5
complete local FoV-crossing oracle work; no 50S.6 optimization or later
satellite behavior is authorized.


### Accepted 50S.5A complete-oracle audit

The documentation-only 50S.5A review adds no runtime behavior. It identifies
the accepted 50S.4C/50S.4D chain as the only local trajectory authority,
retains `satellite_crossings.py` as provider-neutral immutable contracts, and
proposes `satellites/crossing_oracle.py` as a distinct future scientific
owner for exhaustive adaptive solving.

Completeness means validated numerical completeness under declared time and
angular tolerances, not a formal interval-arithmetic theorem over SGP4.
Every selected snapshot record must be scanned. Uncertain, singular, or
non-converged intervals subdivide or fail closed and cannot be reported as
negative. No 50S.5 runtime or 50S.6 acceleration is implemented.


The candidate 50S.5A documentation gate passed all 136 tests in 3.27 seconds
on macOS, and the corrected branch diff check was clean. Fernando scientifically and
architecturally accepted 50S.6A on 2026-09-15, authorizing only bounded 50S.6B
implementation of the first topocentric cone/orbital-shell selector. The final acceptance
documentation gate passed all 136 tests in 3.00 seconds. Fernando scientifically
and architecturally accepted 50S.5A on 2026-09-15. This authorizes only bounded
50S.5B implementation; 50S.6 and later behavior remain unauthorized.

### Accepted 50S.5B complete local crossing oracle

The accepted implementation adds the immutable `LocalSatelliteCrossingQuery`, exhaustive
`LocalSatelliteCrossingOracle`, and explicit
`SatelliteCrossingConvergenceError` in
`satellites/crossing_oracle.py`. Every selected snapshot record follows the
accepted 50S.4C/50S.4D chain. Endpoint/midpoint subdivision, topocentric angular
rate, curvature evidence, bracket-preserving roots, bounded minimum refinement,
and recursive time-and-angular tolerance connectivity produce ordered connected
visits.

A no-sign-change tangent in the angular uncertainty band becomes one refined
zero-duration boundary event. Disconnected visits remain separate. The final
state retains snapshot, record, SGP4, observer, IERS-A, solver, tolerance, and
warning evidence. Resource exhaustion or any record failure aborts the complete
query rather than returning a partial negative result. It adds no
50S.6 filter, illumination, photometry, CLI, report, drawing, or export.

Candidate verification on Fernando's Mac passed the 13-test dedicated oracle
gate in 60.62 seconds, the 108-test expanded satellite/coordinate/package
gate in 70.80 seconds, the 137-test documentation gate in 3.33 seconds, and
the complete plugin-disabled suite of 2,538 tests in 163.36 seconds. The
working tree was clean and `git diff --check aa6f91a...HEAD` passed. Fernando scientifically and architecturally accepted 50S.5B on 2026-09-15,
closing 50S.5. Only a documentation-first 50S.6 conservative-acceleration audit
is authorized next; runtime acceleration and all later behavior remain
unauthorized.

### Accepted 50S.6A conservative acceleration audit

The documentation-only audit keeps the accepted 50S.5 exhaustive oracle
independently callable and proposes a separate conservative candidate-selection
owner. Rejection requires a recorded topocentric cone/orbital-shell bound that
covers the complete inclusive interval, observer displacement, Earth rotation,
model discrepancy, numerical margin, and the accepted angular tolerance.
Uncertain or unsupported bounds retain the record for exact solving.

The audit rejects horizon and Earth-occultation filters because the current
query reports geometric directional crossings rather than visibility. It
defers phase, coarse vectorized propagation, and HEALPix/time indexing behind
separate correctness and benchmark gates. No runtime, package, dependency,
coordinate path, result, or output changes under 50S.6A. The candidate Mac
verification passed all 138 documentation tests in 3.99 seconds and the
corrected branch diff check was clean.

### Accepted 50S.6B conservative cone-shell selector

The candidate adds `satellites/crossing_acceleration.py` as the distinct owner
of immutable tri-state first-stage evidence. It evaluates one accepted
SGP4/WGS-72 and installed-IERS-A topocentric start state, derives an
OMM-shell Kepler perigee speed with an explicit 2.5 safety factor plus observer
speed bound, and encloses the complete admitted interval in a topocentric
reachable cap.

The supported production domain is deliberately limited to
`synthetic_50s4b_v1` and intervals of at most 60 seconds. All unsupported or
weak cases are `indeterminate`. The accepted exhaustive oracle is unchanged
and remains independently callable. This slice adds no accelerated coordinator
and cannot return crossing results. Candidate verification passed the 9-test
dedicated gate, 78-test expanded gate, 139-test documentation gate, and all
2,549 plugin-disabled tests. The branch and diff checks were clean. Fernando scientifically and
architecturally accepted the bounded selector on 2026-09-16. Only a
50S.6C documentation-first coordination, broader-domain, and benchmark audit is
authorized next.

### Accepted 50S.6C exact-solver coordination audit

The accepted documentation-only audit preserves the accepted exhaustive 50S.5 oracle
as the independent scientific reference and the accepted 50S.6B selector as a
tri-state evidence producer. It specifies one shared exact record seam:
exhaustive solving calls it for every record, while a later accelerated route
could call it only for ordered retain and indeterminate decisions.

The audit defines fail-closed decision coverage, exhaustive-result equivalence,
broader-domain evidence, instrumented evaluation accounting, and reproducible
benchmark admission. The three-record synthetic snapshot remains composition
evidence rather than a performance fixture. No source, runtime test, benchmark,
dependency, package export, coordinate path, or result changes in 50S.6C.
Fernando scientifically and architecturally accepted 50S.6C on 2026-09-16.
Only a bounded 50S.6D coordinator inside the existing three-record, 60-second
domain is authorized next.


### Accepted 50S.6D bounded accelerated crossing coordinator

The accepted implementation extracts one package-internal exact-record seam from
`LocalSatelliteCrossingOracle.solve(query)` without changing its numerical
algorithm. The exhaustive route remains independently callable and invokes that
seam for every snapshot record.

`AcceleratedLocalSatelliteCrossingOracle` is an opt-in coordinator. It
validates complete query-bound, NORAD-ordered `ConeShellSelection` evidence,
sends every retained and indeterminate record through the shared exact seam,
and omits only accepted reject decisions. `solve(query)` returns the ordinary
exact result tuple; `solve_with_evidence(query)` returns that tuple plus
separate immutable `AcceleratedCrossingEvidence`.

Selector exceptions fall back to the complete exhaustive route by default or
fail closed under explicit immutable policy. Missing, inconsistent, duplicate,
unknown, reordered, or out-of-domain rejection evidence fails closed. The
candidate remains limited to `synthetic_50s4b_v1` and intervals no longer than
60 seconds. It adds no broader selector domain, benchmark claim, default
enablement, coordinate path, CLI, reporting, drawing, or later filter stage.


Candidate 50S.6D verification at commit `a7aecba` passed the 37-test
dedicated gate, 93-test expanded immediate-seam gate, 141-test documentation
gate, and complete 2,566-test plugin-disabled suite. Fernando scientifically and architecturally accepted 50S.6D on 2026-09-16.
No broader-domain, benchmark, default-enablement, or later acceleration work is
authorized by this acceptance.


## Accepted 50S.6E multi-FoV and interchange direction

The accepted runtime remains the single-FoV exhaustive oracle and the narrowly
admitted opt-in 50S.6D coordinator. The accepted documentation-only
`satellite_multifov_interchange_audit_50s6e.md` proposes one observer, any
non-empty ordered number of independently timed FoVs whose field centres meet
a configurable airmass limit throughout their complete intervals, and exact
equivalence to independent calls. The initial geometric vacuum AltAz policy
uses plane-parallel `X = sec(z)` with `X_max = 2` by default. Only the field
centre is checked; the FoV radius does not enter airmass admission. Ten FoVs
are a
reference workload and proposed processing chunk, not a hard-coded public
limit. This admission condition does not filter satellite crossings.

The accepted roadmap places generic JSON/ECSV/VOTable crossing reports and exact
binocular, regional, and stereographic chart tracks in 50S.6G; observatory
adapter auditing in 50S.6H; component-resolved Sunlight, solar Earthshine,
Moonlight, and Lunar-Earthshine geometry in 50S.7; and brightness in 50S.8.
Fernando scientifically and architecturally accepted this direction on
2026-09-16. The accepted 50S.6F implementation adds an immutable
same-observer batch request, atomic ordered validation failures, centre-only
airmass admission, execution-only chunking, and ordered composition of the
accepted 50S.6D single-field route. It remains restricted to the installed
synthetic snapshot and 60-second per-field intervals. No CLI, file adapter,
generic report, chart, useful-speed claim, physical-state cache, observatory
adapter, illumination, photometry, broader catalogue, or later milestone is
implemented or authorized by this milestone. Fernando scientifically and
architecturally accepted 50S.6F on 2026-09-17 after 2,577 plugin-disabled tests
passed. Only a separately bounded 50S.6G audit is authorized next.

The accepted 50S.6G delivery audit records future seams only. No external
snapshot directory, representative catalogue, exact-crossing report,
multi-FoV CLI/file protocol, validation-output file, exact local track layer,
or ordinary chart integration is implemented. The proposed delivery must
compose the accepted 50S.6F domain and the canonical chart pipeline; it may not
change current coordinate, crossing, rendering, or export meaning.
Fernando scientifically and architecturally accepted the audit on 2026-09-17
after all 145 plugin-disabled current-documentation tests passed in 4.36
seconds. Only bounded 50S.6G.1A external immutable snapshot loading is
authorized next.

The accepted 50S.6G.1A implementation adds one explicit-directory snapshot
loading seam. It constructs the same immutable `SatelliteElementSnapshot`
through the existing complete byte-level validator, rejects symlink or missing
filesystem resources, and treats the manifest rather than the directory name
as scientific identity. No external snapshot is admitted to crossing runtime,
and no acquisition, network, report, CLI, or chart behavior is added.
Fernando scientifically and architecturally accepted 50S.6G.1A on 2026-09-17
after the 164-test focused gate and all 2,583 plugin-disabled tests passed.
Only a separately bounded 50S.6G.1B representative snapshot preflight and
evidence audit is authorized next, not its implementation.

The accepted 50S.6G.1B audit adds no implementation. It proposes a separate
satellite acquisition owner with a two-phase CelesTrak policy receipt and exact
digest acknowledgement, followed by at most one fixed `GROUP=active` CSV bulk
request. Exact raw bytes and deterministic canonicalization receipts precede
atomic content-addressed external publication. Active is representative scale,
not complete orbital-population coverage. External evidence admission must be
bound to the canonical-record digest; installed synthetic defaults remain
unchanged.
Fernando scientifically and architecturally accepted 50S.6G.1B on 2026-09-17
after all 147 plugin-disabled current-documentation tests passed in 4.54
seconds. Only bounded 50S.6G.1B.1 fake-transport implementation is authorized
next; no live CelesTrak request or representative admission is authorized.

## Implemented 50S.6G.1B.1 offline snapshot builder

`satellites/snapshot_acquisition.py` now implements the accepted policy
receipt, exact policy-response SHA-256 acknowledgement, deterministic Active
CSV normalization, and atomic external publication contract. The production
owner has no network adapter: callers must inject its single-request
transport. Therefore this implementation and its tests cannot initiate live
CelesTrak access. The acknowledgement is checked before the GP transport is
called, every row passes the existing typed OMM validator, and the staged
snapshot passes `load_snapshot_directory()` before publication.

This slice does not authorize a live request, cache-refresh override,
representative admission or evidence, 50S.6G.1B.2, or a runtime default.

Fernando accepted the bounded 50S.6G.1B.1 implementation on 2026-09-17 after
175 focused plugin-disabled tests and all 2,594 plugin-disabled tests passed.
`git diff --check` and the working tree were clean. Acceptance does not
authorize a live CelesTrak request or 50S.6G.1B.2.

Fernando accepted the direct-policy-URL correction on 2026-09-17 after all
2,595 plugin-disabled tests passed in 205.93 seconds. The protected endpoint is
`https://celestrak.org/usage-policy.php`; no GP request was performed.

Fernando accepted the exact `non-HTTP 200` policy-clause compatibility
correction on 2026-09-17 after 10 focused tests and all 2,595 plugin-disabled
tests passed. The resulting 14,643-byte policy receipt is bound to SHA-256
`67bf0faa7e026a7cd49799069db9d3355f2a867894133afd39e130d6185724aa`. No GP request was made or authorized; approval of that exact
digest remains a separate human checkpoint.

Fernando accepted the exact CelesTrak epoch and HTTP-media compatibility repair
and its 16,559-record external Active snapshot on 2026-09-17 after 15 focused
tests and all 2,600 plugin-disabled tests passed. Raw response SHA-256 is
`e54730e14b2097444c5e20bba6dd13d3e2d92f956797d49256ddb1a70ffe5014`; canonical-record SHA-256 is `e80306c843b9e3004b1d5bf7a8e4e7eb76a4f56284cd659978dc9bd3461f2347`. The implemented seam
normalizes the provider-declared UTC epoch to explicit `Z` and preserves the
captured `text/plain; charset=UTF-8` value. No second request was made, and
50S.6G.1B.2 remains a separate milestone.


## Accepted 50S.6G.1B.2A external admission audit

The current external loader verifies canonical bytes and digest, while
`ConeShellPolicy`, `AcceleratedCrossingPolicy`, and
`MultiFieldCrossingPolicy` independently admit by logical snapshot ID. The
candidate 50S.6G.1B.2A audit records that an external evidence snapshot must be
authorized by exact canonical-record SHA-256 plus validated manifest identity
through one shared predicate. No such runtime owner is implemented yet; the
ordinary synthetic default and all current behavior remain unchanged.
Fernando scientifically and architecturally accepted this boundary on
2026-09-17 after all 150 plugin-disabled current-documentation tests passed in
3.84 seconds. Only bounded 50S.6G.1B.2B implementation is authorized next.


## Accepted 50S.6G.1B.2B digest admission

`satellites/snapshot_admission.py` now separates external evidence
authorization from immutable snapshot loading. An explicit finite policy
compares schema version, logical ID, canonical-record SHA-256, source identity,
source URL, and builder identity before producing an opaque immutable token.
The token contains no path and performs no acquisition.

The conservative selector, accelerated coordinator, and multi-FoV batch accept
the same optional token. External work without an exact token fails before
selection, airmass certification, propagation, or exact evaluation as
appropriate. The existing `synthetic_50s4b_v1` defaults and ordinary results
remain unchanged. This candidate adds no medium tier, matrix, runtime
discovery, report, track, chart, coordinate change, or provider request.


Fernando scientifically and architecturally accepted 50S.6G.1B.2B on
2026-09-17 after 51 focused runtime tests, 151 current-documentation tests,
and all 2,611 plugin-disabled tests passed; the complete suite took 215.89
seconds. `git diff --check` and the working tree were clean. Only bounded
50S.6G.1B.2C deterministic medium-specimen work is authorized next; 50S.6G.1B.2D
matrix execution and later delivery remain separately unauthorized.


## Accepted 50S.6G.1B.2C medium-specimen audit

The current architecture has no medium-subset owner. The candidate audit
separates deterministic evidence selection from immutable loading, provider
acquisition, digest admission, and later matrix execution. It proposes an
external three-file derived snapshot with a default target of 256, independent
one-dimensional bin coverage, deterministic digest-based ranking, and a
complete selection receipt. No runtime behavior or installed data changes.


Fernando scientifically and architecturally accepted 50S.6G.1B.2C on
2026-09-17 after all 153 plugin-disabled current-documentation tests passed in
4.58 seconds; `git diff --check` and the working tree were clean. Only bounded
fake-data implementation is authorized next. The first real medium selection,
50S.6G.1B.2D matrix execution, and later delivery remain separately
unauthorized.

### Candidate 50S.6G.1B.2C deterministic medium evidence

The candidate fake-data implementation in
`satellites/snapshot_evidence.py` derives a deterministic coverage specimen
only from an explicitly loaded, digest-admitted external snapshot. It binds the
validated parent manifest, acquisition report, and captured provider-response
bytes before applying the accepted scalar bins. Publication is canonical,
content-addressed, receipt-bound, and atomic. The developer
`select-medium` command is offline and requires explicit acknowledgement of
the accepted parent digest.

On 2026-09-17, 30 plugin-disabled focused tests passed in 5.99 seconds. The
ordinary installed default remains `synthetic_50s4b_v1`; no external product
is packaged or discovered. The candidate does not authorize the first real
medium selection or 50S.6G.1B.2D matrix execution.

### Accepted 50S.6G.1B.2C implementation

Fernando scientifically and architecturally accepted the fake-data
implementation on 2026-09-17 at `1d9d4e4`: 2,622 plugin-disabled tests passed
in 225.75 seconds and the 185-test focused gate passed in 9.03 seconds.
`satellites/snapshot_evidence.py` is now the accepted owner of deterministic
medium selection and receipt-bound atomic publication. The real parent has not
been selected; that operation requires separate authorization. 50S.6G.1B.2D
remains unauthorized.

### Candidate real 50S.6G.1B.2C specimen evidence

The external specimen contains 256 records with canonical-record SHA-256
`2e85c576e287a047b12fe58b9487f96533ae739c46a594945cedb4236f08ab8b`.
Its canonical selection receipt has SHA-256
`1a1048a24d619ec15817dbbc63cb461240fbce243a5414f266179f9cba57a895`.
It derives from the accepted 16,559-record parent
`e80306c843b9e3004b1d5bf7a8e4e7eb76a4f56284cd659978dc9bd3461f2347`
using age reference `2026-09-17T15:52:23.000000Z`.

The offline operation produced 48 mandatory representatives plus 208
deterministic fill records, covered all 24 bins with none empty, preserved the
parent bytes, and made no provider request. The external artifact is not
packaged, installed, discovered, or selected by default. Its evidence record
awaits acceptance and does not authorize 50S.6G.1B.2D.

### Accepted real 50S.6G.1B.2C specimen

Fernando accepted the exact external specimen on 2026-09-17 at `c4cd009`
after 157 plugin-disabled documentation tests passed in 4.66 seconds. Its
canonical digest is
`2e85c576e287a047b12fe58b9487f96533ae739c46a594945cedb4236f08ab8b`
and its receipt digest is
`1a1048a24d619ec15817dbbc63cb461240fbce243a5414f266179f9cba57a895`.
This closes 50S.6G.1B.2C without changing the installed synthetic default.
50S.6G.1B.2D remains separately unauthorized.

### Candidate 50S.6G.1B.2D equivalence-matrix audit

The candidate audit in
`satellite_equivalence_matrix_audit_50s6g1b2d.md` defines a documentation-only
boundary for comparing the exhaustive and accelerated production services on
the exact accepted 256-record external specimen. It requires 10 deterministic
same-observer, same-night fields with independent intervals and one
shared-interval research control, strict canonical result equality, complete
selector evidence, fail-closed execution, isolated resource observations, and
atomic external publication.

No matrix is executed, no runtime changes, and no performance claim, chart,
track, report route, provider access, or default change are authorized.

### Accepted 50S.6G.1B.2D matrix audit

Fernando scientifically and architecturally accepted the documentation-only
audit on 2026-09-17 at `6e7a8b9`, after 159 plugin-disabled documentation
tests passed in 10.75 seconds. Only bounded fake-data implementation of the
strict equivalence and evidence harness is authorized next. Real matrix
execution, resource claims, delivery, and charting remain unauthorized.

### Candidate 50S.6G.1B.2D fake-data matrix implementation

`satellites/crossing_matrix.py` now contains the candidate bounded
fake-data-only exact-equivalence matrix owner. It fail-closes on route-result,
canonical-byte, digest, selector-partition, fallback, admission, or published
manifest mismatches. At candidate commit `19520f3`, 2634 plugin-disabled
full-suite tests passed in 230.25 seconds on 2026-09-17. No accepted real
specimen was read and no real matrix was executed. The candidate awaits
Fernando's scientific and architectural acceptance before any separately
authorized real-matrix execution.

### Accepted 50S.6G.1B.2D fake-data matrix implementation

Fernando scientifically and architecturally accepted the fake-data-only matrix
implementation on 2026-09-17. The accepted evidence is 2634 plugin-disabled
full-suite tests in 230.25 seconds at `19520f3`, plus 161 plugin-disabled
current-documentation tests in 3.32 seconds at `3ef6a4d`. Acceptance does not
authorize reading the accepted real specimen or executing the real matrix.
Only a separately bounded real-execution audit is authorized next.

### Candidate 50S.6G.1B.2D real-execution readiness finding

The integrated fake-data matrix owner at `9bdf301` is not yet a production
real-execution path. Its executor and airmass certifier are injected seams; no
frozen ten-field real fixture, fresh-subprocess worker, or explicit offline
developer command exists. The accepted real specimen was not read and no
matrix was executed during this audit. Only bounded production-path
implementation with fake-data tests may proceed next; real execution remains
separately unauthorized.

### Accepted 50S.6G.1B.2D real-execution readiness finding

Fernando scientifically and architecturally accepted the fail-closed readiness
finding on 2026-09-17 after 163 plugin-disabled current-documentation tests
passed in 3.80 seconds at `054ac39`. Only bounded fake-data implementation of
the frozen fixture, receipt constraints, production airmass certifier,
fresh-subprocess worker, offline command, and tests is authorized next. Real
specimen access and real matrix execution remain unauthorized.\n

### Candidate 50S.6G.1B.2D production execution path

The candidate production boundary is isolated in
`satellites/crossing_matrix_execution.py`: an exact external-medium gate,
digest-frozen ten-field La Ligua fixture, production whole-interval airmass
certifier, canonical fresh-subprocess worker/executor, and explicit offline
developer command. The fixture uses only 15- and 60-second intervals. The
accepted `crossing_matrix.py` equivalence and atomic-publication owner remains
unchanged except for accepting canonical worker result mappings and recording
complete subprocess digests. No provider or implicit execution path exists.\n

Candidate verification on Fernando's Mac completed at executable commit
`81f9031`: the 14-test focused matrix gate passed in 9.35 seconds, the
210-test immediate-boundary and documentation gate passed in 60.26 seconds,
and all 2,645 plugin-disabled tests passed in 243.71 seconds. `git diff
--check 5cd60fd...HEAD` and the working tree were clean. No accepted real
specimen was accessed and no real matrix was executed. The candidate still
requires Fernando's scientific and architectural acceptance.\n

### Accepted production-path implementation

Fernando scientifically and architecturally accepted the bounded fake-data
production-path implementation on 2026-09-18. The executable evidence remains
14 focused tests in 9.35 seconds, 210 immediate-boundary tests in 60.26
seconds, and all 2,645 plugin-disabled tests in 243.71 seconds at `81f9031`.
After documentation-only evidence recording, 164 current-documentation tests
passed in 3.94 seconds at `602eed7`; the whitespace check and working tree
were clean.

Preserve the exact accepted-medium and receipt constraints, digest-frozen
ten-field La Ligua fixture with only 15- and 60-second intervals, production
whole-interval airmass certifier, canonical fresh-subprocess worker/executor,
explicit offline command, and shortened fake-data test practice. This
acceptance does not authorize accessing the accepted real specimen, executing
the real matrix, publishing real evidence, making a performance claim, or
advancing later delivery. Any real execution requires a separate explicit
authorization.\n

### Candidate first-real-execution authorization

No architectural or runtime change is proposed after `e1cdec9`. The candidate
50S.6G.1B.2D.1 audit would authorize one use of the accepted explicit offline
command against the exact accepted medium, with one new empty external output
root and no retry. The matrix remains 10 fields, two routes, one warm-up and
three measured repetitions, for at most 80 fresh subprocess invocations.
Evidence remains external and requires independent acceptance.\n

### Accepted first-real-execution authorization

Fernando scientifically and architecturally accepted 50S.6G.1B.2D.1 on
2026-09-18 after all 165 plugin-disabled current-documentation tests passed in
5.07 seconds at `af8044a`; the whitespace check and working tree were clean.

This acceptance authorizes exactly one operator-started offline execution
against the exact accepted 256-record medium, using the three frozen digests,
exact acknowledgement, accepted ten-field 15/60-second fixture, one new empty
external output root with at least 2 GiB free, the existing 3600-second
per-subprocess timeout, and no retry or resume. It does not itself start the
run. The exact absolute Mac paths must be resolved before the command is
issued. Failure or interruption authorizes no restart. Successful evidence
remains external and unaccepted pending an independent review; no performance
claim or later 50S.6G delivery is authorized.\n

### Candidate matrix execution progress display

`MatrixProgressBar` is a parent-process terminal concern inside
`crossing_matrix_execution.py`. The production wrapper derives its total from
field count, two routes, warm-up count, and measured repetitions; the accepted
default is 80. Progress is not part of the subprocess protocol, canonical
evidence, resource observations, scientific result, or publication identity.

## Candidate 50S.6G.1B.2D.2 progress verification

Candidate commit `b0b4432` was verified on 2026-09-18: 180 focused plugin-disabled tests passed in 5.44 seconds, and all 2647 plugin-disabled tests passed in 239.53 seconds. The diff check was clean. The parent-only progress display changes no scientific or canonical-evidence architecture; acceptance, merge, and renewed real-run authorization remain pending.

## Accepted 50S.6G.1B.2D.2 progress display

Fernando scientifically and architecturally accepted candidate `96b9ba0` on 2026-09-18 after the recorded 180-test focused gate, 2647-test full suite, 167-test final documentation gate, and clean diff check. The accepted behavior remains parent-only and outside canonical evidence. Merge and renewed real-run authorization remain separate.

## Renewed 50S.6G.1B.2D.3 one-run authority

After the accepted progress display was merged at `9c4b808`, Fernando explicitly renewed authorization on 2026-09-18 for exactly one real matrix run. The bounded run retains the accepted 10-field, 15/60-second, two-route, one-warm-up plus three-measurement, 80-invocation maximum contract. Progress remains parent-only and noncanonical; no retry or resume is authorized.

## Accepted 50S.6G.1B.2D.3 renewed authority

Fernando scientifically and architecturally accepted candidate `dd71e01` on 2026-09-18 after 169 plugin-disabled documentation tests passed in 4.29 seconds and repository checks were clean. The single bounded run remains unstarted and may proceed only after this record is merged and external preflight is repeated.

## Candidate 50S.6G.1B.2D.4 real-matrix evidence

The one authorized run from `9d93113` produced candidate report `d200f3920aeda64df4d385d6f695fc3a69694df519f1520341e90d25e3037258` on 2026-09-18. Independent review found exact canonical equality across 10 fields and 60 measured observations, with no fallback or rejected exhaustive crossing. All real fields had zero crossings, so the result establishes empty-result equivalence and partition integrity only; positive-crossing evidence remains synthetic. Timing is descriptive for this run and hardware, not an architectural performance claim.

## Accepted 50S.6G.1B.2D.4 real-matrix evidence

Fernando scientifically and architecturally accepted report `d200f3920aeda64df4d385d6f695fc3a69694df519f1520341e90d25e3037258` at candidate commit `186e255` on 2026-09-18 after 171 documentation tests passed in 4.46 seconds. The accepted finding is limited to deterministic empty-result equivalence and conservative partition integrity; all 10 real fields had zero crossings. No second run, universal performance claim, refactor, or parallel implementation is authorized.


## Candidate bounded 50S.6G.1B closure

At integrated baseline `b010a6c`, the accepted representative-snapshot work
provides policy-governed acquisition, immutable external validation,
digest-bound admission, deterministic medium selection, and exact
empty-result route equivalence with complete conservative partitions for the
accepted ten-field matrix. All real fields had zero crossings. Positive
crossings remain synthetic evidence, and no full-snapshot, broader FoV-count,
universal performance, concurrency, or reuse claim is established.

The candidate closure changes no implemented architecture or coordinate
meaning. It does not authorize another real run. Pending Fernando's separate
acceptance, 50S.6G.1B remains open and 50S.6G.2A remains unauthorized.
Acceptance would authorize only a documentation audit of the canonical
exact-crossing report and deterministic JSON boundary.


## Accepted bounded 50S.6G.1B closure

Fernando scientifically and architecturally accepted the bounded closure on
2026-09-19 at `c62a451`, after 173 plugin-disabled documentation tests passed
in 3.82 seconds and repository checks were clean. The accepted architecture
claim remains exact empty-result equivalence and conservative partition
integrity; all real fields had zero crossings.

Only a 50S.6G.2A documentation audit is authorized next. Report implementation,
another real run, refactoring, parallelization, and broader performance claims
remain unauthorized.


## Candidate 50S.6G.2A exact-report architecture

The documentation-only audit at
`satellite_exact_crossing_report_audit_50s6g2a.md` proposes a distinct
renderer-neutral exact-crossing logical model beside, not inside, the existing
SatChecker sampled-candidate presentation owner. It consumes retained immutable
batch results only and changes no crossing, coordinate, projection, rendering,
or export path. Explicit creation time, complete context, stable ordering,
nullable future science, canonical digest, closed Draft 2020-12 schema, and
typed byte-identical JSON round trips form the candidate boundary.

No runtime implementation is authorized pending Fernando's separate acceptance.


## Accepted 50S.6G.2A exact-report audit

Fernando scientifically and architecturally accepted the documentation audit
on 2026-09-19 at `835ddfe`, after 175 documentation tests passed in 3.27
seconds and repository checks were clean. Only the bounded exact-report logical
model, Draft 2020-12 schema, deterministic encoder/decoder, and focused tests
are authorized next; no other runtime or delivery work is authorized.


## Candidate 50S.6G.2A exact-report implementation

The dedicated `satellite_crossing_reports.py` owner now constructs an
immutable exact-local report only from already computed ordered
`MultiFieldCrossingResult` values. Its compact canonical scientific payload
is immutable; `document` returns a detached copy. The packaged closed Draft
2020-12 schema and typed semantic reconstruction jointly validate observer,
coordinate, interval, snapshot, airmass, acceleration, satellite identity, and
connected-visit context.

Serialization is deterministic UTF-8 JSON with a final newline. The report
digest excludes only its own identity field. Decoding rejects duplicate keys,
unknown fields, unsupported product/status/version, non-finite numbers,
invalid UTC, context/count/order mismatches, non-null version-1 future science,
and digest changes. Schema bytes are loaded once as package authority, so
decode and re-encode perform no network, clock, filesystem, propagation,
coordinate, airmass, or crossing work.

The candidate adds no ECSV/VOTable, CLI/file publication, exact track, chart,
illumination, magnitude, detector effect, provider access, or new scientific
execution. Scientific and architectural acceptance remains pending.


## Accepted 50S.6G.2A exact-report implementation

Fernando scientifically and architecturally accepted the bounded 50S.6G.2A
implementation on 2026-09-19. The executable candidate at `a65e5ac` passed
all 2,676 plugin-disabled tests in 234.08 seconds; the final pre-acceptance
documentation gate at `8af0d14` passed 179 tests in 5.05 seconds; diff and
working-tree checks were clean.

The accepted architecture adds only the immutable exact-local logical model,
packaged closed schema, deterministic JSON identity/encoding, strict typed
decoder, and round-trip boundary. Existing crossing, coordinate, presentation,
rendering, and export paths remain unchanged. 50S.6G.2B and later work require
separate authorization.


## Candidate 50S.6G.2B interoperability audit

The candidate audit proposes no current runtime change. It defines ECSV and
IVOA VOTable 1.5 as alternate lossless carriers of the accepted exact-report
logical model. JSON-derived `report_identity_sha256` remains the scientific
identity; tabular or XML bytes do not replace it.

A future accepted implementation must use one immutable format-neutral tabular
projection for row kinds, field definitions, units, masks, stable joins,
ordering, reconstruction, validation, and resource limits. Thin ECSV and
VOTable adapters may own only wire-specific syntax and metadata. This shared
layer is deliberately reusable by later publication work without accepting
paths or performing science. No implementation is authorized by this audit.

## Accepted 50S.6G.2B interoperability audit

Fernando scientifically and architecturally accepted the documentation-only
audit on 2026-09-19 at `ef14bc1`, after 181 plugin-disabled documentation
tests passed in 4.88 seconds and repository checks were clean.

The authorized implementation boundary is one reusable format-neutral
in-memory tabular projection with thin ECSV and VOTable 1.5 adapters. Canonical
JSON and `report_identity_sha256` remain the logical authority. Filesystem
publication, CLI, tracks, charts, visibility science, provider access, and new
scientific execution remain outside this milestone.


## Accepted complete 50S.6G.2B in-memory interoperability

Fernando scientifically and architecturally accepted the complete bounded
50S.6G.2B implementation on 2026-09-19. Executable commit `3bbd82f` passed
208 focused tests in 6.68 seconds and all 2,689 plugin-disabled tests in
215.15 seconds. Documentation evidence commit `ece80c7` passed all 186
current-documentation tests in 4.60 seconds; diff checks and the clean,
synchronized Mac working tree passed.

The exact local crossing report now has alternate deterministic lossless
in-memory ECSV and VOTable 1.5 carriers through exactly one private
schema-derived format-neutral projection. Canonical JSON and
`report_identity_sha256` remain the logical authority. Nullable Unicode
VOTable values use explicit Boolean `__is_null` companions because Astropy
7.1.0 discards string BINARY2 masks. No coordinate, propagation, crossing,
visibility, provider, filesystem, CLI, or rendering responsibility moved into
the adapters. No later milestone is authorized.

## Candidate 50S.6G.2C CLI/file protocol boundary

The documentation-only 50S.6G.2C candidate assigns argument parsing, versioned
initial-request and validation-output JSON, typed exit status, symlink-safe
paths, and atomic no-clobber report-bundle publication to one dedicated CLI
adapter. The accepted batch coordinator remains the scientific validation and
solve owner; canonical JSON plus the reusable ECSV/VOTable projection remain
the only report encoders. No runtime implementation, provider access, new
execution science, track, chart, visibility, illumination, or brightness work
is authorized by this candidate.

## Accepted 50S.6G.2C audit boundary

Fernando scientifically and architecturally accepted the documentation-only
50S.6G.2C CLI/file-protocol audit on 2026-09-19 at `bcac404`, after 188
plugin-disabled current-documentation tests passed in 5.29 seconds and
repository checks were clean. Only the bounded offline CLI/filesystem
implementation is authorized next. Preserve the existing batch coordinator and
canonical JSON plus reusable ECSV/VOTable report owners. Tracks, charts,
providers, new execution science, visibility, illumination, and brightness
remain unauthorized.

## Candidate 50S.6G.2C implementation state

The bounded candidate adds one offline `wenu_satellite_crossings` adapter,
three packaged closed protocol schemas, a public validation-only composition
method on the existing multi-FoV coordinator, and focused CLI/filesystem tests.
The command reuses the accepted exact report and shared tabular adapters,
publishes fixed no-clobber bundles, and performs no provider access, new
execution science, track, chart, visibility, illumination, or brightness work.

## Verified candidate 50S.6G.2C implementation

Candidate commit `e08ebf5` passed 235 immediate tests and all 2,709
plugin-disabled repository tests on Fernando's Mac. The help preflight, diff
check, and clean synchronized working tree passed. This is verification, not
scientific or architectural acceptance; the implementation remains bounded to
the offline CLI/filesystem responsibility.

## Accepted 50S.6G.2C implementation

Fernando accepted the bounded offline CLI/file protocol on 2026-09-19. The
accepted implementation preserves the batch and report owners and adds only
validation-only composition plus safe deterministic filesystem delivery. Only
a documentation-first 50S.6G.3A exact-local-track audit is authorized next.

## Candidate 50S.6G.3A exact-local-track boundary

The documentation-only candidate defines one immutable exact local track per accepted connected crossing and one output-neutral layer over that retained evidence. Mandatory entry, closest-approach, and exit anchors partition a deterministic adaptive midpoint-deviation sampler that composes the accepted snapshot, SGP4/TEME, and geometric topocentric owners and fails closed. SatChecker candidate tracks and Solar-System tracks remain scientifically distinct. No runtime, report, CLI, chart, renderer, or provider change is authorized by this audit.

## Accepted 50S.6G.3A audit boundary

Fernando scientifically and architecturally accepted the documentation-only exact-local-track audit on 2026-09-19 at `ce54971`, after 193 plugin-disabled documentation tests passed in 5.73 seconds and repository checks were clean. Only the bounded evidence realizer and output-neutral layer are authorized next. Chart integration, planisphere work, provider/report/CLI changes, visibility, illumination, and brightness remain unauthorized.

## Candidate 50S.6G.3A implementation state

The candidate adds immutable exact connected-visit evidence and science-free path/event layers. A timeless `gcrs-axes` collection retains `sample_time_scale="utc"` and per-vertex UTC instants, preserving the existing instant/time-scale invariant. The accepted SGP4/TEME and topocentric owners remain the only state route. The initial focused gate passed 69 tests; full verification and separate acceptance remain pending.

## Verified candidate 50S.6G.3A implementation

Candidate `f0a4164` passed all 2,728 plugin-disabled tests in 222.01 seconds after its 195-test documentation gate passed in 5.86 seconds. Diff and clean synchronized-tree checks passed. The exact-track evidence and output-neutral layer remain an unaccepted candidate.

## Accepted 50S.6G.3A implementation

Fernando accepted the complete bounded exact-local-track implementation on 2026-09-19. Preserve the snapshot-bound evidence, exact anchors, deterministic fail-closed sampling, identity/provenance, timeless collection plus per-sample UTC representation, evidence-only layers, exact-visit semantics, and narrow fixed-axis coordinate-service seam. Only a documentation-first 50S.6G.3B chart-integration audit is authorized next.

## Candidate 50S.6G.3B binocular/regional chart boundary

The documentation-only candidate connects already-realized 50S.6G.3A evidence to explicit regional and binocular chart requests. The chart builder may install and clean up accepted path/event views, apply independent labels and appearance, and use the canonical projection, clipping, renderer, and PNG/PDF/semantic-SVG exporters. It performs no crossing, propagation, transformation science, sampling, provider access, report/CLI work, or planisphere integration. No runtime implementation is authorized by this audit.

## Accepted 50S.6G.3B audit boundary

Fernando accepted the documentation-only binocular/regional exact-track audit on 2026-09-19 at `ef58180`, after 198 plugin-disabled documentation tests passed in 5.30 seconds and repository checks were clean. Only the bounded ordinary-request chart integration and required specimens are authorized next. Planisphere and later science work remain unauthorized.

## Candidate 50S.6G.3B implementation state

The candidate implements explicit already-realized exact-track display requests for regional and binocular stereographic horizontal charts. Strict observer, coordinate-policy, and reference-instant admission occurs before preparation. Request-owned path and event layers use the ordinary fixed product-frame transformation, detail, style, projection, clipping, renderer, export, semantic-SVG, and cleanup owners. SVG provenance contains only ordered bounded summaries rather than retained samples. No provider, solver, report, CLI, planisphere, visibility, illumination, or brightness responsibility changed.

## Candidate 50S.6G.4A stereographic polar-planisphere boundary

The documentation-only candidate proposes an event-specific exact-track
overlay for the paired physical `PolarPlanispherePair` only when both faces use
stereographic projection. It reuses already-realized 50S.6G.3A evidence and
the accepted display request, preserves each sample's geometric topocentric
direction in fixed GCRS/ICRS axis orientation, and projects the same evidence
independently through the north and south declination caps.

The existing physical horizon, constellation masks, calendar, and page
furniture do not admit, reject, or clip the track. Face overlap may display the
same visit twice intentionally; cap clipping creates no scientific event.
Observer/reference validation and request-owned cleanup precede and surround
the two canonical face exports. This audit changes no runtime and authorizes no
implementation, ordinary full-sky/circumpolar track, visibility science, or
later satellite behavior.

## Accepted 50S.6G.4A audit boundary

Fernando accepted the documentation-only paired stereographic-planisphere
audit on 2026-09-19 at `c1d9015`, after 200 plugin-disabled documentation
tests passed in 5.29 seconds and repository checks were clean. Only the
bounded 50S.6G.4B integration and required physical north/south specimens are
authorized next; all later satellite science remains unauthorized.

## Corrective 50S.6G.4A ordinary-planisphere boundary

The accepted 2026-09-19 paired equatorial polar-planisphere scope selected the
wrong product and is superseded for 50S.6G.4B. The requested product is the
ordinary ChartRequest planisphere: one FullSkyChart, horizontal AltAz,
zenith-centred stereographic projection, and the horizon as the chart boundary.

The as-is architecture already supplies the correct chart, fixed horizontal
LayerRealizationContext, exact-track layers, request-owned lifecycle, canonical
projection/preparation/render/export flow, and bounded provenance. Only a
future separately accepted widening of exact-track family admission from
regional/binocular to planisphere is proposed. This corrective audit changes
no runtime and authorizes no implementation.

## Accepted corrective 50S.6G.4A AltAz planisphere boundary

Fernando accepted the corrected ordinary-planisphere scope on 2026-09-20 at
80855938. A bounded 50S.6G.4B may widen the existing exact-track request
admission to family="planisphere" and add focused and physical acceptance
evidence. It must reuse FullSkyChart, the fixed horizontal realization context,
request-owned lifecycle, canonical rendering/export, and bounded provenance.
No paired equatorial or later satellite behavior is authorized.

## Verified candidate 50S.6G.4B ordinary-planisphere implementation

The candidate admits already-realized exact tracks on the existing ordinary
horizontal stereographic planisphere. `FullSkyChart`, the fixed AltAz
realization context, horizon boundary, request-owned lifecycle, semantics,
bounded provenance, renderer, and exporters remain the implemented owners.
No new chart, coordinate, projection, layer, renderer, exporter, or scientific
calculation is introduced. This remains an unaccepted candidate.

## Accepted complete 50S.6G.4B ordinary-planisphere implementation

PR 176 merged the accepted corrected implementation at `f0730d8`.
Non-empty ordinary planisphere requests may now carry already-realized exact
satellite tracks through the existing fixed AltAz realization, FullSkyChart
horizon boundary, request-owned lifecycle, stable semantics, bounded
provenance, renderer, and exporters. All other all-sky/circumpolar families
remain rejected. No new coordinate or satellite science owner was introduced.
## Accepted 50S.6H observatory-planning adapter audit

The documentation-only
`satellite_observatory_planning_adapter_audit_50s6h.md` preserves the
canonical `ExactSatelliteCrossingReport` as the sole scientific source and
proposes a later pure, offline planning-advisory JSON projection. It does not
change the implemented architecture. Paranal p2 is treated as an external,
state-changing system; no API call or OB mutation is admitted. ELT has no
accepted operational profile and must not be aliased to Paranal.

Fernando accepted this documentation architecture on 2026-09-20. Only the
bounded offline general planning-advisory implementation is authorized next.
Network access, credentials, observatory writes, scheduling decisions, ELT
mapping, and 50S.7+ behavior remain unauthorized.
## Accepted 50S.6H offline planning-advisory implementation

The feature candidate adds one downstream pure owner,
`satellite_planning_advisories.py`. It accepts the existing validated
`ExactSatelliteCrossingReport` plus a frozen general-profile planning
context, computes only half-open UTC interval intersections, and returns an
immutable independently identified JSON advisory.

The candidate does not alter the implemented propagation, coordinate,
crossing, report, file-protocol, chart, renderer, or export owners. It has no
network or facility-write capability and makes no illumination, brightness,
detector, or scheduling claim. Fernando accepted this bounded implementation on 2026-09-20.
## Accepted complete 50S.6H implementation state

Revision `32dce675` verifies the pure general-profile projection with 226
focused/documentation tests, all 2,769 repository tests, and offline positive
and endpoint-touch zero-row JSON specimens. The manifest declares no network
access. Fernando accepted the verified candidate on 2026-09-20. The architecture
becomes implemented on merge; only a documentation-first 50S.7 audit is
authorized next.

## Candidate 50S.7A illumination architecture

The documentation-only candidate introduces no implemented owner. It proposes
one downstream `satellites/illumination.py` composition over the accepted
snapshot, SGP4/TEME, Earth-orientation, topocentric, and installed-ephemeris
owners. That owner would produce immutable geometry, incident source fields,
shadow-transition events, identity, and provenance without changing crossing
truth or chart/report/planning behavior.

Sunlight, solar Earthshine, Moonlight, and Lunar-Earthshine remain separate.
Earth-reflected terms retain their extended directional character until 50S.8
supplies spacecraft surface orientation and BRDF. The candidate authorizes no
runtime; after separate acceptance, only bounded direct-Sun and geometric
observer-night state would be next.

## Accepted 50S.7A illumination architecture

Fernando scientifically and architecturally accepted the documentation-only
50S.7A architecture on 2026-09-20 at `fdf7e005a41a5a4d45200f841e914815d37da870`.
No implemented owner changes in this audit. After merge, only a bounded
50S.7B `satellites/illumination.py` composition for finite uniform-Sun/WGS-84 vacuum
occultation, typed shadow state, observer geometric twilight, provenance, and
offline validation is authorized.

Sunlight, solar Earthshine, Moonlight, and Lunar-Earthshine remain independent.
50S.7C+ transitions and radiometry, reflected-source fields, 50S.8 attitude,
BRDF and apparent brightness, 50S.9 detector effects, visibility, facility
integration, and scheduling remain unauthorized.
## Candidate 50S.7B direct-Sun and observer-night architecture

The unaccepted candidate installs `satellites/illumination.py` as a downstream,
output-neutral composition owner. It consumes the accepted immutable
topocentric satellite state and injected geometric ephemeris source, uses the
same installed-IERS-A evidence to place the Earth-to-Sun vector in ITRS, and
then owns only finite-Sun/WGS-84 occultation and geometric observer twilight.

`SatelliteIlluminationGeometry` retains all input state/resource identity,
common-frame vectors, a converged uniform-disk visible fraction, typed shadow
and twilight classes, explicit lunar-occultor `not_evaluated` status,
numerical policy, provenance, and warnings. The bounded adaptive
equal-solid-angle ray quadrature fails closed if its declared fraction
tolerance is not met. No crossing, chart, report, planning, radiometric,
brightness, visibility, detector, facility, or scheduling owner changes.
50S.7C and later work remain unauthorized.
## Validated candidate 50S.7B numerical boundary

At candidate `51b935f`, 24 focused tests passed in 5.58 seconds. The offline
SPICE oracle agreed on clear/sunlit, partial/penumbra, umbra, and
annular/antumbra cases. The installed DE440 kernel
`c1c7feeab882263fc493a9d5a5b2ddd71b54826cdf65d8d17a76126b260a49f2`
also produced 20 matching Skyfield full-light and 5 matching full-shadow
states. This validates the bounded numerical architecture but does not yet
constitute scientific or architectural acceptance.

## Verified candidate 50S.7B architecture

Executable revision `086e7da1` passed the 291-test expanded gate, 208-test
documentation gate, clean branch diff, all 2,796 plugin-disabled repository
tests in 233.66 seconds, and exact upstream/clean-tree checks. Together with
the installed-DE440/SPICE/Skyfield receipt, this verifies the bounded
output-neutral architecture. The candidate still requires Fernando's separate
acceptance before merge; 50S.7C and later work remain unauthorized.

## Accepted 50S.7B architecture

Fernando accepted the complete output-neutral 50S.7B architecture on
2026-09-21 at `054ac53a`. Preserve `satellites/illumination.py` as the
downstream direct-Sun and observer-night composition owner, the accepted
topocentric module as the Earth-orientation owner, and the existing ephemeris
boundary as the Sun-state owner. The final documentation gate passed all 208
tests in 4.19 seconds.

Merge remains a separate decision. After merge, only a documentation-first
50S.7C shadow-transition audit may begin; transition runtime and all later
radiometric, reflected-source, brightness, visibility, detector, facility,
and scheduling behavior remain unauthorized.

## Candidate 50S.7C shadow-transition architecture

The documentation-only audit proposes a complete bounded, observer-independent
event search in the existing `satellites/illumination.py` owner. Transition
time is isolated with continuous signed finite-Sun/WGS-84 limb-contact
geometry, not the quadrature-quantized visible fraction. The accepted
quadrature remains the reported fraction owner.

A minimal shared geocentric TEME-to-ITRS state seam would remain in
`satellites/topocentric.py`; both the existing observer route and a later
transition search would compose it with the same installed-IERS-A evidence.
The candidate defines directed events, certified UTC brackets, deterministic
identity, complete interval certification, terminal failure, and independent
SPICE/Orekit event validation.

This audit changes no runtime. 50S.7C implementation, 50S.7D+ radiometry and
reflected fields, brightness, visibility, detector, facility, and scheduling
behavior remain unauthorized pending separate acceptance.

## Accepted 50S.7C shadow-transition architecture

Fernando scientifically and architecturally accepted the documentation-only
architecture at `030a6322` on 2026-09-21 after 210 documentation tests passed
in 5.81 seconds and repository checks were clean.

After merge, implement only the bounded observer-independent transition service
in the existing illumination owner plus the minimal shared geocentric ITRS
seam in the topocentric owner. Preserve continuous contact geometry, complete
bounded closed-interval search, directed events, certified brackets,
deterministic identity, terminal failure, and independent event validation.
No later illumination, brightness, visibility, detector, facility, or
scheduling behavior is authorized. PR 182 merge remains separate.

## Candidate 50S.7C shadow-transition implementation architecture

Executable `69375fab` implements the accepted bounded architecture in the
existing illumination owner. `SatelliteShadowTransitionFinder` composes one
selected snapshot record, SGP4 propagation, the shared geocentric ITRS seam,
same-instant installed ephemeris, continuous finite-Sun limb margins, and a
complete bounded recursive interval search. It returns ordered immutable
directed brackets or a typed terminal failure; no observer enters event
identity.

The existing topocentric transformer now composes the same internal
TEME-to-ITRS implementation as the new geocentric transformer. The accepted
visible-fraction quadrature and every crossing/output owner remain unchanged.
The 58-test focused gate passed in 16.67 seconds, and the installed-resource
SPICE/Skyfield receipt reproduced full and annular directed sequences plus
20 full-light and 5 full-shadow binary states. Complete gates and acceptance
remain pending; 50S.7D+ and all integration remain unauthorized.

## Verified candidate 50S.7C implementation architecture

Exact candidate `bf877404` passed 311 expanded tests in 21.47 seconds, 212
documentation tests in 7.01 seconds, the clean diff, and all 2,816
plugin-disabled repository tests in 218.58 seconds. Exact upstream equality
and a clean working tree were confirmed. Together with the SPICE/Skyfield
receipt, this verifies the bounded observer-independent event architecture.

Fernando's separate acceptance is still required. Merge, branch deletion,
50S.7D+, and all crossing/output, radiometric, brightness, visibility,
detector, facility, or scheduling integration remain unauthorized.

## Accepted 50S.7C implementation architecture

Fernando scientifically and architecturally accepted the complete bounded
50S.7C implementation on 2026-09-21 at branch head
`eaeab6085b52bfed6136d37f3010c2f353e59f53`. Executable candidate
`bf877404` passed the independent SPICE/Skyfield receipt, 311-test expanded
gate, 212-test documentation gate, clean diff, complete 2,816-test
plugin-disabled suite, exact upstream, and clean-tree checks. The final
documentation-only timing clarification passed all 212 tests in 4.72 seconds.

Preserve the observer-independent single-record query, continuous
finite-Sun/WGS-84 contact geometry, shared geocentric ITRS seam, complete
bounded search, six directed adjacent events, certified UTC brackets,
deterministic identity, and typed terminal failure. Merge and branch deletion
remain separate explicit decisions. 50S.7D+, transition attachment to outputs,
radiometry, reflected fields, brightness, visibility, detector, facility,
scheduling, and unrelated work remain unauthorized.
