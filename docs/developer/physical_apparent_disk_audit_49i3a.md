# Physical apparent-disk audit — Milestone 49I.3A

**Status:** Scientifically and architecturally accepted

**Audit date:** 2026-08-31

**Implementation baseline:** `449a3c9`

## 1. Purpose

This audit defines the smallest scientifically honest boundary between the
accepted symbolic Solar-System points and future resolved apparent disks. It
changes no runtime type, public command, style, geometry, chart, or output.

The first implementation target is Venus, followed by the Moon. Both must reuse
the accepted ephemeris, apparent-direction, product-frame transformation,
projection, visibility, renderer, and PNG/PDF/SVG export path.

## 2. Accepted user-facing intent

Wenu needs two deliberately different representations.

1. **Symbolic representation.** By default a planet remains a point-like chart
   symbol participating in the chart's magnitude hierarchy. Its label uses the
   customary astronomical glyph where one exists. A symbolic marker makes no
   claim about angular diameter or phase.
2. **Resolved representation.** Regional and binocular charts may explicitly
   request the physically visible illuminated disk. A body-specific display
   magnification may enlarge that disk for legibility. Magnification changes
   page-space appearance only; it never changes the body's physical angular
   diameter, centre, visibility, or scientific provenance.

Planisphere and all-sky products retain symbolic representation. They do not
silently switch to resolved disks or inherit a regional-chart magnification.

## 3. As-is findings

### 3.1 Scientific position

`SolarSystemPointLayer` currently realizes one observer-origin apparent
direction and transforms it once into the chart product frame. Venus and the
Moon are thin descriptor specializations. The resulting
`SphericalPoints` contains a centre direction and semantic identity, but no
radius, phase, body orientation, illuminated fraction, or photometry.

This direction remains the authoritative centre of every future symbolic or
resolved representation.

### 3.2 Appearance

`PublicationStyle` currently assigns Venus and the Moon fixed hollow circular
markers and fixed label settings. Those markers are provisional symbols. Their
areas are not derived from stellar magnitude, angular diameter, or output
scale.

The existing point renderer is therefore sufficient for symbolic bodies but
cannot represent an illuminated disk without a new, renderer-neutral appearance
record and ordinary projected geometry.

### 3.3 Product restrictions

Regional and binocular charts already have the controlled viewport and scale
needed for an opt-in resolved disk. Planisphere and all-sky charts compress too
much sky for a physical disk to remain generally useful and must preserve
symbolic rendering in the first slices.

## 4. Separate scientific quantities

The implementation must keep the following concepts distinct.

| Quantity | Meaning | Owner |
| --- | --- | --- |
| apparent centre direction | observer-relative location at reception | accepted Solar-System direction chain |
| physical angular diameter | apparent limb-to-limb angle before display enlargement | physical-appearance realizer |
| illuminated fraction | physical fraction of the visible disk illuminated | physical-appearance realizer |
| bright-limb position angle | orientation of the illuminated limb on the tangent plane | physical-appearance realizer |
| body-axis orientation | orientation of north and body-fixed surface features | body-specific orientation model |
| apparent magnitude | photometric brightness used by symbolic hierarchy | body-specific photometric model |
| display magnification | dimensionless page-space enlargement | request/detail policy, validated by chart family |
| colour, line, fill, glyph | graphical appearance | chart style |

An observation instant is not an equinox or position reference epoch. A body
orientation model is not a coordinate transformation. Display magnification is
not an astronomical quantity.

## 5. Proposed physical-appearance contract

A frozen renderer-neutral `SolarSystemApparentDisk` value should accompany,
not replace, the accepted apparent centre result. At minimum it records:

- target and semantic body identity;
- reception instant and time scale;
- observer identity or geodetic provenance;
- ephemeris/model provenance;
- apparent centre direction;
- physical angular diameter;
- illuminated fraction;
- bright-limb position angle measured in an explicitly named tangent-plane
  convention;
- the correction and orientation policies used;
- optional body-axis position angle only when supplied by a validated
  body-orientation model.

The record must not contain projection coordinates, points, pixels, font sizes,
output filenames, chart classes, or display magnification.

The exact tangent-plane sign and zero-angle convention must be frozen by a
numerical audit before runtime implementation. No renderer may infer it from
screen axes.

## 6. Geometry and canonical pipeline

The physical realizer evaluates the appearance at the same reception instant
and observer context as the accepted centre direction. The resolved disk then
enters the normal pipeline:

```text
ephemeris state and observer
    -> accepted apparent centre direction
    -> physical apparent-disk state
    -> product-frame centre and tangent orientation
    -> ordinary spherical disk boundary / illuminated-region geometry
    -> existing projection-domain guard and projection
    -> projected preparation and clipping
    -> existing renderer
    -> shared PNG/PDF/SVG export
```

No body-specific renderer, Matplotlib patch injected after chart composition,
SVG-only overlay, or alternate exporter is permitted.

A resolved disk is not merely a large scatter marker. Its boundary and
illuminated region must be explicit semantic geometry so that projection,
clipping, vector export, and future body-specific surface detail remain
governed.

For the small fields and small angular extents of the first Venus slice, a
tangent-plane construction may be sufficient, but its approximation and
tolerance must be tested against a spherical construction. The Moon must not
inherit a Venus approximation without a separate error bound.

## 7. Symbolic magnitude hierarchy

The requested default is a planet symbol comparable with stellar symbols at
the same apparent magnitude. This requires a governed photometric model; the
current fixed Venus marker cannot honestly be described as magnitude-scaled.

The first symbolic-photometry slice should therefore:

- compute or obtain apparent visual magnitude with model provenance;
- feed the existing configured stellar symbol-size mapping rather than create a
  second magnitude scale;
- cap or specialize exceptionally bright bodies so that the Moon and very
  bright planets do not dominate the page;
- retain a recognizable planet marker or customary glyph without implying a
  resolved disk;
- keep label glyph selection separate from the scientific object name and
  semantic identity.

Until that model is validated, the present hollow symbols remain explicitly
provisional fixed-size markers.

## 8. Display magnification and request policy

Display magnification is object-specific and opt-in. A proposed internal
request shape is a mapping from body selection key to a positive finite factor,
rather than one global factor. For example, Venus and the Moon may carry
different values in one composition.

The public interface must be designed in its implementation milestone. A
possible vocabulary is:

```text
--planet venus
--planet-appearance venus=resolved
--planet-disk-magnification venus=40
--moon
--moon-appearance resolved
--moon-disk-magnification 4
```

These names are illustrative, not accepted API.

Rules:

- factor `1` means physical angular scale;
- a factor must be positive, finite, and bounded by an explicit safety limit;
- the factor changes only the apparent disk geometry presented for drawing;
- the unscaled physical angular diameter remains in scientific metadata;
- symbolic mode ignores disk magnification rather than pretending the symbol
  is a magnified disk;
- resolved mode is initially valid only for regional and binocular charts;
- planisphere and all-sky requests reject or explicitly decline resolved mode;
- default requests and existing commands remain byte/graphically compatible.

## 9. Venus and Moon are not the same physical model

### 9.1 Venus first

Venus is the smallest architectural slice:

- nearly spherical limb;
- apparent angular diameter from observer-target distance and adopted physical
  radius;
- illuminated fraction and bright-limb orientation from the Sun–Venus–observer
  geometry;
- no surface-orientation rendering required initially;
- strong phase variation provides a clear numerical and visual test.

The first resolved Venus may use a neutral monochrome illuminated disk. Colour
and atmospheric appearance are style questions, not ephemeris facts.

### 9.2 Moon second

The Moon is the stronger scientific and rendering validation:

- large topocentric angular diameter;
- phase and bright-limb orientation;
- body-axis orientation, libration, and observer-dependent limb orientation if
  surface features or a lunar north marker are claimed;
- separate body-radius and orientation-model provenance;
- stronger projection and clipping tests because its enlarged disk is visible.

A simple phase-only lunar disk may precede surface texture, but it must say
explicitly that it does not represent libration or named surface features.
The Moon correction and orientation policies must be numerically validated
rather than copied from Venus.

## 10. Semantic SVG boundary

Resolved output should retain the existing body root:

- `sky/solar_system/planets/venus`;
- `sky/solar_system/natural_satellites/moon`.

Descendants should distinguish at least `symbol`, `disk/limb`,
`disk/illuminated`, and `label`. Physical diameter, illuminated fraction,
reception instant, model identity, and display magnification should remain
available as semantic metadata where the export contract permits it.

PNG, PDF, and SVG must consume the same prepared projected records.

## 11. Proposed implementation sequence

### 49I.3B — Venus physical-appearance state

Add frozen physical-appearance contracts and an installed-DE440 Venus
validator. Compare angular diameter, phase fraction, and bright-limb position
angle with independent Skyfield or explicitly documented analytical
authorities. Add no visible output.

### 49I.3C — First resolved Venus disk

Add one opt-in regional/binocular Venus disk, object-specific magnification,
ordinary projected geometry, shared renderer/export, semantic SVG structure,
and visual acceptance. Existing symbolic output remains the default.

### 49I.3D — Symbolic photometry and planet glyphs

Integrate validated Venus apparent magnitude with the existing stellar
magnitude scale, define bright-object capping, and use the customary Venus
glyph for labeling. Generalization to another planet requires its own
photometric model.

This may move before 49I.3C if symbolic hierarchy is prioritized, but it must
not be conflated with physical disk geometry.

### 49I.3E — Moon physical-appearance state

Validate topocentric lunar angular diameter, phase, bright-limb angle, and the
minimum orientation model required by the intended drawing. Add no visible
output.

### 49I.3F — First resolved Moon disk

Add the opt-in regional/binocular lunar disk through the same appearance and
geometry boundary, with a Moon-specific magnification and explicit
phase-only versus body-oriented capability.

## 12. Acceptance requirements for this audit

Fernando must review and accept:

1. symbolic and resolved representations as separate contracts;
2. physical angular diameter and display magnification as separate values;
3. object-specific rather than global magnification;
4. regional/binocular first scope and symbolic planisphere/all-sky behavior;
5. explicit apparent-disk geometry through the canonical pipeline;
6. Venus-first physical state, followed by separate Moon validation;
7. photometry as the prerequisite for honest magnitude-scaled symbols;
8. the proposed implementation sequence and non-goals.

Automated documentation checks protect the recorded boundary. They do not
constitute scientific or visual acceptance.

## 13. Non-goals

49I.3A does not add:

- a runtime apparent-disk type;
- angular-diameter, phase, photometric, or orientation calculations;
- a resolved Venus or Moon;
- a new CLI or TOML key;
- changes to existing Venus/Moon markers or labels;
- textures, albedo maps, atmospheric rendering, shadows, rings, or satellite
  transits;
- planisphere/all-sky resolved disks;
- tracks for additional bodies;
- a renderer, projection, or exporter;
- caching, batching, or performance optimization.

## 14. Stop conditions

Stop and re-audit if an implementation would:

- enlarge a marker and call it a physical disk;
- store display magnification in the scientific appearance record;
- derive phase orientation from projected screen axes;
- let style choose angular diameter, phase, or body orientation;
- let an ephemeris provider choose chart appearance;
- copy the Venus physical model into the Moon without separate validation;
- bypass spherical geometry, projection, clipping, or the shared exporter;
- make PNG, PDF, and SVG consume different body geometry.


## 15. Scientific and architectural acceptance

Fernando accepted the symbolic-versus-resolved distinction, separation of
physical angular diameter from object-specific display magnification,
regional/binocular first scope, symbolic planisphere/all-sky behavior,
explicit semantic geometry through the canonical pipeline, Venus-first
physical validation, separate Moon validation, photometry prerequisite, and
proposed implementation sequence on 2026-08-31.

Initial acceptance verification passed all 58 current-documentation tests in
2.51 seconds on Fernando's Mac. At the accepted branch head, all 58
current-documentation tests passed in 1.95 seconds, the routine suite passed
1,926 tests with 30 deselected in 28.95 seconds, and the complete suite passed
all 1,956 tests in 91.38 seconds. This accepts the audit contract and sequence. It does not pre-accept the future
49I.3B numerical model, tolerance, runtime contract, public interface, or any
resolved visual result.
