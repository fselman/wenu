# Repository source index (Milestone 49J.3C)

**Status:** Implemented for review.

## Scope

49J.3C audits and consolidates immutable repository-source discovery, reading,
and parsing used by architectural tests. It changes no installed package,
runtime behavior, marker, chart path, scientific calculation, or output.

The audit found one global AST scan in `test_package_boundaries.py`, repeated
AST work over its `src/wenu/objects` and `src/wenu/sky` subsets in
`test_dependency_boundaries.py`, and a separate text scan over tools and
examples. The 49J.1 "canonical cartoon legacy-import scan" is instead an
independent subprocess/import-isolation oracle; 49J.3C deliberately leaves it
unchanged.

## Implementation and retained fault models

`tests/repository_sources.py` owns one deterministic, session-local tuple of
all Python paths below `src`, `tests`, `examples`, `tools`, and
`example_scripts`. Each frozen record lazily caches its UTF-8 text and parsed
AST. `sources_below()` supplies cached immutable subset tuples.

The architectural tests retain independent assertions and diagnostics:

- package dependency direction still applies `PACKAGE_RULES` package by
  package;
- obsolete static and literal dynamic imports still cover every Python file
  below `src`, `tests`, and `examples`, except the test containing the forbidden
  literals;
- domain reverse-dependency and direct-draw rules remain separate tests;
- tools and examples still receive their distinct retired-coordinate token
  check; and
- `test_repository_sources.py` independently enumerates every applicable
  `.py` path and proves exact inventory equality, preventing silent omissions.

No assertion consumes a mutable production cache. The index lives only in the
pytest process, and repository files are immutable inputs for that run.

## Measurement and acceptance

On the Linux review environment at base `6fc8bee`, three unmodified baseline
runs of the two affected boundary modules passed 13 tests in 2.54, 2.39, and
2.38 seconds (median 2.39 seconds). Three post-change runs, including the new
inventory-coverage test, passed 14 tests in 2.43, 2.49, and 2.52 seconds
(median 2.49 seconds). This environment therefore does not demonstrate a
wall-time improvement; it demonstrates removal of duplicated discovery,
reading, and parsing work while adding coverage. Mac measurement must decide
whether its slower filesystem makes that consolidation materially faster.

The broader Linux routine gate reached 2,091 passes and 24 deselections, but
14 unrelated cases could not load the absent `de440s.bsp` through this
environment's failing TLS certificate path or depended on a different
Matplotlib SVG serialization. Those environment failures do not touch the
changed boundary tests and are not recorded as acceptance.

Acceptance requires focused boundary and documentation tests, three routine
and three complete Mac runs, unchanged gate semantics, order checks, and a
deliberate forbidden-import fault experiment. The coordinate-system guide was
reviewed and remains current because this test-only index changes no scientific
meaning, ownership, provenance, coordinate explanation, or runtime API.

## Non-goals

49J.3C does not consolidate tests, weaken forbidden-import lists, cache mutable
runtime objects, alter catalogue or sphere fixtures, change parallel policy,
or optimize the independent subprocess/import-isolation oracle.
