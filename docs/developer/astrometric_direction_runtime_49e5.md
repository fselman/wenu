# Milestone 49E.5 — Astrometric direction runtime

**Status:** Implementation and scientific review candidate

**Implementation baseline:** `888ca2c`

**Date:** 2026-08-30

## 1. Purpose

49E.5 implements the accepted 49E.4 astrometric stage for one observer and
one Solar-System target. It converts typed barycentric provider states into an
observer-relative ICRS direction with one-way light time while retaining the
distance, reception instant, retarded emission instant, convergence evidence,
observer identity, and exact ephemeris resource identity.

Venus remains the controlled first body. This milestone creates no installed
Venus layer and changes no chart or output.

## 2. Runtime contracts

`solar_system_directions.py` adds four renderer-neutral values:

- `ObserverBarycentricState`: the terrestrial site's complete position and
  velocity relative to a declared centre at the reception instant;
- `AstrometricDirectionRequest`: target, centre, reception instant/scale, and
  explicit light-time tolerance and iteration limit;
- `AstrometricDirection`: one `SphericalPoints` direction surrounded by
  distance, light time, emission instant/scale, iteration count, target ID,
  typed observer state, and provenance; and
- `AstrometricDirectionRealizer`: the bounded retarded-time iteration.

All request, observer-state, and result records are frozen. The spherical
record uses `frame="icrs"`, `origin="observer"`, and
`PositionStatus.ASTROMETRIC`. Its only correction is
`one-way-light-time`. Its `epoch` and `equinox` are both absent; `instant` is
the reception instant.

## 3. Observer-state adapter

`skyfield_observer_barycentric_state(observer, source=...)` evaluates the
already-constructed `Observer.skyfield` Earth-plus-WGS84-site vector at
`Observer.t`. It returns position in AU and velocity in AU/day on ICRF axes.

The adapter accepts only a `SkyfieldEphemerisStateSource` borrowing the exact
same `Observer.ephemeris` object. It neither opens nor closes a kernel and
cannot attach an unrelated resource identity to the observer state.

The observer state is evaluated exactly once at reception. The target is
evaluated repeatedly at emission times. The realizer consumes both typed
boundaries and never reaches through a chart, renderer, or global observer.

## 4. Numerical method

Starting with zero light time, iteration \(n\) evaluates

\[
\boldsymbol\rho_n =
\boldsymbol r_t(t_r-\tau_{n-1})-\boldsymbol r_o(t_r),
\qquad
\tau_n=\frac{\lVert\boldsymbol\rho_n\rVert}{c}.
\]

Iteration stops when
\(|\tau_n-\tau_{n-1}|\) is at most the declared tolerance. The default is
`1e-12` day with at most 10 iterations. The speed of light is Astropy's
physical constant converted to AU/day. Emission instants are serialized with
nanosecond decimal precision so the timing evidence is not truncated to
milliseconds.

Non-convergence raises `AstrometricDirectionConvergenceError`. Mismatched
centre, frame, unit, reception instant, or resource identity raises
`AstrometricDirectionIdentityError`. Target-specific provider coverage errors
propagate from every emission-time state request.

## 5. Result identity and retained evidence

The result does not treat a moving direction as a catalogue position.
Reception and emission are physical instants, not position reference epochs
and not equinoxes. ICRS fixes the native axis orientation without a selectable
equinox. A later `CoordinateService` call may represent the realized direction
in an FK5 or ecliptic frame with an explicitly requested equinox.

The result retains:

- ICRS longitude and latitude in degrees;
- distance in AU and one-way light time in days;
- reception instant/scale in the `CoordinateSpec`;
- emission instant/scale on the surrounding result;
- actual iteration count and requested tolerance;
- observer and target identities;
- provider-native target ID;
- provider, DE model, BSP filename, SHA-256, and resource provenance; and
- an explicit statement that the observer is held at reception while the
  target is iterated at retarded emission time.

## 6. Deterministic and real-resource verification

`tests/test_solar_system_directions.py` uses a deterministic state source to
verify frozen contracts, two-step stationary-target convergence, spherical
angles, distance, light time, emission time, observer subtraction, coordinate
identity, exact correction set, convergence failure, and identity failures.

`tests/test_skyfield_ephemeris.py` verifies the observer adapter's site state,
units, identity, and same-borrowed-kernel guard.

`tools/validate_49e5_astrometric_direction.py` refuses to download a missing
kernel. With the installed `de440s.bsp`, it compares Wenu's Venus direction
from La Ligua at `2026-08-30T00:00:00Z` with direct
`observer.skyfield.at(t).observe(venus)` for ICRS right ascension,
declination, distance, one-way light time, and emission instant. It prints the
kernel identity, instants, iteration count, values, and residuals.
This is a direct Skyfield `observe()` comparison, not an independent
revalidation of the DE440 dynamical solution.

## 7. Canonical output boundary

The 49E.5 result is renderer-neutral spherical geometry, but no production
layer consumes it yet. 49I.1 must transform it exactly once into the requested
product frame and then use the existing semantic preparation, projection,
Matplotlib renderer, and single PNG/PDF/SVG exporter.

No future Venus, Moon, Sun, or planet may be drawn through a post-export
overlay, SVG-only astronomy, or a separate SVG generator. 49E.5 imports no
chart, projection, style, Matplotlib, or exporter module.

## 8. Non-goals

49E.5 does not add:

- aberration or gravitational deflection;
- `PositionStatus.APPARENT` or atmospheric refraction;
- phase, illumination, magnitude, angular diameter, disk, or trail geometry;
- a Venus, Moon, Sun, or planet layer;
- product-frame transformation;
- CLI or TOML controls;
- caching or global ephemeris state; or
- any current chart, PNG, PDF, or SVG change.

Apparent-place realization remains 49E.6. The first drawable Venus remains
49I.1, followed by the Moon as the stronger topocentric-parallax test.

## 9. Acceptance requirements

Acceptance requires:

1. focused deterministic direction, Skyfield-adapter, ephemeris, coordinate,
   and documentation tests;
2. the installed-DE440 Venus comparison with reported residuals;
3. routine and complete regression suites;
4. Fernando's scientific review of observer state, light-time iteration,
   frame, timing, identity, retained evidence, and non-goals;
5. pedagogical review of coordinate-guide version `0.9.5.20260830.6`; and
6. confirmation that no visual render is required because no chart layer can
   consume the result.
