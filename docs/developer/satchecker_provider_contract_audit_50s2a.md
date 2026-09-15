# SatChecker provider-contract audit (Milestone 50S.2A)

**Status:** Candidate audit for Fernando's scientific and architectural review
**Audit date:** 2026-09-15
**Wenu baseline:** `06c05a2994683e8ac8f04abf0a1480a0abeb566e`
**Provider source reviewed:** SatChecker 1.8.0, commit
`a638d72b67c7d93de043e47e6156d54474f377d6`

## 1. Decision

Split the former 50S.2 milestone into this provider-contract audit and a
separately reviewed adapter implementation. This audit changes no runtime code.

50S.2B may implement a policy-compliant cached SatChecker adapter, but it must
normalize successful provider output only to `SatelliteCrossingCandidate` plus
provider-sampled evidence. It must not construct `SatelliteCrossingResult`.
SatChecker returns sampled candidate points, not verified entry, closest-
approach, and exit events, and currently admits points within 1.2 times the
requested circular-FoV radius. Exact connected visits remain Wenu's 50S.5 local
oracle responsibility.

## 2. Official evidence reviewed

The review used the official SatChecker documentation and the tagged source
state represented by the commit above:

- [SatChecker documentation](https://satchecker.readthedocs.io/en/latest/);
- [field-of-view endpoint documentation](https://satchecker.readthedocs.io/en/latest/fov.html);
- [SatChecker source repository](https://github.com/iausathub/satchecker);
- [FOV route source](https://github.com/iausathub/satchecker/blob/a638d72b67c7d93de043e47e6156d54474f377d6/src/api/entrypoints/v1/routes/fov_routes.py);
- [FOV service source](https://github.com/iausathub/satchecker/blob/a638d72b67c7d93de043e47e6156d54474f377d6/src/api/services/fov_service.py);
- [propagation source](https://github.com/iausathub/satchecker/blob/a638d72b67c7d93de043e47e6156d54474f377d6/src/api/utils/propagation_strategies.py);
- [release history](https://github.com/iausathub/satchecker/blob/a638d72b67c7d93de043e47e6156d54474f377d6/changes.md);
- [software licence](https://github.com/iausathub/satchecker/blob/a638d72b67c7d93de043e47e6156d54474f377d6/LICENSE);
- [README licensing statement](https://github.com/iausathub/satchecker/blob/a638d72b67c7d93de043e47e6156d54474f377d6/README.md).

No successful live specimen response was obtained during this audit. The
implementation must therefore validate one bounded live request separately
before acceptance; ordinary tests remain network-free.

## 3. Request mapping

The adapter uses the versioned `/v1/fov/satellite-passes/` endpoint and the
returned task identifier with `/v1/fov/task-status/<task_id>`. The service
base URL remains configurable and the exact resolved URLs are provenance.

The 50S.1 request maps as follows:

| Wenu meaning | SatChecker parameter and policy |
| --- | --- |
| observer | explicit `latitude`, `longitude`, and `elevation`; do not substitute an implicit site |
| closed UTC interval | `start_time_jd` plus `duration`; conversion policy is recorded as described below |
| circular field centre | `ra`, `dec`, and `fov_radius` in degrees |
| response grouping | `group_by=satellite` |
| orbit evidence | `include_orbital_data=true` and `convert_omm_to_tle=false` |
| geometric completeness | `illuminated_only=false` |
| catalogue scope | no constellation restriction; `data_source=any` unless the caller explicitly requests a supported source |
| execution | `async=true` |

Native OMM must remain OMM. Converting OMM to generated TLE text would weaken
the orbit-source identity. Provider illumination may be retained as evidence,
but it must not remove geometric candidates.

## 4. Time and coordinate semantics

The public endpoint calls its input a Julian Date without declaring a time
scale. The reviewed route constructs Astropy `Time(..., scale="ut1")`, and the
propagation path uses Skyfield UT1 Julian dates. Wenu's interval is UTC.
50S.2B must perform an explicit UTC-to-UT1 conversion under a declared
Earth-orientation-data policy, retain both representations, and never trigger a
hidden IERS download. A missing or out-of-validity Earth-orientation resource
is a bounded failure, not permission to relabel UTC as UT1.

The provider source forms a one-second grid with `numpy.arange`. Both the
start-time and midpoint forms exclude the computed stop endpoint. This is a
provider sampling interval, not Wenu's inclusive interval. The adapter records
the returned sample instants exactly and must not invent the omitted endpoint.

Returned right ascension and declination are observer-relative geometric
topocentric directions on ICRF/ICRS-oriented axes in the reviewed propagation
implementation. They are not observed/apparent directions and carry no
refraction correction. Because the public documentation does not fully state
this distinction, the normalized evidence must mark the semantics as inferred
from provider source at the reviewed commit.

## 5. Candidate envelope and normalization

SatChecker 1.7 changed angular separation to great-circle geometry and added a
20 percent FoV margin for uncertainty. Consequently:

- a returned point can lie outside Wenu's closed requested FoV;
- absence between one-second samples is not a proof that no crossing occurred;
- a sample on the provider envelope is not a Wenu boundary event;
- provider grouping does not prove one connected visit.

For each uniquely identified object, 50S.2B may create a
`SatelliteCrossingCandidate` carrying the observer, field, inclusive UTC
query interval, provider identity, orbit/snapshot evidence when supplied,
warnings, and normalized provider provenance. A separate immutable sampled-
evidence contract may retain ordered provider points, angles, range, altitude,
azimuth, illumination, orbital epoch/source, and provider fields whose meaning
is documented. Unknown fields remain available in the exact raw receipt but
must not silently acquire Wenu semantics.

NORAD catalogue number and provider `object_id`, when both exist, are retained
without truncation. Conflicting identities, missing stable identity, nonfinite
coordinates, out-of-query sample times, or inconsistent grouping fail
normalization explicitly.

## 6. Async state machine and access policy

Submission and polling are separate adapter operations. Submission accepts the
initial `PENDING` response, or an immediate `SUCCESS` response when no
catalogue rows exist. Polling recognizes `PENDING`, `PROGRESS`, `SUCCESS`,
`FAILURE`, and `ERROR`; every other state is a schema-drift failure.
`PROGRESS` retains the provider's numeric progress when valid.

The provider publishes limits of 50 FOV submissions per second and 1,000 per
minute, and 100 task-status requests per second and 2,000 per minute. Wenu uses
serial access far below those ceilings: no parallel submissions, no automatic
retry, and no hidden polling loop. Any convenience waiter must require an
explicit poll interval, timeout, and maximum poll count, expose progress, and
remain cancellable. HTTP non-success, timeout, transport failure, malformed
JSON, task-ID mismatch, provider `FAILURE` or `ERROR`, invalid progress, and
unknown state are distinct bounded failures.

## 7. Exact cache and provenance

The cache key is a canonical serialization of the resolved provider/versioned
endpoint, all transmitted parameters, the original Wenu request, the
UTC-to-UT1 conversion and Earth-orientation identity, and adapter schema
version. It is not merely a hash of the geometric query.

The cache stores immutable exact response bytes for submission and every poll,
with SHA-256, retrieval instant, HTTP status, media type, relevant response
headers, task ID, provider-reported API source/version, and the normalized
interpretation. A hit is usable only when all identities and hashes validate.
Corrupt, partial, mismatched, or obsolete-schema entries fail closed. Provider
server caching does not replace this Wenu-owned exact cache.

SatChecker software is BSD-3-Clause, while the README also applies CC BY 4.0
language to “this work.” That does not establish redistribution terms for
provider response data. Exact response bytes may be retained in a user's local
cache, but they must not be committed, packaged, or redistributed until their
data licence is clarified. Ordinary tests use synthetic source-shaped
specimens; a live acceptance response stays local and is identified by digest.

## 8. Failure and non-goal boundary

50S.2B does not add SGP4, TEME state, local orbit acquisition, exact crossing
solution, illumination physics, brightness, reports, charts, projection,
rendering, or export. It must not make a live service an import-time,
construction-time, or ordinary-test dependency.

This audit authorizes no implementation until Fernando accepts the request
mapping, UTC-to-UT1 policy, candidate-only normalization, async access policy,
cache identity, and response-data redistribution boundary.
