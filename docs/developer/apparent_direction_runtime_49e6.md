# Milestone 49E.6 — Apparent direction runtime

**Status:** Implementation and scientific review candidate.  
**Implementation baseline:** `3752142`  
**Date:** 2026-08-30

## Purpose

49E.6 converts one accepted 49E.5 astrometric Solar-System direction into an
apparent direction by applying declared gravitational-deflection and
aberration corrections. It does not solve light time again and does not create
a drawable planet layer.

## Scientific boundary

The input is `AstrometricDirection`: observer state at reception, target state
at retarded emission time, distance, light time, retained relative velocity,
and exact kernel identity. `SkyfieldApparentDirectionRealizer` reconstructs
that accepted Cartesian line of sight and calls Skyfield `apparent()`—never
`observe()`—with an explicit `ApparentCorrectionPolicy`.

The default policy records NAIF deflectors 10, 599, and 699 (Sun, Jupiter, and
Saturn), near-Earth gravitational deflection, and stellar aberration. Skyfield
applies gravitational deflection before aberration. A policy may not silently
disable either correction and still label the result apparent.

The result is observer-origin, `PositionStatus.APPARENT`, and expressed on
fixed ICRS-oriented axes. Its reception instant is an observation instant. It
has no position reference epoch and no equinox. In particular, apparent
status does not mean “equinox of date”; a later `CoordinateService`
transformation may choose an equinox-based product frame without recomputing
the physical direction.

## Identity and failure rules

- source and observer borrow the same already-open kernel;
- source identity equals the accepted astrometric resource identity;
- observer time equals the astrometric reception instant;
- freshly evaluated observer position and velocity equal the retained state;
- the target provider identifier is an integer NAIF ID;
- output provenance records kernel filename, SHA-256, model, deflectors,
  observer, target, and correction sequence.

These checks prevent a direction obtained with one kernel, observer, or
instant from being corrected as though it came from another.

## Retained velocity correction

49E.6 makes one additive correction to the accepted 49E.5 result contract:
`AstrometricDirection` now retains the target-at-emission minus
observer-at-reception relative velocity in AU/day. The light-time algorithm and accepted
angles are unchanged. The velocity was already computed by 49E.5; retaining it
allows Skyfield's apparent-place operation to consume Wenu's accepted result
without a second observation/light-time authority.

## Verification and non-goals

Deterministic tests prove policy validation, identity failures, correction
metadata, retained-velocity handoff, and the absence of a second `observe()`
call. `tools/validate_49e6_apparent_direction.py` refuses network downloads and
compares installed-DE440 Venus output with direct Skyfield
`observe().apparent()` at the same observer and reception instant.

49E.6 adds no configuration, CLI option, sky layer, body symbol, phase model,
label, projection, renderer, or exporter. No future Venus, Moon, Sun, or planet
may be drawn by a separate SVG generator or post-export overlay. 49I.1 must
transform this renderer-neutral spherical geometry once into the product
frame, then use the existing projection, Matplotlib renderer, and shared
PNG/PDF/SVG exporter.
