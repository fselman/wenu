# Generic numbered asteroids (Milestone 50A.3D)

**Status:** Candidate implementation; numerical and visual acceptance pending

**Base:** `d538473869c82e6fe125f7b9d7a69596639c7d97`

## Scope

This slice implements the accepted 50A.3C contract. The existing
`--asteroid` and `--asteroid-track` options accept the permanent number or an
exact, case-folded official name declared by the explicitly selected local
resource manifest. Rendering remains offline. `(79989)` is the acceptance
specimen, not a special runtime case.

`tools/acquire_numbered_asteroids.py` is the separate networked acquisition
boundary. It resolves each requested permanent number with Horizons and SBDB,
writes one bounded SPK per object, and records structured identity, solution,
classification, target, provenance, and digest fields in a new immutable
collection manifest.

## Ownership and preserved pipeline

`MinorBodyResourceCollection` validates the collection and creates one
request-owned `SolarSystemBodyDescriptor` per selected permanent number. The
number remains the selection and semantic identity; an optional official name
is only display metadata and an exact local alias. A request transports those
descriptors without mutating the built-in catalog. Request preparation
temporarily registers only the selected layers and removes them when a
reusable-sphere build closes.

The asteroid SPK remains the target-state source and the observer's DE440
Skyfield source remains the observer/apparent-correction source. Direction,
fixed product frame, projection, clipping, preparation, renderer, semantic
SVG, and export paths are unchanged. The old 50A.2 manifest and `ceres` route
remain supported.

Display text is `Name (number)` for named objects and `(number)` for unnamed
objects. Semantic paths are number-based, for example
`sky/solar_system/minor_bodies/asteroids/79989` and its `track` child.

## Acceptance still required

The explicit macOS acquisition on 2026-09-11 resolved `(79989)` as unnamed
main-belt asteroid `1999 FH1` (`MBA`), Horizons target `20079989`, solution
`JPL#42` dated `2026-Jun-06_12:19:06`, osculating epoch `2458360.5 TDB`, and
SPK SHA-256
`d62bbf1aef90560db4cd5fa89dce2b4ddce15a5c807beae909ca75cce7fc9d87`.
The first public-path render exposed and then corrected a semantic-boundary
fault: layer names must begin with a letter, while semantic path components
may be a permanent decimal number. The internal layer is therefore
`asteroid_79989` and the stable semantic path component is `79989`.

Before acceptance, acquire `(79989)`, freeze and run the 50A.2-style numerical
comparison at at least three epochs, run focused and complete tests, and have
Fernando inspect a regional PNG and semantic SVG containing its point and
dated track. The point and track make no brightness or detectability claim.

No user example implies automatic discovery, catalog sweep, provisional
designation, comet, dual-status object, photometry, field intersection, or
network access during chart generation. The coordinate-system guide and the
focused minor-body diagram are updated because request identity ownership
changes; no other architecture diagram requires modification.
