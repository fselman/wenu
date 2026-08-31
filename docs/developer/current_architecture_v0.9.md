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

Packaged defaults and schema-version-1 configuration resolve into immutable
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
- `coordinate_transformation_audit_09a2afd.md` for scientific coordinate
  evidence;
- `public_interface_audit_v0.9.5.md` for the accepted executable inventory and
  public system, frame, equinox, and epoch boundary;
- `celestial_scene_dependency_audit_49d1.md` and
  `layer_realization_context_49d2.md` for scene dependencies and the minimal
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

Milestone 49I.3A is a proposed contract audit, not implemented architecture.
The current runtime still realizes Venus and the Moon as apparent centre
points and style still draws provisional fixed hollow symbols. No current
record carries physical angular diameter, illuminated fraction, bright-limb
orientation, body orientation, photometry, or display magnification.

The proposed boundary keeps a future physical-appearance state renderer-neutral
and keeps object-specific display magnification outside that scientific state.
Any resolved disk must become ordinary semantic geometry before the existing
projection, clipping, renderer, and shared exporter.
