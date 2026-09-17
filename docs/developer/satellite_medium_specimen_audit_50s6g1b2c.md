# 50S.6G.1B.2C — Deterministic medium satellite specimen audit

**Status:** Accepted documentation-only audit.

Fernando scientifically and architecturally accepted this audit on 2026-09-17
after all 153 plugin-disabled current-documentation tests passed in 4.58
seconds; `git diff --check` and the working tree were clean. It changes no
runtime, installed data, external snapshot, default, coordinate meaning,
report, track, chart, or provider access. Only bounded fake-data
50S.6G.1B.2C implementation is authorized next.

## 1. Purpose and roadmap position

The accepted 50S.6G.1B.2B boundary can explicitly admit one exact external
snapshot to the selector, accelerated coordinator, and multi-FoV batch.
50S.6G.1B.2C now defines a deterministic offline medium specimen derived from
the accepted 16,559-record CelesTrak Active snapshot. The specimen is intended
for development and mandatory equivalence gates that are more representative
than the three-record synthetic oracle but substantially smaller than the
complete Active response.

The specimen is **not a statistical sample**, completeness claim, frequency
estimate, operational catalogue, or new runtime default. It preserves diverse
contract and failure domains deliberately; it does not reproduce the
population distribution. Matrix execution remains 50S.6G.1B.2D.

## 2. As-is assessment

The repository already provides:

- `load_snapshot_directory()` with complete manifest, canonical-byte,
  record-schema, ordering, count, and digest validation;
- the accepted exact CelesTrak Active identity and digest-bound admission token;
- immutable `SatelliteElementRecord` and `SatelliteElementSnapshot`;
- canonical JSON encoding and content-addressed publication precedents;
- the external acquisition report with retrieval interval, raw digest,
  canonical digest, record count, epoch range, and provider identity;
- an installed three-record synthetic exact oracle and no packaged external
  catalogue.

The repository does not provide a subset policy, deterministic stratifier,
selection receipt, derived-manifest contract, medium publication owner, or
medium artifact. Selection must not be hidden in the runtime loader,
acquisition adapter, admission token, selector, coordinator, or matrix runner.

## 3. Parent admission and offline boundary

The input is one explicit external snapshot directory. Before selection, the
operation must:

1. load it through `load_snapshot_directory()`;
2. require an exact `ExternalSnapshotAdmission` token;
3. require the accepted CelesTrak Active manifest identity and canonical digest
   `e80306c843b9e3004b1d5bf7a8e4e7eb76a4f56284cd659978dc9bd3461f2347`;
4. read and validate the sibling `acquisition-report.json`;
5. require report status `success`, matching canonical digest, source URL,
   provider-response digest, record count, and retrieval interval.

There is no provider request, refresh, discovery, newest-directory choice,
fallback, merge, or current-clock decision. The operation reads only the
explicit admitted parent and writes only beneath an explicit external output
root.

## 4. Reference instant and element age

Element age is signed and deterministic. The reference instant is exactly the
parent acquisition report's `retrieved_stopped_utc`, never the wall clock.
For an element epoch (t_e) and reference (t_r):

[
a = (t_r - t_e) / 86400 {m days}.
]

A negative value therefore identifies an element epoch later than the recorded
retrieval stop. The receipt stores the exact reference instant and each age-bin
definition. No epoch is rounded before bin assignment.

## 5. Stratification axes and bins

Every parent record belongs to exactly one bin on each axis. Bounds use the
canonical record values without derived orbit propagation.

### 5.1 Mean motion

| Bin | Canonical condition |
|---|---|
| `geo_deep_like` | (0 < n < 1.2) rev/day |
| `meo_like` | (1.2 le n < 8) rev/day |
| `leo_like` | (n ge 8) rev/day |

These are selection labels, not orbit-class assertions. In particular,
`geo_deep_like` is not a claim that every member is geostationary.

### 5.2 Inclination

| Bin | Canonical condition |
|---|---|
| `i_0_30` | (0 le i < 30) deg |
| `i_30_60` | (30 le i < 60) deg |
| `i_60_90` | (60 le i < 90) deg |
| `i_90_120` | (90 le i < 120) deg |
| `i_120_180` | (120 le i le 180) deg |

### 5.3 Eccentricity

| Bin | Canonical condition |
|---|---|
| `e_0_0p01` | (0 le e < 0.01) |
| `e_0p01_0p1` | (0.01 le e < 0.1) |
| `e_0p1_0p25` | (0.1 le e le 0.25) |
| `e_over_0p25` | (0.25 < e < 1) |

The last bin deliberately represents records outside the current cone-shell
eccentricity domain; admission does not imply accelerated rejection authority.

### 5.4 BSTAR

| Bin | Canonical condition |
|---|---|
| `bstar_negative_large` | (B^* < -10^{-4}) |
| `bstar_negative_small` | (-10^{-4} le B^* < 0) |
| `bstar_zero` | (B^* = 0) exactly |
| `bstar_positive_small` | (0 < B^* le 10^{-4}) |
| `bstar_positive_large` | (B^* > 10^{-4}) |

### 5.5 Signed element age

| Bin | Canonical condition |
|---|---|
| `age_future` | (a < 0) days |
| `age_0_1` | (0 le a le 1) day |
| `age_1_7` | (1 < a le 7) days |
| `age_7_14` | (7 < a le 14) days |
| `age_over_14` | (a > 14) days |

### 5.6 NORAD identifier width

| Bin | Canonical condition |
|---|---|
| `norad_five_or_fewer` | ID (le 99999) |
| `norad_more_than_five` | ID (> 99999) |

No identifier is truncated, padded, parsed as a float, or replaced.

## 6. Deterministic selection algorithm

The policy default target is exactly **256 records**. It is configurable and
recorded, but there is no fixed public maximum. A non-positive or non-integer
target fails.

For every non-empty bin on every axis:

1. compute for each member the lowercase hexadecimal SHA-256 of the UTF-8
   sequence
   `parent_digest + NUL + axis + NUL + bin + NUL + decimal_full_norad_id`;
2. order by that rank, then by the full integer NORAD identifier;
3. require the first two distinct records, or every member when the bin contains
   fewer than two.

The union of these mandatory representatives establishes independent
one-dimensional coverage. It does not claim Cartesian-product coverage. If the
mandatory union exceeds the requested target, selection fails and reports the
minimum admissible target; it never silently enlarges the product.

Remaining places are filled from unselected parent records ordered by SHA-256
of
`parent_digest + NUL + "fill" + NUL + decimal_full_norad_id`, then by full
NORAD identifier. If the parent contains fewer records than the target, every
parent record is selected and the receipt records that exhaustion warning.
Final canonical records are ordered by full NORAD identifier, independent of
selection rank.

The algorithm never uses input row order, Python hash randomization, directory
name, wall clock, network state, CPU count, or floating-point tolerance.
Identical validated parent bytes, report, policy, target, and implementation
produce identical selected identifiers and canonical bytes.

## 7. Selection receipt

A versioned canonical `selection-receipt.json` records:

- document kind, schema version, and implementation identity;
- parent complete identity, canonical digest, record count, acquisition report
  digest, provider-response digest, and retrieval stop instant;
- admission-policy identity;
- requested target and actual count;
- exact axis order, bin order, bounds, inclusivity, units, and age reference;
- rank recipes and the two-per-non-empty-bin coverage rule;
- membership count, required representatives, and selected representatives for
  every bin;
- every empty bin;
- global fill order entries actually used;
- final selected full NORAD identifiers in canonical order;
- subset canonical-record SHA-256;
- warnings and the explicit no-population-frequency statement.

A receipt digest is included in the derived manifest provenance. The receipt
does not store the parent directory path.

## 8. Derived immutable publication

A later implementation should add a distinct
`satellites/snapshot_evidence.py` owner. The closest loader,
`snapshots.py`, must remain a reusable validator; `snapshot_acquisition.py`
must remain the provider/policy/raw-response owner; and
`snapshot_admission.py` must remain authorization-only.

A thin `select-medium` subcommand may extend
`tools/build_satellite_snapshot.py` because that developer tool already owns
explicit external satellite snapshot operations. The command receives parent
directory, output root, exact accepted digest, policy identity, and target. It
has no transport.

Publication uses a sibling staging directory and atomic rename:

```text
<output-root>/<subset-canonical-record-sha256>/
    manifest.json
    records.json
    selection-receipt.json
```

The derived manifest has its own content digest and snapshot ID, names the
parent digest and receipt digest in provenance, retains the provider source URL
and policy check identity, and warns that the product is a deterministic
coverage specimen rather than a complete or statistical population. Before
publication, the staged product is reloaded through
`load_snapshot_directory()` and every receipt binding is rechecked. Existing
destinations are never overwritten; identical destinations are fully
revalidated before reuse.

No provider or policy response bytes are copied into the subset. The subset
remains outside the repository, package, release assets, and test fixtures.

## 9. Test ownership and gates

A new `tests/test_satellite_snapshot_evidence.py` is justified by the distinct
stratification, receipt, parent-binding, and atomic-publication fault model.
All tests use hand-authored immutable snapshots and reports; none uses the
16,559-record external directory or network access.

The bounded implementation gate must prove:

- exact parent admission and acquisition-report binding before selection;
- every boundary value enters exactly one declared bin;
- two-per-non-empty-bin coverage and empty-bin reporting;
- independence from parent record order;
- deterministic repeatability and full-NORAD tie-breaking;
- failure when mandatory coverage exceeds target;
- parent exhaustion behavior;
- canonical final ordering and derived digest;
- receipt completeness and digest binding;
- staging cleanup, no overwrite, and identical-product revalidation;
- loader round trip and no path in the receipt;
- no mutation of parent bytes;
- unchanged installed synthetic default and admission behavior.

## 10. Coordinates and downstream boundary

Selection inspects stored OMM scalars and signed epoch age only. It performs no
SGP4 propagation, TEME transformation, Earth-orientation interpolation,
observer calculation, FoV evaluation, airmass certification, crossing solve,
projection, rendering, or export. No coordinate, frame, origin, position
status, epoch, or time-scale meaning changes.

The medium product receives no privileged scientific status. 50S.6G.1B.2D must
run the same admitted exact and accelerated services and compare exact result
digests. The medium specimen alone supports no speed, capacity, memory, or
equivalence claim.

## 11. Non-goals and stop conditions

50S.6G.1B.2C does not run the matrix, benchmark performance, add concurrency,
reuse propagated states, install or package external records, change runtime
defaults, discover snapshots, access a provider, add reports, accept request
files, create exact track samples, draw charts, compute illumination, or add an
observatory adapter.

A first real medium artifact may be created only after the bounded
implementation passes fake-data gates and Fernando separately approves the
explicit offline command against the already accepted parent. No second
CelesTrak request is needed or permitted.

## 12. Acceptance criteria

This audit was accepted when:

- every active authority agrees on the exact parent, reference instant, bins,
  target, deterministic ranks, receipt, publication, and non-claims;
- source ownership separates loading, acquisition, admission, selection, and
  later matrix execution;
- the coordinate guide records no change in scientific coordinate meaning;
- documentation tests protect the precise choices and exclusions;
- the plugin-disabled documentation gate and `git diff --check` pass.

Acceptance authorizes only bounded 50S.6G.1B.2C implementation with fake
data. It does not authorize the first real medium selection; 50S.6G.1B.2D
matrix execution and later 50S.6G delivery remain separately unauthorized.

## 13. Candidate fake-data implementation record

Candidate 50S.6G.1B.2C fake-data implementation now lives in
`satellites/snapshot_evidence.py`. It requires an exact
`ExternalSnapshotAdmission`, validates the acquisition report and captured
provider-response bytes, uses the recorded retrieval stop as its age reference,
applies the accepted independent bins and digest ranks, writes a canonical
selection receipt, and atomically publishes a content-addressed derived
snapshot. The offline `select-medium` command is explicit and transport-free.

All tests use hand-authored fake data. On 2026-09-17, 30 plugin-disabled
snapshot-evidence, admission, and acquisition tests passed in 5.99 seconds;
compilation, `git diff --check`, and the working tree were clean. This is a
candidate implementation awaiting scientific and architectural acceptance. It
does not authorize the first real medium selection or 50S.6G.1B.2D matrix
execution.

## 14. Accepted fake-data implementation

Fernando scientifically and architecturally accepted the bounded
50S.6G.1B.2C fake-data implementation on 2026-09-17. The complete
plugin-disabled suite passed 2,622 tests in 225.75 seconds; the 185-test
implementation-and-documentation gate passed in 9.03 seconds; compilation,
`git diff --check`, and the working tree were clean at `1d9d4e4`.

Acceptance covers the deterministic selector, exact parent-evidence binding,
canonical path-free receipt, content-addressed atomic publication, and offline
operator seam. It does not itself authorize executing `select-medium` against
the real 16,559-record parent. That first real selection is the next separately
bounded 50S.6G.1B.2C operation. 50S.6G.1B.2D matrix execution remains
separately unauthorized.
