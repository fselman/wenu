# First drawable asteroid audit (Milestone 50A.3A)

**Status:** Proposed for Fernando's architectural and product review

**Base:** `50cf383`

**Runtime effect:** None. This audit authorizes no body registration, public
option, resource resolver, style, chart layer, track, renderer, or output.

## 1. Decision

Use **(1) Ceres** as Wenu's first drawable asteroid. Its accepted 50A.2
Horizons solution and type-21 SPK provide a stable main-belt case without the
exceptional close-approach and short useful interval of Apophis. Apophis
remains a numerical parallax oracle and is not silently promoted to ordinary
chart content.

Split implementation into one later bounded 50A.3B slice. It may add an
opt-in symbolic Ceres point and an independently opt-in dated Ceres track, but
no photometric visibility model, physical disk, occultation, uncertainty
envelope, comet behavior, or second asteroid.

## 2. Reuse audit

The existing shared route is already correct after provider resolution:

1. a frozen `SolarSystemBodyDescriptor` supplies identity and correction
   policy;
2. `SolarSystemPointLayer` produces one apparent `SphericalPoints` record;
3. `SolarSystemTrackRequest`, `SolarSystemTrackRealizer`, and
   `SolarSystemTrackLayer` produce one fixed-product-frame trajectory;
4. ordinary coordinate transformation, projection, preparation, visibility,
   rendering, semantic SVG annotation, and PNG/PDF/SVG export remain shared.

The only unsuitable assumption is that point and track realization currently
construct `SkyfieldEphemerisStateSource.from_observer` directly. 50A.3B must
introduce one descriptor-aware source binding or injected source resolver. A
planet continues to receive the existing Skyfield source; Ceres receives the
accepted `SkyfieldMinorBodyStateSource` backed by an exact
`SpiceMinorBodyKernel` plus the observer's existing DE440 source. The point and
track algorithms must not branch on `asteroid`.

Do not add asteroid-specific coordinate, projection, preparation, renderer,
exporter, or trajectory implementations.

## 3. Identity and designation policy

Adopt these first-body identities:

| Role | Value |
| --- | --- |
| internal selection key | `ceres` |
| body class | `asteroid` |
| canonical designation | `(1) Ceres` |
| display name | `Ceres` |
| Horizons command | `1;` |
| Horizons SPK target | `20000001` |
| semantic point path | `sky/solar_system/minor_bodies/asteroids/ceres` |
| semantic track path | `sky/solar_system/minor_bodies/asteroids/ceres/track` |

The IAU number and name are separate typed fields even though the first
display label combines them. Aliases may resolve input later but may not alter
semantic identity or provenance. Do not call Ceres a planet or place it below
`sky/solar_system/planets`.

The ordinary label should be `(1) Ceres`. Do not depend on the specialized
Unicode Ceres symbol: font coverage and monochrome export must not determine
whether the object remains identifiable.

## 4. Resource and failure policy

Rendering remains offline. Selecting Ceres must require one explicit local
minor-body resource directory, supplied by CLI/configuration, containing:

- `acquisition-report.json` from the governed acquisition boundary; and
- the exact SPK named and hashed by that report.

The proposal is one reusable public setting named
`minor_body_resource_directory`, exposed initially as
`--minor-body-resource-directory PATH`. It is a resource location, not a
scientific target selector, and serves both the point and track. No default
path may imply that a milestone-validation cache is a permanent production
installation. A later resource-management slice may install or refresh such a
directory explicitly.

The resolver must match `ceres`, target `20000001`, the manifest digest,
solution identity, segment centre/frame/type, and requested coverage before
returning a provider. Missing directory, manifest, SPK, target, provenance, or
coverage fails before chart output is written. Rendering must never download,
refresh, extrapolate, fall back to two-body propagation, or substitute a
different solution.

One chart build owns one opened minor-body kernel and closes it exactly once.
A track reuses that opened resource for its samples; it must not reopen the
SPK per epoch. DE440 remains owned by the observer/Skyfield route.

## 5. Public selection and time semantics

Keep the public vocabulary class-aware and adapt it immediately to the common
internal selection and request types:

```text
--asteroid ceres
--asteroid-track ceres
--minor-body-resource-directory PATH
```

The existing `--track-start`, `--track-sample-step`, `--track-tick-step`,
`--track-tick-count`, and `--track-tick-labels` fields are reused unchanged.
`--asteroid` and `--asteroid-track` are independent, matching the accepted
planet point/track behavior. Supplying the resource directory alone draws
nothing. Selecting a minor body without it fails with a direct actionable
message.

The point uses the chart observation epoch. A track uses its explicit sample
epochs while remaining transformed into the chart's one fixed product frame,
exactly like the accepted Venus track. Point display may apply to every chart
family; tracks remain restricted to regional and binocular charts until a
separate review changes that rule.

## 6. Appearance and photometry boundary

The first Ceres point is a fixed-size symbolic mark. Use one style-owned small
hollow diamond plus the `(1) Ceres` label, with no encoded angular diameter or
brightness. The mark must remain distinguishable in atlas print,
presentation, grayscale, and semantic SVG without relying only on color.

No magnitude field is admitted in 50A.3B. Horizons apparent magnitude, the
asteroid `H,G` law, phase functions, rotational light curves, opposition
effects, and limiting-magnitude culling require a later scientific audit.
Because selection is explicit, Ceres is drawn when it lies within the
projection and viewport even if a future photometric model would call it too
faint.

Track line, tick, and label preparation reuse the existing generic style and
layout contract. 50A.3B may add an asteroid style role but may not duplicate
the track annotation algorithm.

## 7. Tests and acceptance evidence

Extend tests according to current owners rather than creating a parallel
asteroid suite:

- body/catalog tests: Ceres identity, class, designation, and semantic path;
- provider/resource tests: manifest resolution, digest/coverage checks,
  one-open/one-close ownership, and deterministic failures;
- point and track tests: inject the already-tested minor-body provider and
  verify generic requests, identity, fixed-frame sampling, and selection;
- CLI/configuration tests: class-aware options map to the common internal
  content and track contracts;
- style/semantic tests: hollow-diamond role and stable point/track paths;
- documentation tests: public guide, resource installation contract, example,
  and non-goals.

Do not repeat 50A.2 CSPICE interpolation, Cartesian, light-time, apparent-place,
parallax, projection, renderer, or exporter oracles. The frozen Horizons
validator remains the independent numerical authority.

Before acceptance, require:

1. focused and complete pytest gates;
2. one installed-resource regional PNG with Ceres point and dated track;
3. the matching semantic SVG, with normalized graphical comparison where
   appropriate;
4. visual review that the point, label, path, ticks, and dates remain legible;
5. inspection that absent/out-of-coverage resources fail before output;
6. confirmation that no network request occurs during chart generation.

## 8. Documentation, examples, and diagrams

This audit changes no user-visible behavior, so no user-guide or example edit
is required yet. 50A.3B will require:

- configuration/user-guide documentation for acquisition versus offline use;
- one runnable Ceres regional point-and-track example;
- CLI help and failure examples; and
- updates to the focused minor-body architecture diagram showing the accepted
  provider connected through the shared point/track route.

The current diagrams remain truthful during 50A.3A because the provider is
still not connected. No diagram edit is required by this audit.

## 9. Stop conditions

Stop and re-audit if implementation would:

- let rendering acquire or refresh an ephemeris;
- accept an SPK without its matching manifest and solution identity;
- add an asteroid-only point, track, projection, renderer, or exporter;
- reopen the SPK for every track sample;
- use color, fixed symbol area, or explicit selection as a magnitude claim;
- silently extrapolate, propagate a two-body orbit, or substitute Apophis;
- alter planet, Moon, cold-oracle, or existing track behavior;
- add a comet, physical disk, uncertainty region, occultation, or photometric
  model under 50A.3A/50A.3B.

Fernando's acceptance of this audit would authorize only the bounded 50A.3B
implementation described above.
