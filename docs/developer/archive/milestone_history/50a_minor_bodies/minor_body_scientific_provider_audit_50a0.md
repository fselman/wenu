# Minor-body scientific and provider audit (Milestone 50A.0)

**Status:** Accepted by Fernando

**Baseline:** `b96a033`

**Date:** 2026-09-10

**Runtime effect:** None

**Acceptance:** Fernando accepted the scientific and architectural decisions
in this record on 2026-09-10. Milestone 50A.0 is closed; 50A.1, the generic
minor-body state-provider seam, is the next authorized milestone.

## 1. Purpose

50A.0 selects the scientific boundary for asteroids and comets before Wenu
adds a provider, body registration, CLI option, track, or visible object. It
decides the first state source, resource and solution provenance, validity,
time and frame semantics, apparent-place handoff, uncertainty policy,
identifier policy, photometric scope, and cometary non-gravitational treatment.

The decision is deliberately narrower than a universal minor-body system. The
first implementation must be accurate, offline while rendering, reproducible,
and compatible with Wenu's existing `EphemerisStateSource`, apparent-direction
realizer, descriptor catalog, projection, semantic, renderer, and exporter.

## 2. As-is Wenu boundary

Wenu already separates provider-native geometric state from direction
realization. `EphemerisState` requires target and centre, Cartesian frame,
evaluation instant and time scale, complete position and velocity, explicit
units, resource identity, provider identifiers, and provenance. The existing
direction machinery owns iterative light time, the observer state, apparent
corrections, and the observer-origin ICRS result. A raw state is not drawable
geometry.

`SolarSystemBodyDescriptor` already separates stable Wenu identity,
classification, parent relationships, physical properties, and capabilities.
The generic point and track layers do not require a planet-specific renderer.
Therefore 50A must add provider science upstream and later register validated
bodies through the existing catalog; it must not introduce asteroid- or
comet-specific coordinate, projection, rendering, semantic-export, or file-
export paths.

The current `SkyfieldEphemerisStateSource` is specialized to one already-open
JPL planetary SPK. A Horizons-generated small-body SPK may require composition
with the separately resolved planetary ephemeris. 50A.1 must make that resource
relationship explicit rather than pretending that two files are one kernel or
loading an unrecorded second authority.

## 3. Authoritative evidence

Sources were reviewed on 2026-09-10. Versions are recorded where the service
publishes one.

| Source | Authority | Material finding for Wenu |
| --- | --- | --- |
| [Horizons API v1.3](https://ssd-api.jpl.nasa.gov/doc/horizons.html) | NASA/JPL Solar System Dynamics, 2025-06 | Supports asteroid/comet SPK generation, geometric vectors, osculating elements, ICRF, TDB, explicit centres, uncertainty output, and user-supplied non-gravitational parameters. |
| [Horizons system manual](https://ssd.jpl.nasa.gov/horizons/manual.html) | NASA/JPL Solar System Dynamics | Distinguishes geometric, astrometric, and apparent products; documents statistical uncertainty limits and warns that linearized covariance can be optimistic far from the solution epoch or across close encounters. |
| [SBDB API](https://ssd-api.jpl.nasa.gov/doc/sbdb.html) | NASA/JPL Solar System Dynamics | Supplies canonical and alternate designations, SPK ID, orbit solution ID/date/source, TDB osculating epoch, J2000 ecliptic elements, covariance, uncertainties, observation arc, perturbing ephemerides, validity fields, physical parameters, and comet model parameters. |
| [SPK Required Reading](https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/C/req/spk.html) | NASA/JPL NAIF | SPK states are target relative to centre in a declared frame and have explicit segment coverage; loaded-file/segment priority affects the selected state. |
| [MPC public documentation](https://docs.minorplanetcenter.net/) | IAU Minor Planet Center | MPC is the authority for minor-planet/comet observations and designation practice and exposes best-fit asteroid/comet orbital elements. |
| [Marsden, Sekanina & Yeomans 1973](https://doi.org/10.1086/111402) | Astronomical Journal | Establishes the standard Style-II comet non-gravitational model underlying the radial, transverse, normal, and lag parameters exposed by Horizons/SBDB. |

API responses are mutable services, not reproducible resources by themselves.
The JPL APIs explicitly require clients to check the returned schema version
and to avoid unnecessary repeated requests. Wenu must acquire and freeze
resources before chart generation rather than treating either API as a live
runtime dependency.

## 4. Decisions

### D50A0-1 — First numerical state source: Adapt

Use a **bounded Horizons-generated small-body SPK** as the first production
state authority. Resolve it locally before rendering, fingerprint its bytes,
inspect target/centre/frame/segment coverage, and evaluate only within that
coverage. Combine it with the already resolved planetary ephemeris only through
an explicit composite resource/provenance contract in 50A.1.

This adapts the existing JPL/Skyfield route without assuming that a small-body
SPK contains the planetary states needed for observer realization. SPK coverage
is a hard interpolation boundary, not a claim that the orbit solution has equal
accuracy throughout the interval.

### D50A0-2 — Live Horizons/SBDB during rendering: Reject

Do not query Horizons, SBDB, or MPC from a chart request. Network state,
service versions, mutable orbit solutions, ambiguity resolution, throttling,
and outages are incompatible with offline deterministic rendering. Acquisition
or refresh must be a separate explicit operation whose result becomes a local
identified resource.

### D50A0-3 — Orbital-element provider: Defer

Retain heliocentric osculating elements as a future interchangeable provider,
but do not make a two-body Keplerian propagator the silent fallback for 50A.1.
Before acceptance, an element provider must declare its epoch in TDB, reference
ecliptic and obliquity, planetary and massive-asteroid perturbations,
relativistic terms where material, numerical integrator and tolerances, and
comet non-gravitational law. It must be compared independently with Horizons
over its claimed interval and across a demanding nearby-object case.

### D50A0-4 — State and apparent-place ownership: Adopt

The minor-body provider returns a simultaneous **geometric** Cartesian state
with complete velocity. It must not pre-apply light time, stellar aberration,
gravitational deflection, topocentric parallax, refraction, or chart-frame
transformation. Wenu's existing astrometric and apparent realizers own the
retarded emission time and correction handoff. The existing observer state
produces topocentric parallax; topocentricity remains an origin, not a position
status.

### D50A0-5 — Frame, epoch, and time: Adopt

Production state output converges on ICRF axes and TDB evaluation. If orbital
elements are retained as source metadata, their osculating epoch, time scale,
heliocentric centre, ecliptic reference and obliquity must remain explicit.
`J2000` ecliptic elements must not be relabelled as ICRF Cartesian vectors.
Observation UTC, provider TDB, osculating epoch, reference equinox, chart epoch,
and product frame remain separate fields.

### D50A0-6 — Resource and solution provenance: Adopt

Every resolved minor-body state must retain:

- provider and service/schema version;
- Wenu target key and object class;
- IAU number when assigned, primary designation, name when assigned, aliases,
  Horizons command form, and provider SPK ID as separate identifiers;
- orbit solution ID, source/producer, solution date, osculating epoch and
  reference system;
- local filename, SHA-256 digest, SPK target/centre/frame, segment identifiers,
  load priority, and exact coverage;
- planetary and small-body perturber ephemeris identities where reported;
- model parameters, observation arc and counts, last observation, fit RMS,
  condition code, covariance epoch and availability, and source lineage.

A name alone is never a stable lookup key. Numbered asteroids use the
unambiguous Horizons small-body form with its terminating semicolon; comet and
provisional designations retain their exact provider form. Wenu identity stays
distinct from all provider-native identifiers.

### D50A0-7 — Validity and uncertainty: Adapt

Fail closed outside SPK segment coverage. Also retain any provider
`not_valid_before`/`not_valid_after` limits. Absence of those fields does not
mean zero uncertainty. Covariance, element sigmas, condition code, observation
arc, solution age, and close encounters are quality evidence, not one
interchangeable scalar.

50A.1 preserves available uncertainty provenance but does not propagate or
display an uncertainty region. 50A.2 must validate a well-determined main-belt
object and a fast nearby object at multiple epochs and sites against a direct
authoritative Horizons observer solution. Claimed tolerances must be set from
that evidence, not from SPK polynomial precision alone. Uncertainty display or
Monte-Carlo/line-of-variation propagation requires a later contract.

### D50A0-8 — Asteroid photometry: Adapt

Keep dynamics independent of brightness. For the first drawable asteroid,
retain the provider's absolute-magnitude parameters and explicit model tag.
Implement the IAU `H,G` phase law only when both its source and parameters are
identified, and validate apparent magnitude independently. Do not invent a
default slope parameter or convert missing data into certainty.

`H,G1,G2`, `H,G12`, rotational light curves, opposition effects, color,
albedo-derived size, activity, and phase laws outside the validated domain are
deferred. A user-explicit object may still be drawn when no accepted magnitude
is available, but it must not pass a magnitude-limited automatic selection as
though its brightness were known.

### D50A0-9 — Comet photometry and appearance: Defer

Comet total magnitude (`M1`, `K1`) describes activity-dominated coma brightness;
nuclear magnitude (`M2`, `K2`, and phase coefficient where applicable) is a
different and often uncertain quantity. Neither is an asteroid `H,G` model.
50A.4 validates nucleus direction and model provenance; 50A.5 may draw an
explicitly selected nucleus position and track without claiming a reliable
visibility limit. Coma, dust/gas morphology, tail direction and length,
surface-brightness selection, and automatic comet visibility remain a later
physical-appearance program.

### D50A0-10 — Comet non-gravitational dynamics: Adapt

For the first comet, prefer a Horizons-generated SPK whose orbit solution
already incorporates the provider's accepted dynamical model. Preserve SBDB/
Horizons `A1`, `A2`, `A3`, lag `DT`, the model constants, estimated-parameter
list, covariance, alternate orbit solutions, and solution identity when
present. Wenu must not reapply those accelerations after reading the SPK.

A future element propagator may support the Marsden-style law only through an
explicit model identifier and parameters. If the selected solution requires
non-gravitational terms that the provider cannot implement, it must reject the
request rather than silently propagate a gravity-only orbit. Fragmentation,
outbursts, asymmetric or time-variable outgassing, and specialized sungrazer
laws are deferred.

### D50A0-11 — Nucleus, coma, and tail semantics: Adopt

The ephemeris target is the modeled centre of the nucleus. A point or dated
track represents that direction only. It does not represent the photocentre,
coma boundary, ion tail, dust tail, or their brightness. Coma and tail geometry
require separate physical state, semantic components, selection policy, and
validation; they must not be encoded as a larger point marker.

### D50A0-12 — Acquisition and packaging: Adapt

50A.1 must define an explicit acquisition/import boundary, but downloading and
redistribution policy are not assumed here. A user-resolved file may live in
the existing Wenu cache with a manifest and digest. Packaging a specific SPK
requires a separate size, license/redistribution, update, and release decision.
Rendering must never update a resource implicitly.

## 5. Required 50A.1 contract

The next implementation may add only the provider/resource seam needed to
produce the existing `EphemerisState`. It must:

1. resolve a small-body SPK plus its companion planetary ephemeris explicitly;
2. fingerprint every file once and preserve ordered segment/load provenance;
3. identify the target, centre, frame, units, TDB instant, and exact coverage;
4. return complete finite position and velocity without correction;
5. reject ambiguous identifiers, missing state chains, unsupported frames,
   incompatible time, and out-of-coverage requests deterministically;
6. perform no network access, body registration, CLI exposure, direction
   realization, projection, rendering, or export;
7. use a deterministic synthetic/test resource for structural tests and keep
   installed-kernel numerical validation for 50A.2.

If the existing single `EphemerisResourceIdentity` cannot truthfully describe
the small-body-plus-planetary resource chain, 50A.1 must propose the smallest
typed composite provenance extension. It must not hide the second file in a
free-form string merely to avoid a contract change.

## 6. Validation plan

50A.2 should choose at least:

- one well-determined main-belt asteroid with slow, stable apparent motion;
- one well-determined near-Earth object during a faster but non-pathological
  interval, with explicit topocentric parallax evidence.

Compare target/centre Cartesian state, light time, observer-origin apparent
ICRS RA/Dec, distance, and site-dependent parallax at multiple epochs against
direct Horizons output. Freeze the exact resource digests, Horizons/SBDB
solution identifiers, query parameters, returned API versions, observer
coordinates, timestamps, and tolerances. Do not use the same Wenu provider to
construct its oracle.

50A.4 must repeat the pattern with a comet whose selected solution declares
whether non-gravitational parameters are present. At least one validation case
must demonstrate that this distinction survives provenance and, when material,
affects the accepted comparison.

## 7. Explicit non-goals

50A.0 does not add or change Python runtime code, dependencies, files in the
ephemeris cache, downloaded data, body descriptors, CLI/TOML options, magnitude
selection, symbols, labels, tracks, coma/tail geometry, projection, rendering,
SVG semantics, exporters, or current chart output. It sets no numerical
tolerance and accepts no particular asteroid or comet for display.

No visual comparison is required because this audit changes no chart request,
geometry, style, renderer, or output. The coordinate-system guide requires a
minor-body provider-decision update but no change to coordinate mathematics.
The user guide and examples require no edit because there is still no public
minor-body selector, configuration, default, or visible result. Architecture
diagrams require no edit because 50A.0 accepts a future provider boundary but
installs no component and changes no current ownership edge.
