# Drawable Ceres point and track (Milestone 50A.3B)

**Status:** Accepted by Fernando on 2026-09-11

**Base:** `9a57f05`

## 1. Bounded result

50A.3B connects **(1) Ceres** to Wenu's existing descriptor-driven symbolic
point and dated-track machinery. Ceres is opt-in through `--asteroid ceres`
and `--asteroid-track ceres`; no second asteroid, comet, photometry, physical
disk, uncertainty envelope, occultation, catalogue discovery, or field-query
behavior is added.

The point is a fixed small hollow diamond labeled `(1) Ceres`. Its area has no
magnitude or angular-size meaning. The ordinary generic track line, ticks,
date layout, projection, preparation, renderer, PNG/PDF/SVG export, and
semantic annotation are reused unchanged.

## 2. Identity and shared provider binding

`CERES_BODY` records separate selection key, body class, IAU number,
canonical designation, display name, Horizons target, classifications,
capabilities, and ephemeris-source key. Its semantic paths are:

```text
sky/solar_system/minor_bodies/asteroids/ceres
sky/solar_system/minor_bodies/asteroids/ceres/track
```

The generic point and track realizers now accept an `EphemerisSourceBinding`.
For planets both members are the existing Skyfield/DE440 source. For Ceres,
the target source is `SkyfieldMinorBodyStateSource`, while observer state and
Skyfield apparent corrections retain the observer's DE440 source. The layers
do not branch on asteroid class.

## 3. Offline resource and lifecycle contract

`MinorBodyResourceSession` accepts only one explicit local directory containing
`acquisition-report.json` and the SPK named by its Ceres record. Before a
source is returned it verifies the manifest record, target `20000001`, accepted
JPL#48 solution identity, file confinement, SHA-256 digest, one target segment,
centre `10`, frame `1`, type `21`, and requested coverage through the accepted
provider.

The session caches sources by descriptor. One chart build opens the Ceres
kernel at most once, reuses it for point realization, every track sample, and
all exports owned by that build, then closes it exactly once. Rendering never
downloads, refreshes, extrapolates, invokes a two-body fallback, or substitutes
Apophis. Missing or inconsistent resources fail before output is written.

The resource is supplied by either:

```text
--minor-body-resource-directory PATH
observer.minor_body_resource_directory in a version-1 TOML profile
```

Explicit CLI input wins over the profile. Supplying a directory without
selecting Ceres draws nothing.

## 4. Future collection boundary

The catalog remains extensible and the resource session resolves a collection
of descriptor keys with cached resources rather than a closed Ceres enum in
the point or track algorithms. Discovery, WCS/instrument footprints,
exposure intervals, field intersection, photometric filtering, and risk
ranking remain separate future owners.

Artificial satellites may later share the observed-trajectory, projection,
preparation, and footprint-intersection outputs only. OMM/TLE plus SGP4/TEME,
Earth orientation, topocentric satellite evaluation, freshness, and
illumination remain scientifically separate from the SPK/TDB minor-body
provider.

## 5. Tests and documentation

Tests extend the existing body, point, track, CLI, request, configuration,
style, semantic, and documentation owners. `test_minor_body_resources.py` is
the one justified new test file because manifest resolution and opened-kernel
lifecycle form a new durable resource boundary with failure and isolation
semantics distinct from numerical SPK evaluation.

The tests do not repeat 50A.2 CSPICE interpolation, Cartesian-state,
light-time, apparent-place, parallax, projection, renderer, or exporter
oracles. The frozen Horizons validator remains the independent numerical
authority.

The user guide documents acquisition versus offline rendering, CLI and TOML
resource selection, failure behavior, symbol meaning, and a runnable regional
Ceres point-and-track command. The focused architecture diagram is updated;
no unrelated user document or example script requires modification.

## 6. macOS acceptance

On macOS 10.16 with Python 3.11.7, the focused implementation gate passed 185
tests and the complete repository gate passed all 2,181 tests in 94.74 seconds.
The acquired 50A.2 Ceres resource generated both PNG and semantic SVG. The SVG
contained the required point and track paths plus their point, line, and label
subpaths.

Fernando's first macOS product review found the scientific track and semantic
SVG satisfactory but rejected the duplicated Ceres/start-date labels and the
low-contrast asteroid point label. When a selected point has the same body and
instant as the track start, its hollow diamond supplies the symbol, the point's
ordinary label is suppressed, and the track start receives the single visible
label `Ceres (1)` without a date. That label is placed opposite the initial
projected direction of motion; later dated ticks are unchanged. `(1) Ceres`
remains the canonical internal designation. Atlas presentation uses the
accepted planetary cream `#FFE6A3` for the asteroid symbol and name. Fernando
accepted the regenerated PNG and SVG on 2026-09-11. This closes 50A.3; comet
numerical validation in 50A.4 is next.
