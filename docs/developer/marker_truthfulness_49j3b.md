# Test-marker truthfulness (Milestone 49J.3B)

**Status:** Implementation complete; Mac verification pending
**Implementation baseline:** `21ee528`
**Runtime effect:** None
**Test assertion and fixture effect:** None

## 1. Purpose

49J.3B applies the accepted 49J.2 marker meanings to the committed suite. It
changes gate membership only where the operation and assertion demonstrate
that an existing marker is too broad. It does not delete a test, weaken an
assertion, change fixture scope, optimize runtime, or claim a speedup.

## 2. Accepted marker meanings

- unmarked routine tests are deterministic, offline, focused, and suitable for
  the normal feedback loop;
- `integration` crosses meaningful architectural component boundaries or
  exercises a canonical composition;
- `visual` validates rendered appearance, physical layout, or image structure;
- `slow` denotes work that remains intrinsically expensive after accepted
  optimization.

Markers describe work and resources, not filenames, imported libraries, or
incidental calls. Creating a Matplotlib artist, writing a temporary file, or
using a test name containing `visual` does not by itself require `visual`.
Multiple markers remain valid when the meanings independently apply.

## 3. Audit result

The committed function- and module-level `integration`, `visual`, and `slow`
markers were inspected against their setup and assertions. The canonical
observer-time sequence remains both `integration` and `slow`. The 300-dpi
calendar-label containment check remains both `visual` and `slow`. Existing
function-level integration tests retain their classifications because they
build canonical compositions or cross meaningful production boundaries.

One module-level classification was too broad. In
`tests/test_planisphere_composition.py`, only these tests inspect rendered
appearance or physical image layout:

- the exported raster's transparent corner and opaque centre; and
- the rendered legend extents relative to the axes.

They now carry explicit `visual` decorators. The shared-background contract
and horizon/content-independence contract inspect deterministic geometry and
recorded calls, so their five parametrized cases return to the routine gate.
No assertion or setup changed.

The module-level `integration` marker in `tests/test_cen_a_binocular.py` was
also too broad. The two tests that build across the example/chart boundary now
carry explicit `integration` decorators. The focused constants contract
returns to the routine gate.

## 4. Installed scientific resources

No committed pytest case requires an installed DE440 kernel or another
external scientific resource. Tests mentioning DE440 use deterministic fake
resources; installed-kernel comparisons remain separately run scientific
acceptance procedures. Registering `scientific_validation` now would therefore
create an empty gate and misleading provenance. The marker remains a future
option for the first committed test that genuinely requires such a resource;
its absence or skip must then be reported explicitly.

## 5. Gate impact and acceptance

Before this change, the visual module marker selected all seven cases in
`test_planisphere_composition.py`; afterwards it selects two. The Cen A module
marker selected three integration cases; afterwards it selects two. The 49J.1
baseline plus this milestone's documentation contract therefore predicts
2,101 routine cases with 24 deselected, 21 integration cases, 3 visual cases,
2 slow cases, and 2,125 complete cases.
Mac collection is the acceptance authority for these counts. The complete
suite membership remains unchanged.

Acceptance requires:

- collection evidence for routine, integration, visual, slow, and complete
  gates before and after the change;
- the focused planisphere-composition and documentation tests;
- the routine and complete suites on the Mac with plugin autoload disabled;
- confirmation that only marker placement and its governing documentation
  changed test behavior; and
- no unexplained collection, scientific, rendering, or product regression.

The coordinate-system guide was reviewed. This milestone changes no
scientific meaning, provenance, implementation ownership, coordinate
transformation, or public coordinate explanation, so the guide remains
current.
