# Wenu current architecture v0.7

**Status:** Implemented baseline for the v0.8 migration
**Baseline commit:** `b72eef8`
**Date:** 2026-08-05

Wenu v0.7 implements independently selectable equatorial, ecliptic, and
Galactic coordinate-grid layers. It does not implement an observer-local
AltAz grid, although horizontal coordinates are already the canonical
spherical geometry used by projection and rendering. The horizon remains
chart-owned boundary geometry and is not optional reference content.

The canonical flow, ownership boundaries, declarative examples, render-local
detail policy, style ownership, and packaged-example parity documented by
`target_architecture_v0.7.md` remain in force.

The permanent test suite is organized by these current responsibilities rather
than by completed milestone history. Fast unit, integration, visual, and full
commands are recorded in `source_tree.md`; the full suite remains the release
authority and atlas print remains the visual reference baseline.

The v0.8 migration now provides one immutable canonical load profile and one
maximal-sphere factory. It loads complete reusable astronomical content for an
observer and returns the existing `CelestialSphere`; chart geometry,
coordinate-grid spacing, detail, presentation, and export remain downstream
request concerns.

Stellar AltAz realization is cached per loaded `Stars` layer using observer
location, instant, ephemeris identity, data directory, catalogue identity,
and source revision. Render-local magnitude and identifier selections mask
that immutable maximal realization, and constellation figures reuse it.
Vectorized point catalogues use the same key identity: open-cluster and
planetary-nebula selections index immutable maximal AltAz center arrays.
