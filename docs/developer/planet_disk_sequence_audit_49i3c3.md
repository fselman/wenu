# Multi-epoch resolved planet-disk audit — Milestone 49I.3C.3

**Status:** Scientifically and architecturally accepted  
**Audit date:** 2026-08-31  
**Acceptance date:** 2026-08-31  
**Implementation baseline:** `6745403`

## 1. Purpose

This audit freezes the scientific and architectural boundary for drawing several
resolved planet disks at declared instants in one static chart. It changes no
runtime type, public command, geometry, style, chart, renderer, or output.

Two products are required, but they do not describe the same physical scene:

1. an **observed sequence**, in which the topocentric observer and planet are
   independently realized at every sample instant and placed in one fixed chart
   product frame; and
2. a **frozen-Earth ecliptic sequence**, a constructed heliocentric diagram in
   which Earth's heliocentric position is frozen at the start instant while the
   selected planet advances.

Calling the second product an observed or apparent sky would be scientifically
incorrect. The two policies may share typed sequence records, physical disk
geometry, post-projection magnification, semantic components, rendering, and
export only after their different direction and appearance states are resolved.

## 2. Accepted baseline

49I.3C.2 draws one explicitly selected resolved Venus disk in regional and
binocular charts. Its physical state, centre, illuminated face, limb, and
terminator are ordinary pre-projection semantic geometry. Its object-specific
display magnification is applied after projection about the separately
projected physical centre. Symbolic Venus remains the default.

49I.2D supplies the related trajectory precedent: every moving-body sample has
its own physical instant, while the complete path is transformed into one fixed
chart frame. A disk sequence differs from a track because it needs no minor
curve cadence and draws an independently realized physical disk at every major
sample.

## 3. Common immutable sequence contract

A sequence request names:

- one supported planet;
- one realization model;
- a UTC start instant;
- one positive major step;
- a non-negative number of major intervals;
- optional epoch labels; and
- one positive finite object-specific display magnification.

The start instant is included. The count is the number of intervals, so
`n_steps = 8` produces nine disk samples at indices 0 through 8. There is no
minor step and no interpolated path. Each displayed disk is realized at its
exact declared sample instant.

The result retains, for every sample:

- exact instant and time scale;
- realization-model identity;
- target, centre, observer, resource, and kernel provenance;
- typed direction and its coordinate status;
- full physical distance with declared origin and unit, physical angular
  diameter, phase angle, illuminated fraction, and bright-limb orientation;
- physical centre, illuminated-face polygon, limb curve, and terminator curve;
- stable object-and-epoch semantic identity.

The full physical distance is retained even though the present 2D chart uses
it chiefly to derive angular size. It must not be discarded after projection:
a future 3D Solar-System visualizer may consume the same scientifically
provenanced sequence state without reconstructing distance from page geometry.
That future visualizer remains outside this milestone and must receive its own
architecture and validation.

One common magnification applies to all samples of one object in one request.
This preserves their relative physical angular-size changes. Factor `1` means
physical projected scale. Magnification changes display geometry only; it does
not alter any retained physical angular diameter, direction, visibility, phase,
or provenance.

Every disk is sampled finely enough before projection for the requested
magnification. After ordinary projection, each component is scaled around that
sample's separately projected physical centre. No disk may be a large scatter
marker or a post-export overlay.

## 4. Model 1 — observed

At every sample instant, the implementation independently reevaluates:

- the geographic observer's barycentric state;
- the target's retarded astrometric state;
- apparent-place corrections;
- the topocentric apparent direction;
- target distance and physical angular diameter;
- phase, illuminated fraction, and bright-limb direction.

The samples are then transformed exactly once into the fixed product frame of
the static base chart and follow the canonical projection and rendering path.
The background scene, grid, horizon, and chart furniture belong to the base
chart observer instant. They are not recomputed or duplicated for each disk.

This model is therefore suitable for regional and binocular charts containing
the normal Wenu scene: stars, coordinate grids, constellation lines and labels,
constellation boundaries, deep-sky objects, the observer horizon, and ordinary
chart furniture. The sequence shows how independently observed planet states
move through that fixed chart.

## 5. Model 2 — frozen Earth in a fixed ecliptic frame

This model is a constructed orbital-geometry diagram, not an observed sky.

At the start instant, freeze Earth's heliocentric position vector
\(\mathbf{r}_{E,0}\). For each requested epoch \(t_i\), evaluate the planet's
heliocentric geometric position \(\mathbf{r}_{P}(t_i)\) and form

\[
\mathbf{d}_i = \mathbf{r}_{P}(t_i) - \mathbf{r}_{E,0}.
\]

The Sun direction is the fixed vector from frozen Earth to the heliocentric
origin,

\[
\mathbf{d}_{Sun} = -\mathbf{r}_{E,0}.
\]

The diagram uses one explicitly declared fixed ecliptic reference frame and is
centred on \(\mathbf{d}_{Sun}\). The planet direction must be described as a
**frozen-observer geometric direction**, never as an apparent direction.
Distance, angular diameter, phase, illuminated fraction, and bright-limb
orientation are computed consistently from the frozen observer and the
same-epoch Sun/planet geometry; no topocentric observer motion, aberration, or
ordinary apparent-place chain is implied.

The fixed Earth vector and fixed Sun direction make the construction legible:
planet motion is isolated from Earth's orbital displacement. The equatorial
grid may be transformed into the fixed ecliptic frame to show obliquity.

## 6. Permitted content

| Content | Observed | Frozen-Earth ecliptic |
| --- | :---: | :---: |
| Resolved Venus sequence | yes | yes |
| Resolved Mercury sequence | later validated slice | required generalization |
| Central Sun symbol | ordinary selection if supported later | automatic |
| Equatorial grid | yes | yes, expressed in the fixed ecliptic frame |
| Other coordinate grids | yes | no |
| Stars and deep-sky objects | yes | no |
| Constellation lines, labels, boundaries | yes | no |
| Horizon and AltAz grid | yes | no |
| Ordinary chart furniture | yes | no, except construction-specific labels |

The narrow frozen-mode content is mandatory. Stars, constellations, deep-sky
objects, boundaries, horizon, and ordinary observer-local furniture would
silently mix changing physical epochs with a non-observational frame.

## 7. Central Sun contract

Frozen-Earth ecliptic mode automatically installs one semantic Sun layer at the
fixed centre. Its default glyph is a six-point star. It is a diagram symbol,
not a resolved solar disk and not evidence of apparent solar angular size.

The Sun keeps stable upstream identity under
`sky/solar_system/star/sun`. Style owns its color, size, stroke, fill, and
z-order. The request may later expose an explicit visibility/style control, but
the first frozen-mode slice keeps it present so the construction cannot be
mistaken for an uncentred observed chart.

## 8. Proposed public vocabulary

The first implementation should use one coherent family:

```text
--planet-disk-sequence venus
--disk-sequence-model observed|frozen-earth-ecliptic
--disk-sequence-start 2026-08-30T00:00:00Z
--disk-sequence-step 7d
--disk-sequence-n-steps 8
--disk-sequence-labels
--planet-disk-magnification venus=120
```

The existing object-specific magnification option is reused. The sequence
selector explicitly enables sequence disks; magnification alone cannot enable
them. A single-disk resolved request and a disk sequence for the same body must
either be rejected as conflicting or normalized by one documented request
owner; silent duplication is forbidden.

This vocabulary remains proposed until the relevant runtime slice is separately
reviewed and accepted.

## 9. Shared architecture

Both models produce one frozen typed sequence after scientific realization.
Three drawable component layers—illuminated faces, limbs, and terminators—share
that sequence and its semantic parent. They do not recompute states.

The canonical flow remains:

```text
model-specific states and directions
    -> per-epoch physical appearance
    -> per-epoch spherical disk geometry
    -> one fixed product-frame transformation
    -> projection-domain guard and projection
    -> per-centre display magnification
    -> ordinary renderer and PNG/PDF/SVG export
```

The frozen model may have a separate realization policy, but it may not create
a second disk-geometry, projection, renderer, or exporter pipeline.

## 10. Semantic and label contract

A sequence parent identifies the object and model. Each sample identity includes
an exact normalized epoch, beneath which the illuminated face, limb, and
terminator remain separate semantic children. Labels derive from retained
sample instants and use the established collision-aware chart-annotation
machinery where applicable.

Frozen-mode output and metadata must visibly state that Earth is frozen at the
start instant and that planet directions are geometric. SVG metadata must not
mislabel the construction as topocentric apparent sky content.

## 11. Validation requirements

The observed slice must compare every sample's centre and appearance state with
independent direct-Skyfield evidence using the installed accepted kernel. It
must verify one fixed chart frame, exact sample instants, relative disk-size
changes, phase orientation, semantic identity, and PNG/PDF/SVG parity.

The frozen slice must independently validate:

- the frozen Earth heliocentric vector;
- each same-epoch planet heliocentric vector;
- frozen-Earth target direction and distance;
- phase and illuminated fraction;
- fixed Sun direction and centring;
- ecliptic-frame identity and equatorial-grid transformation;
- rejection of every forbidden scene layer.

Mercury requires its own accepted physical radius, provider identifiers,
kernel coverage, numerical comparison, and phase/orientation evidence. Venus
success cannot be copied as Mercury validation.

Human review remains mandatory for sequence legibility, label placement,
relative scale, phase orientation, central-Sun hierarchy, and the scientific
clarity of the frozen construction.

## 12. Bounded implementation sequence

- **49I.3C.3.1 — Observed multi-epoch Venus disks.** Implement the common typed
  sequence and the observed policy in regional and binocular charts.
- **49I.3C.3.2 — Frozen-Earth ecliptic Venus sequence.** Add the constructed
  fixed-ecliptic policy, restricted content, and central six-point Sun.
- **49I.3C.3.3 — Mercury generalization and validation.** Add the independently
  validated Mercury body model and enable it in frozen-Earth ecliptic mode.

Each slice requires separate authorization and acceptance. This audit does not
pre-accept runtime types, command spelling, numerical tolerances, styles,
rendered output, or Mercury constants.

## 13. Non-goals

This audit does not add animation, a minor curve cadence, an interpolated
trajectory, adaptive sampling, multiple bodies in one request, planisphere or
all-sky resolved sequences, physical Sun geometry, Earth-orbit integration,
post-export annotations, or performance caching.

It also does not implement the possible future 3D Solar-System visualizer for
which physical distances are deliberately preserved, and it does not make the
frozen construction a general planetarium mode. Wenu remains a static-chart system, and both products must pass through the canonical
static projection, rendering, and export machinery.


## 14. Acceptance

Fernando scientifically and architecturally accepted this audit on 2026-08-31,
including preservation of full physical distance and provenance for possible
future 3D Solar-System visualization. Initial acceptance verification passed all 63 current-documentation tests in
2.04 seconds. Final verification passed all 63 current-documentation tests in
1.88 seconds, 1,971 routine tests with 30 deselected in 27.08 seconds, and all
2,001 tests in 85.97 seconds. This acceptance authorizes only the separately
bounded
49I.3C.3.1 observed multi-epoch Venus implementation; it does not pre-accept
runtime types, numerical tolerances, public command spelling, visible output,
the frozen-Earth implementation, Mercury support, or a 3D visualizer.
