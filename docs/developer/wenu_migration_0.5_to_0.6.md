# Wenu migration roadmap: v0.5 to v0.6

**Status:** Proposed incremental roadmap
**Source:** `current_architecture_v0.5.md`
**Target:** `target_architecture_v0.6.md`
**Base commit:** `33cd5aa`

## 1. Objective

Create five canonical, documented example families across atlas/cartoon and
print/presentation, add reusable celestial-reference and chart-credit
furniture, and remove obsolete examples without losing regression coverage.

The migration extends the completed v0.5 pipeline. It does not replace it.

## 2. Migration rules

### 2.1 Preserve the v0.5 architecture

All work continues through `ChartComposition`, chart export, and
`CelestialSphere.draw_chart()`. No milestone may add an example-only pipeline.

### 2.2 Replace before deleting

An existing example may be removed only after:

1. its user-facing purpose has a canonical replacement;
2. tests no longer import it as a fixture;
3. its scientific and visual regression coverage has moved elsewhere;
4. the full suite passes.

### 2.3 Furniture does not change geometry

Reference labels, pole markers, footers, and legends use resolved chart and
render information. They do not change projection, viewport, chart boundary,
or astronomical selection.

### 2.4 Examples express requests

Ordinary examples may select chart type, target, style, mode, detail,
furniture, and output. They may not implement clipping, backend dispatch,
catalogue joins, legend assembly, or repeated saving.

### 2.5 Small commits

Each milestone must compile, pass focused and full tests, preserve warning
hygiene, and leave the repository usable.

## 3. Required visual matrix

For each family, approve:

| Family | Atlas print | Atlas presentation | Cartoon print | Cartoon presentation |
|---|---:|---:|---:|---:|
| Planisphere | Required | Required | Required | Required |
| Constellation group | Required | Required | Required | Required |
| Single constellation | Required | Required | Required | Required |
| Circumpolar | Required | Required | Required | Required |
| Binocular object | Required | Required | Required | Required |

Retained projection regressions include the Summer Triangle with Milky Way
isophotes and the southern circumpolar LMC boundary crossing.

## 4. Milestone 44A — Architecture control documents

### Goal

Record the audited v0.5 baseline, the v0.6 target, and this roadmap before
implementation.

### Work

- add `current_architecture_v0.5.md`;
- add `target_architecture_v0.6.md`;
- add this roadmap;
- record the 23-script mixed examples baseline;
- define the five canonical families and 20-product matrix;
- define ownership of masks, references, credits, and stellar counts;
- establish replace-before-delete rules.

### Verification

- all terms agree across the three documents;
- no target requires a second rendering or export path;
- documentation contract tests name the new architectural authority;
- no runtime or example files change.

### Commit

```text
Milestone 44A: Define the Wenu v0.6 architecture and roadmap
```

## 5. Milestone 44B — Chart furniture contracts

### Goal

Define backend-independent resolved options for new chart furniture while
preserving `LegendOptions` compatibility.

### Work

- define reference-plane annotation options;
- define pole selection and semantic presentation options;
- define application/version and copyright footer options;
- add `stellar_counts` or equivalent to legend options;
- define automatic placement and explicit override contracts;
- keep all options immutable and inspectable.

### Tests

- defaults preserve v0.5 output;
- style and mode do not alter geometry;
- options resolve independently;
- existing `legends=` callers remain valid;
- policy modules have no Matplotlib dependency.

### Commit

```text
Milestone 44B: Define canonical chart furniture contracts
```

## 6. Milestone 44C — Celestial reference annotations

### Goal

Render semantic ecliptic/Galactic-plane labels and canonical pole crosses.

### Work

- label reference planes independently of numeric grid labels;
- compute boundary-aware automatic anchors from prepared reference curves;
- support explicit position overrides;
- normalize NCP/SCP, NEP/SEP, and NGP/SGP cross symbols;
- adapt colors and scale through style and mode;
- let normal clipping remove non-visible requested poles.

### Tests

- rectangular, circular, and binocular boundaries;
- semantic labels never expose internal curve names;
- numeric grid labels remain independently controlled;
- both-pole requests are safe;
- print/presentation and atlas/cartoon geometry equality;
- sequential renders do not leak reference state.

### Commit

```text
Milestone 44C: Add celestial reference annotations
```

## 7. Milestone 44D — Credits and cumulative stellar counts

### Goal

Complete reusable footer and stellar-legend information.

### Work

- draw caller copyright at lower left in figure margin;
- draw `Wenu <version>` at lower right from installed metadata;
- reserve sufficient figure margin in both modes;
- calculate cumulative rendered-star counts for every magnitude entry;
- format optional labels as `magnitude (count)`;
- retain the count-free v0.5 default.

### Scientific contract

For entry `m`, count only actually rendered stars with magnitude `<= m` after
all selection and chart-footprint constraints.

### Tests

- no catalogue-global counts;
- circular and horizon footprints count correctly;
- constellation-vertex and explicit-star behavior is correct;
- footer text and placement are independent;
- version is not hard-coded;
- footers do not overlap axes or legends at reference sizes.

### Commit

```text
Milestone 44D: Add chart credits and stellar legend counts
```

## 8. Milestone 44E — Uniform example interface

### Goal

Establish one declarative command-line pattern for all reference examples.

### Work

- implement shared argument conventions without an example-only framework;
- support `--style`, `--mode`, `--output`, and `--all`;
- define deterministic output names and directories;
- keep family-specific target arguments local and simple;
- test source for prohibited low-level operations.

### Tests

- invalid style and mode fail clearly;
- one invocation writes one output;
- `--all` writes four outputs;
- version, furniture, detail, and legends resolve through public APIs;
- examples do not call `savefig()` or renderer clipping methods.

### Commit

```text
Milestone 44E: Establish the canonical example interface
```

## 9. Milestone 44F — Planisphere and regional examples

### Goal

Create the first three canonical example families.

### Work

- add `planisphere.py` using La Ligua and the accepted observing date;
- add `regional_constellation_group.py`;
- add `regional_constellation.py`;
- include optional reference planes, poles, credits, legends, and star counts;
- use optional outside masks for regional emphasis;
- preserve the Summer Triangle and Sgr-Sco-Oph-Ser regressions.

### Tests and visual acceptance

- all 12 style/mode products execute;
- group mask is the union of selected IAU regions;
- single mask follows one IAU region;
- constellation labels remain readable;
- atlas print remains scientifically and visually accepted;
- cartoon products remain sparse without changing geometry.

### Commit

```text
Milestone 44F: Add canonical planisphere and regional examples
```

## 10. Milestone 44G — Circumpolar example

### Goal

Create the canonical circumpolar family without losing polar and LMC
regressions.

### Work

- add `circumpolar.py`;
- use the uniform interface;
- integrate references, poles, credits, legends, and counts;
- preserve circular grid-label anchors;
- preserve visible-region constellation-label placement;
- preserve the LMC boundary-crossing product.

### Tests

- all four style/mode products execute;
- circular boundary and grid labels remain correct;
- LMC isophotes clip canonically;
- reference annotations remain inside the usable chart region;
- no circular placement logic appears in the example.

### Commit

```text
Milestone 44G: Add the canonical circumpolar example
```

## 11. Milestone 44H — Binocular object workflow and example

### Goal

Make selected-object binocular charts fully canonical.

### Work

- move aperture rendering and artist clipping into `BinocularChart` or
  canonical export;
- center charts on a selected coordinate or catalogue object;
- add `binocular_object.py`, initially documenting Centaurus A;
- support the uniform style/mode interface;
- integrate appropriate furniture without overcrowding the field.

### Constraints

- no Matplotlib patches or `set_clip_path()` in the example;
- no object-specific chart subclass;
- no duplicate catalogue or coordinate-transform pipeline.

### Tests

- all four style/mode products execute;
- field diameter and tangent point remain correct;
- circular aperture owns all clipping;
- target label and contextual metadata are correct;
- example source contains no renderer internals.

### Commit

```text
Milestone 44H: Add canonical selected-object binocular charts
```

## 12. Milestone 44I — User guide and README image

### Goal

Document the complete public workflow with one reproducible README chart.

### Work

- add the structured user guide;
- document each chart family;
- document chart type, style, mode, detail, legends, references, masks,
  credits, and counts;
- place one concise executable planisphere example in the README;
- generate and approve the README planisphere image;
- record exact image provenance and regeneration command.

### Verification

- documented imports execute;
- documented commands generate expected files;
- README code is synchronized with the canonical example;
- the checked-in image matches its provenance contract;
- English and Spanish README links remain correct.

### Commit

```text
Milestone 44I: Add the Wenu v0.6 user guide
```

## 13. Milestone 44J — Example and test cleanup

### Goal

Leave `examples/` containing only the five canonical families.

### Work

- move diagnostic example fixtures into tests or stable APIs;
- preserve catalogue, symbol, legend, clipping, and style regressions;
- remove historical milestone scripts;
- remove superseded component demonstrations;
- enforce the exact five-file example contract.

### Tests

- no test imports a deleted user example;
- package-boundary tests still pass;
- the full 20-product visual matrix executes;
- all former example-backed regression assertions remain represented;
- full suite passes without warnings.

### Commit

```text
Milestone 44J: Complete the canonical examples directory
```

## 14. Milestone 44K — v0.6 closure

### Goal

Make active documentation describe the final implementation and close the
migration.

### Work

- update implementation reference and source tree;
- mark target implemented and roadmap complete;
- archive superseded v0.5 migration documents as appropriate;
- run dependency and warning audits;
- record final visual approvals.

### Verification

- five canonical examples only;
- all 20 products approved;
- README image provenance verified;
- documented imports and commands execute;
- full test suite passes without warnings;
- working tree is clean.

### Commit

```text
Milestone 44K: Complete the Wenu v0.6 migration
```

## 15. Stop conditions

Pause and review the architecture if a change would require:

- a second chart, projection, clipping, legend, or export pipeline;
- style or mode changes to chart geometry;
- catalogue queries from furniture rendering;
- Matplotlib imports in semantic policy modules;
- manual clipping or saving in a canonical example;
- deleting an example before its regression coverage is relocated;
- committing a generated gallery rather than the single approved README
  image;
- accepting an unexplained atlas print regression.

## 16. Completion definition

The migration is complete when the target architecture completion criteria
are satisfied and the five canonical examples are the clearest supported path
for learning and verifying Wenu.
