# First drawable comet audit (Milestone 50A.5A)

**Status:** Scientifically and architecturally accepted by Fernando on 2026-09-12

**Base:** `70a36ee`

**Runtime effect:** None. This audit authorizes no selector, descriptor,
resource conversion, style, chart layer, track, acquisition, or output change.

## 1. Bounded recommendation

Use **2P/Encke** as Wenu's first drawable comet. A later 50A.5B may add one
opt-in symbolic nucleus point and one independently opt-in dated nucleus track.
It must reuse the accepted minor-body provider and shared Solar-System
point/track pipeline validated in 50A.4.

50A.5B must not add comet discovery, automatic acquisition, orbital-element
propagation, magnitude or detectability, a physical nucleus disk, coma, tail,
photocentre, jets, activity, uncertainty region, or occultation behavior.

## 2. As-is reuse assessment

The implemented path is already generic after descriptor and source resolution:

1. `SolarSystemBodyDescriptor` carries identity, capabilities, and source key;
2. `MinorBodyResourceSession` binds a selected target SPK to the ordinary
   planetary observer source;
3. `SolarSystemPointLayer` realizes one apparent point;
4. `SolarSystemTrackRealizer` samples apparent directions into one fixed chart
   product frame;
5. projection, clipping, preparation, rendering, semantic SVG, and export are
   shared.

No comet-specific direction, track, projection, renderer, or exporter is
needed. The asteroid-specific assumptions are earlier: CLI fields, positive
integer parsing, collection identity validation, diagnostics, automatic
preflight, semantic classification, and style selection. Those boundaries
must be generalized explicitly rather than treating `2P` as asteroid `(2)`.

## 3. Identity and designation

Adopt these identities for the bounded implementation:

| Role | Value |
|---|---|
| selection key | `2p` |
| body class | `comet` |
| primary designation | `2P` |
| canonical/display designation | `2P/Encke` |
| Horizons apparition command | `90000091;` |
| permanent NAIF SPK target | `1000025` |
| accepted orbit solution | `K273/14` |
| semantic point path | `sky/solar_system/minor_bodies/comets/2p` |
| semantic track path | `sky/solar_system/minor_bodies/comets/2p/track` |

The periodic-comet number and `P` suffix are one designation. They must not be
stored or displayed as minor-planet number `(2)`. Exact installed aliases may
include case-insensitive `2p`, `2p/encke`, and `encke`, but all resolve to one
descriptor and one solution identity. Apparition record `90000091` remains
provider provenance; it is not the stable Wenu selection key or physical SPK
target.

The identity model must not encode `P` as the only possible cometary
designation class. It must be able to represent and validate the IAU/MPC
prefix vocabulary separately from dynamical state availability. The supported
identity vocabulary is `P`, `D`, `I`, `C`, `X`, and `A`:

| Prefix | Identity meaning | 50A.5B behavior |
|---|---|---|
| `P` | periodic comet | recognize; only installed `2P` is authorized |
| `D` | defunct, disappeared, disrupted, or lost periodic comet | recognize identity; require a separately valid installed ephemeris and coverage |
| `I` | interstellar object | recognize identity; require separate scientific validation before drawing |
| `C` | non-periodic comet | recognize identity; require separate scientific validation before drawing |
| `X` | comet without a reliable orbit | recognize identity; reject drawing without an authoritative bounded state |
| `A` | object determined to be asteroidal in the cometary designation system | recognize classification; do not silently route through `--comet` |

Numbered forms such as `2P`, `3D`, and `1I` retain their letter as part of
identity. Provisional forms such as `C/2020 F3`, `P/2011 NO1`, and fragment
suffixes such as `-A` or `-B` require structured fields rather than destructive
punctuation stripping. Normalization may trim spacing and case-fold exact
aliases, but must preserve the canonical designation and must not collapse
different prefixes, provisional designations, fragments, or dual-status
objects onto one integer.

The bounded parser/identity seam may diagnose these classes, but recognizing a
well-formed designation is not a promise that Wenu can draw it. Only a matching
installed descriptor, scientifically accepted solution, digest, target, and
coverage authorize state evaluation. In particular, a `D` object normally
fails for lack of a current valid state, while a future validated `I` SPK can
reuse the generic minor-body provider without being called a periodic comet.

The 50A.4 `A1` and `A2` records remain attached to the provider solution.
Wenu neither reapplies nor removes their modeled accelerations.

## 4. Resource boundary

50A.5B must use an explicit installed resource directory containing a
structured collection manifest and the exact validated SPK. The collection
loader may admit a typed comet record alongside typed asteroid records, but it
must validate class-specific identity:

- comet designation `2P`, exact provider target `1000025`, solution `K273/14`,
  model parameters, segment centre `10`, type `21`, digest, and coverage;
- asteroid permanent-number rules remain unchanged;
- duplicate aliases across classes fail closed;
- filenames may not escape the resource directory;
- one chart build opens the selected kernel once and closes it once.

The raw `50a4-raw-v2` evidence directory is an acquisition/validation artifact,
not silently a production collection. A bounded offline installer or fixture
builder may convert the already inspected identity and SPK into the production
manifest form. It must not contact the network, mutate the raw evidence, or
weaken digest and solution checks.

Selecting Encke without an explicit compatible resource directory fails before
output. 50A.5B must not extend the numbered-asteroid automatic preflight to
comets. A later acquisition milestone must separately govern periodic-comet
identity, apparition selection, refresh, coverage, and solution changes.

## 5. Public request and time contract

Propose the class-aware vocabulary:

```text
--comet 2P
--comet-track 2P
--minor-body-resource-directory PATH
```

`--comet` may be repeated. The current chart request owns only one track, but
that restriction is unsuitable when one field contains several moving
objects. 50A.5B must replace the singular internal track slot with an immutable
collection and allow planet, asteroid, and comet track selectors together.
The class-aware options may be repeated, for example:

```text
--comet-track 2P --planet-track venus --asteroid-track 79989
```

All selected tracks share the existing `--track-start`, sample step, tick step,
tick count, and tick-label policy in this bounded slice. Per-track timelines
remain future work. Exact duplicate selections are rejected or deterministically
deduplicated before realization; they must never create duplicate layers.
Point and track selection remain independent. Merely supplying resources draws
nothing.

The point uses the chart observation epoch. Every track reuses `--track-start`,
`--track-sample-step`, `--track-tick-step`, `--track-tick-count`, and
`--track-tick-labels`, evaluates every sample independently, and transforms all
samples into the chart's single fixed product frame. One realization may mix
Skyfield planet states with manifest-backed asteroid and comet states, while
each descriptor retains its own target source and provenance. The selected
minor bodies share one resource session; every selected kernel is opened at
most once and closed once. Tracks remain regional or binocular only. Point
support may use all chart families already admitted for symbolic minor bodies.
Artificial-satellite tracks remain outside this contract.

## 6. Appearance and physical meaning

The first Encke mark is a fixed-size **constructed vector symbol**, not a
font-dependent marker and not a resolved nucleus, coma, tail, brightness,
visibility, or activity model. Fernando specifies:

- one hollow central circle;
- several evenly distributed short radial spokes beginning at the outside of
  the circle;
- three longer adjacent spokes forming the symbolic tail fan;
- two equal outer tail spokes delimiting an initial total fan angle of
  `25 deg` (**TBD by visual acceptance**);
- one central tail spoke on the fan bisector whose exposed radial length is
  `1.5` times the exposed length of either outer tail spoke; and
- the label `2P/Encke`.

Wenu must own this geometry as one canonical reusable vector symbol. Define
the normalized circle-and-spoke geometry once in the established symbol owner
(or a dedicated immutable symbol value reached through that owner), package it
with Wenu, and reuse that same definition for every comet instance and output
backend. It must not depend on a Unicode comet glyph, font outline, bitmap, or
backend-specific marker.

Using the symbol consists only of **placement, orientation, and
magnification** of the canonical normalized geometry. Rendering must not
reconstruct its circle and spokes from scratch for each object, track sample,
chart, or output format. The symbol value must be immutable and safe to reuse
across repeated charts without mutable transform or style leakage. A renderer
may materialize backend path objects from the canonical value at its normal
adapter boundary, but must not redefine the geometry.

Normal-spoke count, circle radius, base spoke length, outer-tail-spoke length,
and the final fan angle are initially fixed when the canonical symbol is
visually accepted. Linewidth and output-mode color remain style-owned. These
values do not vary with physical coma or tail size. A later deliberate symbol
revision changes the single canonical definition and its contract fixture,
not call sites throughout Wenu.

At the projected point, rotate the complete symbol so the central long spoke
points **antisolar** in the apparent sky: locally away from the apparent
direction of the Sun at the same observation instant. The two outer long
spokes remain symmetric about that direction.

This is a physical direction claim and must be computed before projection from
the observer-relative apparent comet and Sun directions. Transport a short
local tangent in the antisolar position-angle direction through the ordinary
fixed product frame, then let projection/preparation rotate the page glyph. Do
not infer the angle from the chart center, page axes, comet velocity, ecliptic,
or a projected Sun that may lie outside the viewport. Near exact solar
conjunction, where the apparent position angle becomes ill-conditioned, fail
closed or suppress the fan under one documented angular threshold rather than
invent an orientation.

50A.5B must validate the antisolar position angle before rendering it. Freeze
independent direct-Horizons apparent Sun and comet directions at several
accepted epochs, including different chart orientations, and establish an
explicit angular tolerance after characterization. Existing 50A.4 comet
position tolerances do not by themselves validate this new directional
quantity.

Only the fan direction is physical. The hollow circle, number of normal
spokes, `1.5` length ratio, opening angle, and page lengths remain a fixed
symbolic class glyph and do not encode measured coma or tail geometry. The
symbol must remain identifiable in atlas print, presentation, grayscale, and
semantic SVG without relying on color. Circle and spokes form one semantic
comet-symbol entity even if the renderer requires several path primitives.

Comet color, marker geometry, size, linewidth, alpha, and label style belong to
the Solar-System style contract. Track geometry and annotation remain shared;
only class-owned color may differ. No code may collapse every non-asteroid body
to the Venus style fallback.

## 7. Tests and acceptance

Extend existing responsibility-owned tests rather than create a comet-specific
runtime suite:

- descriptor/catalog tests: `2P` identity, comet class, capabilities, label,
  aliases, and semantic paths;
- resource tests: typed comet manifest, preserved `A1`/`A2`, digest, target,
  solution, coverage, alias collision, and one-open/one-close ownership;
- argument/request tests: `--comet`, repeated mixed-class track selectors,
  duplicate policy, shared track timing, and satellite exclusion;
- point/track tests: the existing injected provider and fixed-frame route;
- symbol/style/semantic tests: one canonical immutable circle/spoke geometry,
  symmetric tail fan, central `1.5` ratio, reuse without reconstruction,
  placement/orientation/magnification transforms, backend independence, no
  state leakage, one semantic entity, and stable point/track paths;
- documentation tests: explicit resources, offline failure, and non-goals.

Do not repeat 50A.4 Cartesian, light-time, apparent-place, parallax, or
non-gravitational-model numerical oracles. Do not repeat generic projection,
renderer, exporter, or track-annotation tests unless the new class changes the
fault model at that seam.

Before acceptance require focused and complete test gates, explicit missing
and out-of-coverage failures before output, confirmation of no network access,
and regional PNG plus semantic SVG review showing the antisolar-oriented point
and simultaneous dated comet, planet, and asteroid tracks.

## 8. Documentation and coordinate review

50A.5A changes no public guide because it changes no behavior. 50A.5B must
document installed-resource use, CLI examples, symbolic meaning, and the
absence of coma/tail and brightness claims. It must update the minor-body
architecture diagram without creating a second pipeline.

The Coordinate System Guide has been reviewed. Encke's SPK supplies the same
TDB/ICRF provider state accepted in 50A.4; the existing observer, astrometric,
apparent, product-frame, projection, and rendering ownership is unchanged.

## 9. Stop conditions

Stop and re-audit if implementation would:

- interpret `2P` as asteroid `(2)` or derive a provider target arithmetically;
- discard or reapply `A1`/`A2`, or substitute another apparition/solution;
- render directly from the raw validation directory without an explicit
  production manifest boundary;
- acquire, refresh, extrapolate, or use two-body fallback during charting;
- add a comet-specific direction, track, projection, renderer, or exporter;
- reopen the SPK for every track sample;
- derive the fan from chart center, velocity, ecliptic direction, or page axes,
  or render it without accepted antisolar position-angle validation;
- substitute a font or Unicode glyph for the constructed circle-and-spoke
  symbol, or let backend serialization define its geometry;
- reconstruct or redefine the symbol at each object, sample, chart, renderer,
  or call site instead of transforming Wenu's canonical immutable definition;
- retain a singular track request or prevent mixed planet, asteroid, and comet
  tracks in one supported field;
- admit artificial satellites into the shared multi-track slice;
- imply that the fixed symbol is measured coma, tail, orientation, magnitude,
  visibility, activity, or physical nucleus size;
- alter asteroid, planet, Moon, reusable-sphere, or existing track behavior;
- admit arbitrary comet designations or automatic comet preflight under the
  bounded first-Encke implementation merely because their syntax is
  recognized.

Fernando accepted this audit on 2026-09-12. That acceptance authorizes only the
bounded 50A.5B implementation described here.
