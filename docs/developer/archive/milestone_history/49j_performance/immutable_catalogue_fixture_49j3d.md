# Immutable catalogue fixture (Milestone 49J.3D)

**Status:** Accepted and merged in `63beb17`.

## Scope and audit result

49J.3D audits the accepted D5--D10 fixture policy against repeated catalogue
and canonical-sphere construction. It introduces only one bounded reuse: the
two polar-binocular target assertions may share immutable evidence extracted
from five identically requested packaged catalogues.

The canonical sphere is not eligible for session scope. Its layers own mutable
selection and observer-geometry caches, and the horizon-order contract
temporarily adds and replaces a horizon layer. `test_maximal_sphere.py` retains
an independent cold canonical factory build; `test_reusable_canonical_sphere.py`
retains its narrower module-scoped sphere specifically to test reuse and order;
`test_request_horizon.py` retains another cold sphere because mutation and
restoration are the behavior under test. No sphere/build registry is installed.

## Shared value and safety proof

`test_polar_binocular_targets.py::catalogue_positions` loads the canonical
nonstellar, galaxy, open-cluster, globular-cluster, and planetary-nebula
catalogues once per module. It discards every mutable Astropy table and exposes
only nested `MappingProxyType` values containing catalogue-family strings,
identifier strings, and declination `float` values. Both outer and inner
mutation attempts are required to raise `TypeError`.

Construction is not the behavior independently under test in either consumer:
one assertion owns exact identifier presence and order, while the other owns
north/south overlap counts. Their failure meanings and test names remain
separate. The object classes' own catalogue modules retain cold `load()` tests,
normalization, selection, geometry, and metadata coverage. The fixture owns no
resource requiring teardown.

Acceptance requires forward, reverse, and isolated execution to produce the
same results, a deliberate missing-identifier fault to fail during immutable
summary construction, three before/after Mac timings, routine and complete
gates, and unchanged counts. The coordinate-system guide was reviewed and
remains current because this test-only fixture changes no scientific meaning,
catalogue provenance, coordinates, runtime owner, or installed API.

## Initial measurement

At base `23d1b32` in the Linux review environment, three cold module runs
passed three tests in 1.27, 1.21, and 1.47 seconds (median 1.27 seconds). The
two repeated catalogue consumers respectively cost about 0.21--0.23 and 0.20
seconds. Three post-change runs passed in 1.11, 1.18, and 1.20 seconds (median
1.18 seconds), a local diagnostic reduction of about 7 percent. Reverse and
isolated orders also passed. Replacing `NGC0224` in a temporary copy of the
packaged galaxy catalogue caused immutable-summary construction to fail with
the exact missing identifier.

Fernando's Mac measurement at branch commit `72340d6` passed three cold module
runs in 2.69, 1.78, and 2.11 seconds (median 2.11 seconds; range 0.91 seconds).
The unchanged `main` baseline passed in 2.33, 2.62, and 2.22 seconds (median
2.33 seconds; range 0.40 seconds). Total median elapsed time fell by 0.22
seconds, about 9.4 percent, but process-start variability is larger than that
difference. The directly attributed catalogue work is clearer: two baseline
loads had a combined median near 0.76 seconds, while the shared setup had a
0.38-second median, an approximately 50-percent reduction in the intended
work.

Mac verification passed 159 focused documentation, catalogue, geometry, and
cold-factory tests in 17.49 seconds; 2,106 routine tests with 24 deselected in
26.66 seconds; and all 2,130 tests in 85.61 seconds. Complete-suite durations
continued to report the cold canonical factory, module-scoped reusable sphere,
and independently mutated horizon sphere as three distinct nodes.

## Non-goals

49J.3D does not share mutable tables, observers, provider state, figures,
artists, output paths, chart views, prepared geometry, scientific results, or
canonical spheres. It does not change fixture scope outside the one target
module, remove cold builders, consolidate assertions, or alter markers.
