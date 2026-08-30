# Milestone 49E.4 — Solar-System direction-realizer audit

**Status:** Scientific review candidate; documentation and tests only

**As-is baseline:** `644bac7`

**Date:** 2026-08-30

## 1. Decision

49E.4 defines the smallest correct boundary between a Cartesian ephemeris
state and drawable spherical geometry. It changes no runtime type, chart,
command, or output. The first implementation slice after this audit will
realize an **astrometric Venus direction**. Apparent-place corrections follow
as a separate, explicit operation before the 49I.1 Venus chart layer.

This separation follows the accepted physical sequence:

```text
simultaneous geometric states
    -> observer state at reception
    -> target state at retarded emission time
    -> astrometric observer-to-target direction
    -> aberration and gravitational deflection
    -> apparent direction
    -> CoordinateService product-frame transformation
    -> canonical projection, renderer, and exporter
```

## 2. Why two angular numbers are insufficient

**[Foundation]** A planet chart needs a direction, but it also matters how the
direction was obtained. Venus is seen where it was when the arriving light
left it, not where a simultaneous map says it is now. Wenu must therefore keep
the observation time, the earlier emission time, the travel time, and the
distance together with longitude and latitude.

**[Undergraduate]** Let the observer's barycentric position at reception time
\(t_r\) be \(\boldsymbol r_o(t_r)\), and the target's barycentric position at
emission time \(t_e\) be \(\boldsymbol r_t(t_e)\). The astrometric line of
sight is based on

\[
\boldsymbol\rho = \boldsymbol r_t(t_e)-\boldsymbol r_o(t_r),
\qquad
t_e=t_r-\frac{\lVert\boldsymbol\rho\rVert}{c}.
\]

Because \(t_e\) depends on the distance that the solution itself determines,
the target state is evaluated iteratively. A target state sampled only at
\(t_r\) is not an astrometric place.

## 3. Required immutable request and result

The implementation milestone must introduce a request that declares:

- target identity;
- reception instant and input time scale;
- an explicit observer/topocentre;
- requested physical status;
- light-time convergence policy; and
- the already-resolved state source/resource.

The astrometric result must retain:

- one `SphericalPoints` direction in ICRF/ICRS-oriented axes;
- `origin="observer"` and `PositionStatus.ASTROMETRIC`;
- reception instant and time scale, never mislabeled as an equinox or position
  reference epoch;
- distance in an explicit unit;
- one-way light time;
- retarded emission instant and its time scale;
- iteration count and convergence tolerance;
- target, observer, provider, DE model, filename, SHA-256, coverage, and
  provider-native identifiers; and
- corrections containing `one-way-light-time`, but not aberration,
  gravitational deflection, precession-nutation, or refraction.

Distance and timing data may live in a dedicated frozen result surrounding
`SphericalPoints`; they must not be discarded into an undocumented array or
inferred later from chart geometry.

## 4. Observer-state boundary

The observer is not synonymous with Earth and is not merely a string centre.
For a terrestrial site, its reception-time barycentric state includes the
Earth state plus the site's displacement and velocity. This is what preserves
topocentric parallax and diurnal effects for the later Moon test.

The implementation must therefore supply an explicit observer-state adapter.
It may borrow `Observer.skyfield`, `Observer.t`, the open kernel, and the
resolved timescale in the first implementation, but the scientific realizer
must consume a typed observer state rather than silently reaching through a
chart or renderer. The state source remains responsible for ephemeris states;
the observer adapter remains responsible for the terrestrial site state.

## 5. Astrometric and apparent are separate statuses

Skyfield's `Barycentric.observe()` performs the light-time solution and returns
an astrometric position. Its `Astrometric.apparent()` then applies
gravitational deflection and aberration. These are distinct scientific
operations, not alternative names for one result.

The first runtime slice will stop at astrometric direction and validate its
angles, distance, light time, and provenance against direct Skyfield. A later
apparent-place slice may use the same resolved resource and must explicitly
record:

- aberration model and observer velocity;
- gravitational-deflection model and deflecting bodies;
- whether Earth deflection applies; and
- the resulting `PositionStatus.APPARENT`.

Atmospheric refraction is not part of apparent ICRF direction. It belongs only
to a later `OBSERVED` AltAz product.

## 6. Frame, equinox, epoch, and instant

The native vector components returned by Skyfield's astrometric and apparent
positions are oriented along ICRF axes. Calling `radec()` with no epoch yields
right ascension and declination on those fixed axes. No selectable equinox is
introduced by this operation.

For the result:

- `frame="icrs"` identifies the spherical reference frame used by Wenu;
- `epoch` remains absent because the moving direction is evaluated, not a
  catalogue position published at a reference epoch;
- `equinox` remains absent because ICRS has no defining equinox parameter; and
- `instant` records the reception instant while the result separately retains
  the emission instant.

If a later chart requests FK5 or ecliptic coordinates at a chosen equinox,
`CoordinateService` performs that representation change after direction
realization. It must not cause the ephemeris realizer to relabel the reception
instant as an equinox.

## 7. Numerical and failure policy

The implementation must:

1. evaluate the observer state once at reception;
2. iterate target emission time until a declared light-time tolerance is met;
3. use a bounded maximum iteration count;
4. reject non-convergence deterministically;
5. propagate explicit target-specific coverage failures at every iteration;
6. reject unsupported units, frames, statuses, or mismatched resources; and
7. avoid hidden downloads and global ephemeris state.

The controlled installed-DE440 test uses Venus first. It compares Wenu with
direct `observer.skyfield.at(t).observe(venus)` for ICRF right ascension,
declination, distance, and light time. The Moon remains the subsequent
high-parallax proof that the observer-state boundary is truly topocentric.

## 8. Canonical output boundary

49E.4 produces no drawable layer. The later Venus layer will transform the
realized spherical direction exactly once into the product frame and enter
the existing semantic preparation, projection, Matplotlib renderer, and
single exporter. PNG, PDF, and SVG consume the same projected record.

No future Sun, Moon, or planet may use a post-export overlay, an SVG-only
coordinate calculation, or a separate SVG generator. Reserved semantic paths
such as `solar-system/planets/venus` identify already-realized geometry; they
do not perform astronomy.

## 9. Non-goals

49E.4 does not add:

- a runtime direction result or realizer;
- a Venus, Moon, Sun, or planet layer;
- apparent-place, phase, magnitude, angular-diameter, disk, or trail physics;
- CLI or TOML controls;
- caching;
- projection, rendering, or export code; or
- any numerical or visual change to existing charts.

## 10. Proposed implementation sequence

1. **49E.5 — Astrometric direction runtime:** typed request/result,
   observer-state adapter, iterative light-time solution, deterministic tests,
   and installed-DE440 Venus comparison.
2. **49E.6 — Apparent direction runtime:** declared aberration and
   gravitational-deflection policy with direct-Skyfield comparison.
3. **49I.1 — Venus vertical slice:** one semantic point/disk layer through the
   canonical product frame and shared PNG/PDF/SVG exporter.
4. **49I.2 — Moon vertical slice:** topocentric parallax, angular size, phase,
   and stronger observer-location acceptance.

Scientific acceptance of this audit is required before 49E.5 implementation.
