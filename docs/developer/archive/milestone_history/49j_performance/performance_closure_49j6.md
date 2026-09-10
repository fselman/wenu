# Performance closure (Milestone 49J.6)

**Status:** Accepted performance program; documentation closure pending merge.

## Scope and accepted implementation

49J closes the measured test and production-performance program without adding
another runtime change. PR #88, merged as `de78e14`, installed the bounded
loaded-sphere reuse seam. PR #89, merged as
`a028e8945f5f2903702adbc2cbd2a46e3bffff06`, installed its exact equivalence
diagnostic and retained evidence. Cold execution remains the default
complete-render correctness oracle, and `reuse_loaded_sphere` remains an explicit,
selectable route.

Reuse is limited to one observer-independent loaded canonical celestial sphere
identified by its immutable load profile. Every frame still creates and closes
a fresh `Observer` and follows the canonical realization, transformation,
projection, preparation, rendering, and export route through
`generate_chart_request()`. No mutable observer-local state, projected state,
renderer state, or product is shared.

## Final Mac equivalence and performance evidence

Fernando ran `tools/benchmark_fixed_sky_reuse.py` at commit `167d379` with
Python 3.11.7 on macOS-10.16-x86_64-i386-64bit. The accepted threshold was
exact. All three frames matched exactly for scientific evidence and for PNG,
normalized semantic SVG, and rendered PDF. The PDF comparison used the built-in
macOS `sips` renderer. Fernando also visually accepted the six paired PNG
frames.

| Format | Cold | Reuse | Speedup |
| --- | ---: | ---: | ---: |
| PDF | 34.934 s | 28.094 s | 1.243x |
| PNG | 35.897 s | 25.267 s | 1.421x |
| SVG | 55.511 s | 49.019 s | 1.132x |

Cold execution built three canonical spheres; `reuse_loaded_sphere` built one.
The raw durations and ratios are characterization evidence, not enforced
performance thresholds.

## Final acceptance gates

The two non-overlapping Mac gates covered all 2,146 collected tests:

- routine: 2,122 passed, 24 deselected in 33.24 seconds;
- integration, visual, or slow: 24 passed, 2,122 deselected in 56.47 seconds.

The accepted benchmark additionally supplies focused scientific, projected-
record, clipping, furniture, normalized-SVG, PNG, rendered-PDF, and sequence
evidence. The retained cold route and the reused route remain independently
selectable.

## Documentation and ownership audit

Current architecture, implementation reference, source tree, roadmap, and
assistant guidance were reconciled with the accepted ownership. The coordinate-
system guide was reviewed and remains current because the reuse seam changes no
coordinate meaning, reference epoch, equinox, product frame, projection,
provenance, or output semantics.

The user guide contained one stale statement that described scientifically
keyed reuse as future work; that planning statement was corrected. No CLI
example changes are required because 49J.5 adds no CLI selector, default, or
output change. No architecture-diagram change is required because the same
sequence orchestrator and complete canonical static pipeline retain ownership;
only the lifecycle of one observer-independent loaded input differs.

## Closure

Milestones 49J.0 through 49J.6 are accepted and archived. Both the cold oracle
and measured reuse route are retained. The next authorized work is Program
50A.0, the scientific and provider audit for asteroids and comets.

**Runtime effect:** None; this closure changes documentation and documentation
contracts only.

**Test behavior effect:** Documentation contracts follow the archived records
and closed status; no runtime assertion, marker, fixture, or gate changes.
