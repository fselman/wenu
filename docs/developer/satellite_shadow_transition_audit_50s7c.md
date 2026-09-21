# 50S.7C shadow-transition audit

**Status:** Candidate documentation-only scientific and architectural audit

**Audit date:** 2026-09-21

**As-is program base:** `f9aa2dd7e7d197f015b0df7667c1fd5804e99428`

**Scope:** Complete bounded search for direct-solar shadow-class transitions
under the accepted uniform finite-Sun/WGS-84 vacuum model. This audit changes
no runtime and authorizes no implementation before Fernando's separate
scientific and architectural acceptance.

## 1. Decision summary

50S.7C should add one output-neutral, observer-independent event service for
the boundaries between the accepted `sunlit`, `penumbra`, `umbra`, and
`antumbra` states. A future immutable `SatelliteShadowTransition` binds:

- the left and right `SolarOccultationClass` values;
- a typed transition kind;
- one canonical UTC event instant;
- a closed UTC bracket containing the contact;
- the declared time tolerance and achieved bracket width;
- the complete satellite, orbit solution, snapshot, propagation,
  Earth-orientation, ephemeris, Earth/Sun shape, shadow-model, and search-policy
  identity; and
- deterministic evaluation counts, provenance, and warnings.

A contact instant is an event, not a fifth occultation state. The two certified
open sides of the bracket determine the transition classes. The result makes
no brightness, visibility, detectability, detector, facility, or scheduling
claim.

The first implementation after acceptance must remain bounded. It searches one
selected immutable snapshot record over one non-empty closed UTC interval,
uses the accepted SGP4/TEME, installed-IERS-A, and installed-ephemeris route,
and returns every admitted transition in chronological order or fails closed.
It does not search a catalogue, alter a geometric crossing, or attach events
to a report or chart.

## 2. As-is assessment

Accepted 50S.7B already provides:

- `SolarOccultationPolicy` with the finite uniform solar disk, vacuum WGS-84
  ellipsoid, nominal solar radius, contact tolerance, and bounded quadrature;
- same-instant Earth-to-Sun and satellite vectors in ITRS;
- typed `sunlit`, `penumbra`, `umbra`, and `antumbra` geometry;
- a converged visible-disk fraction with explicit quadrature evidence;
- stable illumination failure codes and complete resource provenance; and
- offline analytic, SPICE, Skyfield, and Astropy validation evidence.

The accepted propagation and topocentric route can evaluate a selected
snapshot record at arbitrary UTC instants and fails closed on propagation or
Earth-orientation failure. The 50S.5 crossing oracle demonstrates useful
bounded-cache, adaptive-subdivision, root-bracketing, deterministic ordering,
and terminal-budget patterns. Its angular FoV function, motion envelope,
connected-visit merging, and result type are not shadow-contact algorithms and
must not be copied as scientific truth.

No current owner finds shadow contacts. Chart samples, exact-track samples,
crossing entry/exit times, report rows, SatChecker flags, and planning
advisories are not transition evidence.

## 3. Continuous contact geometry

### 3.1 Why visible fraction is not the root function

The accepted visible fraction is computed by deterministic finite ray
quadrature. Near a contact it changes in discrete sample increments. Its
numerical convergence tolerance certifies the reported fraction, not a smooth
zero or a contact time. Root-finding that fraction, a ray count, or the
`SolarOccultationClass` enum would make event time depend on quadrature
resolution and could miss a narrow penumbra interval.

The future event search must therefore use continuous signed contact geometry
derived from the same satellite-to-Sun direction, finite solar
angular radius, and forward WGS-84 ellipsoid silhouette. The contact evaluator
must expose enough independent signed margins to distinguish:

- exterior contact: `sunlit <-> penumbra`;
- interior containment with Earth outside the solar disk:
  `penumbra <-> umbra`; and
- interior containment with the Earth silhouette inside the solar disk:
  `penumbra <-> antumbra`.

The margins use the exact accepted shape constants and common-frame vectors.
They are event-search internals, not a replacement radiometric model. The
reported visible fraction remains the accepted bounded adaptive quadrature.

### 3.2 Class coherence and equality

Away from the declared contact tolerance, continuous topology and the public
occultation class must agree. 50S.7C may refactor the internal class decision
from quadrature ray counts to the continuous topology, while retaining the
accepted public class meanings and fraction calculation.

At equality, the event owns the contact. A regular geometry state sampled
exactly at that time does not create a new class and must not be used to infer
both sides. The solver evaluates certified side instants separated from the
contact by its time/geometry tolerances. Sub-tolerance perturbations must not
produce alternating event kinds or duplicate contacts.

## 4. Query, policy, and result contract

A future immutable `SatelliteShadowTransitionQuery` should contain:

- one validated `SatelliteElementSnapshot`;
- exactly one full NORAD catalogue identifier present once in that snapshot;
- one `InclusiveTimeInterval` in canonical UTC;
- one `SolarOccultationPolicy`; and
- one `ShadowTransitionSearchPolicy`.

The search policy names its algorithm and declares a positive time tolerance,
a positive contact-function tolerance, a maximum interval duration, maximum
subdivision depth, maximum state evaluations, and maximum returned events.
Every limit is finite, validated before scientific evaluation, and retained in
result identity.

`SatelliteShadowTransition` should retain the exact record and snapshot
identity rather than only a display name. Its bracket endpoints are canonical
UTC, ordered, inside the query interval, and no wider than the declared time
tolerance. The representative event instant is the deterministic midpoint of the final
certified closed UTC bracket; it is not claimed to be exact beyond that
bracket.

Transition kinds are directed and closed:

- `sunlit_to_penumbra`;
- `penumbra_to_sunlit`;
- `penumbra_to_umbra`;
- `umbra_to_penumbra`;
- `penumbra_to_antumbra`; and
- `antumbra_to_penumbra`.

Direct `sunlit <-> umbra`, `sunlit <-> antumbra`, or
`umbra <-> antumbra` outputs are invalid because a finite-source continuous
path must pass through penumbra or represents unresolved simultaneous
contacts. A genuine simultaneous/degenerate contact outside the admitted
topology fails closed rather than inventing an ordering.

An empty tuple is a valid result only after the complete interval is certified
transition-free. It is never a fallback for uncertainty or exhausted work.

## 5. Observer-independent state seam

Earth shadow is independent of an observing site. The accepted
`SatelliteTopocentricTransformer` currently performs the governed
TEME-to-ITRS transformation and then continues through observer subtraction
and angular conversion. A transition search must not construct a dummy
observer or let observer identity alter a physical shadow event.

Before or within the bounded implementation, extract the smallest shared
observer-independent geocentric Earth-fixed state seam from
`satellites/topocentric.py`. It should transform one accepted
`SatelliteTemeState` into immutable same-instant satellite ITRS position and
velocity plus the exact `SatelliteEarthOrientationEvidence`. The existing
topocentric route and the transition evaluator must both compose that one seam;
there must be no second TEME/EOP implementation.

This is a responsibility-preserving extraction, not a new coordinate model.
The public instant remains UTC, Earth rotation remains installed-IERS-A
UT1/polar-motion work, and the Sun ephemeris retains its internal TDB and SPK
identity. The transition result contains no observer and no twilight class.

## 6. Complete bounded search

The solver searches the complete closed query interval and must detect every
admitted class boundary, including ingress and egress wholly between two
initial samples. A fixed cadence plus sign-change scan is insufficient.

The accepted algorithmic contract is:

1. validate the complete query and all resource coverage before returning
   scientific results;
2. evaluate and cache deterministic propagated, Earth-fixed, Sun, and signed
   contact states by exact UTC instant;
3. recursively isolate intervals using continuous contact margins and a
   documented conservative whole-interval exclusion bound;
4. retain any interval whose exclusion is not certified, including equality,
   non-monotonic samples, possible double roots, or competing contact margins;
5. refine each isolated contact to the declared time and geometry tolerances;
6. classify certified left and right sides, map them to one permitted directed
   kind, and reject inconsistent topology;
7. sort chronologically and deduplicate only contacts whose certified brackets
   overlap and whose directed kind and side evidence agree; and
8. certify the remaining portions of the closed interval transition-free
   before returning, including an empty result.

The first implementation must document the conservative exclusion bound and
its admitted orbital/interval domain. If a defensible bound cannot be
established for an interval, that interval is unsupported and the service
fails closed. Sampled curvature heuristics, chart interpolation, and the 50S.5
empirical motion envelope are not conservative shadow-contact exclusions.

Endpoints are included. A transition exactly at the requested start or stop is
returned with a one-sided interval-boundary certificate plus the available
interior side; its missing exterior class is obtained only when the query
explicitly supplies an admitted adjacent evaluation interval. If the directed
kind cannot be certified from the requested domain, the query fails closed.
The implementation audit may instead choose to reject endpoint contacts
explicitly; it may not silently omit them.

## 7. Failure, ordering, and identity

50S.7C continues to use `SatelliteIlluminationGeometryError` with stable
illumination-domain codes. The implementation must distinguish at least:

- invalid or unsupported query/search policy before scientific work;
- record or snapshot identity mismatch;
- propagation failure;
- Earth-orientation unavailable or outside coverage;
- ephemeris coverage unavailable;
- frame mismatch or non-finite geometry;
- unsupported or degenerate shadow topology;
- contact-bracket inconsistency;
- transition-search budget exhaustion; and
- quadrature non-convergence when a retained event-side geometry is produced.

The existing `transition_search_exhausted` code remains the terminal budget
failure. Additional stable codes may be added for topology and bracket
failures; messages alone are not machine contracts.

Results are ordered by bracket start, bracket stop, transition kind, and full
NORAD identifier. Duplicate output is forbidden. Search identity includes the
complete query, orbit/snapshot/resource identities, shadow and search
policies, implementation identifier, tolerances, limits, and achieved counts.
A policy, resource, or model change changes identity.

No partial tuple is returned after any terminal failure. Cached values are
local to one call and cannot leak between records, queries, ephemeris sources,
or resource versions.

## 8. Ownership and dependency direction

The closest production owner is
`src/wenu/satellites/illumination.py`. The transition query, policy, signed
contact evaluator, bounded search, result, failures, identity, and provenance
share the same direct-Sun model, dependencies, and reason to change as 50S.7B.
File size alone does not justify a new module.

The minimal geocentric Earth-fixed extraction remains in
`src/wenu/satellites/topocentric.py`, because that module already owns
TEME-to-ITRS and installed Earth-orientation evidence. Propagation remains in
`satellites/propagation.py`; ephemeris state remains in the existing
provider-neutral ephemeris owner.

`tests/test_satellite_illumination.py` remains the enduring scientific and
failure-boundary test file. Extend it rather than creating a milestone-named
test file. A separate offline
`tools/validate_50s7c_shadow_transitions.py` may own independent installed-
resource event comparisons and must refuse downloads.

No chart, exact-track, crossing, report, CLI, planning-advisory, renderer, or
export module imports the transition service in 50S.7C.

## 9. Validation and acceptance gates

### 9.1 Analytic and synthetic evidence

Focused tests must cover:

- no-transition full-light and full-shadow intervals;
- exterior ingress and egress;
- penumbra-to-umbra and umbra-to-penumbra interior contacts;
- admitted antumbra ingress and egress synthetic geometry;
- two transitions strictly between initial samples;
- an interval starting or ending at contact under the chosen endpoint rule;
- grazing/tangent and near-simultaneous contacts;
- chronological ordering and no duplicates;
- agreement between event-side classes and ordinary geometry evaluation;
- time/contact tolerances, exact bracket containment, and deterministic
  midpoint selection;
- maximum duration, depth, evaluation, and event budgets;
- propagation, EOP, ephemeris, frame, non-finite, degenerate-topology, and
  quadrature failures;
- immutable identity and cache isolation; and
- proof that observer choice is absent from event identity.

Spherical special cases should have independently computed analytic contact
times. Oblate WGS-84 cases must exercise equatorial, polar, and grazing limb
orientations. LEO, MEO, GEO, and highly elliptical synthetic states belong to
the evidence even if the first runtime domain is narrower and fails closed for
some of them.

### 9.2 Independent event oracles

The controlled offline validator must compare selected full/partial/annular
transition times and directed sequences against an independently executed
SPICE `gfoclt` or Orekit eclipse detector. It pins exact versions, kernels,
Earth/Sun shapes, frames, time scales, input states, aberration settings,
step/search policies, tolerances, and receipts.

The validator also checks selected binary sides with Skyfield
`is_sunlit()`, while recognizing that Skyfield is not an oracle for partial
disk fraction or all transition kinds. Production must not import SPICE,
Orekit, or Skyfield to reproduce the oracle.

Acceptance requires the focused illumination/topocentric/propagation gate,
current-documentation gate, complete plugin-disabled suite, diff check, exact
head/upstream, clean tree, and Fernando's scientific review of the independent
event receipt. Every result is tied to the exact executable commit.

## 10. Explicit exclusions

This audit and the possible first implementation add no:

- transition attachment to crossings, tracks, reports, charts, CLI files, or
  planning advisories;
- observer twilight-transition search;
- Moon-as-solar-occultor evaluation;
- atmospheric transmission, refraction, terrain, or clouds;
- solar or lunar irradiance and no spectral/passband quantity;
- solar Earthshine, Moonlight radiometry, or Lunar-Earthshine field;
- spacecraft attitude, shape, projected area, BRDF, magnitude, or glint;
- visibility, detectability, detector effect, facility integration, or
  scheduling decision;
- network access, acquisition, implicit ephemeris download, or new package
  resource; or
- change to accepted geometric crossing identity or result membership.

50S.7D and later illumination work, 50S.8 brightness, and 50S.9 detector work
remain unauthorized.

## 11. Recommendation and authorization boundary

Adopt the continuous-contact, observer-independent, complete bounded event
contract above. Acceptance of this document would authorize only a separately
reviewed 50S.7C implementation in the existing illumination owner plus the
minimal shared geocentric ITRS extraction, focused tests, and one offline
independent event validator.

This candidate audit itself authorizes no runtime, merge, branch deletion, or
50S.7D+ work. Fernando's separate scientific and architectural acceptance is
required before implementation begins.
