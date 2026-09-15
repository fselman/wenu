# 50S.5A complete local crossing-oracle audit

**Status:** Candidate documentation-only scientific and API audit  
**Base:** accepted 50S.4 closure at merge commit `41978bc`  
**Date:** 2026-09-15

## 1. Purpose and scope

This audit freezes the smallest scientifically honest contract for the first
complete local circular-field crossing oracle. It adds no runtime code,
dependency, snapshot, generated product, CLI, report, drawing, illumination,
photometry, detector behavior, or acceleration.

The authorized implementation after acceptance is 50S.5B. It scans every valid
record in one selected immutable snapshot and returns every connected visit of
the accepted local geometric trajectory through one closed circular spherical
field over one inclusive UTC interval.

## 2. Existing accepted authorities

50S.4 supplies the complete state chain:

1. an immutable digest-verified synthetic OMM snapshot;
2. explicit WGS-72 Vallado-compatible SGP4 propagation;
3. typed geocentric geometric TEME position and velocity;
4. explicit installed IERS-A identity with no download or degraded accuracy;
5. WGS-84 observer subtraction in ITRS;
6. vacuum AltAz and a topocentric geometric vector expressed in GCRS axes.

`SatelliteIdentity`, `SatelliteObserver`, `SatelliteFieldOfView`,
`InclusiveTimeInterval`, `SatelliteCrossingCandidate`, and
`SatelliteCrossingResult` already own provider-neutral value contracts.
They do not implement a local trajectory evaluator or crossing solver.

The 50S.4E specimen is sampled input evidence only. It is not an oracle,
verified crossing, tolerance authority, or completeness proof.

## 3. Coordinate compatibility decision

The first local oracle accepts only a circular
`SatelliteFieldOfView` whose `CoordinateSpec` declares:

- frame `gcrs-axes`;
- origin `topocentric-direction`;
- geometric position status;
- UTC;
- the same observer, vacuum policy, and Earth-orientation policy used by the
  propagated trajectory.

The field centre is one fixed unit vector expressed in GCRS axes for the whole
query. Its coordinate-spec instant records the query reference instant; it
does not make the field rotate with the evaluation instant.

The oracle compares that fixed vector with the accepted 50S.4D topocentric
geometric GCRS-axis vector using a dot product and a clipped angular
separation. It must not compare provider apparent ICRS values, vacuum AltAz
angles, projected chart coordinates, or mixed-position-status samples
numerically. Apparent ICRS, spherical rectangles, WCS footprints, refraction,
and moving fields require later separately admitted conversions.

## 4. Query and output decision

50S.5B owns one explicit immutable local-query contract containing:

- selected `SatelliteElementSnapshot`;
- `SatelliteObserver`;
- compatible circular `SatelliteFieldOfView`;
- inclusive `InclusiveTimeInterval`;
- positive requested time tolerance in seconds;
- positive requested angular tolerance in degrees.

The first public owner is proposed as
`src/wenu/satellites/crossing_oracle.py`. This is a new production module
because adaptive continuous-trajectory evaluation, numerical convergence,
connected-visit assembly, and fail-closed completeness are a distinct
scientific responsibility and failure boundary. Adding this behavior to
`satellite_crossings.py` would mix provider-neutral immutable records with a
specific local numerical oracle.

The oracle returns an immutable ordered tuple of existing
`SatelliteCrossingResult` values. Each result retains the snapshot digest,
record identity and element epoch, observer and coordinate policy, closed
field, inclusive interval, ordered entry/closest/exit instants, closest
separation, closest range and angular rate, solver tolerances, implementation
identity, SGP4 identity, IERS-A identity, and warnings through typed fields or
explicit provenance. Illumination remains `None`.

Results are ordered by full NORAD catalogue identifier and then entry instant.
Disconnected visits are separate results. A visit already inside at query
start uses the inclusive start as entry; a visit still inside at query stop
uses the inclusive stop as exit. A zero-duration boundary touch is one valid
result. Adjacent numerical fragments belonging to one continuous visit are
merged within the declared time and angular tolerances.

## 5. Numerical completeness decision

### 5.1 Meaning of complete

For floating-point SGP4 and Astropy transformations, “complete” means validated
numerical completeness under the declared time and angular tolerances. It is
not a formal interval-arithmetic proof for every possible black-box function.

The implementation scans every valid record in the selected snapshot. No
plane, phase, horizon, occultation, HEALPix, coarse catalogue, or measured
population filter may remove a record or interval in 50S.5B.

### 5.2 Signed field function

For field radius `r` and spherical separation `d(t)`, use the signed
function

`g(t) = d(t) - r`.

Inside is `g <= 0`; outside is `g > 0`. Closed-boundary equality therefore
counts. Dot products are clipped before inverse trigonometric evaluation.
Longitude wrap, poles, and chart seams do not appear in this predicate.

### 5.3 Adaptive subdivision

Every query interval is recursively evaluated at endpoints and midpoint.
Refinement continues until the signed-separation behavior and interval motion
envelope converge below the requested angular tolerance, or the interval width
falls below the requested time tolerance.

The motion envelope uses topocentric Cartesian position and velocity,
instantaneous angular rate
`|rho x rho_dot| / |rho|^2`, midpoint curvature evidence, and successive
refinement. An interval may be rejected only when its conservative envelope
keeps the complete interval strictly outside the closed field by more than the
angular tolerance.

A loose, singular, non-finite, or non-converged envelope is never a negative
answer. The implementation subdivides it. If it reaches the admitted
subdivision/resource limit without convergence, it raises an explicit
`SatelliteCrossingConvergenceError`; it must not return an incomplete result
set.

This operational envelope is a validated floating-point bound, not a formal
analytic enclosure of SGP4. Its safety margin and convergence rule are frozen
by tests against separately constructed trajectories and refinement stability.
A fixed sampling grid, endpoint-only sign test, unconstrained interpolation,
or catalogue-wide maximum angular speed is forbidden.

### 5.4 Roots, extrema, and visits

A sign-changing bracket is refined to the requested time and angular
tolerances by a bracket-preserving root method. Boundary equality at an
endpoint is retained.

Each retained possible-contact interval also receives bounded
closest-approach refinement; this detects tangency without requiring a sign
change. Extrema refinement must remain inside its bracket. A candidate
tangency becomes a crossing only when its refined minimum is within the closed
field plus angular tolerance.

The solver evaluates final entry, exit, and closest states through the ordinary
50S.4C/50S.4D path. It never reports linearly interpolated astronomical state.
Returned instants are normalized UTC and ordered inside the inclusive query
interval.

## 6. Failure behavior

The complete local query fails explicitly when:

- the field coordinate identity is incompatible;
- observer or policy identity differs;
- the snapshot, record, SGP4, or IERS-A resource is invalid;
- propagation returns a non-zero status;
- Earth-orientation coverage is unavailable;
- evaluation produces non-finite state;
- requested tolerances are invalid;
- adaptive refinement cannot certify the result under its resource limit.

One invalid record does not silently disappear. The bounded 50S.5B decision is
to fail the complete query with record identity and cause. A later policy may
represent per-record failures, but cannot call the surviving subset complete.

## 7. Independent validation

The closest existing test is `tests/test_satellite_crossings.py`, which owns
immutable provider-neutral value contracts. Extending it with numerical-oracle
tests would obscure the independence of provider normalization and local
continuous solving.

The admitted durable test owner is
`tests/test_satellite_crossing_oracle.py`. It owns:

- analytic fixed, linear great-circle, tangent, and no-contact trajectories
  with independently known roots and minima;
- entry at start, exit at stop, exact boundary touch, and zero-duration touch;
- two disconnected visits;
- longitude seam and polar fields expressed by vectors;
- fast near-zenith geometry and mandatory subdivision;
- tolerance tightening and refinement stability;
- explicit convergence failure rather than a false negative;
- all-record deterministic scan and ordering for the installed synthetic
  snapshot;
- preserved snapshot, SGP4, observer, IERS-A, and solver provenance;
- rejection of apparent ICRS and mixed coordinate policies.

Analytic trajectory tests exercise the solver independently of SGP4 and
Astropy. Installed-snapshot tests exercise composition and provenance without
using 50S.4E sampled output as the expected crossing oracle.

Acceptance requires zero missed events for the analytic/adversarial suite,
agreement under materially tighter tolerances, deterministic repeated output,
focused crossing/SGP4/topocentric gates, the complete plugin-disabled suite,
clean diff evidence, and Fernando’s scientific and architectural review.

## 8. Explicit non-goals

50S.5B does not add:

- 50S.6 plane, phase, horizon, occultation, HEALPix, batch, or cache
  acceleration;
- illumination, penumbra, umbra, night, brightness, flare, detector, or
  exposure-overlap science;
- spherical rectangles, WCS/instrument footprints, moving fields, or
  refraction;
- live provider access, catalogue acquisition, retry, cache refresh, or CLI;
- reporting, chart layers, projection, rendering, or export;
- production performance claims from the three-record synthetic snapshot.

## 9. Proposed implementation boundary

After Fernando accepts this audit, only 50S.5B may:

1. add the immutable local query, solver evidence, convergence error, and
   exhaustive oracle in `src/wenu/satellites/crossing_oracle.py`;
2. add intentional package exports only for the supported query/oracle result
   boundary;
3. add `tests/test_satellite_crossing_oracle.py`;
4. update active documentation for the candidate implementation;
5. add no behavior listed in the non-goals.

Acceptance of 50S.5A authorizes 50S.5B only. It does not accept numerical
tolerances in advance, close 50S.5, or authorize 50S.6.
