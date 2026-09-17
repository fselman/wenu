# 50S.6G.1B representative satellite snapshot preflight and evidence audit

**Status:** Accepted documentation-only provider, acquisition, publication,
admission, and performance-evidence audit.

**Base:** accepted 50S.6G.1A at merge commit `15b122f`.

**Runtime effect:** None. This audit adds no network client, snapshot builder,
catalogue data, runtime admission, benchmark result, report, CLI, or chart.

## 1. Purpose

50S.6G.1A can load one explicitly selected immutable snapshot directory through
the complete Wenu manifest and canonical-record validator. It deliberately
does not decide where a representative snapshot comes from, whether provider
policy permits a request, how raw bytes become canonical OMM records, how a
directory is published atomically, or what evidence admits its scale.

50S.6G.1B must define those missing boundaries before any representative
catalogue is acquired. The design must protect the provider, keep live access
outside ordinary calculation, preserve exact response provenance, and avoid
turning one convenient provider group into a claim of complete orbital
population coverage.

## 2. As-is assessment

The repository already provides:

- the accepted `load_snapshot_directory(directory)` fail-closed runtime seam;
- strict immutable `SatelliteElementRecord`, `SatelliteSnapshotManifest`, and
  `SatelliteElementSnapshot` contracts;
- canonical JSON bytes, SHA-256 content identity, full NORAD identifiers,
  deterministic ordering, duplicate rejection, and OMM/SGP4 field validation;
- an independently callable exhaustive 50S.5 oracle;
- configurable 50S.6B and 50S.6F policy objects whose accepted defaults remain
  restricted to `synthetic_50s4b_v1`;
- content-addressed, staging-directory, and atomic-publication precedents in
  `minor_body_acquisition.py`;
- plugin-disabled tests and benchmark-practice rules that distinguish cold and
  warm evidence and prohibit unsupported speed claims.

The repository does not provide:

- a satellite provider-policy receipt or human policy-acceptance boundary;
- a CelesTrak GP bulk client or provider-specific CSV adapter;
- an immutable raw-response and transformation receipt;
- a satellite snapshot staging/publication owner;
- a policy-cleared representative external snapshot;
- digest-bound external-snapshot admission for the selector or batch
  coordinator;
- representative-scale exact-equivalence, resource, or timing evidence.

The minor-body acquisition code is a lifecycle precedent, not a reusable
satellite provider. Satellite OMM/GP response semantics, provider policy,
cadence, canonicalization, population scope, and evidence are different and
must not be hidden in `minor_body_acquisition.py`.

## 3. Authoritative provider review

The following primary sources were checked on 2026-09-17:

- CelesTrak usage policy, updated 2026-05-22:
  `https://celestrak.org/usage-policy.php`;
- CelesTrak GP query and format documentation, updated 2026-06-23:
  `https://celestrak.org/NORAD/documentation/gp-data-formats.php`;
- CelesTrak current GP groups:
  `https://celestrak.org/NORAD/elements/`;
- Space-Track API help and usage guidance:
  `https://www.space-track.org/documentation`.

CelesTrak requires documented queries, downloading only needed data and only
once per update, with GP updates treated as two-hour products. Machine clients
must stop on every non-200 response, including redirects and server errors,
and report the failure to a human rather than retrying. CelesTrak currently
supports GP queries by `CATNR`, `INTDES`, `GROUP`, `NAME`, or `SPECIAL`, and
offers XML, KVN, JSON, and CSV OMM-compatible products. CSV is now the default,
is smaller than TLE, and supports catalogue identifiers beyond five digits.

Space-Track remains an authenticated independent source and later comparison
oracle. Its account terms, credentials, query limits, and redistribution
conditions make it unsuitable as Wenu's automatic first acquisition route.
SatChecker remains a crossing-candidate service and comparison oracle, not the
owner of Wenu's frozen local element snapshot.

## 4. Provider and population decision

**Adopt CelesTrak as the first bounded acquisition provider.** The first
implementation supports exactly one documented HTTPS bulk GP request:

```text
https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=CSV
```

This is one explicit representative-scale population, not a complete
resident-space-object catalogue.

The query keys and values are fixed, uppercase, and recorded exactly. Redirects
are errors. There is no per-object mode, arbitrary URL, arbitrary group, TLE,
JSON, XML, SupGP, SATCAT join, fallback provider, pagination, polling, parallel
download, or automatic retry in the first implementation.

`GROUP=active` is a provider-defined active-satellite population. It is useful
representative-scale evidence but is not the complete public
resident-space-object population: inactive payloads, rocket bodies, debris,
analyst objects,
restricted objects, lost objects, and objects absent from the group are not
claimed to be covered. Wenu must label every result with this population scope.

A complete supported GP population is not invented from multiple groups,
because overlapping groups would require duplicate resolution and several
provider requests. Space-Track full-population acquisition, CelesTrak groups
beyond `active`, and any multi-request union require a later policy and
scientific audit.

## 5. Two-phase provider-policy preflight

Policy review and data acquisition are separate explicit operations.

### 5.1 Freeze the policy receipt

The policy-preflight operation performs one direct HTTPS GET of the official
CelesTrak usage-policy URL, accepts only HTTP 200 without redirect, and writes
an immutable local receipt containing:

- schema version and document kind;
- exact policy URL and retrieval UTC instant;
- HTTP status, media type, response byte count, and SHA-256;
- exact policy response bytes or a sibling file bound by that digest;
- parsed policy title, published/updated date when unambiguously present, and
  the clauses used by Wenu: documented query, two-hour GP cadence, one download
  per update, caching, and immediate stop on non-200 responses;
- Wenu version and policy-preflight implementation identity;
- no statement that software has legally or scientifically accepted a changed
  policy.

The operation performs no GP request. Any redirect, non-200 status, timeout,
unexpected host, invalid TLS result, unreadable response, absent required
clause, or ambiguous policy version fails closed without retry.

### 5.2 Explicit human acceptance

Acquisition requires both the policy receipt and an explicit command argument
containing its exact SHA-256. This is a deliberate human acknowledgement of the
reviewed bytes, not a generic `--yes` flag. If the receipt digest, URL, parsed
date, required clauses, or expected provider identity differs, acquisition
stops before any GP request. A new policy response therefore requires a new
receipt and a new explicit acceptance.

The acquisition report records the accepted policy digest, acceptance UTC
instant, and the operator-supplied acknowledgement. Wenu does not store an
account, credential, token, or legal conclusion.

## 6. Single bulk acquisition contract

After policy acceptance, acquisition performs at most one GP network request.
It uses a declared finite timeout, an identifying User-Agent with the Wenu
version and project URL, and accepts only a direct HTTPS 200 response from
`celestrak.org`. It does not follow redirects and does not retry.

Before requesting, the preflight checks the local content-addressed acquisition
index. If a fully validated receipt for the same query is younger than two
hours, the default mode reuses it without network access. Refresh inside that
two-hour window fails unless the operator explicitly chooses a later separately
audited override; the first implementation has no override.

The exact response bytes are retained locally before transformation, together
with:

- resolved URL and exact ordered query parameters;
- retrieval start/stop instants and HTTP metadata;
- raw media type, byte count, SHA-256, and filename;
- accepted policy-receipt digest;
- provider population label `CelesTrak GROUP=active`;
- acquisition implementation and Wenu versions;
- terminal success or failure status and warnings.

An empty response, HTML/error body, malformed CSV, duplicate header, missing
required column, invalid record, duplicate full NORAD identity, or unsupported
OMM/SGP4 value invalidates the whole acquisition. No partial snapshot is
published.

## 7. Deterministic CelesTrak CSV normalization

The provider adapter parses the exact UTF-8 CSV response with a fixed expected
header contract. It maps OMM-compatible columns into the existing complete
`SatelliteElementRecord` schema. Constants omitted by CelesTrak's CSV contract
may be supplied only as declared provider-format invariants:

- `CENTER_NAME = EARTH`;
- `REF_FRAME = TEME`;
- `TIME_SYSTEM = UTC`;
- `MEAN_ELEMENT_THEORY = SGP4`.

No physical quantity, epoch, identifier, classification, element-set number,
or orbital value is guessed. Blank values required by Wenu fail closed. Full
integer NORAD identifiers are retained, including six- and future nine-digit
values. Every accepted record must construct successfully through the existing
typed record validator.

The transformation rejects duplicate NORAD identifiers rather than silently
choosing the first, last, or newest row. Accepted records are sorted by full
NORAD identifier and serialized with the existing canonical JSON function.
The acquisition report binds raw-response SHA-256, canonical-record SHA-256,
record count, minimum/maximum element epoch, identifier range, and every
normalization warning.

## 8. Immutable external publication

All work occurs in a new sibling staging directory outside the repository and
outside the installed Wenu package. The builder writes:

```text
<snapshot-root>/<canonical-record-sha256>/
    manifest.json
    records.json
    acquisition-report.json
    policy-receipt.json
    policy-response.html
    provider-response.csv
```

`manifest.json` and `records.json` remain exactly compatible with
`load_snapshot_directory()`. The extra receipts are acquisition evidence and
are not runtime dependencies. The manifest identifies CelesTrak, the fixed
query, retrieval instant, policy URL/check instant, builder identity, warnings,
and canonical content digest.

Before publication, the staged directory is reloaded through
`load_snapshot_directory()` and every report digest is independently checked.
Only then is it atomically renamed to the content-addressed destination. The
builder never overwrites an existing directory. If identical content already
exists, it is completely revalidated and reused; any mismatch fails closed.
Staging is removed after a controlled failure.

Raw provider and policy bytes remain local evidence. This audit does not
authorize committing, packaging, uploading, attaching to a release, or
redistributing them. A repository fixture may contain only hand-authored or
separately licensed synthetic data.

## 9. Representative tiers

Three evidence tiers remain scientifically distinct:

1. **Synthetic oracle:** installed `synthetic_50s4b_v1`; fast deterministic
   unit and exact-equivalence authority.
2. **Medium representative specimen:** a deterministic offline stratified
   subset derived from one validated Active snapshot, with its own selection
   receipt and parent digest. It spans supported LEO/MEO/GEO-like mean-motion
   regimes, inclination bands, eccentricity bands, BSTAR sign/magnitude bands,
   element ages, and both five- and greater-than-five-digit NORAD identifiers
   when present. It makes no population-frequency claim.
3. **Active-group snapshot:** the complete validated result of that one
   `GROUP=active` response, labeled with exact record count and retrieval
   instant. It is representative-scale, not a complete-orbit-population claim.

The medium tier is selected locally and causes no second provider request. Its
algorithm, target count, bin edges, tie-breaking, parent digest, selected full
identifiers, and empty bins are recorded. Selection is deterministic for exact
parent bytes. No fixed public catalogue-size maximum is introduced.

## 10. Admission and exact-equivalence boundary

External snapshots are admitted by exact canonical-record SHA-256 plus the
validated manifest identity, never by directory name or `snapshot_id` alone.
The accepted synthetic defaults remain unchanged.

The 50S.6G.1B implementation may add an explicit evidence-only policy/harness
that supplies the exact external digest to the existing exhaustive,
conservative-selector, and multi-FoV services. It must not make an external
snapshot a default, widen the 60-second per-field interval, weaken centre-only
airmass admission, or claim all provider records satisfy the current selector
domain. Unsupported element age, eccentricity, BSTAR, perigee, propagation, or
Earth-orientation cases remain indeterminate/fail-closed and reach the exact
path where the accepted contracts require it.

Every accelerated result must equal an independent exhaustive 50S.5 result for
the same exact snapshot digest, observer, field, interval, tolerances, and
Earth-orientation resources. A selector rejection mismatch is a scientific
failure, not a benchmark outlier.

## 11. Evidence matrix

The implementation handoff must produce one machine-readable evidence document
outside the repository. It records environment, Wenu/SGP4/Astropy/Numpy
versions, CPU/platform, snapshot/report digests, Earth-orientation digests,
policy identities, query definitions, repetition counts, and raw per-run
measurements before any summary.

The matrix includes:

- tiers: synthetic, medium representative, and Active-group snapshot when
  practical on the acceptance machine;
- FoV counts: 1, 2, 5, 10, 20, and, when practical, 50;
- interval relations: disjoint, partially overlapping, and identical;
- geometry: central, grazing, between-coarse-sample, near-zenith,
  boundary-time, coordinate-seam, multiple-visit, and no-crossing cases;
- at least La Ligua, Paranal, ELT, and one northern-site explicit observer,
  without claiming an observatory scheduling adapter;
- cold process and warm process runs reported separately;
- wall time, peak resident memory, tracemalloc peak, total records, selector
  retain/reject/indeterminate counts, exact-record evaluations, propagation
  and topocentric-state evaluations when instrumentable, fallback count,
  crossing count, and exact-result digest;
- exact equality with the independent exhaustive route.

Synthetic and medium gates are mandatory. The Active-group tier may be marked
not practical only with measured resource evidence and a clear failure/limit;
it may not disappear silently. Timing is descriptive until repeated Mac
measurements show material benefit. This slice makes no useful-speed,
shared-state-reuse, memory-bound, or production-capacity claim.

## 12. Ownership and proposed implementation slices

The durable new responsibility is provider-governed satellite snapshot
acquisition and evidence, distinct from immutable runtime loading. The closest
production owner is `satellites/snapshots.py`, but extending it would mix
offline deterministic loading with network, policy, raw-response, staging,
and publication lifecycles.

A later accepted implementation should therefore add a dedicated satellite
snapshot acquisition owner adjacent to `satellites/`, with a thin developer
command under `tools/`. Its tests require a new stable owner because policy
receipt, no-network-before-acceptance, one-request enforcement, raw receipt,
atomic publication, and provider normalization are a distinct provider and
filesystem fault model. All ordinary tests use injected fake transport and
immutable fixtures; no test performs live network access.

Implementation is decomposed further:

1. **50S.6G.1B.1 — Policy receipt and deterministic builder.** Implement the
   two-phase policy acknowledgement, one fake-transport bulk acquisition,
   CSV normalization, receipts, and atomic external publication. Run one
   separately approved live acquisition only after fake-transport acceptance.
2. **50S.6G.1B.2 — Representative admission and evidence.** Add digest-bound
   evidence-only admission, deterministic medium selection, the matrix runner,
   exact-equivalence evidence, and measured resource results.

The first slice cannot automatically authorize the live request. Before the
live operation, Fernando must inspect the freshly frozen policy receipt and
explicitly approve its exact digest. The second slice cannot broaden ordinary
runtime defaults or assert useful speed without separate evidence and
acceptance.

## 13. Non-goals

50S.6G.1B does not add Space-Track login, credentials, SupGP, SATCAT joins,
multi-provider merge, automatic refresh, daemon/polling behavior, scheduled
download, full-population completeness, catalogue redistribution, an installed
large fixture, implicit runtime acquisition, report formats, CLI/file FoV
input, validation-output files, exact drawable tracks, chart integration,
illumination, brightness, detector effects, or observatory adapters.

It does not change TEME, SGP4/WGS-72, UTC/UT1, GCRS-axis topocentric direction,
centre-only airmass, crossing, projection, rendering, semantic SVG, or export
meaning.

## 14. Acceptance criteria

This documentation audit is acceptable when:

- every active authority agrees on the provider, population scope, two-phase
  policy acknowledgement, one-request rule, receipts, normalization,
  publication, representative tiers, digest-bound admission, and matrix;
- source-tree ownership explains why acquisition is separate from runtime
  loading and minor-body acquisition;
- the coordinate guide records that no implemented coordinate meaning changes;
- documentation tests protect the exact bounded decisions and exclusions;
- `git diff --check` and the plugin-disabled documentation gate pass;
- Fernando explicitly accepts the scientific, policy, and operational
  boundary.

Fernando scientifically and architecturally accepted this audit on 2026-09-17
after all 147 plugin-disabled current-documentation tests passed in 4.54
seconds. Acceptance authorizes only separately bounded 50S.6G.1B.1
policy-receipt and deterministic-builder implementation with fake transport.
It does not authorize a live CelesTrak request, representative
admission/evidence, 50S.6G.1B.2, or any later 50S.6G behavior.

## 15. 50S.6G.1B.1 implementation record

The bounded implementation uses a dedicated satellite acquisition owner, a
mandatory injected transport with no live adapter, and an offline thin
developer command. It verifies exact policy-response SHA-256 acknowledgement
before the GP transport call, normalizes the fixed Active CSV contract through
the existing typed record validator, retains both raw responses and receipts,
reloads the staged snapshot, and publishes by atomic rename. Tests use only
hand-authored fake responses. No live provider request or 50S.6G.1B.2 evidence
is part of this implementation.

Fernando accepted this bounded implementation on 2026-09-17 after 175 focused
plugin-disabled tests passed in 7.24 seconds and all 2,594 plugin-disabled tests
passed in 226.82 seconds. `git diff --check` and the working tree were clean.
Acceptance does not authorize a live policy or GP request, representative
admission/evidence, or 50S.6G.1B.2.
