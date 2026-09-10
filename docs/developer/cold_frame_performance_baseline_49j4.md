# Cold independent-frame performance baseline (Milestone 49J.4)

**Status:** Implementation complete; awaiting Mac measurement and Fernando's
review.

## Scope

49J.4 adds a diagnostic cold-frame harness; it adds no cache, performance
threshold, alternate renderer, or chart-output change. Each of three accepted
fixed-sky circumpolar frames is resolved independently and passed once through
the unchanged `generate_chart_request()` complete-render oracle. Products and
the JSON report must be written to caller-selected paths outside the
repository.

`tools/benchmark_reusable_sphere.py` remains a separate shared-sphere and
overlapping-cProfile diagnostic. Its values are not combined with this
independent-frame table.

## Exclusive accounting

`tools/benchmark_cold_frames.py` uses `time.perf_counter_ns()` and Python call
profiling to maintain the active call stack. Every interval between profiler
events is charged to the deepest declared owner, so nested work belongs to
exactly one of these spans:

1. request/orchestration;
2. catalogue/resource loading;
3. provider evaluation;
4. astronomical transformation;
5. projection;
6. chart preparation;
7. rendering;
8. encoding/export.

Time with no declared owner, including profiler overhead and narrow boundary
work, is reported as `unclassified_residual`. For every raw observation, the
eight spans plus residual equal `complete_frame` exactly. The report retains
raw nanoseconds and derives median, minimum, maximum, and range for every span.
These are characterization values, not additive cProfile totals or test gates.

## Reproducible evidence

The fixed offline workload uses La Ligua and three UTC instants from
2026-08-22 01:00 through 07:00, with a south circumpolar field limited at
-60 degrees. Every frame records its exact canonical request, timeline,
anchor-relative orientation, output format, pixel dimensions, byte count,
SHA-256 digest, semantic paths, and projected record types. The report also
records the Wenu commit, Python and platform identity, canonical catalogue
load profile, and DE440s ephemeris identity.

The semantic paths and projected record types are comparison evidence captured
from the result returned by `generate_chart_request()` itself. They do not
replace later 49J.5 candidate-versus-oracle scientific, normalized-SVG, PNG,
PDF, clipping, furniture, and visual equivalence checks.

## Operation

Run from the repository root with explicit destinations outside the checkout:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python tools/benchmark_cold_frames.py \
  --output /tmp/wenu-49j4/frames \
  --report /tmp/wenu-49j4/cold-frames.json
```

Run the existing reusable-sphere diagnostic separately if comparison evidence
is desired. Do not reinterpret either harness as a pass/fail benchmark.

## Acceptance

Mac acceptance must confirm three completed frames, closed exclusive accounts,
environment and resource identity, output hashes and dimensions, and a clean
working tree. Record the raw report summary here before integration. No 49J.5
reuse work is authorized until Fernando accepts this baseline.

The coordinate-system guide was reviewed and remains current: this diagnostic
observes the existing coordinate and rendering owners without changing
scientific meaning, provenance, frames, epochs, equinoxes, transformations, or
visible output.

**Runtime effect:** None outside explicit diagnostic execution.

**Test behavior effect:** Three unit contracts were added to the existing
fixed-sky baseline test module; no new test file, marker, fixture scope, or
release-gate threshold was introduced.
