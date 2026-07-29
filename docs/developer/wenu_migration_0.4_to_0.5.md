# Wenu migration roadmap: v0.4 to v0.5

Status: proposed incremental roadmap  
Source architecture: `current_architecture_v0.4.md`  
Target architecture: `target_architecture_v0.5.md`

## 1. Objective

Migrate from the current atlas-print-centered implementation to a single
canonical chart workflow supporting:

- styles: atlas and cartoon;
- modes: print/paper and presentation;
- integrated object, stellar-magnitude, and contextual legends;
- all existing chart types.

The migration preserves the current astronomical, projection, preparation, and
rendering architecture.

## 2. Migration rules

### 2.1 Preserve before extending

At the beginning of each milestone:

1. run the focused baseline tests;
2. generate the accepted reference charts;
3. make the smallest required change;
4. rerun focused and full tests;
5. visually compare the reference charts.

No milestone proceeds with an unexplained regression.

### 2.2 Atlas first

Atlas print is the golden baseline.

New infrastructure is first connected to atlas charts. Cartoon behavior is
migrated only after that infrastructure is stable.

### 2.3 No parallel pipeline

New style, mode, legend, or detail behavior must enter through the current
chart and `CelestialSphere.draw_chart()` pipeline.

### 2.4 Deprecate safely

The current cartoon implementation is considered deprecated now, but remains
available and tested until the replacement supports the required chart matrix.

### 2.5 Small commits

Each milestone should be independently testable, reviewable, and reversible.

## 3. Mandatory regression charts

The standard visual test suite is:

1. regional Sagittarius–Scorpius–Ophiuchus–Serpens;
2. circular planisphere;
3. southern circumpolar chart;
4. Summer Triangle regional chart with Milky Way isophotes;
5. circumpolar viewport crossing the LMC.

The first three are exercised across style and mode combinations as those
combinations become available.

## 4. Milestone 43A — Architecture control documents

### Goal

Establish v0.4 as-is and v0.5 target documents before further implementation.

### Work

- add `current_architecture_v0.4.md`;
- add `target_architecture_v0.5.md`;
- add this migration roadmap;
- identify the current cartoon implementation as deprecated;
- define atlas print as the golden baseline;
- define type/style/mode/detail/legend responsibilities;
- record the projection-domain guard introduced in Milestone 42C.

### Verification

- terminology agrees across all three documents;
- no proposed step requires a second chart pipeline;
- all existing working-tree source changes remain untouched.

### Commit

Suggested:

```text
Milestone 43A: Define the Wenu v0.5 architecture and migration
```

## 5. Milestone 43B — Atlas baseline and style/mode contracts

### Goal

Make style and mode explicit in the stable atlas path without changing atlas
print output.

### Work

- define or confirm stable identifiers for:
  - `style="atlas"`;
  - `mode="print"`;
- treat `paper` as documentation terminology or an alias for `print`, not a
  third independent mode;
- define the resolved-style contract:

  ```text
  style + mode + explicit overrides -> resolved visual style
  ```

- add a composition test proving mode resolution does not change:
  - projection;
  - viewport;
  - chart boundary;
  - enabled astronomical content;
- keep current direct `AtlasChartStyle` construction working.

### Constraints

- no palette change;
- no chart constructor change;
- no catalogue or geometry change;
- no cartoon migration yet.

### Tests

- atlas regional print unchanged;
- atlas planisphere print unchanged;
- atlas circumpolar print unchanged;
- full suite passes.

### Commit

```text
Milestone 43B: Establish atlas style and output mode contracts
```

## 6. Milestone 43C — Canonical legend integration for atlas

### Goal

Incorporate yesterday's tested legend system into canonical atlas export.

### Work

- reuse existing:
  - canonical object symbols;
  - contextual metadata;
  - stellar magnitude legend;
  - dual-legend planning;
  - galaxy ellipse legend handle;
- add a `LegendPolicy` or equivalent resolved configuration to chart
  composition;
- allow legends to be independently enabled and positioned;
- derive legend content from enabled layers;
- draw legends before the chart is saved;
- ensure chart export saves exactly once.

### Public behavior

The caller can request:

```python
legends=LegendOptions(
    objects=True,
    stellar_magnitudes=True,
    context=True,
)
```

The exact class name may follow current code conventions.

### Constraints

- examples do not call `draw_chart_legend()` directly after this milestone;
- examples do not perform a second `savefig()`;
- legend code does not query catalogues directly;
- legend layout does not alter projection or viewport.

### Tests

- atlas regional chart with object and stellar legends;
- planisphere contextual legend with observer, date, and time;
- circumpolar chart legend;
- disabled layers absent from object legend;
- filled elliptical galaxy symbol;
- no overlapping independent legends in reference sizes;
- atlas geometry and layer artists unchanged.

### Commit

```text
Milestone 43C: Integrate canonical legends into atlas export
```

## 7. Milestone 43D — Atlas presentation output mode

### Goal

Adapt the useful presentation work from the deprecated cartoon path to atlas
style.

### Work

- define atlas presentation palette;
- use a bright ocean-blue sky background;
- use high-contrast light stars and labels;
- use yellow/gold structural lines where appropriate;
- avoid red-on-blue line combinations;
- increase font, marker, and line scales for projection;
- resolve screen dimensions and DPI through `PresentationMode`;
- preserve atlas symbol semantics and visual hierarchy.

### Constraints

- presentation changes appearance and output scale only;
- presentation does not change chart geometry;
- presentation does not change the detail policy unless explicitly requested;
- print and presentation renders of the same sky do not share mutable resolved
  state;
- atlas print remains unchanged.

### Tests

- regional atlas presentation;
- planisphere atlas presentation;
- circumpolar atlas presentation;
- geometry equality between print and presentation;
- palette contrast assertions;
- sequential print/presentation/print exports reproduce the first print result.

### Visual acceptance

- suitable for a classroom screen or projector;
- labels and important lines remain readable;
- Milky Way is visible but subordinate;
- no low-contrast red structures over blue.

### Commit

```text
Milestone 43D: Add atlas presentation output mode
```

## 8. Milestone 43E — Render-local detail resolution

### Goal

Prevent one chart composition from altering a later export of the same sky.

### Work

- audit mutations performed by `apply_resolved_detail()`;
- resolve selection into render-local layer options where possible;
- where a legacy layer requires mutation, save and restore state within the
  export transaction;
- preserve constellation-vertex metadata in `Stars`;
- retain field-size-dependent limiting magnitude;
- prove that style and mode changes do not leak content.

### Constraints

- no catalogue schema rewrite;
- no new stars implementation;
- no change to existing default selections.

### Tests

- print then presentation then print;
- atlas then cartoon then atlas;
- regional then planisphere using the same `CelestialSphere`;
- explicit star identifiers union correctly with constellation vertices;
- lineless constellations can still contribute bright stars and labels.

### Commit

```text
Milestone 43E: Make chart detail resolution render-local
```

## 9. Milestone 43F — Canonical high-level chart export

### Goal

Make ordinary examples issue chart requests rather than coordinate the
renderer workflow.

### Work

- allow chart export to accept a resolved `ChartComposition`;
- internally:
  - resolve layer options;
  - invoke the existing draw pipeline;
  - add legends;
  - save once;
- preserve legacy `style=` and `layer_options=` arguments;
- expose the resolved plan or result for diagnostics;
- keep Matplotlib figure creation either:
  - behind a convenience export method, or
  - explicitly supplied by advanced callers.

### Target example shape

```python
composition = compose_chart(
    chart,
    style="atlas",
    mode="presentation",
    detail=detail,
    legends=legends,
)

chart.export(
    sky,
    renderer,
    output,
    composition=composition,
)
```

### Constraints

- `CelestialSphere.draw_chart()` remains the execution core;
- no replacement renderer;
- no replacement chart hierarchy;
- no projection or clipping in examples.

### Tests

- old and new export calls produce equivalent geometry and artists;
- legends appear in the saved file without a second save;
- Summer Triangle needs no custom Milky Way preparation;
- output metadata and return values remain available.

### Commit

```text
Milestone 43F: Add canonical composed chart export
```

## 10. Milestone 43G — New cartoon style on the atlas pipeline

### Goal

Create `style="cartoon"` as a normal style of the canonical workflow.

### Work

- derive cartoon visual components from the stable style system;
- provide recommended cartoon detail defaults;
- preserve constellation-vertex stars;
- allow additional bright stars according to field-size detail;
- use thicker constellation lines;
- disable coordinate grids and constellation boundaries by default;
- retain constellation labels;
- support optional Milky Way display;
- retain explicit per-constellation position and offset controls.

### Constraints

- no cartoon-specific chart class;
- no cartoon-specific renderer;
- no cartoon-specific projection or clipping;
- no fork of chart export;
- detail remains a separate resolved object.

### Tests

For regional, planisphere, and circumpolar charts:

- cartoon print;
- cartoon presentation;
- constellation vertices present;
- expected bright non-vertex stars present;
- grids absent by default;
- boundaries absent by default;
- label overrides work;
- optional Milky Way obeys each export independently.

### Commit

```text
Milestone 43G: Add cartoon style to the canonical chart pipeline
```

## 11. Milestone 43H — Example simplification

### Goal

Replace low-level examples with declarative examples.

### Work

- simplify:
  - atlas regional example;
  - atlas Summer Triangle example;
  - planisphere example;
  - circumpolar example;
  - cartoon examples;
- keep one advanced example demonstrating renderer access;
- move reusable workflow code from examples into chart APIs;
- retain explicit label-position dictionaries as documented user
  configuration.

### Example acceptance rules

An ordinary example must not contain:

- clipping callbacks;
- calls to `clip_polygons_to_projection_cap`;
- direct legend assembly;
- duplicate `savefig()`;
- catalogue metadata reconstruction;
- renderer-internal branching.

### Tests

- import and execute every reference example;
- assert each output file exists;
- validate example source does not contain prohibited low-level calls;
- visually inspect the standard regression charts.

### Commit

```text
Milestone 43H: Simplify atlas and cartoon chart examples
```

## 12. Milestone 43I — Deprecation boundary

### Goal

Mark the old cartoon-specific orchestration as deprecated after the canonical
replacement is demonstrated.

### Work

- inventory deprecated public names;
- map every old entry point to its replacement;
- add documented deprecation notices;
- retain compatibility wrappers where inexpensive;
- stop using deprecated APIs in package examples and documentation.

### Constraints

- do not remove working behavior in this milestone;
- do not remove tests until an equivalent canonical test exists;
- no broad file moves solely for tidiness.

### Tests

- deprecated calls still function;
- deprecation message identifies the replacement;
- canonical chart matrix passes without importing deprecated cartoon modules.

### Commit

```text
Milestone 43I: Deprecate the legacy cartoon workflow
```

## 13. Milestone 43J — Documentation and v0.5 closure

### Goal

Make documentation describe the implementation that now exists.

### Work

- update `implementation_reference.md`;
- update `source_tree.md`;
- update public examples and API documentation;
- archive superseded roadmap documents;
- record the compatibility and deprecation policy;
- document style, mode, detail, and legend extension procedures.

### Verification

- documented imports execute;
- documented examples generate charts;
- package dependency audit passes;
- full test suite passes;
- complete visual matrix is approved.

### Commit

```text
Milestone 43J: Complete the Wenu v0.5 architecture migration
```

## 14. Validation commands

Focused commands should evolve with the milestone, but every milestone ends
with:

```bash
pytest
git diff --check
git status
```

Visual examples must write beneath `output/`, grouped by example or chart
family.

## 15. Stop conditions

Pause the migration and review the architecture if a proposed change requires:

- changing catalogue formats solely for chart composition;
- replacing `CelestialSphere.draw_chart()`;
- adding a second projection path;
- letting styles perform clipping;
- letting modes change chart geometry;
- importing rendering from `sky`;
- implementing chart logic in examples;
- accepting an atlas print regression without explicit approval.

## 16. Completion definition

The v0.4-to-v0.5 migration is complete when:

- atlas and cartoon are interchangeable styles;
- print/paper and presentation are interchangeable modes;
- all combinations use the current canonical pipeline;
- legends are integrated and configurable;
- detail resolution is render-local;
- examples are declarative;
- atlas print remains the accepted baseline;
- the standard regional, planisphere, and circumpolar chart matrix passes;
- the Summer Triangle and LMC clipping regressions pass;
- deprecated cartoon orchestration is no longer used by reference code;
- architecture documents and implementation agree.
