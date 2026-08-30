# Milestone 49I.2 — Moon and shared solar-system-body pipeline audit

**Status:** Scientifically and architecturally accepted by Fernando on
2026-08-30; ready for integration.
**As-is baseline:** `e7fa6ab`  
**Date:** 2026-08-30

## Decision

Wenu targets one canonical moving-body chart pipeline, not one class or one
algorithm for every solar-system object:

1. typed body selection;
2. typed geometric state request to an interchangeable state source;
3. observer barycentric state at reception;
4. observer-to-target astrometric direction with retarded emission time;
5. explicit apparent-place correction policy;
6. exactly one transformation into the chart product coordinate system;
7. ordinary projection, visibility, style, semantic hierarchy, and shared
   PNG/PDF/SVG export.

Major planets, the Moon, minor planets, and comets must converge before step
6. They may use different state sources and different physical-appearance
strategies. “One pipeline” therefore means shared typed interfaces and one
downstream chart path; it does not mean relabelling every orbit source as a JPL
kernel or reducing every physical body to a few untyped parameters.

## As-is evidence

`sky/venus.py::VenusLayer` currently owns both reusable orchestration and
Venus identity. The reusable part already accepts injected source, observer
state, astrometric, apparent, and coordinate-service collaborators. The
Venus-specific part is limited to target name, catalogue identity, display
name, selection validation, semantic identity, and style registration.

`ephemeris.py::EphemerisStateSource` is structural and provider-neutral.
`SkyfieldEphemerisStateSource` is only its first implementation. Its
`EphemerisStateRequest(target, centre, frame, instant, time_scale)` already
makes target and centre ordinary typed inputs and returns complete geometric
position-velocity state plus resource identity and provider IDs.

`AstrometricDirectionRealizer` is body-neutral. It holds the observer at the
reception instant, iterates the target at retarded emission time, and checks
that target and observer use the same resource, ICRF axes, units, and provider
centre. `SkyfieldApparentDirectionRealizer` consumes that accepted result and
applies an explicit `ApparentCorrectionPolicy`. `CoordinateService`, chart
projection, viewport/masks, renderer, and exporter have no body knowledge.

## Variation matrix

| Object class | State source variation | Direction variation | Appearance variation |
| --- | --- | --- | --- |
| Major planet | Installed JPL SPK when covered | Shared observer-relative light-time and apparent path | Symbol first; later phase, magnitude, disk, and orientation |
| Moon | Installed JPL SPK when covered | Same typed path, but strong topocentric parallax and Moon-valid correction policy require explicit validation | Symbol first; later angular diameter, illuminated limb, phase, and orientation |
| Natural satellite | JPL SPK or satellite-specific kernel | Shared path after state is expressed in the declared common centre/frame | Symbol, close-pair labeling, later disk where meaningful |
| Minor planet | SPK when available, otherwise validated orbital-elements provider | Shared path after the provider returns the complete geometric state contract | Symbol, magnitude model, uncertainty, optional trail |
| Comet | SPK or validated osculating-orbit provider | Shared path after the same state contract | Nucleus symbol plus optional coma/tail geometry driven by Sun-relative state |
| Artificial satellite | TLE/SGP4 provider | Separate TEME-to-supported-frame adapter before convergence; TEME must never be relabelled ICRS | Symbol and trail through the ordinary renderer/exporter |

## Moon boundary

The Moon is the next object because it is the strongest nearby test of
observer ownership and parallax. The first Moon remains a symbolic point. A
physical lunar disk is a later geometry milestone and must not be smuggled
into the direction or renderer layers.

The audit proposes:

- target provider identity `moon`, expected NAIF ID `301` for the installed
  JPL kernel;
- common state centre `solar system barycenter`, NAIF ID `0`;
- reception instant and scale from `LayerRealizationContext`;
- observer barycentric state borrowed from the request observer, including its
  geodetic longitude, latitude, and height;
- retarded target state and one-way light time through the existing
  `AstrometricDirectionRealizer`;
- a Moon-validated `ApparentCorrectionPolicy`, not automatic reuse of the
  Venus policy merely because the type accepts it;
- observer-origin apparent ICRS direction with neither position reference
  epoch nor equinox;
- exactly one `CoordinateService` transformation to the product coordinate
  system;
- stable semantic path `sky/solar_system/moon`;
- ordinary projection, masking, styling, and PNG/PDF/SVG export.

## Required numerical validation

An installed-DE440 acceptance tool must compare Wenu with direct Skyfield at
one declared observer and instant. It must record kernel filename and SHA-256,
Moon and centre NAIF IDs, observer geodetic location and height, reception and
emission instants, iterations, distance, light time, apparent right ascension
and declination, and residuals.

The test must also compare the topocentric direction with a geocentric result
and prove a non-zero parallax displacement. A second observer or materially
different height should demonstrate that the observer state is not decorative.
Numerical tolerances must be derived from the direct implementation and
floating-point path, not selected merely to make the test pass.

The current default deflectors `(10, 599, 699)` and the separate Earth
deflection option were accepted for Venus. Their applicability to the nearby
Moon is an open review item. 49I.2A must compare the explicit Wenu correction
policy with direct Skyfield `observe(...).apparent()` before installing a Moon
layer. No correction may be implied by the word “apparent.”

## Shared extraction rule

The second body now justifies extracting a renderer-neutral shared component,
provisionally `SolarSystemPointLayer`. It may own the invariant orchestration
from typed body descriptor through transformed `SphericalPoints`. A frozen
body descriptor may carry target key, stable entity key, display name,
semantic category/path role, and correction policy.

It must not own kernel selection, network access, observer construction,
projection, viewport tests, marker shape, label layout, SVG generation, phase,
or orbit propagation. Venus must be migrated atomically and remain
output-identical. The Moon must not be implemented by copying `VenusLayer` and
changing string literals.

## Public vocabulary

The internal request should evolve from the planet-only
`SkyContentSelection.planets` toward a typed solar-system selection without
calling the Moon a planet. CLI ergonomics may remain class-aware—for example,
`--planet venus` and `--moon`—while both adapt into the same internal selection
and realization pipeline. A single CLI spelling is not required to prove a
single architecture.

Minor-body and comet selectors are deferred until their provider contracts are
audited. They must not overload deep-sky-object catalogue selection.

## Proposed bounded sequence

1. **49I.2A — Moon numerical direction validation.** Prove kernel identity,
   observer state, parallax, light time, correction policy, and direct-Skyfield
   residuals without adding a chart layer.
2. **49I.2B — Shared solar-system point layer.** Extract only the orchestration
   demonstrated by Venus and Moon; migrate Venus with output parity.
3. **49I.2C — First drawable Moon point.** Add opt-in typed selection, semantic
   identity, style, all chart-family transport, and shared PNG/PDF/SVG output.
4. **49I.3 — Physical apparent-disk contract.** Audit angular diameter,
   phase/illumination, bright-limb position angle, orientation, occultation,
   and renderer-neutral disk geometry before drawing a physical Moon or planet.
5. **49I.4 — Minor-body/comet state-source audit.** Add no orbit propagator
   until time scales, element epochs, perturbation model, provenance, coverage,
   uncertainty, and Sun-relative tail geometry are explicit.

## Non-goals

This audit adds no runtime type, Moon layer, public option, kernel download,
orbit propagator, phase model, physical disk, comet tail, trail, projection,
renderer, or output change. It does not claim that a shared chart pipeline
makes all astronomical models interchangeable.

## Acceptance

Fernando accepted the audit on 2026-08-30 after all 51 current-documentation
tests passed in 1.88 seconds. He accepted all four governing decisions:

1. Does “one pipeline” mean one downstream typed path with interchangeable
   providers and appearance strategies, as specified here?
2. Is the Moon the next body and a symbolic point the appropriate first slice?
3. Should the public CLI use `--moon` while the internal request uses a general
   solar-system selection?
4. Is physical disk/phase geometry correctly deferred to 49I.3?

The answers are yes: one downstream typed pipeline with interchangeable
providers and appearance strategies; Moon next; symbolic point first;
`--moon` adapting into general internal solar-system selection; and physical
disk/phase geometry deferred to 49I.3. The next bounded implementation is
49I.2A Moon numerical direction validation.
