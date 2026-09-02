# Performance and post-v0.9 closure audit — Milestone 49J.0

**Status:** Proposed for architectural acceptance  
**Audit baseline:** `ea6f340`  
**Scope:** Documentation and documentation tests only  
**Runtime effect:** None

## 1. Decision requested

Accept a measured, correctness-first route into Milestone 49J.

49J.0 records the current execution and measurement seams, separates the
existing reusable-sphere diagnostic from the required independent-frame
oracle, freezes timing vocabulary and cache-key requirements, and divides
implementation into separately accepted slices. It does not add
instrumentation, caching, optimization, a timing threshold, or visible output.

## 2. Current authoritative baseline

The canonical chart path remains:

```text
request
    -> observer and catalogue/resource loading
    -> provider and spherical-layer realization
    -> CoordinateService transformation
    -> projection-domain guard and projection
    -> projected preparation and clipping
    -> Matplotlib rendering
    -> backend encoding and one export
```

`generate_chart_request()` owns one complete ordinary build and export.
`CelestialSphere.draw_chart()` remains the low-level execution core.
Sequences call the ordinary static path for every frame. The accepted
`generate_fixed_sky_rotating_horizon_sequence()` is deliberately uncached
and is the complete-render correctness reference for later fixed-sky reuse.

No 49J optimization may bypass, replace, or silently weaken this route.

## 3. Measured Mac test baseline

Fernando's Intel Mac produced the following clean-main baseline at
`ea6f340` plus the documentation-only 49J.0 candidate:

| Gate | Result | Wall time |
| --- | ---: | ---: |
| documentation closure immediately before 49J.0 | 76 passed | 2.30 s |
| routine: not integration, visual, or slow | 2,089 passed; 30 deselected | 31.89 s |
| complete suite | 2,119 passed | 87.44 s |

The current architecture says the routine gate is expected to finish in less
than 30 seconds on Fernando's Intel Mac. The observed 31.89 seconds is 1.89
seconds, or about 6.3 percent, above that target. One run is a baseline
observation, not enough evidence to attribute a regression or select an
optimization.

Before changing production code, 49J.1 must collect repeated timings and
`pytest --durations` evidence in the same environment. Test-loop speed and
product-render speed are different measurements and must not be conflated.

## 4. Existing performance machinery

### 4.1 Reusable-sphere diagnostic

`tools/benchmark_reusable_sphere.py` is useful and remains supported. It:

- builds one observer-independent canonical sphere;
- constructs six chart families for three observer/instant identities;
- performs 18 view preparations and 18 atlas-print PNG exports;
- reports 37 public-operation wall times;
- reports overlapping cProfile categories;
- records observed-cache entry counts and a compatible repeat check.

It intentionally has no pass/fail timing threshold.

### 4.2 What that diagnostic does not establish

The reusable-sphere diagnostic is not the 49J independent-frame baseline:

- it starts from one already shared sphere rather than measuring a fresh
  complete build for every frame;
- it combines drawing and export in one operation;
- its cProfile group totals overlap and therefore cannot be added into a wall
  time;
- it does not isolate provider evaluation, coordinate transformation,
  projection, preparation, renderer drawing, and backend encoding as exclusive
  spans;
- it exercises atlas-print PNG only;
- it is not paired with a candidate-versus-oracle equivalence comparison;
- it reports cache counts but not a complete scientific cache identity.

49J must preserve this tool as a reuse diagnostic while adding a distinct
baseline harness. It must not reinterpret historical numbers from this tool as
independent-frame timings.

### 4.3 Complete-render sequence oracle

`generate_fixed_sky_rotating_horizon_sequence()` calls
`generate_chart_request()` independently for every resolved frame. The
accepted 49H.3 visual result fixes the celestial scene while the local horizon
rotates, but the executor still performs complete ordinary builds. It is the
first 49J optimization target only after 49J.1 measures it.

`generate_observer_time_chart_sequence()` is also a repeated-static path, but
it changes the physical observer time for the whole chart. It remains a useful
comparison workload, not permission to treat its celestial, moving-body, and
observer-local dependencies as identical.

## 5. Frozen timing vocabulary

49J.1 must report the following non-overlapping wall-time spans for each cold
independent frame:

| Span | Begins | Ends |
| --- | --- | --- |
| request/orchestration | request validation and ownership setup | first scientific resource load |
| catalogue/resource loading | first packaged catalogue or ephemeris resource open | canonical sphere/resource set available |
| provider evaluation | first time-dependent astronomical state evaluation | native typed state/geometry available |
| astronomical transformation | first `CoordinateService` transform | product-frame spherical geometry available |
| projection | projection-domain preparation and projection entry | projected records available |
| chart preparation | first projected selection, clipping, mask, or label preparation | renderer-ready records available |
| rendering | first backend-neutral/Matplotlib draw operation | completed figure before save |
| encoding/export | save begins | verified output path complete |
| unclassified residual | complete-frame wall time minus the exclusive spans | report only |

Nested calls must be assigned to exactly one owning span for accounting.
Overlapping profiler totals may still be reported separately as diagnostic
evidence, clearly labelled non-additive.

Use `time.perf_counter_ns()` for wall spans. Record raw observations and
derive median and range; do not hide variability behind one rounded value.

## 6. Benchmark workloads

49J.1 must use deterministic, offline inputs and write outputs outside the
repository.

### 6.1 Cold independent-frame oracle

Use at least three accepted 49H.3 circumpolar frames with one fresh complete
canonical build per frame. Record:

- exact request and timeline identity;
- Wenu commit and Python/platform information;
- catalogue and ephemeris identities;
- output format, dimensions, and file size;
- exclusive stage timings and complete wall time;
- output hash and semantic/projection comparison evidence.

### 6.2 Reusable-sphere comparison

Run the existing six-family, three-observer benchmark unchanged as a separate
workload. Report its public-operation and non-additive profiler values without
merging them into the independent-frame table.

### 6.3 Test-loop characterization

Run, in this order:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  -m "not integration and not visual and not slow" --durations=50
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q --durations=50
```

Collect at least three routine runs before claiming that the less-than-30-
second expectation is or is not met. Do not improve the number by removing,
reclassifying, weakening, or session-caching a test unless a separately
reviewed test-architecture change preserves its contract.

## 7. Correctness comparison

Every optimized candidate must be compared with a fresh complete-render oracle
from the same request:

- identical astronomical state and provenance;
- identical product-frame spherical geometry within declared scientific
  tolerances;
- identical projected records within declared numerical tolerances;
- identical semantic hierarchy and normalized SVG graphical records;
- identical PNG RGBA where deterministic, otherwise a predeclared explicit
  image tolerance;
- rendered-PDF comparison from the same projected records;
- unchanged clipping, labels, furniture, and chart boundaries;
- accepted fixed-sky celestial invariance and rotating local-horizon behavior.

Timing improvement cannot compensate for a scientific, semantic, or visual
difference.

## 8. Cache identity and invalidation

A reusable value may be cached only behind an immutable key containing every
input that can change it. Depending on the value, that includes:

- catalogue/resource identity and source revision;
- ephemeris provider, model, file digest, and coverage;
- body descriptor and correction policy;
- physical evaluation instant and time scale;
- `ObservationContext`, including site and Earth-orientation/refraction
  policy;
- source and target `CoordinateSpec`;
- sampling count, morphology quality, and relevant geometry options;
- chart product-frame identity for product-frame geometry.

Style, output mode, color, linewidth, font, filename, and exporter do not
belong in a scientific spherical-state key. Conversely, projected geometry
cannot be reused merely because scientific state matches: its projection,
alignment, viewport, and boundary identity must also match.

Mutation of a layer source or reload revision invalidates its derived entries.
A cache miss must fall back to the complete authoritative calculation. Cache
lifetime and ownership must be explicit; no mutable process-global
astronomical cache is authorized.

## 9. Ownership findings

The safest first optimization seam is above the canonical static executor and
below sequence orchestration:

- sequence planners continue to produce immutable frame requests;
- the complete-render oracle remains callable;
- a later candidate may reuse only proven invariant scientific state;
- dynamic Solar-System bodies and observer-local geometry continue to be
  reevaluated at their declared instants;
- projection, preparation, renderer, furniture, and export remain the existing
  owners.

Do not place cache policy in a renderer, exporter, projection class, body-
specific Moon/Venus module, CLI adapter, or style.

## 10. Proposed implementation slices

### 49J.0 — Performance and closure audit

Documentation and documentation tests only. Freeze the baseline, timing
vocabulary, workload matrix, correctness oracle, cache-key rules, and stop
conditions.

### 49J.1 — Independent-frame benchmark harness

Add a diagnostic tool and narrow instrumentation boundary that measures cold
complete frames using the exclusive spans in this audit. Preserve
`tools/benchmark_reusable_sphere.py` unchanged as the separate reuse
diagnostic. Add no cache and change no chart output.

### 49J.2 — Routine-suite characterization and remediation

Use repeated Mac durations to locate the current routine-gate excess. Improve
test construction or consolidate genuinely redundant current contracts only
through a separately reviewed test-only change. Preserve the full release
authority and every scientific/visual contract.

49J.2 may be skipped if repeated clean runs already satisfy the target and no
stable concentration justifies a change.

### 49J.3 — First scientifically keyed reuse

Optimize one bounded fixed-sky circumpolar sequence workload. Reuse only state
proved invariant by the 49J.1 measurements and explicit keys. Keep the
independent-frame path selectable as the correctness oracle. Do not generalize
to every chart family, moving body, or animation in this slice.

### 49J.4 — Post-v0.9 closure

Re-run focused, full, scientific, SVG, visual, and sequence acceptance. Update
the current architecture, implementation reference, source tree, user
documentation, examples, diagrams when ownership changed, and close or
supersede the post-v0.9 roadmap.

Each slice requires separate acceptance before the next begins.

## 11. Stop conditions

Stop and re-audit if a candidate would:

- optimize before an independent cold-frame baseline exists;
- report overlapping profiler categories as additive wall time;
- omit environment, request, resource, or commit identity;
- key scientific reuse by mutable global state or presentation settings;
- reuse observer-local or moving-body state across incompatible instants;
- bypass `CoordinateService`, projection guards, clipping, preparation,
  renderer, semantic SVG, furniture, or canonical export;
- remove the complete-render oracle;
- trade correctness for a timing threshold;
- weaken tests merely to reduce reported suite time;
- write benchmark products into tracked repository paths.

## 12. Explicit non-goals

49J.0 does not authorize:

- runtime instrumentation or optimization;
- a new cache;
- parallel rendering or multiprocessing;
- GPU acceleration;
- renderer replacement;
- catalogue or ephemeris changes;
- Moon, planet, satellite, or coordinate-model changes;
- animation interpolation;
- benchmark pass/fail thresholds;
- deletion or reclassification of tests;
- roadmap closure.

## 13. Acceptance gate

Fernando must accept:

1. the independent-frame versus reusable-sphere distinction;
2. the exclusive timing vocabulary;
3. the cold-frame, reusable-sphere, and test-loop workload separation;
4. the immutable scientific cache-key and invalidation rules;
5. fixed-sky circumpolar scope for the first optimization;
6. the four separately accepted implementation slices;
7. the stop conditions and non-goals.

After acceptance, run documentation tests, the routine gate, and the complete
suite. Only then may 49J.1 begin.
