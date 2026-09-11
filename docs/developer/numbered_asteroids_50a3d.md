# Generic numbered asteroids (Milestone 50A.3D)

**Status:** Candidate implementation; visual and numerical acceptance complete, test gates pending

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

## Acceptance evidence

The explicit macOS acquisition on 2026-09-11 resolved `(79989)` as unnamed
main-belt asteroid `1999 FH1` (`MBA`), Horizons target `20079989`, solution
`JPL#42` dated `2026-Jun-06_12:19:06`, osculating epoch `2458360.5 TDB`, and
SPK SHA-256
`d62bbf1aef90560db4cd5fa89dce2b4ddce15a5c807beae909ca75cce7fc9d87`.
The first public-path render exposed and then corrected a semantic-boundary
fault: layer names must begin with a letter, while semantic path components
may be a permanent decimal number. The internal layer is therefore
`asteroid_79989` and the stable semantic path component is `79989`.
The second public-path attempt exposed the matching detail-policy boundary:
visibility is selected by the descriptor's public selection key, not its safe
technical layer name. That mapping is now explicit and retains the same
number-based geometry selection.
The first successful PNG then exposed an SVG-only hierarchy-label conflict:
the point called the shared body node `(79989)`, while the track inferred
`79989`. Point and track identities now explicitly assign the same body-node
display name and reserve the track wording for the `track` child.

Fernando visually accepted the 7.5-degree binocular PNG and semantic SVG on
2026-09-11. The accepted product contains one hollow-diamond start point, one
`(79989)` label, four dated weekly anchors from 2026-01-15 through 2026-02-12,
and the shared asteroid track appearance. The point and track make no
brightness or detectability claim.

The frozen direct-Horizons comparison was accepted on Fernando's macOS
`macOS-10.16-x86_64-i386-64bit`, Python 3.11.7 environment on 2026-09-11.
It exercises three epochs across 2026, 2027, and 2029, the installed type-21
SPK segment, barycentric position and velocity, geocentric and La Ligua
topocentric astrometric and apparent directions, distance, light time, and
parallax. The accepted maximum residuals are:

- position: `1.2029932605628346e-11 au`;
- velocity: `3.6855067608865255e-14 au/day`;
- astrometric right ascension and declination:
  `6.369987204379868e-09 deg` and `3.0405935547150875e-09 deg`;
- apparent right ascension and declination:
  `6.717181122439797e-08 deg` and `4.6903810613230235e-08 deg`;
- distance: `3.8462300011588013e-10 au`;
- light time: `5.156753246637891e-09 min`;
- parallax: `7.085531775067114e-08 deg`.

The 50A.3D fixture declares a `2e-11 au` position tolerance, selected after
an explicit characterization run reported the roughly 1.80 m maximum above.
It does not change the accepted 50A.2 default of `5e-12 au`; velocity,
direction, distance, light-time, and parallax tolerances remain unchanged.
The enforcing run reported `accepted: true`. Focused and complete test gates
remain required before final milestone acceptance.

No user example implies automatic discovery, catalog sweep, provisional
designation, comet, dual-status object, photometry, field intersection, or
network access during chart generation. The coordinate-system guide and the
focused minor-body diagram are updated because request identity ownership
changes; no other architecture diagram requires modification.
