# Wenu test-practice decisions (Milestone 49J.2)

**Status:** Accepted by Fernando on 2026-09-09; ready for integration  
**Decision baseline:** `3bab45b`  
**Runtime effect:** None  
**Implementation authority:** Governs separately reviewed 49J.3 slices after integration

## 1. Purpose

This document converts the accepted 49J.1 evidence into explicit Wenu policy.
Each material recommendation receives one of the agreed dispositions:

- **Adopt** — use the recommendation directly;
- **Adapt** — retain its principle in a Wenu-specific form;
- **Reject** — do not use it, for the stated reason; or
- **Defer** — make no present commitment, while preserving the question.

The ledger governs later test changes but changes no test, fixture, marker,
runtime module, cache, output, or threshold itself. Milestone 49J.3 may
implement only decisions Fernando accepts here.

The coordinate-system guide was reviewed. These test policies change no
scientific meaning, provenance, implementation ownership, or public coordinate
explanation, so the guide remains current.

## 2. Governing principles

Wenu tests exist to detect meaningful faults, not to maximize test count or
coverage percentage. Faster execution is valuable only when scientific,
architectural, public-interface, rendering, and publication contracts retain
equivalent or stronger independent evidence.

Test independence has two distinct meanings:

1. **state independence** — a test does not inherit uncontrolled mutations or
   ambient state from another test; and
2. **fault-detection independence** — a test protects a genuinely distinct
   route, contract, scientific oracle, composition, or failure mode.

Sharing immutable setup can preserve both. Repeating the same assertion over
the same route does not necessarily provide either.

## 3. Accepted decision ledger

### D1 — Test portfolio: **Adapt**

Wenu will retain unit, component, integration, visual, complete-route, and
scientific-validation tests without imposing a numerical “test pyramid” ratio.
Scientific validation is a separate purpose axis, not merely a synonym for
integration or slow. The smallest test that can detect the intended fault is
preferred, while a bounded set of complete public routes remains mandatory.

### D2 — Complete release authority: **Adopt**

The serial complete suite remains release authority. Routine selection is a
development feedback loop, not evidence that excluded integration, visual,
slow, or installed-resource obligations are satisfied.

### D3 — Determinism and offline execution: **Adopt**

Tests must use explicit time, location, coordinate status, catalogue identity,
resource provenance, random seed, locale, and output destination wherever the
value can affect the result. Ordinary gates must not require network access.
An external authoritative comparison may use a separately controlled workflow,
never an undeclared network fetch during the ordinary suite.

### D4 — External pytest plugins: **Adopt**

Wenu's documented acceptance commands will set
`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`. Required plugins, if any are later approved,
must be explicitly loaded and version constrained. The 49J.1 pre-collection
failure from the incompatible ambient `pytest_filter_subpackage` plugin is the
direct evidence for this rule.

### D5 — Default fixture lifetime: **Adopt**

Function scope remains the default. Broader scope requires a documented reason
based on measured cost and a state-safety proof; it is not justified by brevity
or convenience alone.

### D6 — Reuse of expensive immutable setup: **Adapt**

Module- or session-scoped reuse is permitted only when all of these conditions
hold:

1. construction is expensive in repeated timing or tracing;
2. construction is not the behavior independently under test in every
   consumer;
3. the shared value is immutable, or each consumer receives a controlled copy;
4. owned resources have deterministic teardown;
5. forward, reverse, and isolated execution produce the same results; and
6. at least one cold independent construction test remains.

The proof belongs beside the fixture or in a linked test-policy comment. An
unverified convention that consumers “should not mutate” is insufficient.

### D7 — Canonical sphere/build registry: **Adapt**

49J.3 may introduce one explicit session-scoped registry for byte-identical,
read-only canonical integration products if D6 is proved. Keys must contain
every scientifically or visually relevant request identity. Distinct observer,
instant, catalogue depth, constellation selection, target, mask, framing,
style-sensitive preparation, or output request must not collide.

The registry must not replace cold factory smoke coverage for each chart
family or the complete request-generation oracle. Until 49J.3 implements and
verifies such a registry, current documentation must describe it as planned,
not implemented.

### D8 — Mutable scientific and rendering state: **Adopt**

Observers with owned resources, mutable selections, style objects susceptible
to mutation, Matplotlib figures/axes/artists, temporary output paths, and
provider/cache state remain fresh unless a specific copy/reset contract is
tested. No mutable global cache may be introduced to accelerate tests.

### D9 — Independent scientific recomputation: **Adopt**

Installed-kernel direction, light-time, apparent-place, topocentric parallax,
physical-appearance, frame, equinox, and epoch validators remain independently
recomputed against their stated oracle. They may share verified immutable
kernel bytes or a read-only resource handle only if the comparison itself,
observer state, requested instant, and result are not reused across supposedly
independent validations.

### D10 — Multiple assertions on one artifact: **Adapt**

One test or a tightly owned test group may inspect several properties of one
expensive generated artifact when construction is not the behavior under test,
the artifact is not mutated between assertions, and failure messages preserve
the contract distinctions. Separate cold builds remain required for distinct
public entry points, state-isolation claims, order tests, and scientific
oracles.

### D11 — Parametrization: **Adapt**

Use parametrization when the same contract applies to clearly named cases.
Split cases when they have different setup, oracle, failure meaning, or tier.
When every parameter repeats expensive invariant setup, 49J.3 should move only
the proved invariant portion to an accepted fixture rather than collapsing the
scientific results.

### D12 — New-test admission and duplication control: **Adopt**

Every new test must state, through its name, nearby comment, review description,
or associated audit, the new contract or fault model it protects. Before adding
it, the contributor must search existing tests and record the closest existing
coverage.

A new capability that composes already-tested Wenu functionality does **not**
automatically duplicate all lower-level tests. Its tests should normally cover:

- the new public request or configuration mapping;
- the new seam between existing components;
- the new composition, ordering, provenance, or state-isolation obligation;
- new scientific cases or boundary conditions introduced by the capability;
- one bounded canonical success route; and
- failures newly possible at that seam.

Existing lower-level behavior is referenced, not reasserted, unless the new
context changes its inputs, invariants, numerical tolerance, ownership, or
failure modes. A test that intentionally repeats a complete path must identify
the independent route or oracle that makes the repetition valuable.

During review, a proposed test should answer:

1. What fault would this test catch that existing tests would not?
2. Which existing test is closest?
3. Can the new assertion be added to an existing generated artifact without
   obscuring ownership?
4. Does the new capability alter lower-level behavior, or merely use it?
5. Which marker and gate reflect the work actually performed?

If no distinct answer exists, the default disposition is to extend or
parameterize an existing contract rather than add another full path.

### D13 — Deleting or consolidating tests: **Adopt**

No test may be deleted or consolidated solely because it covers the same lines,
uses similar inputs, or is slow. The change must map old-to-new fault models and
show that public-route, scientific-oracle, order, cold-state, and failure-path
evidence is retained. Where practical, a deliberate fault or mutation
experiment must demonstrate that the replacement still fails.

### D14 — Marker semantics: **Adapt**

Markers describe stable purpose and required resources:

- unmarked routine tests are deterministic, offline, focused, and suitable for
  the normal feedback loop;
- `integration` crosses meaningful architectural component boundaries or
  exercises a canonical composition;
- `visual` validates rendered appearance, physical layout, or image structure;
- `slow` is reserved for intrinsically expensive work after accepted
  optimization, not preventable repetition.

Multiple markers are allowed. Test names containing “visual” do not determine
classification; actual operations and assertions do. 49J.3 must audit the
routine rendering and file-writing leads from 49J.1 without assuming every
such test belongs outside routine.

### D15 — Installed scientific resources: **Adapt**

49J.3 should propose a registered `scientific_validation` marker if doing so
improves selection and provenance reporting. Such tests may also be integration
or slow. They remain part of complete release authority, and their absence must
be reported explicitly rather than silently converted to success.

### D16 — Golden and snapshot products: **Adapt**

Use golden products only for intentionally stable structure or appearance.
Normalize timestamps, backend identifiers, serialization order, and other
irrelevant metadata. Scientific quantities require explicit values, units,
tolerances, and provenance; an opaque image or whole-file snapshot does not
replace those assertions. Fernando's visual or physical-print acceptance
remains authoritative where human judgment is required.

### D17 — Coverage measurement: **Adapt**

Line and branch coverage may identify unexercised code. Per-test dynamic
contexts may be used temporarily during 49J.3 to map overlapping execution.
No repository-wide percentage target is adopted, and coverage overlap alone
cannot justify test deletion because it does not measure assertion quality or
independent fault detection.

### D18 — Flaky tests: **Adopt**

A flaky result is a defect signal. Record node ID, order or seed, environment,
resource identity, and retained artifact. Retry may gather evidence but must
not turn the original failure into acceptance. Permanent quarantine requires
an owner, reason, visible reporting, and removal condition.

### D19 — Timing and benchmarks: **Adapt**

Suite `--durations` remains diagnostic. Compare at least three runs in the same
recorded environment using medians, ranges, counts, and phase-qualified node
IDs. Do not enforce a suite wall-time threshold from the 49J.1 observations.
Production performance thresholds, if later justified, belong to controlled
49J.4 benchmarks and remain separate from correctness assertions.

### D20 — Parallel execution: **Defer**

Do not use parallel execution as a 49J.3 optimization target. First establish
serial order independence and explicit safety for Matplotlib, file outputs,
kernel resources, and any registry. A later audit may evaluate a bounded
parallel gate. Serial complete execution remains the comparison authority.

### D21 — Source-boundary scans: **Adapt**

The two stable source scans taking a combined median of about 3.65 seconds may
share one repository file inventory and parsed-source index if the scan inputs
are immutable for the test session and each architectural assertion remains
independently identifiable. At least one test must prove that every applicable
source file is included. 49J.3 must measure the implementation rather than
assuming the full 3.65 seconds is recoverable.

### D22 — Canonical observer-time sequence: **Reject** test removal

Reject deletion, mocking, or replacement of the 21.00-second median real
canonical observer-time sequence merely to accelerate the complete suite. It
is a complete-route oracle. 49J.3 may reduce repeated invariant setup only if
the test still creates real independent frames through the canonical path and
detects per-frame observer-time errors.

### D23 — Calendar physical-layout render: **Adapt**

Retain the physical-disk containment contract. 49J.3 may determine whether its
7.86-second median cost comes from repeated equivalent renders, font warm-up,
or an intrinsically necessary high-resolution product. Any faster form must
retain the accepted physical dimensions, label-extents evidence, backend, and
failure sensitivity.

### D24 — Documentation tests: **Adapt**

Documentation contracts should protect current authority, required scientific
language, and document placement. Repeatedly reading and normalizing the same
large file may use a session-local immutable text cache, but assertions should
be grouped by current responsibility rather than historical milestone count.
Completed milestone phrase checks should move with their record to appropriate
archive-integrity coverage instead of accumulating indefinitely in the active
authority test.

## 4. Accepted 49J.3 implementation order

The decisions above imply this bounded order:

1. make plugin-isolated commands explicit and audit marker truthfulness;
2. add a new-test admission checklist to contribution instructions;
3. measure and consolidate immutable repository source/document scans;
4. prove and introduce only accepted immutable catalogue/sphere fixtures;
5. preserve cold builders and installed-kernel scientific recomputation;
6. examine the calendar-layout cost without weakening its physical contract;
7. leave the canonical observer-time sequence intact except for proved
   invariant setup reuse;
8. repeat three routine and three complete runs plus order/isolation checks;
9. map every changed test from its prior to retained fault model; and
10. report counts, medians, ranges, and any deliberate fault experiments.

Each materially different implementation group should be a separately
reviewable 49J.3 slice rather than one broad test rewrite.

## 5. Acceptance record

Fernando reviewed and accepted the ledger in five groups on 2026-09-09:

1. D1–D4, portfolio and execution environment;
2. D5–D10, fixture scope and scientific independence;
3. D11–D13, parametrization, new-test admission, duplication control, and
   consolidation;
4. D14–D20, markers, validation, coverage, flaky tests, timing, and
   parallelism; and
5. D21–D24 plus the ordered 49J.3 implementation slices.

Acceptance authorizes 49J.3 planning under these constraints; it does not
modify any test or authorize one broad rewrite. Each materially different
implementation slice remains separately reviewable.
