# SVG semantic naming ledger

**Milestone:** 49F.5A  
**Status:** implementation contract under verification

This ledger is the acceptance inventory for Wenu's designer-facing SVG
hierarchy. It records every currently supported semantic branch and every
configuration-dependent furniture entry. A rendered Matplotlib name is never
part of the public contract.

## Naming principles

1. A visible hierarchy label is unique among its siblings.
2. A child label does not repeat information already supplied by an ancestor.
3. A hierarchy level exists only when a designer can usefully style, hide,
   move, or reorder that level as a unit.
4. The full semantic path and SVG ID are globally unique even when concise
   contextual labels such as `Symbol` occur in different branches.
5. Stable source keys determine identity. Localized or customized display
   text never determines an SVG ID.
6. Backend words such as `patch`, `text`, `line2d`, and `artist` are not public
   hierarchy labels.

## Constellation systems

Constellation hierarchy construction is system agnostic. A constellation
source supplies:

| Field | Meaning |
|---|---|
| `semantic_system_key` | Stable, language-independent system identity |
| `semantic_entity_keys` | One stable constellation key per geometry entity |
| `semantic_entity_display_names` | One human-facing name per geometry entity |

The component and system are combined to avoid an unnecessary level:

```text
Constellations
├── Lines-Western
│   ├── Cen
│   ├── Cru
│   └── Mus
├── Boundaries-IAU
└── Labels-Western
```

Representative paths are:

```text
sky/constellations/lines_western/cru
sky/constellations/boundaries_iau/cru
sky/constellations/labels_western/cru
```

Corresponding globally unique but contextual artist IDs remain concise:

```text
western-lines-cru--0001
western-labels-cru
iau-boundaries-cru
```

The system key is required in an artist ID because two displayed systems may
use the same entity key. Redundant backend and hierarchy prefixes are omitted.

The SVG serializer knows only the supplied keys, names, and paths. It contains
no Western, IAU, or other culture-specific constellation catalogue. Lines,
boundaries, and labels are optional capabilities of a source system.

## Current sky branches

| Parent | Concise child |
|---|---|
| `Sky` | `Galaxies` |
| `Sky` | `Milky Way and Magellanic Clouds` |
| `Sky` | `Deep Sky Objects` |
| `Sky` | `Stars` |
| `Sky` | `Constellations` |
| `Sky` | `Grids` |

Each semantic leaf may contain one or more numbered drawing primitives only
when several primitives cannot be distinguished more meaningfully. The
sequence number is an SVG-ID disambiguator, not a hierarchy label.

## Object key

The object-key container and title are stable regardless of which rows are
enabled. Supported row keys are:

| Source key | Visible row | Children |
|---|---|---|
| `open_cluster` | `Open cluster` | `Symbol`, `Label` |
| `globular_cluster` | `Globular cluster` | `Symbol`, `Label` |
| `planetary_nebula` | `Planetary nebula` | `Symbol`, `Label` |
| `supernova_remnant` | `Supernova remnant` | `Symbol`, `Label` |
| `galaxy` | `Galaxy` | `Symbol`, `Label` |
| `milky_way` | `Milky Way` | `Symbol`, `Label` |

Rows omitted by chart detail or absent source layers produce no empty row.
Custom or localized visible labels retain the same source key and SVG IDs.
Coordinates, frame/equinox, observer, location, time, and custom context lines
belong to the stable object-key title rather than acquiring text-derived IDs.

## Stellar magnitude scale

Each displayed integral magnitude is a stable row with `Symbol` and `Label`
children.

| Display example | Stable row key | Effect on identity |
|---|---|---|
| `-1` | `mag-minus-1` | negative sign remains unambiguous |
| `0` | `mag-0` | none |
| `3` | `mag-3` | none |
| `3 (127)` | `mag-3` | count does not change identity |
| `3 mag` | `mag-3` | suffix does not change identity |
| `3 (127) mag` | `mag-3` | count and suffix do not change identity |

Reference magnitude and reference-range options determine which stable rows
exist. An empty visible range produces no scale. Count visibility, suffix,
title, frame visibility, colors, alpha, spacing, and placement affect
presentation only.

## Furniture and chart branches

| Parent | Current semantic children |
|---|---|
| `Furniture` | `Title`, `Object key`, `Magnitude scale` |
| `Chart` | `Masks and Boundary` |
| `Masks and Boundary` | `Outside constellation-group mask`, `Viewport frame`, `Horizon` when present |
| `Page` | `Background` |
| `Sky` | `Background` |

Disabled furniture is absent rather than represented by an empty semantic
object. Page background, sky background, masks, frames, legends, and title use
explicit source identities rather than generic Matplotlib IDs.

## Automatic validation

Tests must reject or detect:

- duplicate SVG IDs;
- duplicate semantic group paths (several drawing primitives may correctly
  share their owning group's path);
- duplicate visible labels under one parent;
- missing or misaligned entity keys and display names;
- identity changes caused by localization, counts, or suffixes;
- collisions between negative and positive magnitudes;
- unexpected generic editable Matplotlib objects;
- unnecessary system-only constellation hierarchy levels.

The real-chart acceptance audit must cover the enabled regional product and at
least one representative of each optional legend row or variant that cannot
coexist in one chart.
