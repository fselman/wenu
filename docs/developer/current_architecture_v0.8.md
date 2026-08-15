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
