# Generic comet acquisition audit (Milestone 50A.5D.2B)

**Status:** Candidate audit for Fernando's review

**Base:** `59c605f075d29a0f174249cd6d2e6218cee91ee5`

## Decision requested

Authorize only the generic acquisition service behind exact comet preflight.
The service may turn one already resolved comet identity and one bounded
coverage request into a verified, immutable, manifest-backed Horizons SPK
resource. It does not yet connect acquisition to `wenu_chart`, change a chart
request, draw a new object, estimate brightness, or write a moving-object
report.

## As-is assessment

50A.5D.2A now supplies exact, mandatory-class identity through
`resolve_minor_body_identity(selection, expected_class=...)` and the comet
wrapper `resolve_comet_identity`. It reuses installed aliases before network
access and rejects absent, ambiguous, partial, wildcard, wrong-class, and bare
asteroid-number selections without guessing.

`minor_body_acquisition.py` already owns the accepted data policy, bounded
coverage calculation, cache lookup, per-identity lock, staging validation,
content-addressed publication, and numbered-asteroid acquisition. Its live
download and identity parsers are asteroid-specific: they accept positive
integer numbers, require Horizons asteroid comments, and compare an asteroid
number against SBDB.

`MinorBodyResourceCollection` and `MinorBodyResourceSession` already accept
properly formed comet manifest records and validate comet designation class,
provider target, orbit solution, digest, type-21 segment identity, and exact
coverage. `tools/install_comet_resource.py` can publish the accepted Encke
and 161P evidence, but it is an offline fixture installer, not an operational
network acquisition path.

The missing seam is therefore acquisition from a resolved comet identity to
the same verified resource format. No new state, direction, projection,
rendering, or export machinery is required.

## Bounded contract

The candidate implementation should generalize the library boundary rather
than add a second comet downloader. Its public shape may be equivalent to:

```python
acquire_minor_body_resources(
    identities,
    output_directory,
    *,
    start,
    stop,
    fetch_json=provider_fetch,
) -> Path
```

The existing numbered-asteroid function may remain as a compatibility wrapper.
Every identity is typed as `asteroid` or `comet`; the acquisition core must
never infer class from a bare integer, SPK-ID range, filename, or provider
comment.

50A.5D.2B accepts one exact comet per invocation. Multi-object batching,
automatic chart preflight composition, mutable cache indexing, and background
catalog refresh remain later work unless reuse of the existing atomic
publication helper requires an internal iterable.

## Provider resolution and apparition binding

SBDB identity does not by itself authorize a Horizons SPK request. In
particular, Wenu must not derive a Horizons record number arithmetically from
the periodic-comet number or SBDB SPK-ID.

For the resolved comet, the acquisition service must:

1. retain the exact SBDB identity response and its digest;
2. issue an explicit Horizons identity/lookup request suitable for the
   canonical comet designation;
3. stop on zero or multiple Horizons records;
4. bind the unique provider record, apparition when applicable, current orbit
   solution, solution date, osculating epoch, and non-gravitational model
   provenance;
5. use that exact returned Horizons command for the bounded SPK request;
6. verify that the resulting Horizons receipt and SPK target describe the same
   comet identity.

A successful resolution of `10P` or `10P/Tempel 2` must lead to the same
bound identity. `Tempel`, `10`, wildcards, and provider suggestions remain
failures. Production code may contain no `10P` conditional, record constant,
fixture lookup, or special parser branch.

If Horizons exposes several apparition records and cannot identify one
uniquely from the exact current solution, implementation must stop for review.
It must not silently select the first, latest, numerically nearest, or
longest-coverage record.

## SPK request and validation

Coverage is the closed deterministic interval derived from all requested
point, track, sequence, and center instants plus the accepted margin. Request
and actual coverage remain distinct and are recorded in TDB.

The acquired file must be validated before publication:

- binary DAF/SPK identity;
- exactly one applicable target segment for the resolved provider target;
- solar-system centre `10`;
- ICRF frame `1`;
- SPK segment type `21`;
- actual segment coverage containing the complete requested interval;
- Horizons identity, command, solution, and target consistency;
- SHA-256 of the exact SPK bytes.

Interpolation coverage is not a claim of uniform orbital accuracy. Automatic
acquisition trusts the provider's current operational solution; the accepted
Encke and 161P fixtures remain independent numerical oracles and are not
rewritten or replaced.

## Non-gravitational and photometric provenance

The manifest retains whether Horizons declares comet non-gravitational terms
and the exact parameter values or explicit absence supplied by the chosen
solution. The SPK is treated as the provider's complete modeled nucleus state.
Wenu neither reapplies nor removes those terms.

Comet dynamics, total-coma photometry, nuclear photometry, coma, tail, and
photocentre remain separate. Acquisition may retain provider photometric
parameters as provenance, but it computes no apparent magnitude and makes no
visibility claim.

## Immutable resource and policy behavior

Publication reuses the accepted numbered-asteroid rules:

- write only inside a fresh staging directory;
- validate identity, receipt, digest, segment, and coverage before publication;
- publish under a content-addressed immutable directory;
- serialize concurrent work through a normalized identity lock;
- never overwrite a referenced manifest or valid resource;
- leave no published resource or index entry after failure.

`offline` performs no network access and reports the missing exact identity
and required coverage. `acquire-if-missing` reuses an adequate verified
resource and otherwise acquires one. `refresh` always obtains a new current
provider solution and publishes it immutably. A warm-cache result must not
contact SBDB or Horizons.

The explicit `--minor-body-resource-directory` contract remains authoritative
and offline. Connecting exact comet selections and these policies to
`wenu_chart` is deferred to 50A.5D.2C.

## Manifest contract

The installed record must retain at least:

- canonical and primary designation, designation class, permanent number and
  fragment when present, official name, aliases, classifications, and SBDB
  SPK-ID;
- exact Horizons command/record, SPK target, orbit solution, solution date,
  osculating epoch, and non-gravitational provenance;
- request and actual coverage with time scales;
- provider/service signatures, exact request parameters, retrieval instants,
  response receipts, filenames, and SHA-256 digests;
- SPK centre, frame, type, and segment coverage;
- Wenu acquisition implementation/version and selected data policy.

The resulting directory must load unchanged through
`MinorBodyResourceCollection` and `MinorBodyResourceSession`. Rendering
continues to consume only that verified local resource.

## Ownership

- `minor_body_identity.py` continues to own exact installed/provider identity,
  not SPK acquisition.
- `minor_body_acquisition.py` becomes the shared acquisition, coverage,
  validation, lock, and immutable-publication owner.
- `minor_body_resources.py` remains the installed manifest and open-resource
  lifecycle authority.
- `tools/install_comet_resource.py` remains the accepted-fixture installer;
  it is not imported as the live acquisition implementation.
- `cli/chart.py` and renderers do not change in 50A.5D.2B.

The coordinate-system guide was reviewed. This slice changes data availability
and provenance only: target state remains TDB/ICRF from a verified type-21 SPK,
observer state and apparent correction remain in the existing shared path, and
no coordinate or product-frame meaning changes.

## Test placement

Extend `tests/test_minor_body_acquisition.py`, which already owns policy,
coverage, locking, publication, cache reuse, and acquisition failures. Do not
create a milestone-specific test file and do not repeat type-21 interpolation,
direction, projection, renderer, or export tests.

Add only the new seam evidence:

- exact resolved comet identity reaches the Horizons lookup;
- unique apparition/solution binding and no first-result fallback;
- generic manifest formation and loadability;
- target, solution, segment, coverage, digest, signature, and
  non-gravitational failures;
- atomic cleanup and concurrent identity locking;
- warm-cache and `offline` paths attempt no network;
- asteroid behavior remains accepted through its existing wrapper.

Frozen provider responses own deterministic parsing. One deliberate live
diagnostic is acceptance evidence, not a routine network test.

## Acceptance specimen and gates

`10P/Tempel 2` is the first uninstalled operational specimen because 50A.5D.2A
already validated its exact SBDB identity. It is not a special runtime case.

Acceptance requires:

1. Fernando accepts the bounded provider, apparition, provenance, failure, and
   non-goal contract;
2. focused deterministic acquisition, identity, resource, and documentation
   tests pass;
3. a deliberate live diagnostic proves unique Horizons record/solution binding
   for `10P` and records the returned command and target;
4. the acquired type-21 SPK covers the declared interval and loads through the
   existing resource collection/session;
5. a warm-cache repeat performs no network access;
6. the accepted Encke and 161P numerical fixtures remain unchanged;
7. `git diff --check` and the complete Mac suite pass;
8. review confirms no chart, coordinate, projection, renderer, magnitude, or
   report behavior changed.

Acceptance of this audit authorizes only the bounded 50A.5D.2B acquisition
service. It does not authorize 50A.5D.2C CLI preflight integration or
50A.5D.3 reports.
