# Descriptor-driven moving-body architecture — Milestone 49I.3C.3.3A

**Status:** Scientifically, architecturally, and visually accepted

**Decision date:** 2026-09-01

**Baseline:** `4d7925a`

## Purpose

This milestone generalizes the accepted Venus machinery before registering
Mercury. Planets, dwarf planets, minor bodies, natural satellites, and
artificial satellites share one moving-body identity and downstream chart
pipeline. Body classification does not select a renderer.

## Ownership boundary

`SolarSystemBodyDescriptor` owns stable target, entity, display and selection
identity; body class and non-exclusive classifications; an optional parent
relationship; physical-body ID; optional spherical radius and its authority;
and explicit display capabilities. `SolarSystemBodyCatalog` owns immutable
lookup and relationship queries. A planet does not contain its satellites.

Provider-specific state sources remain upstream. JPL SPK, minor-body SPK or
orbital elements, and SGP4/TEME artificial-satellite propagation may implement
different science, but must converge on canonical state and provenance before
ordinary direction, appearance, geometry, projection, and chart rendering.

## Generic drawable machinery

The following factories now consume body metadata rather than Venus classes:

- `SolarSystemPointLayer` for symbolic apparent points;
- `solar_system_disk_layers()` for one resolved spherical disk;
- `observed_solar_system_disk_sequence_layers()` for an observed sequence;
- `frozen_earth_solar_system_disk_sequence_layers()` for a constructed
  frozen-Earth sequence;
- `SolarSystemTrackLayer` for an apparent track.

Layer names, sample IDs, semantic hierarchy, request installation, cleanup,
detail selection, styling dispatch, and frozen-scene enablement derive from
the descriptor and component role. Accepted Venus names and semantic paths
remain unchanged through compatibility factories and aliases.

CLI choices are derived from the built-in catalog and capability set. Adding a
new supported built-in body should require a descriptor/catalog registration
and that body's independent scientific validation, not a new chart factory,
component-layer class, projection, renderer, or exporter.

## Capability policy

Capabilities, not classification, govern supported products. A body may offer
a symbolic point and track without a physical radius. Resolved disks require
a positive governed radius and radius model. Artificial-satellite shadow,
trail, or attitude products and cometary coma or tail products require future
specialized appearance models, while their accepted directions can still use
the shared projection and chart path.

## Proof without a second planet

Deterministic tests register a synthetic minor body with two simultaneous
classifications and a parent relationship. Without a body-specific source
module or layer class it produces symbolic, resolved-disk, observed-sequence,
and frozen-sequence layers; chart installation; stable generated names; and
minor-body semantic paths. Mercury remains unregistered until its independent
radius, provider identity, DE440 sampling, and numerical evidence are reviewed.

## Non-goals

This milestone does not add Mercury, another public CLI body, a minor-body
ephemeris provider, SGP4, TEME conversion, cometary appearance, satellite
shadow state, rotational orientation, or new visible output. It does not claim
that all moving bodies share the same state provider or appearance model.

## Acceptance

Fernando accepted the descriptor/catalog boundary, relationship model,
capability policy, generic drawable factories, and preservation of
provider-specific upstream science on 2026-09-01. The complete Mac suite passed
all 2,045 tests in 86.49 seconds.

Human visual regression accepted the Spanish 31-sample frozen-Earth Venus
sequence, the ordinary resolved Venus crescent in its regional celestial
scene, and the four-epoch observed Venus sequence with date labels. The
observed calibration retains the existing fixed-label crowding; it is not a
generalization regression. Mercury remains the next independently validated
catalog registration.

All three Venus compatibility renders were accepted without a body-specific
projection, renderer, or exporter.
