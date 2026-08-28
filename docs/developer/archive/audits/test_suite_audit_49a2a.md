# Wenu test-suite audit: Milestone 49A.2A

**Status:** Implemented and locally accepted

**Baseline:** `8f66f5e`
**Audit date:** 2026-08-28

## Purpose

Restore a fast routine regression loop without weakening the complete
scientific, integration, visual, or physical acceptance suite.

## Measured baseline

On Fernando's Intel Mac, with third-party pytest plugin autoload disabled:

- complete suite: **1774 passed in 84.64 s**;
- existing marker-filtered candidate: **1761 passed, 13 deselected in 72.34 s**;
- direct `pytest` collection failed because two tests import repository-root
  `tools` modules, while `python -m pytest` passed.

The ten largest entries showed that runtime was concentrated rather than
distributed:

- one real two-frame sequence render and resume check: 20.61 s;
- one 300-DPI calendar-label containment check: 8.23 s;
- real LMC regression-fixture construction: 3.45 s;
- repeated real galaxy catalogue loading and transformation;
- repeated real Cen A chart construction;
- subprocess startup and full-tree source audits.

## Classification decisions

### Retained in the complete suite

No test is deleted in 49A.2A.

The real observer-time sequence test remains the end-to-end proof that
canonical frames render, differ, and resume. It is classified as
`integration` and `slow`.

The 300-DPI calendar-label containment check remains the physical typography
acceptance guard. It is classified as `visual` and `slow`; its per-label
canvas redraw is deliberately not rewritten until an equivalent extent
calculation is proved.

Real catalogue and real chart construction in the galaxy, deep-sky, Cen A,
bright-star, and circumpolar-LMC contracts are classified as `integration`.
Focused synthetic geometry, immutable value, and ordinary unit contracts
remain in the routine suite.

### Import reproducibility

The pytest configuration explicitly adds the repository root to the test
Python path. Both the `pytest` entry point and `python -m pytest` must
therefore collect repository-root audit tools consistently. Documentation
uses `python -m pytest` as the canonical invocation because it states the
interpreter unambiguously.

## Test gates

Routine development gate:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q \
  -m "not integration and not visual and not slow"
```

Target: **under 30 seconds on Fernando's Mac**.

Complete milestone-closure gate:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q
```

The complete gate remains mandatory before merging a milestone. A focused
scientific, SVG, visual, print, sequence, or classroom command may also be
mandatory when the milestone changes that behavior.

## Deferred audit work

After measuring 49A.2A locally:

- consolidate repeated immutable catalogue fixtures where it benefits the
  complete suite without leaking mutable state;
- replace broad real-content setup with synthetic geometry only when one real
  integration boundary remains;
- determine whether the deprecated-composition subprocess still protects a
  supported v0.9 API before retaining, replacing, or deleting it;
- cache parsed syntax trees inside package-boundary tests if their cost remains
  material;
- identify compatibility tests that become obsolete only after formal v0.9
  closure;
- do not remove tests merely to meet a time target.

## Acceptance

Fernando ran both gates on the Intel Mac on 2026-08-28:

- direct-`pytest` routine gate: **1744 passed, 30 deselected in 26.68 s**;
- complete `python -m pytest` gate: **1774 passed in 84.53 s**.

Direct `pytest` collection no longer fails, the routine suite is below the
30-second target, the complete suite preserves every baseline test, and no
test was deleted. Milestone 49A.2A is locally accepted.
