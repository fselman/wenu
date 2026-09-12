# Comet numerical validation audit (Milestone 50A.4)

**Status:** Candidate for Fernando's review

**Base:** `7b72f36`

**Date:** 2026-09-12

**Runtime effect:** None

## 1. Purpose

50A.4 validates the existing generic minor-body state and direction machinery
with a comet nucleus. It must demonstrate that the selected orbit solution's
non-gravitational model survives acquisition, resource binding, state
evaluation, and validation provenance without being discarded or applied a
second time. It adds no drawable comet and changes no chart output.

## 2. Accepted-practice evidence

The governing 50A.0 audit remains authoritative. The current JPL SBDB API
documents distinct numbered- and unnumbered-comet identities, orbit-solution
identifiers, alternate comet orbits, TDB osculating epochs, J2000 ecliptic
elements, and `model_pars` for orbit-determination parameters. Horizons
provides bounded SPKs plus independent vector and observer-table products.

The numerical oracle is therefore a frozen direct-Horizons response, not a
second Wenu evaluation and not a local two-body orbit. SPK and table products
share JPL's dynamical solution, so this validates Wenu ingestion, centre
composition, time scale, light time, apparent place, and topocentric parallax;
it is not an independent rederivation of JPL's comet dynamics.

Primary references:

- [JPL SBDB API](https://ssd-api.jpl.nasa.gov/doc/sbdb.html);
- [JPL Horizons API](https://ssd-api.jpl.nasa.gov/doc/horizons.html);
- [Marsden, Sekanina & Yeomans (1973)](https://doi.org/10.1086/111402),
  the Style-II non-gravitational model already adopted by 50A.0.

## 3. Acceptance specimen

Use periodic comet **2P/Encke** as the bounded acceptance specimen. Its short
period and recurrent activity make non-gravitational solution provenance
material, while `2P` is an exact numbered-comet designation rather than a
fuzzy name. The acquisition must resolve `2P` unambiguously in SBDB and use
the corresponding explicit Horizons small-body command ending in `;`.

Freeze the solution returned at acquisition time; do not encode a mutable
"latest" solution in source. The evidence must preserve:

- primary designation, full name, numbered-comet kind, prefix, and SPK ID;
- orbit ID, solution date/source/producer, observation arc, fit RMS, planetary
  and small-body perturbing ephemerides, and validity fields;
- osculating epoch, reference equinox, elements, covariance when available,
  alternate orbit identities, and every returned model parameter;
- exact Horizons/SBDB query parameters, API signatures/versions, retrieval
  time, filenames, byte counts, and SHA-256 digests.

The accepted solution must declare comet non-gravitational model parameters.
At minimum the evidence records every returned `A1`, `A2`, `A3`, or `DT`
parameter with value, units, uncertainty, and whether it was estimated. A
missing or ambiguous model record is a stop condition, not permission to call
the orbit gravity-only.

## 4. Numerical matrix

Acquire one bounded type-21 SPK covering 2026-10-01 through 2027-06-01. Freeze
three UTC observer epochs spanning the approach, perihelion neighbourhood, and
recession; the acquisition tool may refine the middle date to the provider's
frozen perihelion epoch before the fixture is accepted.

At every epoch compare:

1. geometric barycentric ICRF position and velocity at the same TDB instant;
2. geocentric astrometric ICRS RA/Dec, distance, and light time;
3. geocentric apparent ICRS RA/Dec;
4. topocentric astrometric and apparent ICRS RA/Dec at La Ligua;
5. topocentric distance and the measured geocentric-to-topocentric parallax.

Use the established La Ligua coordinates and DE440 resource identity from
50A.2. The comet SPK target relative to its declared centre is composed with
the planetary resource before the ordinary iterative light-time and apparent-
place realizers run. UTC observation, TDB state evaluation, SPK coverage,
osculating epoch, and product coordinates remain distinct.

## 5. Tolerances and model discrimination

Run the validator first in an explicit `--characterize` mode and record maximum
residuals without claiming acceptance. Set enforced tolerances from those
residuals, numerical precision, and the already accepted 50A.2 envelope; never
loosen a threshold merely until a failing implementation passes.

The frozen fixture must state whether removal of the non-gravitational model
is material over the selected interval. If Horizons exposes a corresponding
gravity-only alternate solution, acquire its direct table only as a diagnostic
and record the separation from the accepted solution. It must not become a
fallback resource or a second accepted orbit. If no comparable alternate is
available, the audit requires provenance survival but makes no invented
quantitative claim about the model's isolated contribution.

## 6. Implementation slice after acceptance

1. add a deliberate networked acquisition tool for the exact `2P` evidence;
2. freeze a compact JSON oracle and acquisition report, not a generated chart;
3. add a comet validator by reusing the 50A.2 state/direction comparison
   machinery rather than duplicating coordinate mathematics;
4. verify that `MinorBodySolutionIdentity.object_class == "comet"` and that
   model parameters and quality fields survive every result;
5. run focused provider, direction, resource, and documentation tests, then
   the complete suite;
6. record the exact Mac commands, environment, residual maxima, and evidence
   digests before acceptance.

Any refactoring shared with the asteroid validator must preserve its frozen
50A.2 oracle and tolerances unchanged. Tests use frozen local evidence and
must never contact SBDB or Horizons.

## 7. Explicit non-goals

50A.4 does not add `--comet`, `--comet-track`, `--center-on comet:...`, comet
preflight acquisition in `wenu_chart`, a descriptor or catalog registration,
symbol, label, track, magnitude, coma, tail, photocentre, activity model,
visibility selection, orbital-element propagator, or renderer/export change.
Those public and visible concerns begin only after numerical acceptance, in
50A.5 or a separately accepted audit.

## 8. Stop conditions

Stop if `2P` is ambiguous, the selected solution does not expose its
non-gravitational model, the SPK and direct tables cannot be tied to the same
solution, the provider changes schema unexpectedly, the required interval is
outside meaningful validity, or the resource chain cannot preserve all model
and dependency identities. Do not substitute another orbit or silently reduce
the physics.
