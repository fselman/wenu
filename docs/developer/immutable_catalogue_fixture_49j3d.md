# Immutable catalogue fixture (Milestone 49J.3D)

**Status:** Implemented for review.

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
the exact missing identifier. Post-change Mac measurements remain the
acceptance authority.

## Non-goals

49J.3D does not share mutable tables, observers, provider state, figures,
artists, output paths, chart views, prepared geometry, scientific results, or
canonical spheres. It does not change fixture scope outside the one target
module, remove cold builders, consolidate assertions, or alter markers.
