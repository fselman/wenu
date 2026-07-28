"""Convenience composition for educational cartoon charts."""

from __future__ import annotations

from dataclasses import dataclass, field

from .composition import ChartComposition, compose_chart
from .detail import (
    CartoonDetailPolicy,
    DetailOverrides,
)
from .modes import ChartMode
from .presets import CartoonChartStyle


@dataclass(frozen=True)
class CartoonChartPreset:
    """Bundle cartoon appearance and content without owning geometry or mode.

    Advanced callers can continue to pass ``CartoonChartStyle`` and
    ``CartoonDetailPolicy`` separately to :func:`compose_chart`.
    """

    style: CartoonChartStyle = field(
        default_factory=CartoonChartStyle
    )
    detail: CartoonDetailPolicy = field(
        default_factory=CartoonDetailPolicy
    )

    def compose(
        self,
        chart,
        *,
        mode: ChartMode | None = None,
        detail_overrides: DetailOverrides | None = None,
    ) -> ChartComposition:
        """Compose this preset with an independently selected chart and mode."""
        return compose_chart(
            chart,
            style=self.style,
            mode=mode,
            detail=self.detail,
            detail_overrides=detail_overrides,
        )

    def components(
        self,
    ) -> tuple[CartoonChartStyle, CartoonDetailPolicy]:
        """Return the explicit style/detail pair represented by this preset."""
        return self.style, self.detail
