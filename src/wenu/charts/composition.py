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


@dataclass(frozen=True)
class ChartComposition:
    """Resolved, output-neutral inputs for a chart rendering operation."""

    context: ChartContext
    style: Any
    mode: ResolvedMode
    detail: ResolvedDetail

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
    mode: ChartMode | None = None,
    detail: DetailPolicy | None = None,
    detail_overrides: DetailOverrides | None = None,
) -> ChartComposition:
    """Resolve independent chart concerns without rendering the chart."""
    context = chart.chart_context
    resolved_mode = (
        PrintMode() if mode is None else mode
    ).resolve(context)
    policy = FixedDetailPolicy() if detail is None else detail
    resolved_detail = apply_detail_overrides(
        policy.resolve(context, resolved_mode),
        detail_overrides,
    )
    return ChartComposition(
        context=context,
        style=style,
        mode=resolved_mode,
        detail=resolved_detail,
    )
