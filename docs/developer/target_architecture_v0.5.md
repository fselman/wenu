# Wenu target architecture v0.5

Status: proposed target  
Migration source: `current_architecture_v0.4.md`  
Migration plan: `wenu_migration_0.4_to_0.5.md`

## 1. Purpose

Version 0.5 extends the working atlas chart system without replacing its
astronomical or rendering architecture.

The target is one canonical chart workflow supporting independent choices of:

- chart type;
- chart style;
- output mode;
- detail policy;
- legend policy.

The first implementation path is deliberately conservative:

1. preserve atlas print output;
2. incorporate the tested legend work into atlas charts;
3. adapt the tested presentation palette and output behavior to atlas charts;
4. derive a new cartoon style as an atlas-style alternative;
5. retire the current cartoon-specific orchestration only after parity is
   demonstrated.

## 2. Non-negotiable development principles

### 2.1 Preserve functionality

Every milestone must preserve:

- catalogue loading;
- spherical geometry;
- coordinate transformations;
- projection behavior;
- projection-domain clipping;
- viewport clipping;
- object selection;
- atlas print appearance;
- existing public chart types.

The full test suite must pass at each milestone.

### 2.2 Extend; do not rewrite

Version 0.5 is an incremental modification of the current architecture.

It must not introduce replacement:

- sky models;
- scene hierarchies;
- projection hierarchies;
- renderer hierarchies;
- parallel chart pipelines.

### 2.3 One canonical pipeline

Atlas and cartoon styles must use the same chart, projection, preparation, and
renderer pipeline.

No style may acquire its own projection, clipping, or export path.

### 2.4 Examples express requests

Examples may:

- construct an observer and sky;
- select chart type and tangent point;
- select style and mode;
- request layers and detail overrides;
- provide explicit label-placement overrides;
- select legend options;
- choose an output path.

Examples must not implement:

- spherical or projected clipping;
- projection-domain guards;
- renderer dispatch;
- legend assembly;
- repeated final saving;
- catalogue joins or astronomical selection logic.

## 3. Target canonical flow

```text
Catalogues and sky definitions
    -> sky layers
    -> spherical geometry
    -> projection-domain guard
    -> projection
    -> projected geometry
    -> chart preparation
    -> resolved render plan
    -> renderer
    -> chart furniture and export
```

This is the existing pipeline with two integration improvements:

- the final layer options are exposed conceptually as a resolved render plan;
- legends and output are coordinated by the chart workflow rather than by
  examples.

No new scene-container class is required for v0.5.

## 4. Independent configuration axes

### 4.1 Chart type

Chart type owns geometry and framing.

Required chart types remain:

- regional;
- planisphere/full-sky;
- circumpolar;
- binocular.

Chart type owns:

- projection;
- tangent point;
- orientation;
- viewport;
- final boundary;
- projection-domain clipping requirements;
- optional observer-horizon clipping.

Chart type does not choose atlas or cartoon appearance.

### 4.2 Chart style

Required v0.5 styles are:

- `atlas`;
- `cartoon`.

Style owns appearance:

- sky and canvas colors;
- star symbol appearance;
- constellation-line appearance;
- coordinate-grid appearance;
- boundary appearance;
- Milky Way appearance;
- deep-sky symbols;
- label typography and halo;
- legend visual styling.

The new cartoon style is not the deprecated cartoon implementation. It is a
normal style operating through the atlas-proven canonical pipeline.

Initial cartoon defaults:

- preserve constellation-vertex stars;
- show only a small number of additional bright stars;
- use thicker constellation lines;
- omit coordinate grids;
- omit constellation boundaries;
- retain constellation labels;
- allow optional Milky Way rendering;
- support explicit label-position and offset overrides.

Content choices such as stellar magnitude remain detail-policy decisions even
when a cartoon preset supplies recommended defaults.

### 4.3 Output mode

Required v0.5 modes are:

- `print`, synonymous with paper output;
- `presentation`.

Mode adapts a style to its output medium without changing chart geometry or
astronomical content.

Print mode controls:

- paper-oriented figure dimensions;
- print DPI;
- print-safe line and font sizes;
- white or otherwise printable canvas;
- print contrast.

Presentation mode controls:

- projector/screen figure dimensions;
- screen DPI;
- enlarged typography and symbols;
- thicker screen-visible lines;
- a bright ocean-blue sky for dark-sky styles;
- high-contrast light stars and yellow/gold structural lines;
- avoidance of low-contrast red-on-blue combinations.

The selected style remains recognizable in both modes.

### 4.4 Detail policy

Detail policy owns astronomical selection and density:

- stellar limiting magnitude;
- constellation-vertex preservation;
- additional selected stars;
- layer enablement;
- deep-sky thresholds;
- label density.

The default stellar limiting magnitude may depend on chart angular field size.
Modes may apply a small readability adjustment, but mode must not replace the
detail policy.

### 4.5 Legend policy

Legend policy owns whether and where chart furniture is drawn.

Required reusable legend components are:

- object-symbol legend;
- stellar magnitude-size legend;
- chart-center and coordinate-system metadata;
- observer, location, date, and time metadata when relevant.

Legend content must be derived from resolved chart content and style. A legend
must not advertise a disabled layer.

Legends are separate from astronomical layers but are coordinated by the chart
export workflow.

## 5. Target composition contract

A resolved chart composition contains:

```python
ChartComposition(
    context=...,
    style=...,
    mode=...,
    detail=...,
    legends=...,
)
```

The exact public constructor may evolve, but these concepts remain independent.

A chart export accepts the composition directly:

```python
chart.export(
    sky,
    renderer,
    output,
    composition=composition,
)
```

Compatibility arguments such as `style=` and `layer_options=` remain supported
during migration.

The chart workflow:

1. resolves style plus mode;
2. resolves detail from chart context;
3. obtains render-local layer options;
4. invokes the existing `CelestialSphere.draw_chart()` pipeline;
5. draws requested legends;
6. saves once;
7. returns the render and export result.

## 6. Resolved render plan

Version 0.5 does not require a new public hierarchy. It requires an inspectable
resolved value, which may initially be a lightweight dataclass or structured
mapping.

It records:

- ordered enabled layers;
- per-layer selection options;
- projection-domain handling;
- projected preparation callbacks;
- resolved visual options;
- label options;
- legend plan;
- export options.

The plan contains no backend artists and no catalogue querying.

## 7. Chart preparation and clipping

The three existing clipping responsibilities remain:

### 7.1 Projection-domain guard

Runs before projection only when required to prevent far-side or invalid
polygon projection.

### 7.2 Chart preparation

Runs after projection for semantic and chart-specific preparation, including
optional observer-horizon selection.

### 7.3 Final viewport clipping

Runs at the renderer boundary and enforces the rectangular, circular, or other
final field stop.

Styles and modes do not alter any of these operations.

## 8. Observer policy

The observer remains required by the normal public construction flow.

Observer and tangent point remain separate:

- observer supplies time, location, and frame context;
- chart type supplies the projection center and orientation;
- planisphere may choose zenith as tangent point;
- regional chart may choose arbitrary RA/Dec or another frame coordinate;
- observer-horizon clipping is opt-in according to chart type and request.

## 9. Style resolution

Target resolution is:

```text
base style
    + output-mode adaptation
    + explicit user style overrides
    -> resolved visual style
```

Detail resolution is independent:

```text
detail policy
    + chart field size
    + explicit content overrides
    -> resolved detail
```

The two results meet only when constructing the render plan.

`PublicationStyle` may remain the compatibility representation consumed by the
current pipeline. New behavior should originate in composed style components,
not be implemented only in `PublicationStyle`.

## 10. Atlas style target

Atlas print mode is the golden reference and must remain visually unchanged
unless a change is explicitly approved.

Atlas presentation mode adapts the atlas hierarchy for screens:

- retains atlas object symbols;
- retains Milky Way hierarchy;
- retains coordinate and constellation information;
- uses an ocean-blue background;
- uses high-contrast light stars and labels;
- replaces unsuitable red-on-blue lines with readable presentation colors;
- enlarges typography and critical symbols;
- keeps density under detail-policy control.

## 11. Cartoon style target

The cartoon style is built as a variant of the canonical style components.

It does not own:

- its own chart class;
- its own export workflow;
- its own projection;
- its own clipping;
- its own renderer;
- its own astronomical-selection algorithm.

Recommended presets may pair cartoon style with cartoon detail defaults, but
the objects remain independently replaceable.

The existing cartoon modules are deprecated immediately in documentation.
They are removed only after all required behavior is available through the
canonical system and visual parity tests pass.

## 12. Legend integration target

The tested Milestone 40H–40J legend work is reused.

The canonical chart workflow resolves and draws:

1. object legend, if enabled;
2. stellar magnitude legend, if enabled;
3. contextual metadata, if enabled.

Legend placement is configurable and coordinated so independent legends do not
overlap.

Galaxy entries use the canonical filled ellipse, not a rectangular proxy.
The stellar magnitude legend uses the same resolved magnitude-to-area mapping
as the plotted stars.

## 13. Label placement

Label placement remains a chart-preparation concern with style-controlled
typography.

The target supports:

- default automatic placement;
- the nine requested relative positions:
  `c`, `ul`, `u`, `ur`, `cl`, `cr`, `ll`, `lc`, `lr`;
- an additional explicit offset;
- per-constellation overrides;
- future collision-aware placement without changing examples.

Label positions do not belong in the renderer backend.

## 14. Public usage target

An ordinary example should approach:

```python
observer = Observer(...)
sky = CelestialSphere(observer)
sky.add_stars(...)
sky.add_constellations(...)
sky.add_milky_way_isophotes()

chart = RegionalChart(...)
composition = compose_chart(
    chart,
    style="atlas",
    mode="presentation",
    detail=...,
    legends=...,
)

chart.export(
    sky,
    MatplotlibRenderer(...),
    output,
    composition=composition,
)
```

Convenience APIs may reduce this further, but must delegate to this same
pipeline.

## 15. Package boundaries

The v0.4 source dependency rules remain mandatory.

In particular:

- no renderer imports from `sky`;
- no chart imports from `objects` to reconstruct astronomical semantics;
- no style performs projection or clipping;
- no mode selects chart geometry;
- no detail policy creates backend artists;
- no example implements pipeline stages.

## 16. Compatibility policy

Version 0.5 uses staged compatibility:

- existing atlas print examples remain valid;
- existing chart constructors remain valid;
- existing `style=` and `layer_options=` calls remain valid during migration;
- deprecated cartoon APIs emit deprecation warnings only after their canonical
  replacements are demonstrated;
- removal is outside the first v0.5 migration unless separately approved.

## 17. Verification matrix

Every migration milestone must test:

| Chart type | Atlas print | Atlas presentation | Cartoon print | Cartoon presentation |
|---|---:|---:|---:|---:|
| Regional Sgr–Sco–Oph–Ser | Required | Required when introduced | Required when introduced | Required when introduced |
| Planisphere | Required | Required when introduced | Required when introduced | Required when introduced |
| Circumpolar | Required | Required when introduced | Required when introduced | Required when introduced |

Additional projection-domain regression:

- Summer Triangle regional chart with Milky Way isophotes;
- circumpolar circular viewport intersecting the LMC.

## 18. Completion criteria

Version 0.5 architecture is complete when:

1. atlas and cartoon are normal styles of one chart pipeline;
2. print/paper and presentation are normal output modes;
3. atlas print output remains accepted;
4. legends are integrated into canonical export;
5. examples contain no clipping or legend assembly;
6. mode does not alter chart geometry or leak state between exports;
7. detail resolution is render-local;
8. deprecated cartoon orchestration is no longer needed by examples;
9. all required chart-style-mode combinations pass tests and visual review;
10. the architecture and implementation reference documents describe the
    actual code.

## 19. Non-goals

Version 0.5 does not aim to:

- replace `CelestialSphere`;
- introduce a new scene graph;
- replace geometry classes;
- replace stereographic projection;
- replace the Matplotlib renderer;
- make Wenu an interactive planetarium;
- remove all compatibility APIs;
- solve general optimal label placement in one milestone.

## 20. Central target

The central v0.5 result is:

> The working atlas chart pipeline becomes the single configurable chart
> pipeline. Atlas and cartoon are styles; print/paper and presentation are
> modes; chart type owns geometry; detail owns content; legends are integrated
> chart furniture.
