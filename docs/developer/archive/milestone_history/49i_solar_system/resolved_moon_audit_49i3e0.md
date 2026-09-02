# Resolved Moon scientific and architecture audit — Milestone 49I.3E.0

**Status:** Scientifically and architecturally accepted

**Audit date:** 2026-09-02

**As-is baseline:** `a8296f5`

## 1. Purpose and boundary

This audit freezes the scientific model, fixed-chart time semantics, reuse
boundary, public vocabulary, validation design, tolerances, and non-goals for
the resolved apparent Moon planned in 49I.3E. It changes no runtime type,
catalog registration, command, chart request, layer, geometry, style,
renderer, exporter, or visible output.

The later slices remain separate: 49I.3E.1 adds output-neutral lunar state and
installed-kernel validation; 49I.3E.2 draws one resolved Moon; 49I.3E.3 draws
an observed multi-epoch sequence in one fixed chart. No runtime Moon behavior
is authorized by this audit alone.

## 2. As-is audit

### 2.1 Identity and catalog

`src/wenu/sky/moon.py` still defines `MOON_POINT` as the older
`SolarSystemPointDescriptor`. The built-in catalog does not contain it, so it
has no catalog-owned physical ID, Earth relationship, radius, localized name,
or resolved/sequence capability.

The runtime slice must replace it with one `SolarSystemBodyDescriptor` while
preserving target, selection, display, entity, and symbolic compatibility. It
will have body class `natural_satellite`, physical body ID `301`, parent
`earth`, the radius below, and only independently accepted capabilities. It
must not create a second Moon identity.

### 2.2 Generic machinery already suitable for reuse

`SolarSystemAppearanceRealizer` already consumes accepted target and Sun
apparent directions plus descriptor-owned radius data. Its immutable
`SolarSystemApparentDisk` records centre, physical diameter, phase,
illuminated fraction, and apparent-ICRS bright-limb angle without display
magnification or page coordinates.

`SolarSystemDiskGeometryRealizer` already constructs physical centre, limb,
visible terminator, and illuminated polygon. `solar_system_disk_layers()` is
descriptor-driven. Ordinary coordinate transformation, projection guard,
projection, clipping, rendering, and PNG/PDF/semantic-SVG export are
body-neutral. Chart preparation already applies

`q_display = q_center + M * (q_physical - q_center)`

after projection about each exact physical centre.

`ObservedSolarSystemDiskSequenceRequest`, its realizer, and
`observed_solar_system_disk_sequence_layers()` already realize independent
topocentric observer, target, Sun, appearance, and geometry state at every
sample epoch, then transform each complete geometry into one product frame.
This is the correct first lunar sequence machinery. Frozen-Earth lunar
behavior is scientifically different and excluded.

### 2.3 Remaining generalization seams

| As-is seam | Required later change |
| --- | --- |
| Moon is absent from `SolarSystemBodyCatalog` | register one descriptor with Earth relationship, physical data, identity, and capabilities |
| public adapters spell disk controls as `planet_...` | adapt Moon vocabulary into the same internal display and sequence requests |
| `chart_disk_options()` admits resolved Venus only | make support capability-driven without widening unvalidated planet capabilities |
| disk/sequence chart gates allow regional and binocular only | allow the resolved Moon in all five ordinary chart families |
| cleanup enumerates Venus compatibility attributes | use descriptor-derived names while retaining required Venus aliases |
| some shared docstrings/errors say Venus or planet | use body-neutral wording where ownership is generic |
| style role strings retain `planet_...` | preserve harmless renderer roles, but derive Moon semantic identity from its descriptor |

The request's one optional sequence is sufficient. Simultaneous multi-body
sequences are outside this milestone. No seam justifies a Moon-specific
projection, preparation, renderer, semantic exporter, or sequence renderer.

## 3. Authoritative lunar identity and radius

Freeze the spherical model as:

- Moon target and NAIF physical body ID `301`;
- Earth parent and NAIF physical body ID `399`;
- equal-volume mean radius `1737.4 km`, quoted uncertainty `0.1 km`;
- radius authority: JPL Solar System Dynamics, *Planetary Satellite Physical
  Parameters*, citing Archinal et al. (2018), *Report of the IAU Working Group
  on Cartographic Coordinates and Rotational Elements: 2015*;
- translational source: Wenu's installed accepted DE440-family SPK, retaining
  actual provider IDs, model, filename, coverage, and SHA-256.

JPL defines mean radius as the radius of an equal-volume sphere. This matches
the phase-only spherical model. Do not substitute an equatorial, polar,
topographic, or nominal radius. Source uncertainty is provenance, not a test
tolerance or a variable runtime radius.

Authorities:

- <https://ssd.jpl.nasa.gov/sats/phys_par/>
- <https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/C/req/naif_ids.html>
- Archinal et al. (2018), DOI <https://doi.org/10.1007/s10569-017-9805-5>

## 4. Apparent state and physical equations

At every physical epoch `t`, evaluate a topocentric observer at the requested
WGS84 site and elevation. Realize the Moon astrometrically with the accepted
retarded-emission solution, apply the accepted apparent correction once, and
independently realize the Sun for the same observer, source, reception instant,
and time scale. Retain the Moon's topocentric astrometric distance `Delta`.
The centre is the resulting observer-origin apparent ICRS direction.
Topocentric parallax is essential and validation must compare it with the
geocentric direction. Atmospheric refraction is excluded.

Skyfield's topocentric `observe()` then `apparent()` chain is the independent
operational reference: <https://rhodesmill.org/skyfield/positions.html>.

Let `R = 1737.4 km`, and let `O`, `T`, and `S` be observer, Moon, and Sun
positions from the accepted state.

### 4.1 Angular diameter

`d = 2 asin(R / Delta)`.

Store limb-to-limb `d` in arcseconds and require `0 < R < Delta`. The
small-angle approximation is diagnostic only.

### 4.2 Phase and illumination

With `u = (O-T)/|O-T|` and `s = (S-T)/|S-T|`,

`i = atan2(|s cross u|, s dot u)`, `0 <= i <= pi`,

`k = (1 + cos(i)) / 2`.

`k` is geometric illuminated area fraction, not photometry or surface
brightness.

### 4.3 Bright-limb position angle

For apparent Moon `(alpha, delta)` and Sun `(alpha_s, delta_s)` in the same
observer-origin apparent ICRS identity,

`chi = atan2(cos(delta_s) sin(alpha_s-alpha),`

`            sin(delta_s) cos(delta)`

`          - cos(delta_s) sin(delta) cos(alpha_s-alpha)) mod 2pi`.

The convention is zero at celestial north and increases toward apparent east.
At coincident or antipodal projected directions the angle is undefined and
must be reported, never invented as zero.

## 5. Chart epoch, sample epochs, and tangent transport

The ordinary chart observer time is chart epoch `t_c`. It fixes catalogue
evaluation, references, horizon, viewport, projection, tangent point, product
coordinate identity, labels, and furniture.

Sequence epochs are

`t_j = start + j * step`, for `j = 0, ..., n_steps`.

The generic convention is start-inclusive: `n_steps` counts intervals and
produces `n_steps + 1` physical samples; zero produces the start sample only.
Every `t_j` gets a new observer, centre, distance, diameter, phase, fraction,
bright direction, and spherical geometry. Each complete geometry is then
transformed through the one product coordinate specification and projection
fixed at `t_c`. A sample's instantaneous AltAz frame must never masquerade as
the fixed chart frame.

At `t_j`, form apparent-ICRS centre `z_j`, celestial north/east `(n_j,e_j)`,
bright direction `l_j = cos(chi_j)n_j + sin(chi_j)e_j`, and perpendicular
`m_j = -sin(chi_j)n_j + cos(chi_j)e_j`. The existing preferred seam constructs
all disk vertices in this basis before coordinate transformation. Transforming
every spherical vertex transports centre and orientation together.

An optimization that transports vectors must apply the same spatial transform
to `z_j` and `l_j`, reproject and normalize `l_j` in the transported tangent
plane, preserve handedness, and prove vertex parity with full geometry. It
must not transform the scalar `chi_j` as though position angle were
frame-invariant or infer orientation from screen axes.

Tests choose `t_c` distinct from every `t_j`, samples on both sides of `t_c`,
and one sample below the fixed horizon. Sample changes may move and rotate the
Moon; they may not rotate the background, grids, horizon, tangent plane, or
furniture.

## 6. Frozen public vocabulary

Single Moon:

```text
--moon
--moon-appearance resolved|symbolic
--moon-disk-magnification FACTOR
```

Omission remains off. `--moon` defaults to resolved; explicit `resolved` is
equivalent and `symbolic` requests compatibility. Magnification alone cannot
select or resolve the Moon, and symbolic mode rejects disk magnification.
Resolved Moon is permitted in regional, binocular, circumpolar, planisphere,
and Mollweide all-sky charts.

Sequence:

```text
--moon-disk-sequence
--disk-sequence-model observed
--disk-sequence-start ISO_TIME
--disk-sequence-step DURATION
--disk-sequence-n-steps COUNT
--disk-sequence-labels
--moon-disk-magnification FACTOR
```

The complete group is required. Only `observed` is accepted. Single and
sequence representations conflict. Existing UTC normalization, positive
duration parsing, optional date labels, and start-inclusive cadence are
retained. `COUNT` is a nonnegative interval count yielding `COUNT + 1`
samples. Moon selectors adapt into the same internal descriptor-driven
requests; internal science must not branch on public spelling.

## 7. Magnification and sampling

Freeze finite `1 <= M_moon <= 1000`, default `1`. It is Moon-specific,
dimensionless, common to one sequence, display-only, and applied after
projection about each separate centre. Here **display-only** means graphical
scaling rather than a physical change; it is unrelated to Wenu's
`presentation` output mode. The same rule applies in atlas and presentation
modes. Magnification cannot change centre, visibility, distance, diameter,
phase, fraction, angle, provenance, or topology.

Retain the generic deterministic 720 samples initially. 49I.3E.2 must verify
smoothness and clipping at `M_moon = 1000` in all five families before the
bound is operationally accepted. If inadequate, improve generic sampling; do
not add a Moon renderer path.

## 8. Numerical validation and frozen tolerances

49I.3E.1 adds an installed-kernel validator that refuses downloads and prints
resource identity, coverage, provider IDs, observer, time scale, correction
policy, radius, model, values, and residuals. Its independent path uses direct
Skyfield topocentric observation and vector equations, not Wenu's appearance
realizer. Before residual inspection freeze:

| Quantity | Maximum absolute residual |
| --- | ---: |
| apparent ICRS right ascension | `2e-7 deg` |
| apparent ICRS declination | `2e-7 deg` |
| topocentric distance | `5e-12 au` |
| physical angular diameter | `5e-6 arcsec` |
| phase angle | `2e-7 deg` |
| illuminated fraction | `1e-9` |
| wrapped bright-limb angle | `5e-6 deg` |
| transported bright vertex in fixed chart frame | `1e-7 deg` |

Angle residuals use minimum wrapped separation. Report a clearly nonzero
geocentric/topocentric separation for a chosen parallax case, without imposing
a universal lower tolerance.

The original pre-validation envelope was revised after the eight-epoch run
showed the finite difference between Wenu's explicit generic realization and
Skyfield's integrated `observe()` path. Fernando accepted this replacement
envelope on 2026-09-02. The new limits use independent margins rather than the
observed maxima: component direction remains sub-milliarcsecond; the diameter
limit is consistent with propagation of the retained distance limit at lunar
distance; and phase, fraction, and position-angle limits remain far below any
meaningful chart scale. This is a validation-boundary correction, not a change
to physical formulas or runtime Moon behavior.

Cases cover new, crescent, quarter, gibbous, full; near perigee and apogee;
northern and southern bright directions; angle wrap; chart boundary; samples
on both sides of the chart epoch; and a sample below the fixed horizon. Exact
orientation degeneracy can be synthetic.

## 9. Required later contracts

Runtime tests must prove one semantic Moon at
`sky/solar_system/natural_satellites/moon`; descriptor/capability ownership;
no Moon-specific appearance, geometry, sequence, projection, preparation,
renderer, or exporter; default-off and resolved-default behavior; symbolic
compatibility; complete CLI and conflict rejection; magnification invariance;
independent state at every exact sample; one distinct chart epoch and fixed
product frame; full-geometry tangent transport; all five chart-family
enablement; ordinary clipping; PNG/PDF/SVG projected-record parity; installed
kernel without download; and rejection of frozen-Earth Moon requests.

## 10. Coordinate-guide review

`coordinate_system_guide_v0.9.5.md` was reviewed. Its distinctions among
observation instant, position reference epoch, equinox, apparent status,
observer origin, product frame, and fixed-frame observed sequences remain
correct. This audit changes no implemented coordinate transformation, so the
guide text and version remain unchanged in 49I.3E.0.

## 11. Non-goals and stop conditions

Non-goals include texture, albedo, craters, named features, topographic
terminator, libration drawing, axes, prime meridian, ellipsoidal limb, eclipse
and Earth shadow, atmospheric refraction across the disk, occultation contact,
frozen-Earth lunar sequences, interpolation, animation, simultaneous
sequences, caching redesign, and photometric surface brightness.

Stop and re-audit if work would copy a Venus path; omit topocentric parallax;
rebuild the chart per sample; use sample AltAz as the chart frame; transport
`chi` as an invariant scalar; infer orientation from screen axes; magnify
before projection or alter physical state; replace resolved all-sky geometry
with a crescent glyph; infer lunar correction validity from Venus; download an
ephemeris; enable frozen-Earth Moon; or give output formats different geometry.

## 12. Scientific and architectural acceptance

Fernando scientifically and architecturally accepted this audit on
2026-09-02, including the radius authority, equations, topocentric correction
requirement, chart/sample epoch separation, tangent-geometry transport,
generic reuse boundary, public vocabulary, magnification bounds, declared
tolerances, non-goals, and stop conditions.

This acceptance authorizes only 49I.3E.1 output-neutral lunar state and
installed-DE440 validation. It does not pre-accept runtime values, drawable
behavior, maximum-magnification visual quality, sequence drawing, or any
visual result.
