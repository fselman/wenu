# Cold builders and installed-kernel oracles (Milestone 49J.3E)

**Status:** Implementation complete; awaiting Mac regression evidence.

## Scope and audit result

49J.3E audits the remaining expensive cold builders and the standalone
installed-DE440 scientific validators under accepted decisions D5--D10. The
result is an explicit preservation decision: no new fixture, build registry,
kernel cache, observer cache, or scientific-result cache is installed.

The complete-render, canonical-factory, reusable-sphere order, horizon
mutation/restoration, and observer-time sequence tests construct distinct
artifacts because construction, mutation isolation, order independence, or a
real end-to-end path is part of each oracle. Sharing one sphere between those
tests would merge their failure meanings and could conceal leaked selection,
observer geometry, horizon, provider, or layer-cache state.

## Installed-kernel validation boundary

The DE440 checks live in independently invoked `tools/validate_49e*.py` and
`tools/validate_49i*.py` commands rather than the committed pytest suite. Each
applicable command creates a fresh `Observer`, obtains the Wenu result through
the public provider or chart path, and independently recomputes its direct
Skyfield comparison for the requested instant. Direction, light-time,
apparent-place, parallax, physical appearance, frame, equinox, and epoch
evidence therefore remains local to one validator execution.

The installed kernel's immutable bytes may already be reused by the operating
system's file cache. Wenu must not add a cross-validator registry: the commands
run in separate processes, refuse an unavailable kernel instead of downloading
one, and share no repeated in-process setup to optimize. Sharing an observer,
requested time, direct Skyfield result, Wenu result, or tolerance decision
would violate D9's independent-recomputation rule. A future immutable kernel
handle may be considered only after measured repeated work exists inside one
process and the comparison path, observer state, time, and result remain fresh.

## Preserved cold oracles

- `test_maximal_sphere.py` retains the independent cold ordinary factory.
- `test_reusable_canonical_sphere.py` retains its module-scoped sphere because
  reuse and forward/reverse family order are the behavior under test.
- `test_request_horizon.py` retains a separate cold sphere because temporary
  horizon mutation and restoration are the behavior under test.
- canonical complete rendering retains its public request-to-output path.
- `test_chart_sequence.py` retains real independent observer-time frames.

49J.3D Mac complete-suite durations continued to expose these as distinct
nodes: 3.43 seconds for the cold ordinary factory, 3.70 seconds for reusable
sphere setup, 3.28 seconds for the horizon-order case, and 20.72 seconds for
the real observer-time sequence. Those measurements characterize different
oracles; they are not duplicate-work evidence authorizing consolidation.

## Acceptance and effects

Acceptance requires documentation-contract tests plus routine and complete Mac
gates with unchanged counts. No speedup is claimed. The coordinate-system
guide was reviewed and remains current because this audit changes no scientific
meaning, provenance, coordinate, frame, epoch, equinox, installed interface,
runtime owner, test behavior, marker, output, or cache.

**Runtime effect:** None.

**Test behavior effect:** None.

## Non-goals

49J.3E does not weaken, merge, skip, or reclassify an oracle; share mutable
spheres, observers, provider state, selections, figures, outputs, or scientific
results; add automatic ephemeris downloads; or convert standalone kernel
validators into ordinary committed tests.
