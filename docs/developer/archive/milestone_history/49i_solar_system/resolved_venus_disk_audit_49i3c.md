# Resolved Venus disk audit — Milestone 49I.3C

**Status:** Scientifically and architecturally accepted

**Audit date:** 2026-08-31

**Acceptance date:** 2026-08-31

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

## 3. Accepted ownership boundary

The resolved disk is a small semantic layer group produced from one physical
appearance state:

- an illuminated-face `SphericalPolygons` layer;
- a limb `SphericalCurves` layer;
- a terminator `SphericalCurves` layer.

This separation permits independent fill and stroke policies for the
illuminated face, limb, and terminator while keeping their geometry and
identity explicit. The three records share the accepted apparent centre,
physical state, sampling contract, and semantic parent. No scientific layer
calculates page coordinates or calls a renderer.

A dedicated scientific disk-geometry module constructs the three physical
spherical records. The ordinary machinery transforms and projects them.
Chart preparation then applies the Venus-specific display magnification around
the projected physical centre. Style owns fill, stroke, widths, alpha, and
drawing order. The renderer remains body-agnostic.

## 4. Physical and displayed radius

Let `rho = d / 2` be the accepted physical angular radius, where `d` is
the 49I.3B angular diameter. The spherical limb, terminator, and illuminated
face are sampled at this physical radius.

Let `M_venus` be the positive finite, object-specific display
magnification. After ordinary projection, chart preparation scales every
projected vertex around the separately projected physical centre:

`q_display = q_center + M_venus * (q_physical - q_center)`.

The physical state and pre-projection spherical geometry retain `d`
unchanged. Magnification must not change the centre, phase, illumination,
visibility, ephemeris state, provenance, or sampling topology.

A factor of `1` means physical projected scale. Resolved mode and
magnification are separate choices. Magnification alone must not silently
enable a disk.

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

## 6. Projection, magnification, and clipping

The physical disk is sampled on the celestial sphere and passed through the
ordinary product-frame transformation and projection. Magnification occurs
after projection, in chart preparation, by scaling projected vertex offsets
about the projected physical centre. It is therefore neither a scatter-marker
approximation nor a renderer transform.

Pre-projection sampling must be fine enough that the enlarged projected limb,
terminator, and illuminated boundary remain smooth at the accepted maximum
magnification and output resolution. The sampling count is a deterministic
geometry parameter retained in metadata. The first implementation must derive
or validate a conservative minimum from the supported magnification range;
adaptive sampling is deferred unless fixed sampling proves inadequate.

Projection-domain clipping acts on the physical spherical geometry before
projection. Viewport clipping acts on the magnified prepared geometry. A
resolved disk whose physical centre lies outside a viewport can still have
magnified geometry inside it, so final visibility cannot use centre-only
rejection.

## 7. Product, request, and multi-epoch policy

The first drawable slice should:

- remain symbolic by default;
- allow resolved Venus only in regional and binocular families;
- reject resolved Venus in planisphere and all-sky families;
- use a positive finite Venus-specific magnification;
- preserve the ordinary Venus point unless the resolved representation
  explicitly replaces it;
- avoid a second centre-direction or appearance realization for an instant.

Wenu must also be able to place magnified resolved Venus disks for several
requested instants in one chart. Each instant owns its apparent centre and
physical appearance state. All centres and disk geometries are transformed
into one fixed chart product frame, following the accepted trajectory
principle, so the chart itself does not rotate between samples. The same
Venus-specific magnification policy is applied after projection to each disk;
a future extension may permit per-sample styling without changing the
scientific state.

Illustrative command vocabulary remains provisional until the runtime slice,
for example `--planet-appearance venus=resolved`,
`--planet-disk-magnification venus=40`, and an explicit list or regular
sequence of disk instants. This audit does not install or accept those
spellings.

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

The geometry and preparation slices must test:

1. unchanged accepted centre and physical state;
2. factor-one and magnified projected radii;
3. limb radius and closure;
4. terminator endpoints on the limb;
5. visible and illuminated inequalities;
6. illuminated-area behavior across limiting phases;
7. bright side toward the accepted Sun direction;
8. rotation through equatorial, horizontal, and a nontrivial chart
   orientation;
9. post-projection scaling about the projected physical centre;
10. sampling adequacy at the supported maximum magnification;
11. projection-domain and magnified viewport-edge behavior;
12. semantic identity and shared-output parity;
13. rejection of invalid magnification and unsupported chart families;
14. unchanged symbolic defaults and output-neutral behavior when unresolved;
15. multiple epochs in one fixed chart frame, with independently correct
    centre, phase, orientation, and date identity at every sample.

Scientific validation must compare at least the accepted La Ligua DE440 Venus
case with an independently constructed tangent-plane phase geometry. Visual
acceptance must include factor `1`, at least one useful magnification in
regional and binocular charts, and a multi-epoch chart that makes changing
position, angular diameter, phase, and bright-limb direction inspectable.

## 10. Accepted implementation slices

### 49I.3C.1 — Resolved Venus spherical geometry

Add renderer-neutral, physically sampled limb, terminator, illuminated-face,
and centre construction plus deterministic geometry tests. Add no chart
request or visible output.

### 49I.3C.2 — First drawable resolved Venus disk

Install the opt-in regional/binocular request, post-projection Venus-specific
magnification, layer group, style, semantic SVG descendants, validation
command, and visual acceptance. Preserve symbolic defaults and
planisphere/all-sky behavior.

### 49I.3C.3 — Multi-epoch resolved Venus disks

Allow an explicit list or regular sequence of instants to place several
independently realized, magnified Venus disks in one fixed chart frame. Reuse
the accepted track-time and fixed-frame principles; do not create a second
projection, renderer, or export path.

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

## 12. Acceptance

Fernando accepted this boundary on 2026-08-31 with two explicit revisions:

1. display magnification occurs after ordinary projection, with physical
   pre-projection sampling fine enough for the enlarged result;
2. the roadmap includes several magnified, independently realized Venus disks
   at different instants in one fixed chart.

He also accepted the separate illuminated-face, limb, and terminator
geometries because they permit distinct fill and stroke policies.

Initial acceptance verification passed all 60 current-documentation tests in
1.80 seconds. After recording the accepted revisions, all 60 documentation
tests passed in 2.81 seconds, 1,937 routine tests passed with 30 deselected in
28.40 seconds, and all 1,967 tests passed in 89.14 seconds. Runtime geometry,
command vocabulary, supported magnification range, and visible output remain
separately authorized implementation work.

