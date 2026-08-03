# Wenu target architecture v0.6

**Status:** Proposed target
**Source architecture:** `current_architecture_v0.5.md`
**Migration plan:** `wenu_migration_0.5_to_0.6.md`

## 1. Purpose

Version 0.6 turns the implemented v0.5 chart pipeline into a small,
well-documented set of reference chart products. It does not replace the
astronomical, geometry, projection, preparation, rendering, composition,
legend, or export architecture.

The target has five user-facing example families:

1. planisphere;
2. regional chart containing a constellation group;
3. regional chart containing one constellation;
4. circumpolar chart;
5. binocular chart centered on a selected object.

Every family supports atlas and cartoon styles and print and presentation
modes.

## 2. Central design

The v0.5 independent axes remain authoritative:

- chart type owns geometry;
- style owns appearance;
- mode adapts appearance and output medium;
- detail policy owns astronomical content and density;
- chart furniture owns legends, reference annotations, and credits.

The target flow remains:

```text
chart request
    -> ChartComposition
    -> render-local plan
    -> CelestialSphere.draw_chart()
    -> renderer
    -> canonical chart furniture
    -> one export
```

## 3. Canonical example set

The final `examples/` directory contains exactly:

```text
examples/
├── planisphere.py
├── regional_constellation_group.py
├── regional_constellation.py
├── circumpolar.py
└── binocular_object.py
```

Each script uses one common user contract:

```text
--style atlas|cartoon
--mode print|presentation
--output PATH
--all

--magnitude-limit VALUE
--constellation-labels
--constellation-boundaries
--references
--poles
--pole-labels

--constellation-line-width VALUE
--constellation-line-color COLOR
--constellation-label-color COLOR
--constellation-boundary-width VALUE
--constellation-boundary-color COLOR

--legends
--object-legend
--magnitude-legend
--star-counts
```

`--all` generates the four style/mode combinations. A normal invocation
generates one chart. Examples may expose family-specific astronomical choices,
such as constellations or binocular target, but must not acquire a private
rendering framework. Content and legend switches are opt-in. An omitted
magnitude limit or visual override preserves the family, style, and mode
default.

The shared arguments retain the independent ownership rules:

- magnitude and astronomical-layer visibility are detail/content choices;
- references and poles are astronomical content presented through canonical
  chart furniture;
- line widths and colors are style choices;
- explicit visual overrides apply after mode adaptation and therefore take
  precedence over mode defaults;
- legends remain independently selectable chart furniture.

The horizon remains chart-owned geometry. Disabling constellation labels,
boundaries, references, poles, or legends must not remove or alter it.

The minimum visual matrix contains 20 products: five families by two styles
by two modes.

## 4. Detailed and cartoon products

Atlas is the detailed reference style; cartoon is the simplified explanatory
style. Detail remains a separate policy even when a style supplies recommended
defaults.

For the same chart request:

- geometry is identical across atlas and cartoon;
- geometry is identical across print and presentation;
- atlas may select denser content through an explicit detail policy;
- cartoon may select sparse content through an explicit cartoon policy;
- no content or style state leaks between sequential exports.

Print and presentation modes provide suitable visual defaults. Callers may
override documented colors and widths without mutating a named style. Such
overrides are immutable, render-local, and applied only after the named style
has been adapted to the selected output mode.

Cartoon products use a deliberately restricted palette. Presentation uses a
deep-blue background, yellow astronomical structure and contextual text, and
white version/copyright text. Print uses a white background and black for all
structure, context, and footer text. The planisphere horizon uses the same
mode-resolved structural color while its geometry remains chart-owned.

## 5. Regional emphasis masks

Single-constellation and constellation-group examples may request a canonical
outside mask.

The mask:

- uses the union of selected IAU constellation regions;
- supports Serpens as the union of its two official regions;
- is clipped by the chart boundary;
- is optional;
- takes color, alpha, and z-order from resolved style and mode;
- is configured by the chart request, not drawn by the example.

## 6. Celestial reference annotations

Reference-plane and pole annotations are canonical chart furniture.

### 6.1 Reference planes

The ecliptic and Galactic plane may be independently:

- omitted;
- drawn without text;
- drawn and semantically labeled.

Their labels default to `Ecliptic` and `Galactic plane`. They do not enable
numeric labels on every coordinate-grid curve.

Label placement:

- uses the prepared projected reference curve;
- respects rectangular, circular, horizon, and binocular boundaries;
- selects a readable automatic anchor;
- supports an explicit user override;
- remains outside the example implementation.

### 6.2 Coordinate-system poles

Celestial, ecliptic, and Galactic poles may be selected as:

- none;
- the relevant visible pole;
- both north and south poles, with normal clipping removing points outside the
  chart.

All poles use a canonical cross symbol family, conventional labels
`NCP`/`SCP`, `NEP`/`SEP`, and `NGP`/`SGP`, and semantic colors adapted by style
and mode. Geometry remains in `CelestialPoints`; selection and presentation
belong to chart furniture and style.

## 7. Credits and application footer

Charts may independently request two footer entries:

- lower left: caller-supplied copyright text;
- lower right: application name and installed Wenu version.

The default application text is resolved from `wenu.__version__`; examples do
not copy a version literal. Copyright remains caller-configurable.

Footer placement uses figure coordinates and reserved figure margin, not sky
coordinates. Footers therefore do not move with projection and are not clipped
by the sky boundary. Style and mode control font size, color, alpha, and
spacing.

## 8. Stellar magnitude legend counts

The stellar magnitude legend may optionally append a cumulative visible-star
count to each magnitude entry:

```text
0 (4)
1 (17)
2 (63)
3 (184)
```

For magnitude `m`, the count is the number of actually rendered chart stars
whose magnitude is less than or equal to `m`.

Counts are resolved from final rendered-star geometry after:

- detail selection;
- constellation-vertex and explicit-star selection;
- projection-domain filtering;
- viewport, circular-footprint, or horizon clipping.

Counts never describe the unfiltered catalogue. The option defaults to off in
order to preserve the v0.5 visual baseline.

## 9. Chart furniture contract

Version 0.6 may introduce a lightweight `ChartFurnitureOptions` or equivalent
resolved value containing:

- existing `LegendOptions`;
- reference-plane annotations;
- pole annotations;
- footer credits.

The exact public spelling may follow repository conventions. Compatibility
with the existing `legends=` composition argument must remain.

Furniture policy is backend-independent. Matplotlib-specific artist creation
remains in rendering or final chart export coordination.

## 10. Binocular chart target

`BinocularChart` owns its circular aperture, final clipping, and framing. A
user example supplies a selected object and field size; it does not add
Matplotlib circles, modify artist clip paths, or save the figure directly.

The initial documented target is Centaurus A. The interface must permit other
selected catalogue or coordinate targets without adding one script per object.

## 11. User guide and README

The target user documentation is:

```text
docs/user_guide/
├── index.md
├── planisphere.md
├── regional_charts.md
├── circumpolar_charts.md
├── binocular_charts.md
└── styles_modes_detail.md
```

The README contains one short executable example and one checked-in chart
image, initially expected to be the La Ligua planisphere.

The image has documented provenance:

- generating script;
- exact arguments;
- application version or commit;
- dimensions and format;
- repository destination;
- visual approval.

Other generated gallery products remain below `output/` and outside version
control.

## 12. Test and diagnostic relocation

Tests must not depend on user-facing examples as permanent fixture modules.
Component-level legend, symbol, catalogue, and renderer diagnostics move into:

- test-local fixtures;
- focused visual-regression helpers under `tests/`;
- stable package APIs where the behavior is genuinely public.

Historical examples may be removed only after their scientific and rendering
coverage is demonstrably retained.

## 13. Completion criteria

Version 0.6 is complete when:

1. `examples/` contains only the five canonical families;
2. all 20 required style/mode products execute through composed export;
3. regional emphasis masks work for one constellation and a group;
4. ecliptic and Galactic-plane labels are semantic and optional;
5. pole crosses are canonical and optional;
6. application/version and copyright footers are optional and correctly
   placed;
7. cumulative visible-star counts are optional and scientifically correct;
8. binocular examples contain no renderer or manual clipping logic;
9. the user guide documents all five families;
10. the README example and image have tested provenance;
11. all relocated regression coverage passes;
12. the full suite passes without warnings and atlas print regressions are
    explicitly approved.
