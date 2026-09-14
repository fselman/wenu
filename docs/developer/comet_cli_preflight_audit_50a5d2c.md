# Exact comet CLI preflight audit (Milestone 50A.5D.2C)

**Status:** Accepted by Fernando on 2026-09-13

**Base:** `cc6527ebbaa2fae0e28c7ee1ec05a19f57436895`

## Decision requested

Authorize only the request-level composition that connects the accepted exact
minor-body identity resolver and shared acquisition service to `wenu_chart`
before chart construction. This slice may make exact comet selections acquire
or reuse a verified local resource under the existing data policies. It does
not change comet state realization, chart geometry, projection, rendering,
photometry, discovery, or moving-object reports.

## As-is assessment

The chart interface already accepts installed comets as symbolic points,
tracks, and moving regional centers. `--comet`, `--comet-track`, and an
explicitly classed `--center-on comet:SELECTION` carry comet intent, while
`MinorBodyResourceCollection` supplies exact local aliases and
`MinorBodyResourceSession` binds the verified SPK to the existing shared
Solar-System state path.

The installed `wenu_chart` adapter already performs one preflight before
maximal-sphere and chart-view construction. That preflight currently collects
only positive permanent asteroid numbers and invokes
`ensure_numbered_asteroid_resources()`. Non-numeric asteroid names require an
explicit installed resource directory. Comet selections therefore work only
when that directory has already been installed and supplied.

50A.5D.2A now provides
`resolve_minor_body_identity(selection, expected_class=...)` and
`resolve_comet_identity()`. Resolution checks an installed collection first,
then performs one exact provider query, and rejects absent, ambiguous, partial,
wildcard, wrong-class, and bare-number comet selections without guessing.

50A.5D.2B now provides `acquire_minor_body_resources()` and
`ensure_minor_body_resources()`. They accept typed resolved identities,
bind a unique Horizons record and solution, validate one bounded type-21 SPK
per target, retain non-gravitational provenance, and publish one immutable
manifest-backed collection. The accepted service already supports an internal
identity iterable, cache reuse, `offline`, `acquire-if-missing`, and
`refresh`.

The missing seam is therefore request composition: collect every requested
minor body with its explicit class, resolve it exactly without unnecessary
network access, derive one coverage interval, acquire or reuse one collection,
and pass that single directory to the unchanged offline chart machinery.

## Selection contract

The preflight must collect exact minor-body requirements from all applicable
request roles:

- `--comet SELECTION`;
- every `--comet-track SELECTION`;
- `--center-on comet:SELECTION`;
- the already accepted `--asteroid NUMBER`, `--asteroid-track NUMBER`, and
  explicitly classed asteroid center forms.

The same normalized class-and-identity pair is acquired only once even when it
appears as a point, track, and center. Request order must not change the
identity set, cache key, manifest meaning, or scientific result.

Provider-backed uninstalled center resolution requires the explicit
`comet:` class prefix. This slice does not reinterpret an unqualified named
center as a comet and does not change constellation, deep-sky, planet, Moon,
or installed-name precedence.

Comet resolution is exact. `10P`, `10P/Tempel 2`, and the exact official
name `Tempel 2` may resolve to the same identity. `Tempel`, `10`,
wildcards, substrings, provider suggestions, and wrong-class results fail
without selecting a candidate. Production code may contain no special
`10P`, Tempel, record-number, or fixture branch.

This milestone does not expose automatic asteroid-name acquisition. Positive
permanent asteroid numbers retain their accepted public meaning. The internal
composition may resolve those numbers through the generic mandatory-class
identity boundary so that mixed asteroid-and-comet requests can publish one
collection, but `--asteroid Hygiea` remains outside the automatic CLI
contract.

## One request, one resource collection

A chart request exposes one effective minor-body resource directory. Automatic
preflight must therefore compose all requested exact asteroids and comets into
one verified collection rather than acquire per-class directories and let one
overwrite the other.

A mixed request such as an asteroid track plus a comet track must use:

1. one deduplicated tuple of typed identities;
2. one closed coverage interval;
3. one policy decision;
4. one immutable manifest-backed resource directory;
5. one `MinorBodyResourceSession` used by the existing chart realization.

Planets and the Moon do not enter this resource collection. Their accepted
ephemeris path remains unchanged.

## Explicit directory and network boundary

An effective `--minor-body-resource-directory`, whether supplied directly or
through configuration, remains authoritative and offline:

- load and validate that exact directory;
- resolve every requested minor body only against its installed aliases;
- require the directory to contain every requested identity and coverage;
- perform no SBDB or Horizons request;
- reject `--data-policy refresh`, as the current CLI already does;
- never supplement, mutate, replace, or shadow the explicit directory.

A missing, ambiguous, wrong-class, corrupt, or insufficient explicit resource
fails before chart construction and identifies the selection and required
coverage.

Without an explicit directory, preflight must inspect verified cached
collections for exact installed aliases before provider resolution. A warm
cache adequate for the full request performs no SBDB or Horizons access.
Provider resolution is permitted only for an exact selection not already
resolved by an adequate verified local collection.

`offline` performs no network access. It may use verified cache contents but
must report every unresolved or uncovered exact selection and the required
coverage. `acquire-if-missing` reuses an adequate complete collection or
resolves and acquires the missing request atomically. `refresh` resolves the
current provider identities and publishes a new immutable complete collection;
it does not overwrite prior resources.

## Coverage contract

Preflight derives one closed TDB acquisition interval from every relevant
instant already owned by the request:

- the chart observation instant;
- every minor-body point or moving-center evaluation instant;
- every asteroid or comet track start and stop;
- every applicable shared sequence instant;
- the accepted coverage margin.

Comet and asteroid tracks continue to share their existing timeline.
Preflight must not create a second timeline, sample a track, evaluate a target,
or calculate a chart direction. The acquired interval is data availability,
not an orbital-accuracy, visibility, or brightness claim.

## Ordering and lifecycle

The order remains:

```text
parse request and effective configuration
    -> construct observer and shared temporal options
    -> collect typed minor-body selections and coverage instants
    -> resolve exact installed/provider identities
    -> verify, reuse, or acquire one immutable resource collection
    -> set the effective minor-body resource directory
    -> construct maximal sphere and resolve center/content
    -> open one ordinary MinorBodyResourceSession
    -> realize, project, render, and export unchanged
```

No network access may occur after chart construction begins. Failure in
identity, policy, acquisition, publication, manifest validation, or coverage
must stop before maximal-sphere construction and leave no partial published
resource.

The preflight result owns any diagnostic such as “acquired” or “reused”.
Libraries do not print. Messages name generic minor-body resources rather than
claiming that a mixed collection is asteroid-only.

## Responsibility boundaries

- `cli/chart.py` owns request-level selection collection, exact preflight
  ordering, policy composition, diagnostic output, and the effective resource
  directory.
- `minor_body_identity.py` remains the sole exact installed/provider identity
  owner.
- `minor_body_acquisition.py` remains the sole network, Horizons binding,
  coverage validation, locking, staging, and immutable-publication owner.
- `minor_body_resources.py` remains the installed manifest, alias, target,
  coverage, and session-lifecycle authority.
- `charts/command_line.py` and `charts/chart_arguments.py` retain parsing and
  request translation; they do not acquire data.
- coordinate, state, temporal-component, projection, renderer, semantic, style,
  furniture, and export owners remain unchanged.

This slice changes resource availability and orchestration only. It introduces
no coordinate system, origin, frame, epoch, equinox, correction, observer,
time-scale, or product-frame meaning.

## Failure contract

The CLI must fail closed before drawing when:

- any selection is absent, partial, ambiguous, wildcarded, or wrong-class;
- a bare asteroid number is supplied in comet context;
- an explicit directory lacks a requested identity or adequate coverage;
- offline cache lacks any requested identity or adequate coverage;
- SBDB identity and Horizons target disagree;
- Horizons lookup is non-unique or its solution changes during acquisition;
- the SPK, digest, segment, target, centre, frame, type, or coverage is invalid;
- atomic publication or post-publication revalidation fails.

No failure falls back to the first provider result, an unrelated installed
alias, the prior asteroid-only path, a builtin comet, or a partially adequate
resource directory.

## Test placement

Extend existing owners rather than add a milestone-specific test module:

- `tests/test_minor_body_acquisition.py` owns preflight policy composition,
  warm-cache, offline, mixed-set, coverage, publication, and network-boundary
  behavior;
- `tests/test_wenu_chart_cli.py` owns installed-adapter ordering and
  pre-construction failure;
- existing track and center tests continue to own request parsing and
  scientific realization and should not be duplicated;
- `tests/test_current_documentation.py` owns audit, roadmap, and source-tree
  consistency.

Required new seam evidence includes:

1. exact `10P` point, track, and explicit comet center deduplicate to one
   resolved identity;
2. exact `Tempel 2` succeeds while `Tempel`, `10`, and wildcards fail;
3. a mixed numbered-asteroid and comet request produces one collection;
4. explicit-directory and warm-cache paths contact neither SBDB nor Horizons;
5. `offline` failure identifies all missing identities and coverage;
6. refresh publishes a new immutable collection;
7. coverage includes chart, track, center, and applicable sequence instants;
8. all identity/acquisition failures occur before sphere construction;
9. existing numbered-asteroid behavior remains accepted;
10. no coordinate, realization, renderer, semantic, or export regression test
    is repeated.

Frozen responses remain the deterministic provider authority. One deliberate
live Mac diagnostic may verify `10P/Tempel 2` automatic acquisition and an
immediate offline chart repeat; it is acceptance evidence, not a routine
network test.

## User-visible acceptance specimen

The acceptance specimen should exercise an ordinary chart command with an
exact uninstalled `10P` or `10P/Tempel 2` selection, a bounded September–
October 2026 track, and no explicit resource directory. The first run should
report one automatic acquisition and render through the accepted comet path.
An immediate `--data-policy offline` repetition should reuse the same
immutable collection and produce the same scientific chart content without
network access.

A second deterministic or live diagnostic should include one numbered
asteroid and one comet track in the same request, proving that a single
effective directory preserves the already accepted simultaneous-track
contract. Visual review is required only to confirm that the existing symbols,
tracks, labels, and center semantics remain unchanged; this milestone
authorizes no new visible design.

## Acceptance gates

Acceptance requires:

1. Fernando accepts this bounded integration, precedence, network, coverage,
   mixed-resource, failure, and non-goal contract;
2. focused identity, acquisition, CLI, center/track, and documentation tests
   pass;
3. the complete Mac regression passes and `git diff --check` is clean;
4. a live Mac first-run acquisition and immediate offline reuse succeed;
5. mixed asteroid-and-comet preflight uses one verified collection;
6. review confirms all provider access precedes chart construction;
7. review confirms existing explicit-directory reproducibility is unchanged;
8. visual comparison confirms no unintended chart-output change.

Acceptance of this audit authorizes only the 50A.5D.2C exact comet CLI
preflight composition. It does not authorize observer-dependent comet
magnitude, discovery-result handoff, fuzzy lookup, automatic asteroid-name
acquisition, new comet graphics, physical coma or tail modeling, or 50A.5D.3
reports.


## Acceptance

Fernando accepted this bounded audit on 2026-09-13 after the focused
current-documentation gate passed all 115 tests in 2.84 seconds. Final Mac
verification passed the updated 115-test documentation gate in 2.62 seconds
and the complete 2,389-test regression in 82.59 seconds. The branch was clean
and synchronized and `git diff --check` was clean.

This acceptance authorizes only implementation of the request-level exact
comet CLI preflight composition specified above. It does not authorize any of
the explicitly excluded magnitude, discovery handoff, fuzzy lookup, graphics,
asteroid-name acquisition, or reporting behavior.

## Candidate implementation checkpoint

The implementation branch composes typed asteroid and comet point, track, and
explicit-center selections in `cli/chart.py`, derives one shared coverage
interval, validates an explicit directory, reuses an adequate complete warm
cache without provider access, and otherwise resolves and acquires one shared
immutable collection before sphere construction. It also formats expected CLI
failures without tracebacks while retaining an explicit `--debug` traceback
mode.

Mac acceptance passed 2,404 tests in 83.97 seconds with a clean synchronized
branch and clean `git diff --check`. Live `10P/Tempel 2` and `C/2006 P1`
diagnostics exercised acquisition and immediate offline reuse. The provisional
McNaught diagnostic additionally verified provider fullname ordering, manifest
prefix reconstruction, installed-identity reuse, and safe SVG semantic paths.
The attached live and offline charts completed with the same scientific chart
content. The deterministic mixed asteroid/comet test confirms one shared
verified collection.
