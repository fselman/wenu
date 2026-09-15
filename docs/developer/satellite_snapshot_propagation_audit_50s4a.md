# 50S.4A local snapshot, propagation, and topocentric contract audit

**Status:** Accepted by Fernando on 2026-09-15
**Audit date:** 2026-09-15
**Wenu baseline:** `ead74169fdcd4aa44a9811394a3dd5b565baa106`

## Purpose

This documentation-only audit freezes the dependency, data, numerical,
coordinate, provenance, and ownership contracts for Wenu's first local
artificial-satellite foundation. It changes no runtime code, dependency, or
packaged data. The scope is deliberately split before implementation because a
catalogue snapshot, SGP4, TEME transformation, topocentric directions, and a
developer specimen builder have different scientific failure modes.

## As-is admission review

Wenu currently has:

- provider-neutral satellite query/candidate/exact-result contracts in
  `satellite_crossings.py`;
- cached SatChecker request/receipt/task/sample normalization in
  `satchecker.py`;
- candidate-only reports and shared-path drawing in
  `satellite_presentations.py` and
  `sky/satellite_candidate_layer.py`;
- Cartesian state vocabulary in `ephemeris.py`;
- governed spherical-coordinate transformation in
  `coordinate_service.py`;
- Astropy and Skyfield dependencies, with `sgp4` present only transitively
  through Skyfield rather than declared as Wenu's direct dependency.

No current owner represents an immutable GP element record, a satellite
catalogue snapshot, a geometric TEME state, an SGP4 propagation receipt, or the
TEME-to-observer chain. These responsibilities must not be placed in the
SatChecker adapter, chart layers, generic coordinate service, or exact crossing
domain.

## Required milestone split

### 50S.4A — this contract audit

Freeze the choices below. No runtime, dependency, fixture, or package-data
change.

### 50S.4B — immutable OMM snapshot and element domain

Add typed OMM/GP element records, snapshot manifest/digest validation, a very
small distributable synthetic geometrical snapshot, installed-resource loading,
and deterministic ordering/duplicate rejection. Add the direct SGP4 dependency
but perform no propagation.

### 50S.4C — validated SGP4/TEME propagation

Map one accepted OMM record explicitly into a Vallado-compatible propagator,
return typed geometric TEME position/velocity, retain error/status and element
age, and validate scalar plus array evaluation against pinned published
reference values. No terrestrial or observer transformation.

### 50S.4D — Earth-orientation and topocentric state chain

Transform typed TEME state through a declared, no-download Astropy
TEME/ITRS/EarthLocation chain and produce observer-relative range, geometric
horizontal direction, and the explicitly selected celestial-direction
representation. Validate against an independent implementation and pathological
observer/time cases. No field intersection.

### 50S.4E — developer specimen builder and closure

Build deterministic network-free propagated track/query specimens from the
small snapshot for later 50S.5 crossing-oracle development. Specimens are
labelled inputs and sampled evidence, not verified exact crossings. Close 50S.4
only after numerical, package, complete-suite, and developer-product acceptance.

## Dependency decision

Wenu will import `sgp4` directly and therefore must declare it directly. Do
not rely on Skyfield's transitive dependency. The proposed requirement is
`sgp4>=2.25,<3`:

- 2.25 added the explicit gravity-constant argument to OMM initialization;
- the current release checked on 2026-09-15 is 2.27;
- the upper bound reserves review for a new major API/model boundary.

The package is the Brandon Rhodes Python wrapper around Vallado's official C++
implementation, falls back to its pure-Python implementation, exposes scalar
and accelerated array evaluation, accepts OMM, returns TEME kilometres and
kilometres per second, and exposes explicit SGP4 status/error codes. Wenu uses
the package API rather than copying or modifying propagation equations.

WGS-72 is mandatory for the initial GP/SGP4 contract. It is passed explicitly
to OMM initialization. WGS-84 is not a modernization of a WGS-72-fitted
element set and must not be selected silently. Improved operation mode is the
upstream default associated with OMM initialization and is recorded in
provenance.

Primary references:

- Python SGP4 project and MIT-licensed source:
  <https://github.com/brandon-rhodes/python-sgp4>
- Python SGP4 package record:
  <https://pypi.org/project/sgp4/>
- Vallado, Crawford, Hujsak, and Kelso, *Revisiting Spacetrack Report #3*,
  AIAA 2006-6753, as linked by the upstream project.

## Canonical OMM/GP element contract

OMM is the canonical Wenu ingestion vocabulary. The typed record retains at
least:

- object name, international designator, full integer NORAD catalogue
  identifier, and classification;
- element epoch as canonical UTC;
- `MEAN_MOTION`, `ECCENTRICITY`, `INCLINATION`,
  `RA_OF_ASC_NODE`, `ARG_OF_PERICENTER`, `MEAN_ANOMALY`, and `BSTAR`;
- `MEAN_MOTION_DOT` and `MEAN_MOTION_DDOT` as retained source fields even
  though SGP4 does not use them;
- `EPHEMERIS_TYPE`, `ELEMENT_SET_NO`, and `REV_AT_EPOCH`;
- `CENTER_NAME=EARTH`, `REF_FRAME=TEME`, `TIME_SYSTEM=UTC`, and
  `MEAN_ELEMENT_THEORY=SGP4`;
- exact source identity, source-record digest, and record provenance.

Angles remain degrees and mean motion remains revolutions per day at the domain
boundary. Unit conversion belongs only to the SGP4 adapter. Unknown, missing,
non-finite, out-of-range, wrong-centre, wrong-frame, wrong-time-system, or
wrong-theory records fail closed.

TLE remains a later optional adapter into exactly this record. No five-column
TLE satellite-number assumption may enter the canonical domain.

The governing message standard is CCSDS 502.0-B-3, *Orbit Data Messages*,
Issue 3, May 2023:
<https://ccsds.org/publications/allpubs/entry/3073/>.
CelesTrak's current GP-format guidance is:
<https://celestrak.org/NORAD/documentation/gp-data-formats.php>.

## Snapshot and redistribution contract

A `SatelliteElementSnapshot` is a deterministic immutable collection of
records plus a manifest. Its content digest is SHA-256 over one canonical JSON
payload that excludes no scientifically relevant field. Record order is full
NORAD catalogue identifier ascending. Duplicate identifiers fail; they are not
resolved silently. The manifest retains schema version, snapshot identifier,
creation/retrieval instant, source identity and URL, source-format identity,
source-byte digest when applicable, record count, software/builder identity,
provider notice/policy URL/check date, provenance, and warnings.

The first packaged snapshot is deliberately **synthetic and non-operational**.
It contains a few hand-authored GP/OMM records spanning LEO, MEO, and
geosynchronous-like regimes and edge geometry needed by later tests. Synthetic
names and identifiers must make it impossible to mistake the records for
current operational predictions. Each record documents how its values were
chosen.

No live CelesTrak, Space-Track, or SatChecker response is committed or
redistributed in 50S.4. CelesTrak now recommends OMM-capable formats because
six-digit catalogue identifiers entered service in July 2026 and asks clients
not to poll more frequently than its two-hour update cadence. Those facts guide
the format and future acquisition policy but do not grant Wenu redistribution
rights. Any later provider-derived packaged snapshot needs an explicit fresh
policy/licensing decision.

The installed snapshot lives below
`src/wenu/data/satellites/snapshots/<snapshot_id>/` and is declared as package
data. Tests must load the installed resource rather than a repository-relative
path. Exact canonical bytes and digest are stable release artifacts.

## Propagation result contract

One immutable `SatelliteTemeState` retains:

- satellite/orbit/snapshot identity;
- evaluation instant in canonical UTC;
- split Julian date components passed to SGP4;
- elapsed days from element epoch;
- geometric TEME position in kilometres;
- geometric TEME velocity in kilometres per second;
- propagator package/version, Vallado implementation identity, WGS-72 gravity
  model, operation mode, and status/error code;
- provenance and warnings.

Time is supplied as split Julian date parts, not one summed modern Julian date,
so later root finding does not inherit a roughly 20-microsecond floating-point
plateau. Scalar and array paths must give the same status and numerical result
within a declared sub-millimetre wrapper tolerance when the accelerated backend
is available. A non-zero SGP4 code is an explicit failed result or exception;
NaNs are never accepted as a valid state.

Element age is reported, never used as a universal hidden cutoff. The initial
warning threshold, if any, is explicit caller policy. No covariance or
confidence interval is inferred.

## TEME, Earth orientation, and observer chain

The SGP4 output is geocentric geometric TEME. It is not ICRS, GCRS, ITRS,
longitude/latitude, AltAz, or topocentric state.

50S.4D uses Astropy's documented satellite chain:

1. construct an Astropy `TEME` Cartesian representation and differential at
   the evaluation UTC instant;
2. transform to geocentric `ITRS` at that instant;
3. construct the observer ITRS position from WGS-84 geodetic longitude,
   latitude, and ellipsoidal height;
4. subtract the observer Cartesian position before any angular conversion;
5. retain the topocentric Cartesian vector and range;
6. rotate/transform into the specifically documented geometric horizontal or
   celestial-direction representation.

Reference:
<https://docs.astropy.org/en/stable/coordinates/satellites.html>.

Astropy IERS automatic download remains disabled. Every result records the EOP
table identity/coverage and UT1−UTC used. An instant outside available coverage
fails closed; degraded accuracy is never enabled silently. Refraction is off.
Polar motion is retained through the governed transformation and is not
discarded by a hand-written Greenwich-angle shortcut.

The final celestial-direction vocabulary requires numerical review in 50S.4D.
It must distinguish an instantaneous geometric topocentric vector expressed in
celestial axes from Astropy apparent/astrometric catalogue semantics. It may
not call an aberration-bearing result “geometric ICRS” merely because its axes
are ICRS-oriented.

## Numerical validation contract

50S.4C uses pinned Vallado reference cases covering at least near-Earth and
deep-space branches, non-zero and error statuses, positive and negative epoch
offsets, scalar and array calls, and split-date sensitivity. Expected vectors,
source citation, upstream version, units, tolerance, and copied-data licensing
are recorded. Wenu validates its mapping and wrapper; it does not claim an
independent reimplementation of SGP4.

50S.4D adds an independent transformation oracle. At minimum:

- compare Wenu against a separately expressed Astropy reference construction;
- compare selected cases with Skyfield or another maintained independent
  high-level chain while documenting convention differences;
- verify observer subtraction and range directly in Cartesian space;
- cover equator, La Ligua, near-pole, antimeridian, overhead/near-zenith,
  horizon-near, RA wrap, LEO, MEO, and geosynchronous-like cases;
- pin local EOP identity and test fail-closed out-of-coverage behavior;
- state angular, position, velocity, range, and time tolerances before results
  are inspected.

Agreement between two paths using the same hidden inputs is not independent
evidence. Each oracle records shared dependencies and the remaining limitation.

## Developer specimen builder

The 50S.4E builder is explicit, deterministic, network-free, and writes only
to a caller-selected output directory. It records snapshot digest, record
identity, evaluation grid, observer, EOP identity, propagator identity, and
software version.

It may construct geometrically useful sampled tracks and query intervals for
50S.5 development. It must label them **propagated sampled specimens — not
verified crossings**. It cannot emit `SatelliteCrossingResult`, claim complete
catalogue search, choose production solver tolerances, or become a hidden
crossing oracle.

## Ownership proposed after acceptance

A small `src/wenu/satellites/` package is now justified because snapshot,
element, propagation, topocentric, and specimen responsibilities form several
collaborating production/developer modules:

- `satellites/elements.py` — typed canonical OMM/GP records;
- `satellites/snapshots.py` — manifest, digest, installed loading;
- `satellites/sgp4.py` — OMM-to-propagator mapping and typed TEME states;
- `satellites/topocentric.py` — declared Earth-orientation/observer chain;
- `tools/build_50s4_satellite_specimens.py` — developer-only specimen output.

Existing `satchecker.py`, `satellite_crossings.py`, reporting/drawing,
generic ephemeris, coordinate, chart, renderer, semantic, and export owners do
not absorb these responsibilities.

## Ordinary and milestone gates

All ordinary tests are network-free and disable IERS downloads. Each bounded
step has focused unit and documentation gates. Snapshot packaging is tested
from an installed build. Numerical tests cover both the accelerated and
pure-Python SGP4 availability contract without requiring acceleration.

50S.4 closes only after:

- exact package-data/digest verification;
- pinned Vallado wrapper validation;
- independent topocentric numerical validation;
- deterministic specimen-builder output;
- focused and complete plugin-disabled suites;
- Fernando's inspection of the manifest, numerical report, and specimens.

## Acceptance

Fernando accepted this contract as 50S.4A on 2026-09-15 after the focused
documentation gate passed all 128 tests and the branch diff check was clean.
Acceptance closes 50S.4A and authorizes only 50S.4B immutable OMM element and
snapshot work. It does not authorize propagation, topocentric transformation,
a crossing solver, or 50S.5.


## Candidate 50S.4B implementation evidence

The dedicated 50S.4B branch implements the accepted immutable element and
snapshot boundary: strict canonical OMM/GP records, a versioned manifest,
canonical-byte and per-record SHA-256 validation, full-NORAD ordering,
duplicate rejection, immutable lookup, installed-resource loading, and three
hand-authored synthetic non-operational LEO/MEO/geosynchronous-like records.
It declares `sgp4>=2.25,<3` directly but imports or invokes no propagator.

The initial focused element, package-boundary, and packaged-configuration gate
passed all 29 tests. At production commit `d3cb597`, the expanded focused gate
passed all 158 tests and the complete plugin-disabled suite passed all 2,483
tests in 87.11 seconds.

A wheel from the same production commit was installed into an isolated virtual
environment. The snapshot loaded from the installed `site-packages` tree,
verified content digest
`b6ab95df3eb180b07694b1b9bafd47c2805b6cc7ebea8636490beec03cd71457`,
reported three records, and preserved ordered full identifiers 900001, 900002,
and 900003. The first no-dependency import and a second inherited-environment
import exposed unrelated NumPy absence and a broken external `spiceypy`
shared library; a package-local import isolated and passed the installed
satellite-resource boundary.

Propagation, TEME state generation, Earth-orientation and observer
transformation, acquisition, exact crossings, and presentation remain absent.
Fernando accepted the scientific and architectural boundary on 2026-09-15.
This closes 50S.4B and authorizes only 50S.4C validated SGP4/TEME propagation.
It does not authorize Earth-orientation/topocentric transformation, specimen
construction, a crossing solver, or 50S.5.


## Candidate 50S.4C implementation evidence

The dedicated 50S.4C branch maps immutable canonical OMM records through the
upstream Vallado-compatible API with explicit WGS-72 and improved operation
mode. It supplies split Julian-date components, converts only declared OMM
units, raises non-zero SGP4 statuses, and returns immutable successful
geocentric geometric TEME position/velocity with complete identity, version,
backend, time, element-age, and provenance fields.

Preflight found that the original synthetic identifiers 900001–900003 exceeded
the upstream `Satrec` maximum 339999. They were corrected openly to
300001–300003; all three source-record digests and the snapshot content digest
were regenerated. No hidden internal satellite identity is permitted.

Pinned AIAA 2006-6753/Vallado verification vectors cover the near-Earth and
deep-space branches at epoch. The upstream case 44160 validates a non-zero
terminal status, and scalar/array evaluation has a sub-millimetre parity gate.
The initial satellite element/SGP4 gate passed all 15 tests. Expanded,
complete-suite, and documentation gates remain pending. No terrestrial or
observer transformation is included.
