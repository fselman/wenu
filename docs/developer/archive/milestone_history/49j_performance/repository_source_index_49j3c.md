# Repository source index (Milestone 49J.3C)

**Status:** Accepted and merged in `23d1b32`.

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

Fernando's Mac measurement at branch commit `c81e7dd` supplied the required
same-environment comparison. The unchanged `main` baseline passed 13 boundary
tests in 4.28, 4.00, and 4.18 seconds (median 4.18 seconds; range 0.28 seconds).
49J.3C, including the new full-inventory test, passed 14 tests in 5.39, 3.80,
and 3.70 seconds (median 3.80 seconds; range 1.69 seconds). The observed median
improvement is 0.38 seconds, or about 9.1 percent, while increasing coverage.

Three Mac routine runs each passed 2,105 tests with 24 deselected in 33.20,
33.22, and 36.05 seconds (median 33.22 seconds; range 2.85 seconds). Three Mac
complete runs each passed all 2,129 tests in 89.59, 89.10, and 90.39 seconds
(median 89.59 seconds; range 1.29 seconds). The canonical observer-time sequence
remained the leading complete-suite node at 21.48--22.77 seconds, and the
independent cartoon subprocess/import-isolation oracle remained at
2.03--2.08 seconds.

Acceptance requires focused boundary and documentation tests, three routine
and three complete Mac runs, unchanged gate semantics, order checks, and a
deliberate forbidden-import fault experiment. The coordinate-system guide was
reviewed and remains current because this test-only index changes no scientific
meaning, ownership, provenance, coordinate explanation, or runtime API.

## Non-goals

49J.3C does not consolidate tests, weaken forbidden-import lists, cache mutable
runtime objects, alter catalogue or sphere fixtures, change parallel policy,
or optimize the independent subprocess/import-isolation oracle.
