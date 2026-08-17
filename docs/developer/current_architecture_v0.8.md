# Wenu current architecture v0.8

**Status:** Implemented baseline for the v0.9 migration
**Baseline commit:** `c169162`
**Release:** `v0.8.0`
**Date:** 2026-08-15
**Target:** `target_architecture_v0.9.md`
**Migration plan:** `wenu_migration_0.8_to_0.9.md`

## Purpose

This document records the implemented starting point for the physical
polar-planisphere work. The complete v0.8 architecture remains described in
`target_architecture_v0.8.md`; this baseline identifies the parts that v0.9
will reuse and the gaps it must close.

Wenu is a static chart-generation package. It has one canonical pipeline from
catalogues and spherical geometry through projection, preparation, rendering,
furniture, and one export. It does not yet produce a physical rotating
planisphere disk, calendar ring, cuttable horizon overlay, or paired
back-to-back polar product.

## Reusable v0.8 owners

Version 0.8 already provides:

- an observer-independent maximal `CelestialSphere` with render-local
  selection and observer-keyed spherical realizations;
- immutable requests, observer-bound geometrical views, and one ordinary
  drawing facade;
- stereographic regional, planisphere, circumpolar, and binocular charts;
- Galactic Mollweide all-sky charts;
- north- and south-centred `CircumpolarChart` geometry bounded by a
  declination parallel;
- equatorial, ecliptic, Galactic, and observer-local AltAz grids;
- celestial-reference curves and pole annotations;
- atlas and cartoon styles, print and presentation modes, configurable
  furniture, and deterministic export;
- configurable product language values `en` and `es`, but no complete shared
  translation catalogue for generated visual labels;
- configurable style and font values, but no curated physical-planisphere
  typography contract.

These are the authorities v0.9 must extend. The physical planisphere must not
create another catalogue, sky, projection-execution, renderer, style, or
export pipeline.

## Projection gap

The existing polar circumpolar chart delegates to the stereographic
projection. Stereographic projection is conformal and appropriate for its
current chart role, but radial scale grows toward the opposite pole. A
two-sided physical planisphere covering from each pole across the celestial
equator needs controlled, linear declination spacing and a shared physical
radius.

Wenu does not yet implement polar azimuthal-equidistant projection. Projection
selection is already immutable chart-view geometry, so the new projection can
enter through the existing projection boundary without changing layer or
renderer contracts.

## Physical-product gap

Export currently produces one ordinary chart image. It does not own:

- a 365-day circular calendar scale;
- month arcs and day typography;
- exact printed disk diameter;
- centre punches, registration marks, glue alignment, or scale checks;
- paired north/south faces with opposite apparent rotation;
- a separate observer-latitude horizon template;
- scissor-cut instructions or assembly guidance.

These are chart geometry and chart-furniture/export responsibilities. They are
not astronomical catalogue layers.

## Appearance and content gap

Existing styles can render magnitude-sized stars, constellation figures and
labels, Milky Way isophotes, reference curves, poles, and deep-sky symbols.
The v0.9 product still needs a deliberately sparse physical-print policy:

- canonical white background and ESO-blue stars;
- stars through magnitude 5.0;
- filled Milky Way shading without contour outlines;
- limited RA structure and declination ticks;
- labelled celestial equator, ecliptic, and Galactic plane;
- ecliptic key points and relevant coordinate poles;
- later experiments with compact filled five-point bright-star symbols;
- later human curation of a small deep-sky selection;
- later typography, night-palette, and complete translation curation.

## Preserved invariants

Version 0.9 must preserve:

- `CelestialSphere.draw_chart()` as the canonical execution core;
- chart ownership of projection, physical framing, viewport, and boundary;
- detail ownership of magnitude limits and selected astronomical content;
- style and mode ownership of appearance only;
- furniture ownership of scales, labels, instructions, and registration marks;
- backend-neutral scientific geometry before Matplotlib rendering;
- one final save for each exported page;
- atlas-print behavior and every existing chart family unless an explicit
  v0.9 product requests new appearance.

Milestone 48B.1 adds the backend-neutral
`PolarAzimuthalEquidistantProjection`. It selects a north or south pole,
places radial distance linearly in polar angular distance, supports explicit
position angle and east-west handedness, provides an inverse and radius
conversions, and reuses the established spherical geometry dispatch protocol.
No chart, request, calendar, horizon, style, renderer, or export path selects
it yet.

Milestone 48B.2 registers `polar_azimuthal_equidistant` and `equatorial` as a
valid immutable `ProjectionSelection` pair and adds canonical AltAz-to-ICRS
spherical-geometry transformation. A chart view exposes its frozen selection,
whose projection is constructed lazily from chart-owned geometry. Existing
v0.8 chart families still reject the polar pair because none constructs a
polar chart yet; that first honest selection belongs to Milestone 48C.1.

Milestone 48C.1 adds the public single-face `PolarPlanisphereChart`. It owns
selected pole, limiting declination, position angle, projected scale,
physical diameter, handedness, circular boundary, square viewport, and the
AltAz-to-equatorial canonical rendering seam. Polar azimuthal-equidistant is
the physical-product default; stereographic is an explicit equatorial
alternative over the same disk contract. Paired requests, calendar rings,
registration, and horizon templates are not yet implemented.

Milestone 48C.2 adds one immutable `PolarPlanispherePairRequest`. It resolves
matched north and south charts with one projection choice, scale, position
angle, physical diameter, sample count, centre, and compatible independently
declared limits. Projection-aware handedness produces opposite paper RA
direction for both equidistant and stereographic pairs. Frozen assembly
metadata supplies shared optional calendar and pivot radii plus asymmetric
marks that fold together without mirrored text. No registration marks,
calendar scale, or physical furniture are drawn yet.

Milestone 48D.1 adds the public immutable `CommonYearCalendarRequest`. It
builds a backend-neutral 365-day scale anchored to local mean sidereal time at
standard-time midnight for configurable longitude, fixed UTC offset, and a
deterministic non-leap reference year. Its exact `360 / 365` degree step
closes the ring, while day records preserve midnight RA and the neutral
calendar angle needed for the future bottom-midnight alignment. True month
arcs, boundaries, semantic month keys, and labels on days 5, 10, 15, 20, 25,
and 30 are resolved without drawing, translation, daylight-saving, or face
handedness policy.

Milestone 48D.2 adds the public immutable
`PolarCalendarFurnitureRequest`. It resolves the common-year scale onto an
already matched north/south pair as millimetre geometry: 365 daily ticks per
face, stronger month boundaries, selected five-day labels, semantic month
labels at true arc centres, and radial rotations whose typographic bases face
outward. An explicit star-disk radius keeps every calendar element outside the
astronomical aperture. Date angles are derived as the direction opposite each
face's projected midnight RA, so projection-owned handedness reverses between
the glued faces and bottom-date alignment sends the correct RA vertically
upward. The records contain no Matplotlib, localized month text, horizon, or
style policy.

Milestone 48E.1 adds the packaged `PolarPlanisphereDetailPolicy` and registers
it as the ordinary atlas-detail default for `polar_planisphere`. It selects
stars through magnitude 5.5 plus constellation figures, constellation labels,
the Milky Way, and both Magellanic Clouds. It disables constellation-boundary,
coordinate-grid, and deep-sky symbol layers, and prevents constellation
vertices from bypassing the magnitude ceiling. North and south compositions
resolve identical render-local catalogue geometry options before projection,
preserving common content throughout their overlap without a separate sky or
catalogue path.

Milestone 48E.2 adds a packaged physical-planisphere palette and applies it
only to named atlas-print compositions of `polar_planisphere`. It derives from
the ordinary atlas style while selecting white paper, configurable provisional
blue stars, reduced circular stellar area, translucent filled Milky Way
polygons with every outline path disabled, restrained constellation structure,
and no legend. Ordinary atlas families and screen presentation are unchanged.
The deterministic `render_48e2_polar_preview.py` diagnostic uses the canonical
sphere, composition, chart rendering, and resolved calendar geometry to create
the two images required for visual review; it is not a product pipeline.

Milestone 48E.3 applies the first review corrections without changing that
accepted palette. The paired default overlap is now +20/-20 degrees, default
stereographic handedness is corrected, and constellation-label anchors remain
inside an inset stellar aperture. The canonical reference-furniture path now
prepares polar overlays into ICRS and supplies four RA meridians, short
declination ticks every 20 degrees, labelled principal planes, cardinal points,
and face-visible pole annotations. Calendar geometry records labelled-day
ticks separately so rendering can strengthen them without changing length;
day and month typography now share a tighter radial band. The second review
correction moves month names slightly outward, renders declination marks as
short projected disk furniture rather than spherical parallels, selects the
pole belonging to each face explicitly, unifies principal references under a
neutral blue-grey style, and enlarges their labels by 50 percent. The
diagnostic footer obtains the installed Wenu version from package metadata.

Milestone 48H.2 adds one reviewed, packaged binocular-target selection shared
by both polar faces before projection. Catalogue identifiers remain the
selection and provenance authority; a separate immutable label policy prefers
Messier designations and concise common names, and can suppress one label in a
close pair without suppressing either symbol. The generic projected-geometry
renderer applies the resulting formatter, so no catalogue rows or
polar-specific object classes are rewritten. The physical polar palette also
sets a configurable 40-arcminute display floor for ordinary outline-based
deep-sky symbols and an 80-arcminute floor for globular clusters. Fixed
open-cluster and planetary-nebula symbols retain their existing fixed print
sizes. Deep-sky label baselines are tangent to their local circle and thus
perpendicular to the disk radius, with typographic down facing the disk
center. Other chart families remain unchanged.
