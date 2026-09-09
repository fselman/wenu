# Test architecture and accepted-practice audit (Milestone 49J.1)

**Status:** Accepted and merged in PR #77 on 2026-09-09  
**Audit baseline:** `d92f393`  
**Access date for external sources:** 2026-09-09  
**Runtime effect:** None

Fernando accepted the evidence after three routine runs, three complete runs,
and 81 focused documentation tests passed on the Mac. Integration completed at
merge commit `3bab45b`.

## 1. Purpose and boundary

This audit answers two questions before Wenu changes its tests:

1. what maintained testing guidance currently recommends; and
2. where the as-is Wenu suite appears to repeat work, share state, or declare a
   tier differently from the work it performs.

This milestone records evidence only. It changes no test, marker, fixture
scope, production module, cache, output, or timing threshold. Milestone 49J.2
will give every material recommendation an explicit **Adopt**, **Adapt**,
**Reject**, or **Defer** disposition, subject to Fernando's review. Milestone
49J.3 may implement only the accepted decisions.

The coordinate-system guide was reviewed. This audit changes no scientific
meaning, object provenance, implementation ownership, or public coordinate
explanation, so the guide remains current.

## 2. Method and limits

The repository assessment used source enumeration and Python-AST inspection of
the committed `tests/` tree, plus targeted searches for fixtures, markers,
parametrization, canonical request entry points, observer and sphere builders,
Matplotlib saving, and subprocess use. Static occurrences are leads, not
runtime call counts: monkeypatching, helper indirection, parametrization, and
imports can make the executed count higher or lower.

The baseline has 199 files under `tests/`, including 187 `test_*.py` modules.
AST inspection found 1,767 test-function definitions and 127 parametrization
decorators; pytest collection on Fernando's Mac expanded these to 2,123 test
cases. There is no committed CI workflow, so the documented Mac gates are the
present acceptance authority.

The assistant environment does not contain the repository's pytest runtime and
could not supply comparable durations. Fernando therefore captured three
routine and three complete runs in the established Mac environment. Section 6
records the observations. Static evidence and timing together identify
decision candidates, not authorized optimizations.

## 3. Sources and evaluated guidance

The sources below are maintained primary project documentation or a standards
publisher, except for the clearly identified Google engineering guidance.
ISO/IEC/IEEE 29119 supplies general testing vocabulary and process concepts;
it does not prescribe Wenu's fixture scopes, marker taxonomy, or time budget.

| Source | Authority and currency | Recommendation evaluated here |
|---|---|---|
| [pytest: How to use fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html) | pytest project, stable documentation, accessed 2026-09-09 | Fixture lifetime must match the resource; broader scope shares a cached instance and therefore requires controlled state. |
| [pytest: Temporary directories and files](https://docs.pytest.org/en/stable/how-to/tmp_path.html) | pytest project, stable documentation, accessed 2026-09-09 | `tmp_path_factory` can create an expensive artifact once at session scope while tests receive explicit paths. |
| [pytest: Flaky tests](https://docs.pytest.org/en/stable/explanation/flaky.html) | pytest project, stable documentation, accessed 2026-09-09 | Control system state, avoid hidden coupling, and investigate flakes rather than accepting retries as correctness. Parallel execution can expose order dependence and unsafe global state. |
| [pytest: Good integration practices](https://docs.pytest.org/en/stable/explanation/goodpractices.html) | pytest project, stable documentation, accessed 2026-09-09 | Test the installed package in an isolated environment and use deliberate import/configuration policy. |
| [pytest: Usage and duration profiling](https://docs.pytest.org/en/stable/how-to/usage.html#profiling-test-execution-duration) | pytest project, stable documentation, accessed 2026-09-09 | Use `--durations` and `--durations-min` to expose slow setup, call, and teardown observations. |
| [pytest: Marking test functions](https://docs.pytest.org/en/stable/how-to/mark.html) | pytest project, stable documentation, accessed 2026-09-09 | Register and select meaningful markers; marker names describe purpose or required environment, not merely current inefficiency. |
| [coverage.py: Branch coverage](https://coverage.readthedocs.io/en/latest/branch.html) | coverage.py project, current documentation, accessed 2026-09-09 | Coverage can reveal unexercised decisions, but execution percentage is evidence, not proof that assertions detect faults. |
| [coverage.py: Dynamic contexts](https://coverage.readthedocs.io/en/latest/contexts.html) | coverage.py project, current documentation, accessed 2026-09-09 | Per-test contexts can map tests to executed code and support a duplication audit without equating identical coverage with identical fault detection. |
| [ISO/IEC/IEEE 29119-1:2022](https://www.iso.org/standard/81291.html) | ISO/IEC/IEEE vocabulary standard | Use consistent test concepts and documented process; do not misrepresent the standard as a pytest implementation recipe. |
| [Google Testing Blog: Test sizes](https://testing.googleblog.com/2010/12/test-sizes.html) | Influential engineering guidance, not a Wenu standard | Classify tests by resource and execution properties, keep small tests hermetic, and retain larger tests for cross-component confidence. |

## 4. Accepted-practice findings for 49J.2 to decide

### 4.1 Portfolio and independent routes

Fast unit tests should isolate a small contract; component and integration
tests should prove collaborations; end-to-end tests should protect a small
number of complete user routes. Scientific validation is an additional Wenu
axis: a numerically authoritative installed-kernel comparison can be essential
even when it is not fast or hermetic in the same sense as a pure unit test.

Candidate Wenu adaptation: retain at least one independent complete path for
each public chart family and every scientifically independent oracle. Do not
remove a path merely because its lines overlap another test. Consolidate only
when assertions inspect the same generated artifact without requiring cold
state, distinct public entry, independent scientific recomputation, or order
isolation.

### 4.2 Isolation and deterministic inputs

Tests should not depend on execution order, wall-clock time, network state,
ambient locale, mutable module globals, or files outside declared resources.
Wenu's `-p no:remotedata` configuration is consistent with offline execution.
Ephemeris and catalogue tests must also expose resource provenance and validity
rather than treating an installed file as anonymous test data.

Candidate Wenu adaptation: keep function-scoped fresh state where a test
mutates selection, style, observer, Matplotlib objects, output directories, or
provider state. Any proposed broader fixture must have an immutability or
reset proof and an order-reversal check.

### 4.3 Fixture scope and expensive immutable setup

pytest explicitly supports function, class, module, package, and session
scope. Broader scope is not automatically better: it deliberately shares a
cached value. It is suitable for expensive immutable inputs or an artifact
whose construction is not itself under test. It is unsafe when a consumer can
leak mutations or when independent construction is part of the contract.

Candidate Wenu adaptation: distinguish read-only catalogue/resource bytes,
parsed immutable catalogue values, canonical spheres, observers, prepared
charts, Matplotlib figures, and encoded products. They do not have the same
safe lifetime. A shared sphere is a decision, not a blanket suite fixture.

### 4.4 Parametrization, duplication, and assertions

Parametrization is appropriate when one contract must hold for several data
points and failures remain individually identifiable. It becomes poor economy
when each parameter repeats expensive unrelated setup, or when a long table
hides materially different contracts. Conversely, several focused assertions
against one costly immutable product can be clearer and faster than rebuilding
that product for every assertion.

Candidate Wenu adaptation: measure setup/call/teardown first, then inventory
which parameter sets create identical scientific requests. Preserve separate
tests for separate public routes and failure meanings even when they share
coverage.

### 4.5 Correctness, performance, coverage, and flakes

Correctness tests should make deterministic assertions. Benchmarks should
characterize distributions in controlled environments and should not turn a
noisy wall-clock observation into a correctness failure without an accepted
statistical and environmental policy. Line or branch coverage can identify
gaps; it cannot by itself show assertion quality or justify deletion.

A flaky test is a defect signal. Quarantine or retries may keep diagnosis
moving but must not convert intermittent failure into acceptance. Wenu should
record the failing seed, order, environment, resource identity, and artifact
where applicable.

Candidate Wenu adaptation: keep `--durations` diagnostic in 49J.1. Decide in
49J.2 whether coverage contexts, order perturbation, repeat runs, or deliberate
mutation experiments are proportionate. Do not install a timing threshold in
this audit.

### 4.6 Markers, gates, snapshots, and parallelism

Markers should correspond to stable test purpose or resource requirements.
Wenu currently registers `integration`, `visual`, and `slow`; the complete
suite remains release authority. A test that renders or crosses components
should not evade its semantic tier simply because it currently runs quickly.
Likewise, `slow` should not become a place to hide preventable repetition.

Golden files are useful for intentional stable products, but assertions should
normalize irrelevant backend metadata and make reviewable what changed.
Scientific values should normally use explicit quantities and tolerances;
opaque whole-file snapshots must not replace scientific assertions.

Parallel execution is not an optimization assumption. It may expose coupling,
but can also hide serial contention and violate Matplotlib, temporary-file,
installed-kernel, or mutable-cache assumptions. Decide suitability per gate
only after serial independence is demonstrated.

## 5. As-is Wenu suite inventory

### 5.1 Fixture topology

Static inspection found 16 declared fixtures: 12 function-scoped and four
module-scoped. No class-, package-, or session-scoped fixture and no
`tests/conftest.py` was found.

The four module-scoped fixtures are:

- `test_deep_sky_polygons.py::observer`;
- `test_galaxy_catalogue.py::catalogue`;
- `test_reusable_canonical_sphere.py::canonical_sphere`; and
- `test_reusable_canonical_sphere.py::observers`.

`test_reusable_canonical_sphere.py` intentionally tests reuse, order, and
observer-cache separation; its repetition is not prima facie accidental.
However, `source_tree.md` currently says canonical integration tests use a
session-scoped build registry. The committed test topology does not substantiate
that statement. 49J.2 must decide whether the documentation describes an
unimplemented intention or whether another mechanism provides the claimed
registry before any correction is made.

### 5.2 Markers and declared tiers

Static inspection found 19 function-level `integration` decorators, plus one
module-level integration marker covering three tests; two function-level
`slow` decorators; one function-level `visual` decorator; and one module-level
visual marker covering four tests. A test can carry more than one marker, so
these are not additive suite totals.

Fernando's baseline collection reported 30 cases deselected by the routine
expression and 2,123 cases in the complete suite. The small marked share is
not itself proof of misclassification, but it makes semantic review of tests
that initialize Matplotlib, encode files, scan documentation, or traverse the
canonical path especially important.

### 5.3 Static repeated-work leads

Selected direct call sites in test code were:

| Construct | Direct static calls | Interpretation limit |
|---|---:|---|
| `Observer(...)` | 53 | Does not count helper or library-internal construction. |
| `generate_chart_request(...)` | 7 | Several tests monkeypatch this entry point; a call is not necessarily a full render. |
| `build_chart_request(...)` | 1 | Indirect request builders are not included. |
| `build_maximal_sphere(...)` | 2 | Other helpers may construct equivalent spheres. |
| `generate_celestial_sphere(...)` | 5 | Static count does not prove identical catalogue input. |
| `subprocess.run(...)` | 1 | Other subprocess APIs and imported helpers require runtime tracing. |

There were 91 selected direct occurrences when observer construction,
canonical request/build entry points, subprocess APIs, and `savefig()` were
searched together. These occurrences identify measurement targets; they do not
establish 91 expensive operations.

The largest modules by defined test functions include
`test_current_documentation.py` (80), `test_style_contracts.py` (67),
`test_legend_export.py` (54), `test_stellar_magnitude_legend.py` (40),
`test_detail_policy.py` (39), `test_spherical.py` (37),
`test_constellation_labels.py` (35), and `test_chart_furniture.py` (33).
Module size is a maintainability and collection lead, not a duration ranking.

### 5.4 Preliminary classification

The following classifications remain hypotheses until timed and traced:

| Category | Current evidence | 49J.2 question |
|---|---|---|
| Intentional independent repetition | Canonical family, CLI parity, scientific validation, and reusable-sphere contracts exercise different obligations. | Which complete routes and independent scientific recomputations are mandatory? |
| Possible accidental repetition | Numerous observer construction sites and repeated documentation-file normalization may reproduce identical setup. | Do runtime contexts show identical inputs and assertions without independent fault detection? |
| Possibly shareable immutable setup | Packaged resource bytes, parsed read-only catalogues, or a proven immutable sphere may be expensive. | What exact immutability and order tests are required before broader scope? |
| Must remain fresh | Mutable chart selection/style, observers with owned resources, Matplotlib figures, output paths, and installed-kernel validators are risk areas. | Which must start cold and which can use a controlled factory? |
| Tier disagreement leads | Rendering/file-encoding and cross-component work appears outside the small explicit marker set. | Is the test actually mocked/unit-level, or is its declared tier incomplete? |

## 6. Mac measurement evidence

### 6.1 Environment and collection isolation

Fernando measured commit `09b97f1` on macOS
`10.16-x86_64-i386-64bit`, Python 3.11.7, pytest 9.1.1, and Matplotlib 3.8.0.
`platform.processor()` returned an empty string, so this report does not infer
a more specific processor identity. Power state and competing-process state
were not recorded; this prevents machine-level benchmark claims but does not
invalidate the within-session diagnostic ranking.

The first invocation, without plugin isolation, failed before collection.
pytest automatically loaded the environment's `pytest_filter_subpackage`
plugin, whose legacy `pytest_ignore_collect(path, config)` hook is incompatible
with pytest 9.1.1's hookspec. All six successful runs therefore used
`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`. This is evidence that Wenu acceptance must
control external plugin loading; whether to encode that policy elsewhere is a
49J.2 decision.

### 6.2 Routine gate

The command was:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q \
  -m "not integration and not visual and not slow" \
  --durations=50 --durations-min=0.05
```

| Run | Passed | Deselected | Wall time |
|---|---:|---:|---:|
| 1 | 2,094 | 30 | 30.40 s |
| 2 | 2,094 | 30 | 27.16 s |
| 3 | 2,094 | 30 | 26.98 s |
| **Median** | **2,094** | **30** | **27.16 s** |
| **Range** | — | — | **3.42 s** |

Recurring leading call phases were:

| Test | Median | Range |
|---|---:|---:|
| obsolete imports and dynamic import-string scan | 2.11 s | 0.04 s |
| canonical cartoon legacy-import scan | 1.54 s | 0.04 s |
| native B1875 boundary sampling and transformation | 0.81 s | 0.13 s |
| rendered page-text physical extents | 0.41 s | 0.02 s |

No setup or teardown phase exceeded the 0.05-second reporting floor in the
routine runs. The two source scans were stable while total wall time fell by
3.42 seconds from the first to third run. The first-run excess is therefore
distributed warm-up or accumulated overhead, not one demonstrated slow node.

The routine list includes SVG writes, visual-reference writes, Matplotlib
artist checks, and physical-page rendering checks. Some are likely focused
contract tests whose names contain “visual”; others may cross the declared
visual or integration boundary. Timing alone cannot classify them, but their
presence confirms the need for the 49J.2 semantic marker review.

### 6.3 Complete gate

The command was:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q \
  --durations=50 --durations-min=0.05
```

| Run | Passed | Wall time |
|---|---:|---:|
| 1 | 2,124 | 87.12 s |
| 2 | 2,124 | 85.49 s |
| 3 | 2,124 | 84.93 s |
| **Median** | **2,124** | **85.49 s** |
| **Range** | — | **2.19 s** |

Recurring dominant phases were:

| Test phase | Median | Range |
|---|---:|---:|
| real canonical observer-time sequence, call | 21.00 s | 0.34 s |
| larger calendar labels inside physical disk, call | 7.86 s | 1.23 s |
| ordinary maximal-sphere factory, call | 3.42 s | 0.04 s |
| reusable canonical sphere, setup | 3.39 s | 0.21 s |
| circumpolar LMC projection/clipping contract, call | 3.25 s | 0.24 s |
| reused-sphere horizon order independence, call | 3.26 s | 0.20 s |
| reduced galaxy-outline sampling, call | 2.73 s | 0.03 s |
| Cen A binocular centering, call | 2.40 s | 0.05 s |

The canonical observer-time sequence alone accounts for about 24.6 percent of
the median complete-suite wall time; the first two tests together account for
about 33.8 percent. That does not make them redundant. The sequence test is an
explicit complete-route oracle, while the calendar test protects physical
layout. 49J.2 must decide their gate placement and required independence before
49J.3 attempts to reduce their cost.

The reusable-sphere module exposes its expensive construction cleanly as a
setup phase. The ordinary maximal factory, horizon-order, projection/clipping,
galaxy, deep-sky polygon, and Cen A tests expose repeated catalogue, sphere, and
geometry work as calls. This runtime ranking confirms the static leads but does
not yet prove that two tests use identical inputs or may share mutable state.

### 6.4 Historical context

The pre-audit single-run observations remain characterization only: routine
`2,093 passed, 30 deselected in 58.32 s`; complete `2,123 passed in 87.66 s`.
The earlier 49J.0 observations were 37.88 s routine and 93.31 s complete. The
new repeated medians are 27.16 s and 85.49 s. The substantial differences
among single sessions reinforce the decision not to enforce a suite wall-time
threshold from this evidence.

## 7. Reproducible measurement protocol

Run from a clean checkout at the audit branch head, in the same established
environment used for acceptance. Do not add plugins or clear shared operating-
system caches between repetitions. Record whether the machine is on battery or
external power and keep that state unchanged.

First record identity:

```bash
git status
git log -1 --oneline
python --version
python -m pytest --version
python -c "import matplotlib, platform; print(platform.platform()); print(platform.processor()); print(matplotlib.__version__)"
```

Then run the routine gate three times, one command at a time:

```bash
python -m pytest -q -m "not integration and not visual and not slow" --durations=50 --durations-min=0.05
```

Then run the complete gate three times, one command at a time:

```bash
python -m pytest -q --durations=50 --durations-min=0.05
```

The six reports were preserved in the review conversation and summarized
above. Future comparisons must preserve every report, tabulate medians and
ranges, and retain phase-qualified node IDs. They must not compare selectively
chosen fastest runs or enforce a pass/fail duration without a later accepted
policy.

## 8. Questions reserved for the 49J.2 decision ledger

1. Which public and scientific routes must remain independently recomputed?
2. Which exact values are immutable enough for module or session reuse?
3. Must canonical integration tests use a shared registry, or should the
   current documentation claim be removed?
4. Which rendering and encoding tests belong in `visual` or `integration`?
5. Should installed-kernel validators have a distinct marker and gate?
6. May multiple contract assertions share one generated artifact?
7. Is coverage with per-test contexts worth adding as temporary audit tooling?
8. Which order, repeat, mutation, or cold-state experiments prove retained
   fault-detection strength?
9. Is any Wenu gate safe and useful to execute in parallel?
10. Should duration remain diagnostic, or should a later controlled benchmark
    receive an explicit statistical threshold?

No answer is adopted by this document.
