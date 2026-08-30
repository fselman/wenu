# Milestone 49E.3 — Borrowed Skyfield ephemeris adapter

**Status:** Scientifically accepted by Fernando on 2026-08-30; integration pending

**Implementation baseline:** `7a978a0`

**Date:** 2026-08-30

## 1. Purpose

49E.3 adapts the JPL SPK kernel already resolved and owned by `Observer` to
the accepted 49E.2 `EphemerisStateSource` boundary. It supplies reproducible
geometric Cartesian states without yet calculating what an observer sees or
drawing a planet.

The first controlled body is Venus, following the accepted Venus-first plan.
Venus is used only to validate the state source; it is not registered as a sky
layer.

## 2. Pedagogical model

**[Foundation]** A planetary ephemeris file is a numerical map of Solar-System
motion. To ask where Venus is, one must also say “relative to what?” Wenu asks
for Venus relative to a named centre, at a named instant, with named axes. The
answer is six numbers: three for position and three for velocity.

The filename is not enough to identify the map. Wenu also records a SHA-256
fingerprint of the exact bytes, rather like a very sensitive seal: changing one
byte changes the fingerprint.

**[Undergraduate]** A JPL SPK segment supplies Chebyshev representations of
Cartesian target states relative to specified centres. Skyfield composes the
necessary segment vectors into an ICRF-oriented barycentric vector function.
49E.3 evaluates the simultaneous geometric difference
`(target - centre).at(t)`. No retarded emission time, aberration,
gravitational deflection, topocentric displacement, or refraction is implied.

## 3. Resource ownership

`SkyfieldEphemerisStateSource.from_observer(observer)` borrows:

- `observer.ephemeris`, the already-open Skyfield `SpiceKernel`; and
- `observer.timescale`, the already-resolved Skyfield time authority.

The adapter opens no second kernel, performs no download, and exposes no
`close()` method. `Observer.close()` remains responsible for closing the
borrowed resource. This is the accepted first-adapter compromise, not a claim
that `Observer` is the permanent universal ephemeris API.

## 4. Exact kernel identity

Resolution reads `kernel.path` and calculates SHA-256 once. The immutable
identity records:

- provider: Skyfield/JPL SPK;
- model inferred from a conventional DE-series filename, for example
  `DE440` from `de440s.bsp`;
- the actual filename;
- the exact SHA-256 digest;
- the conservative common intersection of all SPK segment intervals;
- TDB as the coverage scale; and
- resolved path and segment count as provenance.

The common intersection is deliberately conservative. A minimum-to-maximum
union envelope could claim availability at an instant when a required segment
does not exist. Skyfield remains the final target-specific segment-coverage
authority during evaluation.

A nonstandard filename requires an explicit model name. A renamed or replaced
file therefore cannot silently masquerade as the accepted resource.

## 5. State evaluation

The initial adapter supports only `frame="icrf"`. It converts the request's
declared instant and scale into an Astropy `Time`, then uses
`Timescale.from_astropy()` to represent that same physical instant in
Skyfield.

The adapter resolves both body names through `SpiceKernel.decode()`, evaluates
the simultaneous target-minus-centre vector, and returns:

- position in AU;
- velocity in AU/day;
- provider-native NAIF target and centre identifiers;
- the same immutable resource identity; and
- provenance explicitly calling the result geometric and ICRF-oriented.

Unsupported frames, unresolved bodies, aggregate-coverage failures, and
target-specific Skyfield segment-range failures have separate deterministic
Wenu exceptions.

## 6. Controlled validation

`tests/test_skyfield_ephemeris.py` uses deterministic fake kernel structures.
It verifies hashing, DE model/filename separation, common segment coverage,
borrowed lifetime, time-scale handoff, target/centre subtraction, units,
provider IDs, protocol conformance, and explicit failures.

`tools/validate_49e3_skyfield_adapter.py` is the real-resource acceptance
check. It refuses to download a missing kernel. With the installed
`de440s.bsp`, it evaluates Venus relative to the Solar-System barycentre at
`2026-08-30T00:00:00 TDB` and compares all six adapter components with a
direct Skyfield evaluation to absolute tolerance `1e-15` in AU and AU/day.
It prints model, filename, SHA-256, coverage, NAIF identifiers, and the state.

On Fernando's Mac, the installed `de440s.bsp` acceptance run resolved
`DE440`, SHA-256
`c1c7feeab882263fc493a9d5a5b2ddd71b54826cdf65d8d17a76126b260a49f2`,
and common coverage JD 2396752.5 through JD 2506352.5 TDB. At
`2026-08-30T00:00:00 TDB`, Venus (NAIF 299) relative to the Solar-System
barycentre (NAIF 0) was:

- position AU:
  `(0.3925912533858422, -0.5535374749397038, -0.2738181276850454)`;
- velocity AU/day:
  `(0.016873198219205025, 0.010316441911703824, 0.003574843186544155)`.

All six adapter components agreed with direct Skyfield evaluation to absolute
tolerance `1e-15`; the reported residual was zero within that tolerance.

This comparison validates Wenu's adapter, identity, units, centre, frame, and
time handoff. It does not independently revalidate the DE440 dynamical solution.

## 7. Architectural and output boundary

The returned state is not a sky direction and is not drawable. A later
solar-system direction realizer must establish observer, reception and emission
times, light-time policy, aberration, gravitational deflection, physical
status, and native spherical identity. Only then may a Venus layer transform
the direction into the product frame and enter the existing projection,
preparation, renderer, furniture, and exporter.

PNG, PDF, and SVG must consume the same projected semantic record. The adapter
contains no projection, style, Matplotlib, SVG serialization, or chart command.

## 8. Non-goals

49E.3 does not add:

- a second kernel owner or downloader;
- a global ephemeris singleton;
- permanent public resource selection;
- apparent-place or observer-relative direction realization;
- light-time iteration, aberration, or gravitational deflection;
- Venus, Moon, Sun, or planet layers;
- angular diameter, phase, magnitude, disk, label, or trail geometry;
- CLI/TOML controls;
- caching of body states;
- a renderer or SVG-specific astronomical path; or
- any numerical or visual change to current charts.

## 9. Acceptance requirements

Acceptance requires:

1. focused deterministic adapter tests;
2. the controlled installed-`de440s.bsp` Venus comparison;
3. routine and complete regression suites;
4. Fernando's scientific review of centre, frame, time, units, coverage, and
   borrowed resource ownership;
5. guide review at Foundation and Undergraduate depth; and
6. confirmation that no current chart or output changes.

No visual render is required because no chart layer can consume the adapter in
49E.3. After acceptance, the next scientific milestone is the
observer-relative direction realizer; Venus rendering remains 49I.1.


## 10. Scientific acceptance

Fernando accepted the 49E.3 centre, frame, time, units, common-coverage,
borrowed-resource, NAIF-zero, and canonical-output decisions on 2026-08-30.
Verification evidence is 72 focused tests in 1.73 seconds, 1,830 routine tests
with 30 deselected in 25.80 seconds, and all 1,860 tests in 84.78 seconds. The
installed DE440 comparison produced zero adapter/direct residual within
`1e-15` for all six components.

Acceptance also requires the living guide to preserve the distinctions between
coordinate system and reference frame, and between position epoch and equinox.
Its section-13 table of contents uses explicit stable HTML anchors so navigation
does not depend on GitHub, MacDown, or another renderer's generated heading
rules.
