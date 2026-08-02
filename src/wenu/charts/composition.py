"""Composition of chart geometry, style, mode, and content detail."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .context import ChartContext
from .detail import (
    DetailOverrides,
    DetailPolicy,
    FixedDetailPolicy,
    ResolvedDetail,
    apply_detail_overrides,
)
from .modes import ChartMode, PrintMode, ResolvedMode
from .legend_plan import (
    ChartLegendPlan,
    LegendOptions,
    ResolvedLegendOptions,
    chart_type_name,
)


ATLAS_STYLE = "atlas"
CARTOON_STYLE = "cartoon"
PRINT_MODE = "print"
PRESENTATION_MODE = "presentation"


def _resolve_style(style):
    """Return the stable style identifier and concrete style value."""
    if isinstance(style, str):
        name = style.strip().lower()
        if name not in {ATLAS_STYLE, CARTOON_STYLE}:
            raise ValueError(
                f"Unknown chart style {style!r}. Use 'atlas', 'cartoon', "
                "or pass a chart-style object."
            )
        from .presets import AtlasChartStyle, CartoonChartStyle

        if name == ATLAS_STYLE:
            return ATLAS_STYLE, AtlasChartStyle()
        return CARTOON_STYLE, CartoonChartStyle()

    from .presets import AtlasChartStyle, CartoonChartStyle

    if isinstance(style, AtlasChartStyle):
        name = ATLAS_STYLE
    elif isinstance(style, CartoonChartStyle):
        name = CARTOON_STYLE
    else:
        name = "custom"
    return name, style


def _resolve_mode(mode):
    """Return the stable mode identifier and concrete mode policy."""
    if mode is None:
        return PRINT_MODE, PrintMode()
    if isinstance(mode, str):
        name = mode.strip().lower()
        if name in {PRINT_MODE, "paper"}:
            return PRINT_MODE, PrintMode()
        if name == PRESENTATION_MODE:
            from .modes import PresentationMode

            return PRESENTATION_MODE, PresentationMode()
        raise ValueError(
            f"Unknown chart mode {mode!r}. Use 'print', 'paper', or "
            "'presentation'."
        )

    from .modes import PresentationMode

    if isinstance(mode, PresentationMode):
        name = PRESENTATION_MODE
    elif isinstance(mode, PrintMode):
        name = PRINT_MODE
    else:
        name = "custom"
    return name, mode


@dataclass(frozen=True)
class ChartComposition:
    """Resolved, output-neutral inputs for a chart rendering operation."""

    context: ChartContext
    style: Any
    mode: ResolvedMode
    detail: ResolvedDetail
    style_name: str = "custom"
    mode_name: str = "custom"
    legends: ResolvedLegendOptions | None = None

    def layer_options(
        self,
        sky,
        *,
        overrides=None,
        reload_catalogues=True,
    ):
        """Apply detail and return options ready for ``draw_chart``."""
        from .detail_application import composition_layer_options

        return composition_layer_options(
            self,
            sky,
            layer_options=overrides,
            reload_catalogues=reload_catalogues,
        )


def compose_chart(
    chart,
    *,
    style,
    mode: ChartMode | str | None = None,
    detail: DetailPolicy | None = None,
    detail_overrides: DetailOverrides | None = None,
    legends: LegendOptions | ChartLegendPlan | None = None,
) -> ChartComposition:
    """Resolve independent chart concerns without rendering the chart."""
    context = chart.chart_context
    style_name, resolved_style = _resolve_style(style)
    mode_name, mode_policy = _resolve_mode(mode)
    if not callable(getattr(mode_policy, "resolve", None)):
        raise TypeError("mode must provide resolve() or be a known mode name.")
    resolved_mode = mode_policy.resolve(context)
    if style_name == ATLAS_STYLE and mode_name in {
        PRINT_MODE,
        PRESENTATION_MODE,
    }:
        from .atlas_modes import atlas_chart_style

        resolved_style = atlas_chart_style(
            resolved_mode,
            base=resolved_style,
            mode_name=mode_name,
        )
    elif style_name == CARTOON_STYLE and mode_name in {
        PRINT_MODE,
        PRESENTATION_MODE,
    }:
        from .cartoon_modes import (
            CartoonModeChartStyle,
            cartoon_chart_style,
        )

        already_resolved = (
            isinstance(resolved_style, CartoonModeChartStyle)
            and resolved_style.output_mode_name == mode_name
        )
        if not already_resolved:
            resolved_style = cartoon_chart_style(
                resolved_mode,
                base=resolved_style,
                mode_name=mode_name,
            )
    if detail is None and style_name == CARTOON_STYLE:
        from .detail import CartoonDetailPolicy

        policy = CartoonDetailPolicy()
    else:
        policy = FixedDetailPolicy() if detail is None else detail
    resolved_detail = apply_detail_overrides(
        policy.resolve(context, resolved_mode),
        detail_overrides,
    )
    if isinstance(legends, ChartLegendPlan):
        legends = LegendOptions(plan=legends)
    resolved_legends = (
        None
        if legends is None
        else legends.resolve(chart_type_name(chart))
    )
    return ChartComposition(
        context=context,
        style=resolved_style,
        mode=resolved_mode,
        detail=resolved_detail,
        style_name=style_name,
        mode_name=mode_name,
        legends=resolved_legends,
    )
