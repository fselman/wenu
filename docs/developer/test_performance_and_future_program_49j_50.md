# Wenu test, performance, minor-body, and publication program

**Status:** Current planning and decision document  
**Planning baseline:** `c035313`  
**Runtime effect:** None  
**Authority:** Subordinate to `current_architecture_v0.9.md` and the preserved
canonical Wenu pipeline

## 1. Purpose

This document governs the work that follows the accepted 49J.0 performance
audit. It adds two requirements requested by Fernando:

1. before changing the test architecture, report current accepted testing
   practice and decide explicitly which practices Wenu adopts;
2. before changing publication styles, report current accepted printing,
   typography, contrast, cartographic, and accessibility practice and decide
   explicitly which practices Wenu adopts.

The intended order is test-suite work, production performance work, minor
bodies, and finally publication legibility and economical printing styles.
Each implementation slice remains separately authorized.

## 2. Decision method

Both best-practice reviews must produce an evidence table with one disposition
for every material recommendation:

- **Adopt** — apply directly in Wenu;
- **Adapt** — retain the principle with a documented Wenu-specific form;
- **Reject** — do not apply, with a recorded reason;
- **Defer** — retain as a possible later task outside the current slice.

External authority does not override Wenu's scientific requirements. A
practice is accepted only after its effect on correctness, reproducibility,
maintainability, physical output, and canonical architecture is explicit.
Fernando's review is the acceptance authority for the resulting policy.

## 3. Milestone 49J — Tests and performance

### 49J.1 — Test architecture and accepted-practice audit

Research and report current accepted practice before modifying tests. Prefer
primary and maintained sources, including current pytest and Python packaging
documentation, applicable ISO/IEC/IEEE 29119 vocabulary, and authoritative
guidance on reproducibility, flaky tests, hermetic execution, and performance
measurement. Record source title, organization, version or access date, and
the exact recommendation evaluated.

The review must cover:

- the balance among unit, component, integration, scientific-validation,
  visual, and end-to-end tests;
- isolation, order independence, deterministic inputs, and reproducibility;
- fixture scope and safe reuse of expensive immutable setup;
- protection against mutable shared state and hidden cross-test coupling;
- parametrization, duplicated tests, and contract-focused assertions;
- separation of correctness tests from performance benchmarks;
- collection, setup, call, teardown, and external-process timing;
- flaky-test detection and treatment;
- offline execution and scientific resource provenance;
- markers, routine gates, complete release authority, and meaningful coverage;
- appropriate use of golden files and snapshot comparisons;
- parallel execution, including cases where it hides contention or violates
  resource and backend assumptions.

Map that review onto the as-is Wenu suite. Identify repeated catalogue and
ephemeris loads, sphere and observer construction, coordinate transformations,
chart preparation, Matplotlib setup, PNG/PDF/SVG encoding, subprocesses,
documentation scans, and repeated identical scientific requests. Distinguish:

1. intentional repetition protecting independent public routes;
2. accidental repetition adding no independent fault-detection value;
3. expensive immutable setup that may be shared safely;
4. scientific calculations that must remain independently recomputed;
5. integration or visual work occurring in the routine tier;
6. tests whose behavior and declared tier disagree.

Use repeated `pytest --durations` runs in the same environment and report raw
observations, medians, ranges, collection counts, and environment identity.
49J.1 changes no test, marker, fixture scope, runtime code, or output.

### 49J.2 — Wenu test-practice decisions

Review the 49J.1 evidence item by item and publish the Adopt/Adapt/Reject/Defer
ledger. Decide at least:

- which values may be shared between tests and what proves immutability;
- which tiers must begin from cold independent state;
- which complete canonical paths must remain independently exercised;
- when multiple assertions may inspect one generated artifact;
- whether integration tests may share a session-scoped sphere;
- which installed-kernel scientific validators must remain independent;
- which tests belong in routine, integration, visual, slow, and complete gates;
- whether parallel execution is suitable for any Wenu gate;
- whether timing remains a diagnostic target or becomes an enforced threshold;
- how to demonstrate that faster tests retain fault-detection strength.

No optimization begins until Fernando accepts this policy.

### 49J.3 — Test-suite optimization

Implement only accepted 49J.2 decisions. Compare repeated before/after wall
times, tier and test counts, canonical paths exercised, order independence,
cold-state checks, and the complete suite. Where practical, use deliberate
fault or mutation experiments to demonstrate that consolidation did not remove
meaningful detection. Do not weaken, silently reclassify, or delete a contract
merely to improve elapsed time.

### 49J.4 — Cold chart and sequence performance baseline

Add the independent-frame harness specified by the accepted 49J.0 audit after
the test loop has been rationalized. Measure fresh complete frames using
exclusive request/orchestration, catalogue/resource, provider, transformation,
projection, preparation, rendering, encoding/export, and residual spans.
Preserve `tools/benchmark_reusable_sphere.py` as a separate overlapping-profile
diagnostic and preserve `generate_chart_request()` as the correctness oracle.

### 49J.5 — First scientifically keyed chart reuse

**Status:** Accepted. The 49J.5A seam and 49J.5B equivalence records are
archived under `archive/milestone_history/49j_performance/`.

Optimize only the accepted fixed-sky circumpolar workload. Reuse state proved
invariant by 49J.4, recompute observer-local and moving-object state at their
declared instants, use immutable scientific keys, and keep the cold complete
route selectable. Require scientific, projected-record, normalized SVG, PNG,
rendered-PDF, clipping, furniture, and visual equivalence.

### 49J.6 — Performance closure

**Status:** Accepted. Final evidence is archived in
`archive/milestone_history/49j_performance/performance_closure_49j6.md`; 50A.0
is the next authorized milestone.

Repeat focused, routine, complete, scientific, SVG, visual, and sequence
acceptance. Update architecture, implementation reference, source tree, user
documentation, examples, and diagrams wherever ownership changed. Archive the
completed 49J documents and retain both the cold oracle and measured reuse
route.

## 4. Program 50A — Asteroids and comets

Minor bodies follow performance closure so that their tests enter a measured
and governed suite.

### 50A.0 — Scientific and provider audit

**Status:** Accepted. The record is archived in
`archive/milestone_history/50a_minor_bodies/minor_body_scientific_provider_audit_50a0.md`.
Milestone 50A.1 is next.

Decide orbital-element versus SPK/JPL state sources, provenance and validity
intervals, osculating epoch and frame, perturbation model, light time,
apparent-place treatment, topocentric parallax, magnitude models, uncertainty,
identifiers, and cometary non-gravitational terms. Distinguish a comet nucleus
position from coma and tail appearance. Add no visible object.

### 50A.1 — Generic minor-body state provider

**Status:** Accepted by Fernando on 2026-09-10 and archived in
`archive/milestone_history/50a_minor_bodies/minor_body_state_provider_50a1.md`.

Produce the existing typed state consumed by the shared moving-body direction
machinery. Do not add asteroid- or comet-specific coordinate, projection,
renderer, semantic-export, or file-export paths.

### 50A.2 — Asteroid numerical validation

**Status:** Accepted by Fernando on 2026-09-11 and archived in
`archive/milestone_history/50a_minor_bodies/asteroid_numerical_validation_50a2.md`;
50A.3 is next.

Validate a bounded set including a main-belt asteroid and a fast nearby object,
with an independent authoritative ephemeris comparison where available.

### 50A.3 — First drawable asteroid

**Status:** 50A.3A accepted by Fernando on 2026-09-11 and archived in
`archive/milestone_history/50a_minor_bodies/first_drawable_asteroid_audit_50a3a.md`;
the bounded 50A.3B implementation is authorized.

**Status:** 50A.3B is accepted and archived in
`archive/milestone_history/50a_minor_bodies/drawable_ceres_50a3b.md`. It adds only opt-in Ceres
point/track selection with an explicit offline resource directory and retains
the shared fixed-frame moving-body, rendering, and export route. 50A.3B was
accepted after the documented gates and PNG/semantic-SVG inspection passed.

**Status:** Fernando requested a post-closure generalization before comet
validation. Active 50A.3C audits generic manifest-backed selection by permanent
minor-planet number, using unnamed main-belt asteroid `(79989)` as the bounded
acceptance specimen. If accepted, 50A.3D implements that contract; 50A.4
remains next after the follow-up closes.

Add opt-in symbolic display, designation policy, semantics, and a dated track
through the shared point and trajectory machinery.

### 50A.4 — Comet numerical validation

Validate the comet state and document model limits, including non-gravitational
behavior when relevant.

### 50A.5 — First drawable comet

Begin with nucleus position and optional track. Coma and tail morphology remain
a separate later physical-appearance milestone.

### 50A.6 — Minor-body closure

Close provenance, public interface, validation, and documentation after PNG,
PDF, and semantic-SVG acceptance.

## 5. Program 50B — Publication legibility and economical printing

### 50B.0 — Accepted-practice review

Research and report current accepted practice before changing Wenu appearance.
Use maintained primary or standards-body material where available and clearly
distinguish normative requirements, professional-print recommendations,
accessibility references, cartographic convention, and empirical practice.

The review must cover:

- PDF print exchange, font embedding, output intent, color spaces,
  transparency, physical page boxes, and scale;
- ordinary office printing, professional printing, grayscale, pure black, and
  photocopy reproduction;
- nominal point size versus perceived size, x-height, weight, viewing distance,
  label spacing, and reduction after export;
- minimum reproducible line and symbol dimensions;
- luminance contrast for text and meaningful non-text graphics;
- redundant encodings using size, shape, line weight, and dash pattern rather
  than color alone;
- magnitude-dependent star symbols, crowded-field selection, grid hierarchy,
  line crossings, label collision, legends, angular scale, and apparent
  precision in respected astronomical and cartographic publications;
- needs of older readers and classroom handouts.

The review must evaluate the ISO 15930 PDF/X family, relevant print-production
standards, accessibility contrast guidance such as WCAG as a reference rather
than an automatic print rule, and empirical measurements from respected
printed star atlases. It must not invent universal minimum sizes where the
evidence depends on process, stock, printer, viewing distance, or reduction.

### 50B.1 — Wenu publication-standard decisions

Publish and review the Adopt/Adapt/Reject/Defer ledger. Define accepted Wenu
physical-output profiles only after that review. Candidate use cases include
full-page publication, half-page handout, book-column figure, ordinary
grayscale office print, monochrome photocopy-safe print, and classroom
projection.

For every accepted profile decide:

- intended final physical dimensions and viewing conditions;
- minimum text size by semantic role;
- minimum star-symbol diameter and line width by semantic role;
- contrast hierarchy and permitted gray levels;
- maximum useful content and label density;
- magnitude-limit and grid-label adjustment rules;
- legend requirements;
- whether post-export reduction is permitted;
- font embedding, PDF metadata, color-space, and print-exchange requirements;
- required physical print and reduction tests.

Fernando's printed scientific and pedagogical review is required before these
values become Wenu defaults or named profiles.

### 50B.2 — Physical-output measurement harness

Measure representative Wenu regional, binocular, circumpolar, all-sky, and
applicable planisphere products at their declared final sizes. Prefer vector
geometry and physical units over inference from raster pixels.

### 50B.3 — Monochrome and limited-grayscale styles

Implement the accepted profiles. Monochrome must remain usable without color;
limited grayscale must use only accepted reproducible levels. Keep ownership
separate: detail selects content, style selects appearance, output mode owns
physical dimensions and scale, chart type owns geometry, and furniture owns
legends.

### 50B.4 — Physical print and reduction acceptance

Produce actual-size PDF test sheets and declared reduction matrices. Inspect
ordinary printer output, grayscale behavior, and photocopy behavior where
practical. Screen PNG review is not sufficient.

### 50B.5 — Publication-style closure

Record accepted numerical standards, named profiles, examples, regression
products, limitations, and the human print-acceptance record.

## 6. Stop conditions

Stop and re-audit if a proposed change would:

- share mutable scientific or rendering state across tests;
- remove an independent public-path or scientific-validation oracle without
  equivalent evidence;
- improve a number by weakening, hiding, or merely reclassifying work;
- optimize chart generation before a cold independent baseline exists;
- let test or cache policy enter astronomy, projection, renderer, or export
  ownership;
- let style or output mode alter astronomical geometry;
- claim print legibility from screen inspection alone;
- encode meaning only by color in a monochrome or grayscale profile;
- claim compliance with a standard that Wenu has not validated;
- add a body-specific pipeline where the generic moving-body machinery applies.

## 7. Documentation lifecycle

This file remains in `docs/developer/` only while these programs are current.
Each completed audit or milestone record moves to its matching directory under
`docs/developer/archive/`, and active links plus documentation tests change in
the same commit. The developer root must never become a chronological record.
