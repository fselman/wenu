# 50S.6H observatory-planning adapter audit

**Status:** Accepted documentation-only architecture and interface audit.

**Accepted by Fernando:** 2026-09-20.

**Base:** accepted complete 50S.6G at merge commit
`e37298db29af84bd92443287ae1574cf471b76e8`.

**Research date:** 2026-09-20.

**Runtime effect:** None. This audit adds no adapter, network client, credential
handling, observatory write, scheduling decision, illumination model, or
brightness model.

## 1. Decision

The next authorized implementation may add one deterministic, offline
observatory-planning projection downstream of the accepted
`ExactSatelliteCrossingReport`. The projection is advisory evidence for a
human planning workflow. It is not an observing-block format, a scheduler, or
an observatory API binding.

The first authorized implementation slice shall produce only
an observatory-neutral document. Paranal and other facility profiles may
validate supplied planning context and label the projection, but shall not
contact a facility. No ELT-specific payload is admitted until ESO publishes a
stable operational preparation interface and a later audit accepts its
versioned contract.

## 2. Official interface findings

The sources below were inspected on the research date.

| Source | Finding | Architectural consequence |
|---|---|---|
| [ESO Phase 2 preparation](https://www.eso.org/sci/observing/phase2.html) | Observation Blocks (OBs) are the backbone of ESO observations; Paranal uses p2 and La Silla uses p2ls. | Wenu must not claim that its accepted JSON, ECSV, or VOTable report is an ESO OB. |
| [ESO p2 tool](https://www.eso.org/sci/observing/phase2/p2intro.html) | p2 is the required web application for Paranal Phase 2 material. | A Paranal profile is a downstream planning aid, not a replacement preparation path. |
| [ESO Phase 2 API](https://www.eso.org/sci/observing/phase2/p2intro/Phase2API.html) | The JSON API can create, modify, or delete OBs and containers, and changes are immediately stored in ESO's database. ESO directs tests to its demo server. | Network and mutation are a separate security and operations milestone. They are prohibited here and in the first implementation slice. |
| [ESO p2 API Python tutorial](https://www.eso.org/sci/observing/phase2/p2intro/Phase2API/api--python-programming-tutorial.html) | OB content is instrument-specific; resources use version values for concurrency; the API includes target, constraint, time-window, template, verification, and status operations. | Wenu shall neither guess instrument fields nor bypass facility concurrency, verification, and status rules. |
| [ESO observing constraints](https://www.eso.org/sci/observing/phase2/SMGuidelines/ConstraintsSet.html) | Users set scientific constraints at Phase 2, including Moon, airmass, image quality, transparency, twilight, absolute time, and sidereal-time limits. | A satellite overlap is not an ESO observing constraint. Wenu shall not rewrite or tighten OB constraints. |
| [ESO time-critical policy](https://www.eso.org/sci/observing/phase2/SMPolicies/TimeCriticalOBfailure.html) | Absolute windows express scientific usefulness and affect ranking and expiry; changes require scientific judgment. | Wenu shall not convert satellite avoidance into absolute time constraints or scheduling priority. |
| [ESO ELT timeline](https://elt.eso.org/about/timeline/) | Telescope first light is planned for 2029 and scientific first light for December 2030. | No current ELT operational adapter contract is inferred from Paranal p2. |
| [IVOA VOTable 1.5](https://www.ivoa.net/documents/VOTable/) | VOTable is a transport format for tabular data. | Accepted VOTable remains interoperable evidence, not a scheduling command protocol. |
| [IVOA ObsCore](https://www.ivoa.net/documents/ObsCore/) | ObsCore standardizes discovery metadata for observations. | ObsCore is not adopted as an observing-plan or scheduler-write schema. |

The absence of a published ELT operations interface in these sources is not
evidence that ELT will lack one. It is a reason to leave the profile
unimplemented and require a fresh source review.

## 3. Preserved Wenu authorities

The accepted report remains the sole scientific source of truth. An adapter
must consume `ExactSatelliteCrossingReport` after its strict JSON, ECSV, or
VOTable decoder has verified schema, semantics, and
`report_identity_sha256`. It must not accept a looser parallel crossing
model.

The following accepted meanings remain unchanged:

- snapshot and orbit-solution provenance;
- one observer shared by all fields;
- ordered, uniquely identified fields;
- exact connected-visit entry, closest-approach, and exit instants in UTC;
- closest separation and retained exact-track evidence;
- conservative exhaustive/accelerated equivalence;
- deterministic canonical identity and lossless interchange.

The projection may select and repeat these facts. It may not recompute
propagation, crossing geometry, coordinate transforms, report identity, or
track samples.

## 4. Observatory-neutral planning input

A later pure constructor shall take two already validated values:

1. one `ExactSatelliteCrossingReport`; and
2. one immutable planning-context value supplied by the caller.

The planning context shall contain:

- an opaque `planning_context_id`;
- a declared profile identifier and profile schema version;
- the observatory/site identity expected by the caller;
- one or more opaque observation-unit identifiers;
- for each observation unit, a half-open planned interval
  `[start_utc, stop_utc)`;
- an explicit association to one accepted report `field_id`; and
- optional caller-owned labels that are text only and have no scheduling
  semantics.

Programme IDs, run IDs, OB IDs, container IDs, instrument names, template
names, execution durations, target coordinates, and exposure structure are
external planning facts. When a profile requires one, the caller must provide
it. Wenu must never derive, fabricate, or look it up.

Every instant is an explicit UTC instant. Local civil time, bare date-time
text, leap-second coercion, implicit timezone conversion, and sidereal-time
interpretation are out of scope.

## 5. Deterministic overlap semantics

For each observation unit and each accepted crossing in its associated field,
the adapter computes only temporal interval intersection:

`overlap_start = max(planned_start, crossing_entry)`

`overlap_stop = min(planned_stop, crossing_exit)`

An advisory row exists exactly when
`overlap_start < overlap_stop`. Touching endpoints do not overlap. The
adapter preserves report order within field order and observation-unit input
order; it applies no brightness, illumination, detectability, severity, or
priority filter.

Each row shall include at least:

- planning-context, observation-unit, profile, and field identities;
- canonical report and snapshot identities;
- observer identity and geodetic coordinates;
- NORAD catalogue ID, object name, and orbit-solution identity;
- planned start and stop;
- crossing entry, closest approach, and exit;
- overlap start, stop, and duration;
- closest angular separation and the accepted field geometry identity; and
- the scientific-status statement that brightness, illumination, detector
  contamination, and operational disposition are unknown.

A zero-row document is a valid, identified result, not an error and not proof
that the plan is free of visible trails.

## 6. Output contract

The admitted first slice is one immutable canonical JSON document with:

- `document_kind = "wenu.observatory-planning-advisory"`;
- an independently versioned adapter schema;
- `source_report_identity_sha256`;
- the complete caller-supplied planning context needed to reproduce overlap
  selection;
- ordered advisory rows;
- implementation and Wenu version identities;
- a caller-supplied UTC creation instant; and
- `planning_advisory_identity_sha256`, computed with the same exclude-own-
  digest then canonical-JSON SHA-256 rule used by accepted report contracts.

The format shall use strict UTF-8 JSON, finite JSON numbers, unique object
keys, deterministic ordering, and one final newline. Unknown keys, duplicate
keys, unsupported versions, non-canonical input, and identity mismatches fail
closed.

ECSV and VOTable are deferred. They may be added only if a later audit proves
a consumer need and preserves lossless round-trip identity. No output is
called “p2 JSON”, “OB JSON”, “ELT JSON”, or “scheduler input”.

## 7. Facility profiles

### 7.1 General profile

The general profile validates only the neutral contract. Its identifier shall
not imply compatibility with a named observatory. It is the required first
implementation and test authority.

### 7.2 Paranal profile

A later Paranal profile may require caller-supplied ESO run and OB identifiers
and may use the vocabulary “observation block” in labels. It shall remain an
offline advisory document. It shall not:

- authenticate to ESO or store credentials;
- invoke p2 demo or production endpoints;
- create, save, duplicate, verify, submit, delete, or change an OB or
  container;
- change resource versions, status, priority, constraints, time windows,
  target data, templates, finding charts, or execution sequences; or
- claim instrument-specific validity.

Any future p2 network integration requires a new audit covering the then
current API specification, authentication and secret handling, least
privilege, demo-only integration evidence, optimistic concurrency, idempotency,
rate and retry policy, audit logging, rollback/recovery, and explicit human
confirmation before every write.

### 7.3 ELT profile

The ELT profile is deliberately reserved. The first implementation may
recognize its identifier only to reject it with a stable
`unsupported_profile` failure that explains that no accepted operational
interface exists. It may not alias ELT to Paranal p2.

Admission requires a future official ELT operations source set, explicit
instrument and planning ownership, stable version/capability discovery,
official fixtures, and a new architecture acceptance.

### 7.4 Other observatories

No “universal scheduler” is asserted. A new facility profile must cite its
official interface, version its mapping, identify writable versus advisory
operations, and pass the same safety review. In the absence of that evidence,
use the general profile.

## 8. Failure policy

Construction fails before producing a document when:

- report decoding or identity verification fails;
- the planning observer/site conflicts with the report observer;
- a referenced `field_id` is absent or duplicated;
- an observation-unit ID is empty or duplicated;
- an interval is empty, reversed, non-UTC, or non-finite;
- a profile or profile version is unsupported;
- a required external identifier is absent;
- a supposedly opaque label contains invalid control text; or
- any value would require guessing, coordinate conversion, propagation,
  brightness, illumination, or scheduling policy.

Failures are typed and stable. They include no credentials, provider payloads,
or silent partial output. Batch input is atomic: one invalid observation unit
rejects the whole projection.

## 9. Placement

A later bounded implementation may introduce:

- `src/wenu/satellite_planning_advisories.py` for immutable context,
  advisory, validation, overlap, canonical JSON, and identity;
- public re-exports from `wenu.__init__`;
- `tests/test_satellite_planning_advisories.py`; and
- one offline validation tool using accepted synthetic fixtures.

It shall not modify propagation, crossings, report/tabular encoders, chart
requests, layers, renderers, exporters, provider clients, or the CLI/file
protocol. It shall not add an HTTP dependency.

## 10. Acceptance evidence for a later implementation

The minimum candidate gate is:

- exact-base and clean-tree checks;
- focused unit tests plus the complete plugin-disabled repository suite;
- deterministic JSON golden evidence across separate processes;
- report JSON/ECSV/VOTable decode-to-identical-advisory tests;
- half-open boundary, zero-row, multi-field, multi-OB, and ordering tests;
- observer, field, interval, profile, version, duplicate-key, unknown-key,
  non-finite-number, and digest rejection tests;
- proof that input report and planning context remain unchanged;
- a network-denial test and dependency inspection proving no HTTP client;
- search evidence that no ESO/ELT endpoint, credential, or write verb exists
  in production code; and
- human review of one Paranal-labelled offline specimen and one valid
  zero-row specimen.

Official ESO examples may inform fixtures, but tests must not call ESO and
must not ship real programme credentials or proprietary OB content.

## 11. Explicit exclusions

50S.6H does not authorize:

- adapter runtime or public API implementation;
- p2, p2ls, ELT, or other facility network access;
- observatory authentication or credential storage;
- OB/container creation, modification, verification, submission, or deletion;
- queue ranking, schedule optimization, automatic avoidance, or operational
  recommendations;
- conversion of crossings into scientific or time-critical constraints;
- illumination, shadow, Sun/Moon/night geometry (50S.7);
- apparent brightness or uncertainty (50S.8);
- detector trail contamination (50S.9); or
- statistical programme closure (50S.10).

## 12. Accepted conclusion

The accepted audit authorizes one small, reversible next milestone: implement and verify one
offline general planning-advisory JSON projection from the accepted exact
crossing report. Paranal is vocabulary and validation context only; ELT stays
reserved. No runtime change is part of this audit. Fernando's acceptance authorizes only
the bounded offline general planning-advisory implementation described above;
facility access, facility writes, scheduling decisions, ELT mapping, and 50S.7+
work remain unauthorized.
