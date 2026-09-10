# Canonical observer-time sequence oracle (Milestone 49J.3G)

**Status:** Mac regression-verified; awaiting Fernando's review.

## Scope and decision

49J.3G applies accepted decision D22 to the remaining approximately 21-second
canonical observer-time sequence test. The decision is to retain the test
unchanged. No fixture, mock, injected sphere, reduced frame count, cache, or
alternate generation route is introduced.

`test_observer_time_sequence_generates_real_canonical_frames` already uses the
minimum scientifically meaningful sequence of two instants. Every frame enters
through `generate_observer_time_chart_sequence()` and
`generate_chart_request()`, creates its real observer-bound canonical sphere,
renders its PNG, and records it in the restart manifest. The test verifies both
outputs, equal image dimensions, different image bytes, and zero-render resume
of those verified outputs. Those assertions jointly detect per-frame observer
time errors and exercise the complete public route.

## Rejected reuse

The catalogues and fixed-sky source data are conceptually invariant, but the
current complete route binds each sphere and several layer objects to its
observer. Supplying the existing observer-independent reusable sphere would
require a different preparation/generation path and would stop this test from
being the cold complete-route oracle. Mocking or injecting a prepared sphere
would violate D22 directly.

Changing production sequence orchestration to reuse scientifically keyed
fixed-sky state is also outside 49J.3. The accepted program requires the
independent-frame timing harness in 49J.4 before the first fixed-sky reuse in
49J.5. This test remains the later comparison authority, not the place to
pre-empt that measurement.

## Acceptance and effects

Acceptance requires the unchanged canonical sequence test, its surrounding
sequence/manifest contracts, the routine gate, and the complete gate to pass
on Mac with unchanged scientific and output assertions. No speedup is claimed.
The coordinate-system guide was reviewed and remains current because no
observer, instant, frame, coordinate, provider, or output meaning changes.

Fernando's Mac verification passed the isolated real canonical sequence in
24.69 seconds, with 22.90 seconds in the test call. The combined documentation,
sequence, and manifest slice passed 101 tests in 25.30 seconds; the routine gate
passed 2,109 tests with 24 deselected in 26.54 seconds; and all 2,133 tests
passed in 76.85 seconds. The complete suite continued to report the real
canonical sequence as its slowest test at 20.79 seconds. That retained cost is
the expected evidence that the complete-route oracle was neither removed,
mocked, nor hidden.

**Runtime effect:** None.

**Test behavior effect:** None.

## Non-goals

49J.3G does not optimize chart generation, introduce reusable fixed-sky state,
change sequence APIs, share observers or mutable layers, alter manifest
semantics, weaken PNG comparison, or remove `integration` or `slow` markers.
