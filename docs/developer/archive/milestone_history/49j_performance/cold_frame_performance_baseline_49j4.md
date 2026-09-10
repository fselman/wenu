# Cold independent-frame performance baseline (Milestone 49J.4)

**Status:** Accepted and merged in `f4dcf11`.

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
Console progress advances from 0 to 100 percent by frame and reports frame and
cumulative elapsed time plus the closed-accounting result.

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

Fernando's Intel Mac ran commit `db830c9` with Python 3.11.7 on
`macOS-10.16-x86_64-i386-64bit`. All three frames completed with zero-nanosecond
accounting deltas and identical 1677 by 1740 pixel dimensions. Their PNG sizes
were 466,888, 466,978, and 466,900 bytes, and their distinct SHA-256 digests
began `a3323334`, `73f7e7ea`, and `c9416a16`. The ephemeris was `de440s.bsp`
with SHA-256 `c1c7feeab882263fc493a9d5a5b2ddd71b54826cdf65d8d17a76126b260a49f2`.

Median complete-frame time was 25.509 seconds, with a 24.870-second minimum,
30.739-second maximum, and 5.869-second range. Median exclusive spans were
0.057 seconds request/orchestration, 8.447 catalogue/resource loading, 6.661
provider evaluation, 0.962 astronomical transformation, 0.644 projection,
3.604 chart preparation, 2.421 rendering, and 2.685 encoding/export. The
first-run-sensitive astronomical-transformation range of 2.889 seconds remains
visible rather than being discarded or averaged away.

Mac regression acceptance passed 139 focused tests in 7.31 seconds; 2,114
routine tests with 24 deselected in 28.03 seconds; and all 2,138 tests in
79.21 seconds. The retained real observer-time sequence remained the slowest
complete-suite test at 20.96 seconds. These values characterize the accepted
cold baseline; they introduce no timing threshold or optimization claim.

Fernando accepted this baseline; 49J.5 reuse work is authorized only through
separately reviewed bounded slices.

The coordinate-system guide was reviewed and remains current: this diagnostic
observes the existing coordinate and rendering owners without changing
scientific meaning, provenance, frames, epochs, equinoxes, transformations, or
visible output.

**Runtime effect:** None outside explicit diagnostic execution.

**Test behavior effect:** Three unit contracts were added to the existing
fixed-sky baseline test module; no new test file, marker, fixture scope, or
release-gate threshold was introduced.
