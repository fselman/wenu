# Explicit chart CLI semantics (Milestone 50A.3F audit)

**Status:** Candidate audit; implementation pending

**Base:** PR 98 head `7c2783486d10c51770d60a6e1e758754718833dc`

## Problem

The installed CLI currently overloads a chart *subject*. For example,
`--constellations Vir` can select regional framing, provide the identities
later used by line and label switches, provide the boundary used by `--mask`,
and admit packaged group deep-sky content. PR 98 then made a lone selected
moving object an implicit center. Consequently
`--constellations Vir --planet venus` has no self-evident center and its
meaning changed while the branch was being reviewed.

This is not an astronomical ambiguity. It is an interface ambiguity caused by
combining framing and content selection.

## External CLI practice reviewed

The design was compared with the POSIX Utility Syntax Guidelines, GNU long
option conventions, and Python's `argparse` contract:

- option arguments are required, separate values and different option order
  must not change meaning;
- long options use words separated by hyphens;
- mutually exclusive forms should be represented and rejected explicitly;
- complex resolution and resource handling should occur after syntactic
  parsing, where useful diagnostics and lifecycle control are possible;
- long-option abbreviation should be disabled when similarly named scientific
  controls could otherwise acquire a different meaning as the CLI grows.

References:

- https://pubs.opengroup.org/onlinepubs/9699919799/basedefs/V1_chap12.html
- https://www.gnu.org/software/libc/manual/html_node/Argument-Syntax.html
- https://docs.python.org/3/library/argparse.html

## Accepted principles

1. Center selection, astronomical content, masking, appearance, furniture,
   and export are independent responsibilities.
2. No content selector changes the center.
3. No center selector requests that its object be drawn.
4. Option order has no semantic effect.
5. A configuration value has the same responsibility as its CLI equivalent;
   precedence chooses a value but never changes its kind.
6. Every enabled layer is traceable to explicit CLI input or the effective
   configuration. The documented stellar/background baseline is configuration,
   not a side effect of center resolution.
7. Ambiguous unqualified names fail with the qualified alternatives; they are
   never resolved by a hidden priority order.
8. Canonical multiword spellings are noun-first within a domain. The accepted
   mask spelling is `--constellation-mask`, not `--mask-constellation`.
9. The reset preserves scientific and rendering APIs where they already have
   single responsibilities, but deliberately provides no obsolete CLI aliases.

## Canonical center grammar

Regional and binocular charts accept one named center:

```text
--center-on IDENTIFIER
```

An unqualified identifier is accepted only when it resolves uniquely across
the available namespaces. Stable qualification is available for clarity and
collisions:

```text
constellation:Vir
group:galactic-center
planet:Venus
moon:Moon
asteroid:79989
star:Sirius
galaxy:M31
cluster:M13
nebula:M57
target:Centaurus A
```

The target-family qualifiers validate the packaged target's declared
component family; `target:` accepts any packaged fixed target. Resolution is
case-insensitive where the underlying accepted catalogue is case-insensitive.
Installed asteroid names remain exact case-folded manifest aliases and require
the explicit resource directory. No network discovery or fuzzy matching is
introduced.

Several drawn bodies are never a centering ambiguity:

```bash
wenu_chart regional \
  --center-on planet:Venus \
  --planet venus,mars,jupiter
```

Venus owns the center. All three planets are independently selected for
drawing and ordinary field clipping decides which marks are visible.

### Coordinate centers

Coordinates are not packed into the `--center-on` string. They use one of two
mutually exclusive, complete pairs:

```text
--center-icrs-ra ANGLE --center-icrs-dec ANGLE
--center-altitude ANGLE --center-azimuth ANGLE
```

Accepted angle values carry unambiguous units. Right ascension accepts an
hour-angle form such as `02h20m35s` or an explicit degree form such as
`35.145833deg`. Declination, altitude, and azimuth accept explicit degree
forms. A negative option argument may use the robust shell spelling
`--center-icrs-dec=-15deg`.

ICRS is named deliberately: it has no equinox. A future FK5 center must expose
its frame, equinox, coordinate epoch, and motion semantics independently; it
must not reinterpret these ICRS arguments. Horizontal centers are apparent
observer-local directions at the chart observation instant.

Named center and either coordinate pair are mutually exclusive. Supplying
half a coordinate pair is an error.

## Canonical constellation content and mask grammar

Each constellation option owns its own explicit IAU selection:

```text
--constellation-lines IAU[,IAU...]
--constellation-boundaries IAU[,IAU...]
--constellation-labels IAU[,IAU...]
--constellation-mask IAU[,IAU...]
```

Each may be repeated; repeated selections are combined without changing
their input order. `Ser` continues to resolve internally to its two accepted
line and label identities. The mask controls final regional inclusion and is
not inferred from the center or from boundary visibility.

Examples:

```bash
# Center Virgo; draw Venus only if its apparent position is in the field.
wenu_chart regional \
  --center-on constellation:Vir \
  --planet venus

# Center Venus; independently draw and mask Virgo.
wenu_chart regional \
  --center-on planet:Venus \
  --planet venus \
  --constellation-lines Vir \
  --constellation-labels Vir \
  --constellation-mask Vir
```

The second command requires an explicit field width and height because a
point center does not define an extended viewport.

## Removed installed CLI forms

The following overloaded forms are removed rather than retained as aliases:

| Removed | Replacement |
|---|---|
| `--constellations Vir` | `--center-on constellation:Vir` when framing |
| `--group NAME` | `--center-on group:NAME` |
| `--target NAME` | `--center-on target:NAME` |
| `--ra`, `--dec` | `--center-icrs-ra`, `--center-icrs-dec` |
| `--center-ra`, `--center-dec` | `--center-icrs-ra`, `--center-icrs-dec` |
| `--display-name` | `--center-name` |
| `--mask` | `--constellation-mask IAU[,IAU...]` |
| bare `--constellation-lines` | `--constellation-lines IAU[,IAU...]` |
| bare `--constellation-labels` | `--constellation-labels IAU[,IAU...]` |
| bare `--constellation-boundaries` | same option with an IAU list |

The content selectors `--planet`, `--moon`, `--asteroid`, track selectors,
resolved-appearance selectors, grids, furniture, style, and product controls
retain their existing responsibilities. A separate later audit may decide
whether all drawable point objects should converge on a generic content
selector; that is not required to remove center ambiguity.

## Internal ownership change required

The current `ChartSubjectRequest` cannot represent an independently selected
center and constellation mask. Implementation must therefore separate:

- one resolved center identity and center geometry;
- optional extended-constellation framing when that is the center;
- independent constellation line, boundary, label, and mask selections;
- ordinary astronomical content.

`get_object_center()` remains the typed point-center resolver. Constellation
framing remains extended geometry and must not be forced through the point
resolver. Projection, clipping, realization, rendering, and export remain
unchanged.

Center resolution must not union the centered target into drawable content,
and constellation center resolution must not union lines, labels, boundaries,
or group deep-sky specimens into content. Those layers enter only through
their explicit selectors or effective configuration.

## Configuration and repository migration

The packaged configuration currently contains `[subjects.*]` and family
`mask` booleans. The runtime migration must replace those overloaded values
with center and content/mask sections that express the same independent
responsibilities. Packaged defaults, configuration validation and translation,
`wenu_chart defaults`, current examples, installed example scripts, active
tools, README files, user guides, active developer documentation, and tests
must move together.

Historical documents under `docs/developer/archive/` remain immutable evidence
and retain the CLI spelling accepted at their milestone. They are not runnable
current guidance.

## Acceptance gates

Contract tests must prove:

- option order independence;
- unique unqualified and qualified name resolution;
- diagnostic ambiguity and unknown-name failures;
- one of named, ICRS, or horizontal center, never several;
- center-only objects are not forced into content;
- content-only planets never alter a constellation or coordinate center;
- multiple drawn planets coexist with one explicitly named center;
- constellation center, four independent constellation content/mask
  selections, and disjoint center/mask constellations;
- complete active documentation and tool migration with no removed spelling;
- unchanged canonical projection/render/export path;
- `allow_abbrev=False` for the installed parser;
- macOS focused, complete, and visual acceptance for Virgo/Venus and `(79989)`.
