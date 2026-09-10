# Generic minor-body state provider (Milestone 50A.1)

**Status:** Implemented for Fernando's architectural review

**Base:** `9097d4f`

**Runtime effect:** Adds an unconnected, offline provider/resource seam. No
body, chart request, CLI option, direction, projection, rendering, or output is
changed.

## 1. Scope

50A.1 implements only the provider boundary accepted in 50A.0. One resolved
Horizons small-body SPK is composed explicitly with one existing
planetary state source and produces the existing complete geometric
`EphemerisState`. Both resources are borrowed; the provider does not open,
download, update, close, or package an SPK kernel. It reads the already-
resolved small-body file once to calculate its content digest.

Asteroid numerical acceptance remains 50A.2. Body registration, symbolic
display, designation policy, public selection, and tracks remain 50A.3.

## 2. Typed resource and solution identity

`EphemerisResourceChain` adds the smallest truthful extension to the existing
single-file identity. It contains one primary `EphemerisResourceIdentity`, one
or more distinct dependency identities, and immutable provenance. Existing
single-resource states remain unchanged; `EphemerisState.resource` accepts
either the original identity or the explicit chain.

`MinorBodySolutionIdentity` keeps these roles separate:

- provider and service/schema version;
- stable Wenu target key and asteroid/comet class;
- primary designation, exact Horizons command, provider SPK ID, optional IAU
  number, name, and aliases;
- orbit-solution ID and date, osculating epoch, and reference system;
- named dynamical/model parameters, named quality fields, and provenance.

Names and aliases do not become provider lookup keys. The exact provider SPK
ID selects the acquired kernel segment, while the Wenu key must match the
state request.

`MinorBodyEphemerisState` is a frozen `EphemerisState` subtype that retains the
complete typed solution identity and selected `MinorBodySegmentIdentity` on
the returned value itself.

## 3. State composition

`SkyfieldMinorBodyStateSource` borrows a small-body kernel, a structural
planetary `EphemerisStateSource`, and a Skyfield timescale. Its factory hashes
the small-body file once, retains the planetary resource as a typed dependency,
and records every SPK segment in file order with target, centre, and TDB
coverage.

For one TDB request the provider:

1. requires the accepted Wenu target and `frame='icrf'`;
2. selects the last covering target segment, preserving SPK segment priority;
3. evaluates the target relative to that segment's declared centre;
4. requests that numeric centre relative to the caller's centre from the
   existing planetary source at the same TDB instant;
5. validates the returned request, resource dependency, AU, and AU/day units;
6. adds relative position and velocity and returns the original request with
   the complete resource chain, typed solution, selected segment, and
   provenance.

Numeric provider IDs are therefore accepted by the existing borrowed Skyfield
adapter. They remain provider-native identifiers, not Wenu catalog keys.

## 4. Failure policy

The provider fails deterministically for an untyped request or dependency,
missing or mismatched solution identity, unsupported object class, ambiguous
Wenu target, non-ICRF frame, non-TDB evaluation, absent declared SPK target,
malformed or uncovered segments, undeclared planetary resource, mismatched
dependency request, and incompatible dependency units. It does not extrapolate
or silently substitute a two-body orbit.

SPK segment coverage controls interpolation only; it makes no claim of uniform
orbit-solution accuracy. The single-resource start/end fields bound the target
segments; the ordered segment identities are the exact coverage authority, so
gaps inside that extent still fail closed. Model and quality metadata remain
evidence for 50A.2, which will set numerical tolerances through an independent
Horizons comparison.

## 5. Tests and placement

`tests/test_ephemeris.py` extends the existing immutable state/resource
contract for the resource chain. `tests/test_skyfield_ephemeris.py` extends the
existing borrowed planetary adapter for numeric provider IDs.

The new `tests/test_minor_body_ephemeris.py` owns a durable new component with
distinct two-resource, segment-priority, TDB, and fail-closed obligations.
Placing those tests in the single-resource adapter file would obscure the new
composition boundary. Its kernels and planetary source are deterministic
synthetic objects; it performs no network access and does not repeat direction,
projection, rendering, export, CLI, or complete-chart tests.

## 6. Documentation and diagram review

A focused architecture diagram records the unconnected state-provider/resource-
chain seam because package and type ownership changed. The general overview
and coordinate transformation diagrams remain current: no minor-body state is
converted to spherical geometry or connected to `CoordinateService` in 50A.1.
User documentation and examples remain unchanged because no public request or
visible capability exists.

The coordinate-system guide records the implemented state semantics and keeps
50A.2 numerical validation as the next scientific gate.

## 7. Acceptance

Fernando's review must confirm that the explicit target-segment-centre plus
planetary-centre composition is the correct first implementation of the
accepted Horizons-SPK boundary. Acceptance authorizes 50A.2 numerical
validation; it does not authorize a drawable asteroid.
