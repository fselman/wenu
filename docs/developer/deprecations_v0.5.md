# Wenu v0.5 deprecation boundary

Status: active compatibility policy

Milestone 43I establishes the boundary between the retired
cartoon-specific orchestration and the canonical chart composition pipeline.
Deprecated calls remain functional during the first v0.5 release cycle.

| Deprecated public entry point | Canonical replacement |
|---|---|
| `cartoon_output_mode(mode)` | Pass `mode="print"`, `mode="presentation"`, `PrintMode()`, or `PresentationMode()` directly to `compose_chart()` |
| `compose_cartoon_chart(chart, ...)` | Use `compose_chart(chart, style="cartoon", mode=..., detail=...)` |

For explicit constellation-label positions or offsets, construct the style
with `cartoon_chart_style(...)` and pass that style to `compose_chart()`.

The following cartoon components are not deprecated because they participate
in the canonical separation of concerns:

- `CartoonChartStyle` and `cartoon_chart_style()` for appearance;
- `CartoonDetailPolicy` for astronomical content and density;
- `CartoonChartPreset` as an optional style/detail bundle;
- `PrintMode` and `PresentationMode` for output realization.

Deprecated names are loaded lazily from the top-level `wenu` package. A
canonical `compose_chart()` call therefore does not import the deprecated
`wenu.charts.cartoon_composition` module.
