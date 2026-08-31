# Resolved Venus disk audit — Milestone 49I.3C

**Status:** Candidate architecture for scientific review

**Audit date:** 2026-08-31

**Implementation baseline:** `a9d8342`

## 1. Purpose

This audit defines the smallest canonical route from the accepted
`SolarSystemApparentDisk` state to a first opt-in resolved Venus disk. It
changes no runtime type, public command, chart, style, renderer, or output.

The intended first implementation is limited to regional and binocular charts.
Planisphere and all-sky products retain the default symbolic Venus point.

## 2. As-is findings

The accepted Venus centre is already an observer-origin apparent direction and
49I.3B supplies physical angular diameter, phase angle, illuminated fraction,
and apparent-ICRS bright-limb position angle. Neither record contains display
magnification or page policy.

The canonical layer pipeline realizes spherical geometry, transforms it to the
product frame, applies the projection-domain guard, projects it, prepares it,
and sends the projected geometry to the ordinary renderer and shared
PNG/PDF/SVG exporter.

The existing geometry vocabulary already contains `SphericalCurves` and
`SphericalPolygons`, with corresponding projected records and renderer
support. A `SphericalGrid` is deliberately curve-only, so one grid cannot
honestly contain both the illuminated face and its boundary curves.

## 3. Accepted ownership boundary proposed for review

The resolved disk should be a small semantic layer group produced from one
physical appearance state:

- an illuminated-face `SphericalPolygons` layer;
- a limb `SphericalCurves` layer;
- a terminator `SphericalCurves` layer.

All three share the accepted apparent centre, physical state, display policy,
sampling contract, and semantic parent. They are transformed and projected by
the ordinary machinery. No layer may calculate page coordinates or call a
renderer.

A dedicated scientific disk-geometry module may construct the three spherical
records. Chart request/detail code may select resolved representation and
provide Venus-specific magnification. Style owns fill, stroke, widths, alpha,
and drawing order. The renderer remains body-agnostic.

## 4. Physical and display radius

Let `rho = d / 2` be the accepted physical angular radius, where `d` is
the 49I.3B angular diameter. Let `M_venus` be the positive finite,
object-specific display magnification. The sampled display radius is
`rho_display = M_venus * rho`.

The physical state retains `d` unchanged. Magnification changes only the
angular offsets used to build display geometry. It must not change the centre,
phase, illumination, visibility, ephemeris state, or provenance.

A factor of `1` means physical angular scale. Resolved mode and magnification
are separate choices. Magnification alone must not silently enable a disk.

## 5. Renderer-neutral spherical construction

At the accepted apparent centre, construct an orthonormal tangent basis:

- `n`: apparent celestial north;
- `e`: apparent celestial east;
- `l`: the tangent direction toward the midpoint of the bright limb,
  obtained from the accepted position angle;
- `m`: the tangent direction 90 degrees counterclockwise from `l`;
- `z`: the observer-to-target centre direction.

For bright-limb position angle `chi`, measured from north toward east, use
`l = cos(chi) * n + sin(chi) * e`.

For phase angle `i`, the target-to-Sun direction in this local basis is
`s = sin(i) * l + cos(i) * z`.

A sampled point `p` on the spherical body's unit surface is visible when its
`z` component is non-negative and illuminated when `dot(s, p) >= 0`.

The limb is the complete visible circle. The visible terminator is the
intersection `dot(s, p) = 0` on the observer-facing hemisphere. The
illuminated face is the closed boundary made from the illuminated limb arc and
the visible terminator. These local disk-plane samples are mapped to angular
offsets around the accepted centre and then to ordinary spherical coordinates.

The construction must cover new, crescent, quarter, gibbous, and full limiting
cases without choosing a page rotation. At quarter phase the projected
terminator is a diameter. The illuminated side must point toward the apparent
Sun after every product-frame transformation and projection.

## 6. Projection and clipping

The complete magnified geometry is created before projection. This lets the
existing non-linear projection act on every sampled boundary point and avoids a
post-projection circular-marker approximation.

Projection-domain clipping and viewport clipping remain ordinary pipeline
responsibilities. A resolved disk whose centre is outside a viewport can still
have visible geometry inside it; selection must therefore use the disk
geometry, not centre-only rejection.

Sampling is a deterministic geometry parameter. The first slice should use one
documented default dense enough for accepted regional/binocular output and
retain the value in metadata. Adaptive sampling is deferred unless evidence
shows the fixed contract inadequate.

## 7. Product and request policy

The first drawable slice should:

- remain symbolic by default;
- allow resolved Venus only in regional and binocular families;
- reject resolved Venus in planisphere and all-sky families;
- use a positive finite Venus-specific magnification;
- preserve the ordinary Venus point unless the resolved representation
  explicitly replaces it;
- avoid a second centre-direction or appearance realization.

Illustrative command vocabulary remains provisional until the runtime slice,
for example `--planet-appearance venus=resolved` and
`--planet-disk-magnification venus=40`. This audit does not install or accept
those spellings.

## 8. Semantic identity and output parity

The resolved descendants should have stable identities beneath the accepted
Venus parent:

- `sky/solar_system/planets/venus/disk/illuminated`;
- `sky/solar_system/planets/venus/disk/limb`;
- `sky/solar_system/planets/venus/disk/terminator`.

PNG, PDF, and SVG must consume the same prepared projected geometry. SVG
semantics annotate the ordinary artists; SVG must not receive separate
astronomical geometry.

The illuminated face is filled, the limb is the outer stroke, and the
terminator is an interior stroke. Style owns their appearance and z-order.
The geometry owns neither colour nor line width.

## 9. Validation and acceptance plan

The geometry slice must test:

1. unchanged accepted centre and physical state;
2. factor-one and magnified angular radii;
3. limb radius and closure;
4. terminator endpoints on the limb;
5. visible and illuminated inequalities;
6. illuminated-area behavior across limiting phases;
7. bright side toward the accepted Sun direction;
8. rotation through equatorial, horizontal, and a nontrivial chart
   orientation;
9. projection-domain and viewport-edge behavior;
10. semantic identity and shared-output parity;
11. rejection of invalid magnification and unsupported chart families;
12. unchanged symbolic defaults and output-neutral behavior when unresolved.

Scientific validation must compare at least the accepted La Ligua DE440 Venus
case with an independently constructed tangent-plane phase geometry. Visual
acceptance must include factor `1` and at least one useful magnification in
regional and binocular charts.

## 10. Proposed implementation slices

### 49I.3C.1 — Resolved Venus spherical geometry

Add renderer-neutral limb, terminator, and illuminated-face construction plus
deterministic geometry tests. Add no chart request or visible output.

### 49I.3C.2 — First drawable resolved Venus disk

Install the opt-in regional/binocular request, Venus-specific magnification,
layer group, style, semantic SVG descendants, validation command, and visual
acceptance. Preserve symbolic defaults and planisphere/all-sky behavior.

## 11. Non-goals

49I.3C does not:

- add Venus photometry or magnitude-scaled symbolic appearance;
- generalize unvalidated physical models to other planets or the Moon;
- add surface texture, atmospheric scattering, limb darkening, body-axis
  markings, or topography;
- infer page orientation directly from the apparent-ICRS position angle;
- use scatter-marker size as resolved angular geometry;
- add a renderer-specific or format-specific astronomical path;
- pre-accept the illustrative command vocabulary or a production
  magnification default.

## 12. Review questions

Fernando should review and accept:

1. the three-part semantic geometry group rather than one mixed grid;
2. pre-projection magnified spherical geometry;
3. the physical/display radius separation;
4. resolved-mode and per-object magnification as separate choices;
5. regional/binocular-only first scope;
6. the proposed `49I.3C.1` and `49I.3C.2` split;
7. validation, semantics, and non-goals.

Only after this audit is accepted should runtime geometry be implemented.
