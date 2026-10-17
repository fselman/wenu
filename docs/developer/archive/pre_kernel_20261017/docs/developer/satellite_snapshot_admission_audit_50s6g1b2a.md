# 50S.6G.1B.2A — External snapshot admission audit

**Status:** Accepted documentation-only audit.

Fernando scientifically and architecturally accepted this audit on 2026-09-17
after all 150 plugin-disabled current-documentation tests passed in 3.84 seconds; `git diff --check` and the working tree were clean. It changes no
runtime, default, data, report, chart, coordinate meaning, or provider access.
Only bounded 50S.6G.1B.2B digest-admission implementation is authorized next.

## 1. Roadmap position

50S.6G.1B.1 has produced and validated one immutable external CelesTrak
Active snapshot. Its canonical-record SHA-256 is
`e80306c843b9e3004b1d5bf7a8e4e7eb76a4f56284cd659978dc9bd3461f2347`.
50S.6G.1B.2 must establish representative admission and evidence before that
snapshot can enter the selector, accelerated coordinator, or multi-FoV batch
as scientific evidence.

This audit is only 50S.6G.1B.2A. It defines the admission boundary that a
later bounded 50S.6G.1B.2B implementation may realize. Deterministic
medium-tier selection remains 50S.6G.1B.2C, and the equivalence/resource
matrix remains 50S.6G.1B.2D.

## 2. As-is evidence

The repository already provides these trustworthy pieces:

- `load_snapshot_directory()` validates the manifest, canonical records
  bytes, full record schema, ordering, count, and `content_sha256`;
- `LocalSatelliteCrossingQuery` carries the validated immutable snapshot,
  and result provenance already records its canonical digest;
- `ConeShellPolicy.validated_snapshot_ids`,
  `AcceleratedCrossingPolicy.admitted_snapshot_ids`, and
  `MultiFieldCrossingPolicy.admitted_snapshot_ids` default only to
  `synthetic_50s4b_v1`;
- the batch coordinator also checks that every query uses the same
  `(snapshot_id, content_sha256)` pair.

The missing responsibility is shared external authorization. Each present
service admits by `snapshot_id`, independently. A directory name is already
irrelevant to loading, but adding `celestrak_active_e80306c843b9e300` to
three ID lists would permit any later validated content carrying that logical
ID. It would not bind the reviewed scientific evidence to the accepted bytes.

## 3. Admission decision

External evidence is admitted by **exact canonical-record SHA-256 plus
validated manifest identity**, never by directory name, path, policy-receipt
digest, provider-response digest, or `snapshot_id` alone.

The candidate runtime owner is a small
`satellites/snapshot_admission.py` module. The closest existing owner,
`satellites/snapshots.py`, continues to validate bytes and construct the
immutable snapshot. Extending it with authorization would mix the reusable
loader lifecycle with a separate evidence-policy decision consumed by three
services.

The bounded implementation should expose two immutable internal contracts:

1. an exact external identity containing `schema_version`, `snapshot_id`,
   `content_sha256`, `source_identity`, `source_url`, and
   `builder_identity`;
2. an admission token produced only after comparing that complete identity
   with an explicitly supplied policy entry.

The accepted CelesTrak entry, if Fernando later authorizes implementation,
must name the exact canonical digest above and the manifest identity already
validated in the external directory. The token holds no directory path and
does not acquire, reload, discover, copy, or publish data.

## 4. Shared consumption and atomic failure

The same immutable admission token must be checked at the boundary of the
conservative selector, accelerated coordinator, and multi-FoV batch. Every
consumer compares the token with the actual query snapshot before propagation,
selection, airmass certification, or exact evaluation.

A missing token, malformed identity, digest mismatch, manifest-identity
mismatch, mixed snapshot, or token/query substitution fails closed before
scientific work. No consumer may reconstruct authorization from a
`snapshot_id`, trust a parent directory name, or silently fall back to the
synthetic snapshot.

The exhaustive 50S.5 oracle remains the independent exact authority. Evidence
runs supply it the same already validated snapshot and exact query but do not
make external data a new ordinary default. Selector `indeterminate` records
continue to reach the exact path; admission must not weaken element-age,
eccentricity, BSTAR, perigee, propagation, Earth-orientation, interval,
airmass, or convergence failures.

## 5. Default and public-interface boundary

The ordinary installed default remains `synthetic_50s4b_v1`. Existing
default constructors and ordinary calls require no external path or token.
The external token is explicit and evidence-only. There is no environment
variable, configuration search, newest-directory choice, content discovery,
automatic refresh, provider call, fallback, merge, or implicit global
allowlist.

50S.6G.1B.2B may add the minimum optional seams required to pass one token
through the three existing policy/service boundaries. It must not enable the
external snapshot by default, enlarge the 60-second field interval, change
centre-only airmass admission, assert that every Active record lies inside the
cone-shell validated domain, or claim useful speed.

## 6. Provenance and evidence

Every admitted run must preserve at least:

- the exact canonical snapshot SHA-256 and full validated manifest identity;
- admission-policy and implementation identities;
- observer, field, inclusive UTC interval, tolerances, and IERS-A identity;
- selector decision counts, fallback reason, exact evaluations, and exact
  result digest where the existing service supplies them.

The provider-response digest
`e54730e14b2097444c5e20bba6dd13d3e2d92f956797d49256ddb1a70ffe5014`
and policy digest
`67bf0faa7e026a7cd49799069db9d3355f2a867894133afd39e130d6185724aa`
remain acquisition provenance. Neither substitutes for canonical-record
identity at runtime.

## 7. Coordinates and chart boundary

This audit changes no coordinate system, origin, frame, epoch, time scale,
Earth-orientation resource, observer model, airmass rule, crossing meaning,
projection, renderer, or export behavior. TEME remains the SGP4 propagation
frame; crossing geometry remains topocentric geometric direction expressed in
GCRS axes; chart integration remains later 50S.6G work.

Admission is therefore upstream of exact track generation. It is necessary
before representative data can exercise binocular, regional, or
stereographic chart delivery, but it draws no track itself.

## 8. Test and ownership plan

A later `tests/test_satellite_snapshot_admission.py` is justified because
digest-bound cross-service authorization, substitution rejection, and
before-work atomicity are a distinct policy fault model. Existing snapshot,
acceleration, and batch tests remain the owners of byte validation, selector
science, and many-query coordination respectively; they should add only seam
tests needed to prove that the shared token is consumed.

The bounded gate must prove:

- exact accepted identity succeeds only when explicitly supplied;
- same `snapshot_id` with another digest fails;
- same digest with altered manifest identity fails;
- token reuse with another query snapshot fails before work;
- selector, accelerated coordinator, and batch use the same predicate;
- mixed-snapshot batches remain atomic;
- default synthetic behavior and existing public results remain unchanged;
- no test performs network access or requires the external 16,559-record
  snapshot.

## 9. Deferred work and stop conditions

50S.6G.1B.2A does not implement admission. 50S.6G.1B.2B must stop after the
shared digest-bound evidence-only seam and its tests. It does not select the
medium specimen, execute the matrix, package external bytes, make benchmark
claims, produce reports or files, draw exact tracks, or change charts.

50S.6G.1B.2C will separately audit and implement deterministic medium
selection from the accepted parent digest. 50S.6G.1B.2D will separately own
the machine-readable exact-equivalence and resource matrix. A later provider
remains a separate public, reliable, genuinely independent validation oracle,
never an automatic fallback or merge.

## 10. Acceptance criteria

This audit was accepted when:

- every active authority describes the exact-digest-plus-manifest boundary;
- the three current ID-only admission points and their shared replacement are
  explicit;
- synthetic defaults remain unchanged and external use remains evidence-only;
- runtime admission, medium selection, and matrix execution remain separately
  bounded;
- the coordinate guide records no change in scientific meaning;
- documentation tests protect the boundary and exclusions;
- the plugin-disabled documentation gate and `git diff --check` pass.

Acceptance of this document authorizes only bounded
50S.6G.1B.2B implementation. It does not authorize medium selection, matrix execution, chart integration,
another provider request, or any runtime default change.


## 11. Accepted 50S.6G.1B.2B implementation record

The bounded candidate adds `satellites/snapshot_admission.py` with immutable
exact identity, explicit finite policy, and opaque token contracts. Identity
contains schema version, snapshot ID, canonical-record SHA-256, source
identity, source URL, and builder identity. The accepted CelesTrak Active
constant records the exact audited manifest identity but performs no loading,
discovery, or enablement.

The existing conservative selector, accelerated coordinator, and multi-FoV
batch accept one optional shared token. Missing or mismatched external
admission fails before the component's scientific work; batch validation
remains atomic. Existing synthetic defaults are unchanged. Tests use only the
installed synthetic records under hand-authored external manifest identities;
the 16,559-record directory is neither required nor packaged.

This accepted implementation closes only 50S.6G.1B.2B. It does not implement
deterministic medium selection, the evidence matrix, another provider request,
reports, exact drawable tracks, or chart integration.


Fernando scientifically and architecturally accepted 50S.6G.1B.2B on
2026-09-17 after 51 focused runtime tests, 151 current-documentation tests,
and all 2,611 plugin-disabled tests passed; the complete suite took 215.89
seconds. `git diff --check` and the working tree were clean. Only bounded
50S.6G.1B.2C deterministic medium-specimen work is authorized next; 50S.6G.1B.2D
matrix execution and later delivery remain separately unauthorized.
