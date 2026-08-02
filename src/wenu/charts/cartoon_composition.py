"""Deprecated compatibility wrappers for cartoon chart composition."""

from __future__ import annotations

import warnings

from .cartoon_modes import cartoon_chart_style
from .composition import ChartComposition, compose_chart
from .detail import CartoonDetailPolicy, DetailOverrides
from .modes import ChartMode, PresentationMode, PrintMode


def _resolve_cartoon_output_mode(mode="print") -> ChartMode:
    if isinstance(mode, ChartMode):
        return mode
    normalized = str(mode).strip().lower()
    if normalized == "print":
        return PrintMode()
    if normalized == "presentation":
        return PresentationMode()
    raise ValueError("Cartoon output mode must be print or presentation.")


def cartoon_output_mode(mode="print") -> ChartMode:
    """Return a mode for compatibility with the legacy cartoon workflow."""
    warnings.warn(
        "cartoon_output_mode() is deprecated; pass 'print', "
        "'presentation', PrintMode(), or PresentationMode() directly "
        "to compose_chart().",
        DeprecationWarning,
        stacklevel=2,
    )
    return _resolve_cartoon_output_mode(mode)


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
    """Resolve a cartoon chart through the deprecated compatibility API.

    Use ``compose_chart(chart, style="cartoon", mode=...)`` instead. For
    explicit label controls, pass a style returned by
    :func:`cartoon_chart_style` to ``compose_chart()``.
    """
    warnings.warn(
        "compose_cartoon_chart() is deprecated; use compose_chart(chart, "
        "style='cartoon', mode=..., detail=...) instead. Use "
        "cartoon_chart_style() with compose_chart() for explicit "
        "constellation-label controls.",
        DeprecationWarning,
        stacklevel=2,
    )
    output_mode = _resolve_cartoon_output_mode(mode)
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
