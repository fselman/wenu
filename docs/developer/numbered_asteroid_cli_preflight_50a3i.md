# Numbered-asteroid CLI preflight (Milestone 50A.3I)

**Status:** Accepted by Fernando

**Acceptance:** On 2026-09-12, the focused macOS gate passed all 181 tests
in 5.12 seconds and the complete repository gate passed all 2,248 tests in
91.13 seconds. Fernando then accepted the generated charts after verifying
networked `refresh`, warm-cache `offline`, and automatic acquisition for both
numbered asteroids `(79989)` and `(79990)`.

## Scope

The installed `wenu_chart` command resolves positive permanent asteroid
numbers before chart construction. Its default `acquire-if-missing` policy
reuses a verified cached resource or obtains a bounded type-21 SPK from NASA
JPL Horizons, cross-checking identity with JPL SBDB. `offline` permits only a
verified warm cache, while `refresh` requests a new provider solution.

An explicit `--minor-body-resource-directory` remains authoritative and
offline. Automatic official-name lookup, comets, artificial satellites,
generic orbital-element propagation, extrapolation, and fuzzy discovery are
not part of this milestone.

## Ownership and lifecycle

`minor_body_acquisition.py` owns network access, policy, coverage calculation,
verification, locking, staging, and content-addressed immutable publication.
`cli/chart.py` invokes that boundary once, before sphere, view, request, or
rendering construction. Those downstream owners continue to receive an
ordinary local resource directory and cannot perform network I/O.

The required interval contains the chart epoch, every observer-time sequence
epoch, and the endpoints of an asteroid track, with a thirty-day margin.
Cache acceptance verifies the manifest digest, permanent number, SPK target,
centre, reference frame, data type, and actual segment coverage. Publication
validates the complete staging directory before its atomic rename. A
per-selection lock prevents concurrent partial publication.

## Public contract

```text
--data-policy {acquire-if-missing,offline,refresh}
```

The packaged TOML default is:

```toml
[data]
moving_object_policy = "acquire-if-missing"
```

The policy covers numbered asteroid centers, symbolic points, and tracks.
Both `--center-on asteroid:79989` and the globally unique shorthand
`--center-on 79989` participate. Provider receipts preserve retrieval time,
request parameters, signatures, solution identity, and requested coverage.

## Acceptance gates

- focused acquisition, configuration, CLI, and documentation tests;
- the complete test suite with plugin autoload disabled;
- a cold-cache macOS CLI render proving automatic acquisition;
- an offline warm-cache repeat proving no network dependence;
- inspection of the produced point/center/track chart and immutable cache;
- clean branch status before merge.

All gates passed. The focused and complete test counts above, together with
the accepted cold/refresh and offline/warm-cache renders, close 50A.3I.
