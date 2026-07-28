"""Compose cartoon chart geometry, output mode, style, and content."""

from __future__ import annotations

from .cartoon_modes import cartoon_chart_style
from .composition import ChartComposition, compose_chart
from .detail import CartoonDetailPolicy, DetailOverrides
from .modes import ChartMode, PresentationMode, PrintMode


def cartoon_output_mode(mode="print") -> ChartMode:
    """Return a concrete chart mode from a cartoon-mode selector."""
    if isinstance(mode, ChartMode):
        return mode
    normalized = str(mode).strip().lower()
    if normalized == "print":
        return PrintMode()
    if normalized == "presentation":
        return PresentationMode()
    raise ValueError("Cartoon output mode must be print or presentation.")


def compose_cartoon_chart(
    chart,
    *,
    mode="print",
    detail_policy=None,
    detail_overrides: DetailOverrides | None = None,
    constellation_label_positions=None,
    constellation_label_offsets=None,
    constellation_label_clearance=(0.24, 0.20),
) -> ChartComposition:
    """Resolve a cartoon chart without merging independent concerns.

    The returned ``ChartComposition`` retains separate context, visual style,
    resolved output mode, and resolved sparse-content detail.
    """
    output_mode = cartoon_output_mode(mode)
    policy = (
        CartoonDetailPolicy()
        if detail_policy is None
        else detail_policy
    )
    return compose_chart(
        chart,
        style=cartoon_chart_style(
            output_mode,
            constellation_label_positions=(
                constellation_label_positions
            ),
            constellation_label_offsets=(
                constellation_label_offsets
            ),
            constellation_label_clearance=(
                constellation_label_clearance
            ),
        ),
        mode=output_mode,
        detail=policy,
        detail_overrides=detail_overrides,
    )
