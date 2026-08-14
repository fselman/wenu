# Wenu test-suite audit and rationalization proposal

**Repository:** `fselman/wenu`
**Branch:** `main`
**Audited commit:** `ae810ca` — Milestone 46A: Add semantic AltAz grid
**Audit type:** read-only static audit; no repository files were changed

## Executive conclusion

The suite is extensive primarily because completed migrations were accumulated
as permanent milestone-specific tests. The problem is not literal copy/paste:
only two pairs of test functions have exactly duplicated AST bodies. The main
problem is **semantic repetition**—the same architectural contract is retested
through successive milestones, examples, styles, modes and source-text checks.

The suite should be rationalized, but not by deleting every old milestone test.
The safe approach is to build a current-architecture contract matrix, merge
overlapping tests into responsibility-based modules, and delete the superseded
tests only after the replacement modules pass both before and after the move.

The recommended next milestone is:

> **Milestone 46B — Rationalize the test suite around the current v0.8
> architecture**

This milestone should change tests and test configuration only. Production
behavior must remain unchanged.

## Measured inventory

| Measure | Result |
| --- | ---: |
| Files below `tests/` | 162 |
| Regression-fixture scripts | 11 |
| Python test modules | 151 |
| Milestone-named test modules | 132 |
| Responsibility-named test modules | 19 |
| Static test functions | 885 |
| Test-suite source lines | 18,111 |
| Lines in milestone-named modules | 14,911 (82.3%) |
| Lines in responsibility-named modules | 3,200 (17.7%) |
| Exact duplicate test-body groups | 2 |

The 885 static functions are consistent with the recently reported runtime
suite of approximately 936 collected cases: parametrization expands some
functions into multiple pytest cases.

### Concentration by development period

| Milestone family | Test modules |
| --- | ---: |
| 39 | 9 |
| 40 | 27 |
| 41 | 16 |
| 42 | 3 |
| 43 | 14 |
| 44 | 19 |
| 45 | 9 |
| 46 | 1 |

Milestones 39–45 alone account for 97 modules. This is where most
consolidation work should occur.

## Measured Mac runtime baseline

The authoritative run supplied from the existing Wenu development environment
completed successfully:

| Measure | Result |
| --- | ---: |
| Collected and passed cases | 1,003 |
| Failures | 0 |
| Wall time | 172.74 s (2:52) |

The audit container did not contain `pytest`, `astropy`, or `skyfield`, so no
second dependency environment was installed. The Mac result above is therefore
the runtime baseline for Milestone 46B.

The commands used were:

```bash
pytest --collect-only -q > test-inventory-before.txt
pytest -q --durations=50
```

If `pytest-cov` is already available:

```bash
pytest --cov=wenu --cov-branch --cov-report=term-missing
```

Do not install coverage tooling merely to start the cleanup; it is useful but
not a prerequisite for the first structural milestone.

### Runtime concentration

The slow-test report changes the priority of the cleanup. Runtime is highly
concentrated in repeated canonical-example construction:

| Test module | Listed slow calls | Sum of listed call durations | Share of complete wall time* |
| --- | ---: | ---: | ---: |
| `test_milestone44fb2_canonical_example_controls.py` | 14 | 83.77 s | 48.5% |
| `test_milestone44f_planisphere_regional_examples.py` | 7 | 27.65 s | 16.0% |
| `test_milestone45d_semantic_grid_styles.py` | 5 | 15.52 s | 9.0% |
| **Combined** | **26** | **126.94 s** | **73.5%** |

\*The percentages compare summed pytest call durations with reported wall time;
they are diagnostic rather than an accounting identity because setup, teardown
and reporting overhead are measured separately.

The remaining notable slow families are canonical circumpolar and binocular
example construction, polygon regression charts, and the cartoon gallery.
Most catalogue/geometry unit tests are below a quarter second.

This means the first performance improvement should not touch the scientific
unit tests. It should reduce repeated loading and full chart construction in
example-interface tests.

## Findings

### 1. Test organization records history rather than current ownership

The active architecture separates:

- spherical geometry;
- projection-domain guard and projection;
- projected geometry and clipping;
- chart type and framing;
- detail policy;
- style;
- output mode;
- renderer;
- furniture and export;
- declarative examples and CLI.

The suite instead mostly reflects the order in which features arrived. A
maintainer cannot identify the authoritative tests for `detail`, `legends`, or
`coordinate grids` without reading many milestone files.

### 2. Semantic duplication is much larger than literal duplication

Static inspection found only two exact duplicate-body groups. However:

- 44 modules contain legend-related checks;
- 52 modules mention grids;
- 53 modules render or export;
- 45 modules contain documentation/source-text contract patterns;
- 18 modules inspect or execute example source;
- 21 modules access private-looking attributes.

These categories overlap, but they demonstrate repeated verification at
multiple architectural levels.

### 3. Source-text assertions are overrepresented

Source inspection is justified for a few architectural boundaries—for example,
ensuring policy modules do not import Matplotlib. It is weaker when used to
confirm that examples contain particular strings or implementation calls.
Those tests often duplicate executable behavior and packaged-example parity
tests while making harmless refactoring expensive.

Recommendation: keep a small number of explicit dependency-boundary tests and
replace most example source-text checks with behavioral CLI tests.

### 4. Documentation history is tested as executable product behavior

Files such as architecture-document, migration-closure and historical-status
tests repeatedly assert phrases and cross-links in completed migration
documents. Git preserves those documents and their history. The permanent
suite should validate only:

- the current architecture authority exists;
- the active roadmap points to it;
- public documentation examples are syntactically valid;
- current links and public imports work.

Historical wording should not block production changes.

### 5. Example coverage is repeated at too many layers

Examples are checked through early atlas fixtures, later canonical-composition
tests, uniform-interface tests, packaged-copy parity, user-guide commands and
closure tests. The permanent contract can be much smaller:

1. all canonical examples parse the shared CLI;
2. one representative command per chart family generates output;
3. `--all-products` resolves the expected deterministic matrix;
4. packaged examples are byte-identical to canonical examples;
5. a small regression-fixture set protects defining geometry and visuals.

### 6. Legend tests are the clearest consolidation opportunity

The legend subsystem accumulated separate files for metadata, symbols,
spacing, magnitude scales, visible-star statistics, dual plans, coordination,
render bridges, automatic planning, composed export and later furniture
integration.

Most underlying contracts remain valid, but they should be grouped into four
permanent modules:

```text
test_legend_policy.py
test_object_legend.py
test_stellar_magnitude_legend.py
test_legend_export.py
```

This should be consolidation, not loss of meaningful edge cases.

## Proposed permanent suite structure

```text
tests/
  geometry/
    test_spherical.py
    test_projected.py
    test_projection.py
    test_projection_domain.py
    test_clipping.py
    test_viewport.py
  sky/
    test_stars.py
    test_constellations.py
    test_coordinate_grids.py
    test_deep_sky_layers.py
    test_isophotes.py
  charts/
    test_chart_types.py
    test_chart_preparation.py
    test_detail_policy.py
    test_style_and_modes.py
    test_masks.py
  rendering/
    test_matplotlib_renderer.py
    test_symbols.py
    test_labels.py
  furniture/
    test_reference_annotations.py
    test_poles_and_footer.py
    test_legend_policy.py
    test_object_legend.py
    test_stellar_magnitude_legend.py
    test_legend_export.py
  examples/
    test_cli_contract.py
    test_canonical_examples.py
    test_example_installer.py
    test_packaged_parity.py
    test_regression_fixtures.py
  architecture/
    test_dependency_boundaries.py
    test_current_documentation.py
```

Moving immediately to subdirectories is optional. The responsibility names are
more important than the directory layout.

## Concrete consolidation map

The following are **candidate mappings**, not permission to delete files
immediately.

### A. Core geometry and projection — preserve strongly

Candidate sources:

```text
test_milestone4_projection.py
test_milestone8_boundaries.py
test_milestone8_geometrical_object.py
test_milestone8_polar_boundary.py
test_milestone10_constellation_lines.py
test_milestone11_boundaries.py
test_milestone12_coordinate_grids.py
test_milestone39g_equatorial_meridian_extent.py
test_milestone39i_projection_cap_polygons.py
test_milestone42c_canonical_polygon_clipping.py
test_points.py
test_spherical.py
test_projected.py
test_projected_collections.py
test_projected_geometry_projection.py
test_projection_geometry.py
test_projection_regression.py
test_clipping.py
test_viewport.py
test_visibility.py
```

Disposition: **merge and rename, with minimal test deletion**. These protect
scientific and geometric correctness. Remove only provably duplicated paths.

### B. Renderer and execution pipeline — consolidate

Candidate sources:

```text
test_milestone13_matplotlib_renderer.py
test_milestone14_draw_chart.py
test_milestone15a_pipeline.py
test_milestone16_regional_api.py
test_milestone23_full_sky_chart.py
test_matplotlib_renderer.py
test_viewport_rendering.py
```

Targets:

```text
test_chart_execution.py
test_matplotlib_renderer.py
test_chart_types.py
```

Disposition: **consolidate**. Prefer public execution contracts; retain private
assertions only where they enforce a documented ownership boundary.

### C. Deep-sky catalogues and symbols — retain domain coverage

Candidate sources include milestones 26–38 covering nonstellar objects,
galaxies, globular/open clusters, isophotes, Magellanic clouds, remnants,
planetary nebulae, symbol libraries and stellar classification.

Targets:

```text
test_deep_sky_catalogues.py
test_deep_sky_geometry.py
test_deep_sky_symbols.py
test_isophotes.py
test_stellar_symbols.py
```

Disposition: **rename and consolidate common contracts**. Keep catalogue
provenance, identifier resolution, geometry types and symbol semantics. Avoid
repeating the same add/filter/render lifecycle for every object class when a
parameterized shared contract is sufficient.

### D. Style, mode and cartoon composition — major consolidation

Candidate sources:

```text
test_milestone39a_composed_styles.py
test_milestone39b_atlas_style.py
test_milestone40g_cartoon_visual_style.py
test_milestone40h_cartoon_preset.py
test_milestone41a_cartoon_output_styles.py
test_milestone41b_cartoon_composition.py
test_milestone41c_*.py
test_milestone43b_atlas_composition_contracts.py
test_milestone43d_atlas_presentation.py
test_milestone43g_canonical_cartoon_style.py
test_milestone44fb3_cartoon_palette_and_boundary.py
test_milestone44g1_circumpolar_boundary_style.py
test_milestone44g2_atlas_title_circular_frame.py
test_milestone44h1_binocular_boundary_contract.py
```

Targets:

```text
test_style_contracts.py
test_output_modes.py
test_style_overrides.py
test_chart_boundaries.py
```

Disposition: **consolidate aggressively**. Test invariant ownership once, then
use a small style/mode matrix for palette and scaling differences.

### E. Detail and render-local isolation — preserve the invariants

Candidate sources:

```text
test_milestone40c_adaptive_detail.py
test_milestone40d_detail_application.py
test_milestone40e_constellation_star_identity.py
test_milestone40f_cartoon_detail_policy.py
test_milestone41g_*.py
test_milestone42b0_*.py
test_milestone43e_render_local_detail.py
test_milestone45b_grid_detail_identity.py
test_milestone45c_opt_in_content.py
```

Targets:

```text
test_detail_policy.py
test_detail_application.py
test_layer_identity.py
test_render_isolation.py
```

Disposition: **merge carefully**. Sequential-render isolation and semantic
layer identity are high-value current-architecture contracts.

### F. Labels and placement — consolidate by algorithm

Candidate sources include milestone 41c–41f label repairs,
`test_milestone43h_visible_constellation_labels.py`, and
`test_milestone45e_reference_label_tangents.py`.

Targets:

```text
test_constellation_labels.py
test_reference_label_placement.py
```

Disposition: **merge repair tests into algorithmic regression tests**. Preserve
each distinct bug geometry, but remove milestone terminology.

### G. Legends and furniture — highest-return consolidation

Candidate sources:

```text
test_milestone39d_atlas_legend_isophotes.py
test_milestone40h_*legend*.py
test_milestone40i_*.py
test_milestone40j_*.py
test_milestone43c1_legend_policy.py
test_milestone43c2_canonical_legend_export.py
test_milestone43f_atlas_legend_example.py
test_milestone44b_chart_furniture_contracts.py
test_milestone44c_celestial_references.py
test_milestone44d_credits_and_stellar_counts.py
```

Targets:

```text
test_chart_furniture.py
test_reference_annotations.py
test_object_legend.py
test_stellar_magnitude_legend.py
test_legend_export.py
```

Disposition: **consolidate aggressively while preserving distinct layers**:
policy, statistics, handles, placement and export should each be tested once.

### H. Examples and installer — replace source inspection with behavior

Candidate sources include milestone 39 example tests, 43f/43h canonicalization,
44e–44j example/interface/guide/closure tests, 45d packaged parity,
45f planisphere tests, `test_cen_a_binocular.py`, and
`test_example_installer.py`.

Targets:

```text
test_example_cli.py
test_canonical_examples.py
test_example_installer.py
test_packaged_example_parity.py
test_example_regressions.py
```

Disposition: **major consolidation**. Keep defining geometry and one smoke
generation per family. Remove repeated assertions about exact implementation
calls once public behavior and parity are covered.

### I. Historical documentation and closure tests — strongest deletion candidates

Candidate sources:

```text
test_milestone24_documentation.py
test_milestone43j_documentation_closure.py
test_milestone44a_architecture_documents.py
test_milestone44i_user_guide.py
test_milestone44k_v06_closure.py
test_milestone45a_architecture_documents.py
test_milestone45g_v07_closure.py
```

Target:

```text
test_current_documentation.py
```

Keep only current authority, syntax, public commands/imports and link
integrity. **Delete assertions whose sole purpose is to freeze wording or
closure status of completed migrations.** Historical files remain in Git.

## Explicit early deletion candidates

These are the only exact duplicate bodies found statically:

- the two `*_example_exists` tests in milestone 39e and 39f;
- the two backend-independence tests in milestone 40i magnitude/statistics
  modules.

Even these should be removed only as part of their containing consolidation,
not as an isolated micro-change.

## Proposed test tiers

Add markers only after tests are organized by responsibility:

```toml
[tool.pytest.ini_options]
addopts = "-p no:remotedata"
filterwarnings = ["error::FutureWarning"]
markers = [
    "integration: crosses architectural component boundaries",
    "visual: validates rendered appearance or image structure",
    "slow: excluded from the normal development loop",
]
```

Suggested commands:

```bash
# Fast local development
pytest -q -m "not integration and not visual and not slow"

# Integration contracts
pytest -q -m integration

# Full release suite
pytest -q
```

Do not mark ordinary unit tests `slow` merely because they are currently
inefficient; optimize them first.

## Minimal visual regression set

Retain a deliberately small golden set:

1. atlas-print planisphere;
2. atlas-print regional constellation;
3. atlas-print regional constellation group with mask;
4. atlas-print binocular object;
5. cartoon-presentation chart;
6. one chart with legends and all semantic reference lines.

The existing 11 fixture scripts can probably be reduced or combined, but that
decision requires the runtime and visual review on the Mac.

Milestone 46D.8A adds one parameterized, catalogue-free parity module rather
than duplicating six integration builds. It compares the resolved view inputs
from every canonical example with the equivalent installed-command inputs;
later 46D.8 contracts retain ownership of drawing requests, configuration
isolation, invalid-input ordering, and the required visual matrix.

Milestone 46D.8B adds two more catalogue-free contracts at the shared drawing
adapter: one dense representative request covers every downstream concern,
and one covers the canonical four-product destination matrix. Existing
responsibility tests retain their focused edge cases; no integration build is
duplicated.

Milestone 46D.8C adds two catalogue-free installed-command contracts for
sequential overlay isolation and explicit precedence, and strengthens invalid
configuration failure ordering through the drawing boundary. Existing tests
remain the owners of recursive merge immutability, repeated drawing and grid
cleanup, family-order independence, observer-cache separation, and real
reusable-sphere behavior; those expensive contracts are not duplicated.

Milestone 46D.8D adds one cheap structural contract for the fixed 18-product
visual matrix. It proves unique output names, the six canonical family pairs,
the two supported style/mode products, and coverage of masks, horizons,
explicit framing, four grids, references, poles, legends, counts, and credits.
Rendering remains an explicit Mac acceptance action rather than an automated
golden-image test.

Milestone 46C.10 completed that required Mac validation without changing the
tier definitions. Fast, integration, visual, and full suites passed. The
diagnostic benchmark also produced 18 atlas-print products across all six
families and three observer/instant identities; all were visually approved.
Regional-single and regional-group exercised explicit outside masks. A later
appearance-curation stage may tune faint-star symbol saturation, but no
unexplained visual regression remains in the reusable-sphere closure.

## Incremental implementation plan

### 46B.1 — Record baseline and current contract matrix

- Run collection, durations and full suite on the Mac.
- Add a test inventory document mapping every module to an architectural owner.
- Make no test deletions.

**Status:** runtime baseline complete: 1,003 passed in 172.74 s. The static
contract mapping in this report supplies the initial ownership inventory.

### 46B.2 — Consolidate canonical-example hot spots

- Start with `test_milestone44fb2_canonical_example_controls.py`,
  `test_milestone44f_planisphere_regional_examples.py`, and
  `test_milestone45d_semantic_grid_styles.py`.
- Separate cheap parser/detail/style contract tests from expensive full chart
  construction.
- Replace repeated style × example-family construction with a representative
  matrix.
- Share immutable catalogue/module setup only where isolation behavior is not
  under test.
- Retain one full integration case for each chart family and every distinct
  mask/framing invariant.
- Measure focused and full runtime before and after.

### 46B.3 — Remove historical-document coupling

- Create `test_current_documentation.py`.
- Preserve current syntax, imports, links and architecture authority.
- Remove completed-migration wording tests.
- Run focused and full suites.

### 46B.4 — Consolidate remaining example and packaged-parity tests

- Establish one shared CLI contract matrix.
- Retain one smoke generation per chart family.
- Retain packaged/canonical parity.
- Remove repeated source-text orchestration assertions.

### 46B.5 — Consolidate legends and furniture

- Merge policy, statistics, handle, placement and export tests by ownership.
- Preserve bug-specific cases and public behavior.

### 46B.6 — Consolidate style, modes, labels and detail

- Replace repeated style/mode Cartesian products with representative matrices.
- Preserve render-local isolation, palette contracts and label bug geometries.

### 46B.7 — Rename and consolidate geometry/catalogue tests

- Remove remaining milestone filenames.
- Use shared parametrized contracts for deep-sky layer families.
- Avoid weakening scientific geometry coverage.

### 46B.8 — Add test tiers and close the audit

- Add markers and documented fast/integration/full commands.
- Record before/after module count, collected cases and runtime.
- Run the full suite and mandatory visual regression set.
- Update the current architecture and source-tree responsibility map.

**Closure status:** completed through Milestone 46B.10.

The implementation was deliberately split into smaller reversible steps after
46B.7 so that residual ownership renames and regression-example consolidation
could be validated independently. The final measured Mac results are:

| Measure | Before 46B | After 46B.9 |
|---|---:|---:|
| Collected passing cases | 1,003 | 929 |
| Full-suite wall time | 172.74 s | 58.80 s |
| Milestone-named test modules | 132 | 12 before final ownership rename |

Milestone 46B.10 renames the final twelve modules by responsibility, registers
the `integration`, `visual`, and reserved `slow` markers, documents the fast,
integration, visual, and full commands, and leaves collected full-suite cases
unchanged. No production files or public APIs change.

## Acceptance criteria for Milestone 46B

- No production-code behavior changes.
- Every permanent test maps to a current architectural responsibility, public
  API, scientific invariant or confirmed regression.
- No permanent test filename contains a milestone number.
- Current documentation is protected; historical migration wording is not.
- Canonical and packaged examples retain parity coverage.
- Atlas-print remains the golden visual baseline.
- Fast, integration, visual and full test commands are documented.
- Full suite and required visual checks pass after every submilestone.
- The final report records counts and runtime before and after.
- No arbitrary test-count target is imposed; reductions must result from
  demonstrated overlap or superseded contracts.

## Recommendation

The measured baseline completes the diagnostic part of **46B.1**. Commit the
audit/contract matrix before any cleanup, then proceed with **46B.2** as the
first implementation patch. Its scope should be limited to the three measured
canonical-example hot spots; later consolidation remains in separate,
reversible patches.
