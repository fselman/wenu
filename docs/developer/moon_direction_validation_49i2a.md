# Milestone 49I.2A — Numerical Moon-direction validation

**Status:** Scientifically accepted by Fernando on 2026-08-30; merge pending
full-suite verification.
**Implementation baseline:** `fbf4dd9`  
**Date:** 2026-08-30

## Boundary

49I.2A proves that the accepted provider-neutral direction contracts can
realize the Moon without a copied Moon pipeline. It adds deterministic Moon
contract tests and an installed-DE440 validation tool. It adds no Moon layer,
public option, shared point-layer abstraction, style, projection, or output.

The validation uses:

- target `moon`, expected NAIF ID `301`;
- centre `solar system barycenter`, expected NAIF ID `0`;
- the request observer's already-open kernel and timescale;
- observer barycentric state at reception;
- the existing `AstrometricDirectionRealizer` light-time iteration;
- the existing explicit `ApparentCorrectionPolicy` and
  `SkyfieldApparentDirectionRealizer`;
- direct Skyfield `observer.skyfield.at(t).observe(moon).apparent()` as the numerical
  comparison authority.

## Parallax and observer-height evidence

`tools/validate_49i2a_moon_direction.py` reports the angular separation
between topocentric and geocentric apparent directions. It requires the value
to exceed 0.1 degree, proving that the observer cannot be replaced by the
geocentre for the Moon.

The tool also realizes the Moon for the registered 52 m La Ligua observer and
for the same latitude/longitude at zero elevation. It reports the right
ascension, declination, and norm of the difference and requires a non-zero
height effect. The requirement proves data flow, not a claim that the small
52 m displacement is visually important on an ordinary chart.

## Correction policy

The current explicit policy carries deflector NAIF IDs `(10, 599, 699)`, Earth
deflection enabled, and aberration enabled. 49I.2A does not accept this policy
for the Moon by analogy with Venus. Acceptance requires the Wenu apparent
direction to agree with direct Skyfield `apparent()` within `1e-7` degree
(`0.36` milliarcsecond) in right ascension and declination for the declared installed-kernel case. This deliberately sub-mas
threshold allows small numerical differences between Wenu’s explicit generic
light-time realization and Skyfield’s integrated `observe()` path while still
rejecting any scientifically meaningful chart-position disagreement.

The resulting geometry remains observer-origin apparent ICRS. Its observation
instant is neither a position reference epoch nor an equinox; ICRS has no
defining equinox. The provider state remains geometric ICRF Cartesian state
until the direction service realizes the observer-relative direction.

## Deterministic proof

`tests/test_moon_direction_validation.py` uses a test-only NAIF-301 state. It
proves that the generic astrometric realizer preserves Moon identity, common
centre, resource, units, light time, observer origin, and absent epoch/equinox.
It then proves that the generic apparent realizer reconstructs target 301,
passes the explicit deflector tuple, and produces ordinary apparent ICRS
`SphericalPoints` without invoking a second `observe()`.

## Required Mac acceptance

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_moon_direction_validation.py \
  tests/test_solar_system_directions.py \
  tests/test_apparent_directions.py \
  tests/test_skyfield_ephemeris.py \
  tests/test_ephemeris.py \
  tests/test_current_documentation.py

python tools/validate_49i2a_moon_direction.py
```

The tool output must record model, file, SHA-256, observer geodetic
coordinates and height, reception and emission instants, iteration count,
target and centre NAIF IDs, distance, light time, correction policy, apparent
ICRS direction, direct-Skyfield residuals, topocentric-geocentric parallax,
and the 52 m minus 0 m height displacement.

## Scientific acceptance

Fernando scientifically accepted the 49I.2A direction result and `1e-7`-degree
component tolerance on 2026-08-30. The accepted Mac evidence is:

- 102 focused tests passed in 1.99 seconds;
- installed kernel DE440, file `de440s.bsp`, SHA-256
  `c1c7feeab882263fc493a9d5a5b2ddd71b54826cdf65d8d17a76126b260a49f2`;
- direct-Skyfield residuals `-4.176e-08` degree in right ascension and
  `-1.734e-08` degree in declination (`0.1503` mas and `0.0624` mas in
  magnitude);
- topocentric-geocentric parallax `0.9500231004` degree;
- 52 m minus 0 m displacement `7.751704800e-06` degree (`27.91` mas);
- Moon target NAIF 301, barycentre NAIF 0, and convergence in three iterations.

This accepts the correction policy and numerical Moon direction for the
installed-kernel case. Full-suite verification and merge remain delivery
checks, not unresolved scientific questions.

## Non-goals

49I.2A does not extract `SolarSystemPointLayer`, migrate Venus, install Moon
scene content, choose Moon appearance, expose `--moon`, calculate phase or
angular diameter, draw a physical disk, download a kernel, or change any
PNG/PDF/SVG product. Those remain 49I.2B, 49I.2C, and 49I.3.
