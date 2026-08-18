"""Compose chart legends from an existing chart-rendering result."""

from __future__ import annotations

import numpy as np

from .legend_composition import draw_planned_chart_legends
from .legend_geometry import rendered_star_geometry
from .legend_inputs import resolve_stellar_legend_inputs
from .context import BoundaryKind


def _resolved_footprint(chart, explicit):
    """Return a vectorized final-footprint predicate when required."""
    if explicit is not None:
        return explicit
    context = getattr(chart, "chart_context", None)
    if context is None:
        return None
    boundary = context.clip_boundary
    if context.boundary_kind != BoundaryKind.CIRCULAR or boundary is None:
        return None
    finite = boundary.finite
    x = np.asarray(boundary.x[finite], dtype=float)
    y = np.asarray(boundary.y[finite], dtype=float)
    center_x = float((np.nanmin(x) + np.nanmax(x)) / 2.0)
    center_y = float((np.nanmin(y) + np.nanmax(y)) / 2.0)
    radius = float(np.nanmedian(np.hypot(x - center_x, y - center_y)))
    return lambda px, py: np.hypot(px - center_x, py - center_y) <= radius


def draw_rendered_chart_legends(
    ax,
    chart,
    sky,
    chart_style,
    plan,
    rendering_result,
    *,
    resolved_detail=None,
    stellar_counts: bool = False,
    effective_limit=None,
    star_area_scale=None,
    star_color=None,
    star_alpha=None,
    footprint_contains=None,
    stellar_legend_style=None,
    star_layer=None,
    grid=None,
    object_title=None,
    context_lines=None,
    include_objects=True,
    include_context=None,
    symbol_labels=None,
    stellar_title="Stars",
    stellar_reference_magnitude=None,
    stellar_label_suffix="",
):
    """Draw both legends from already-rendered geometry.

    Normally ``resolved_detail`` and ``chart_style`` provide every stellar
    input.  The explicit keyword arguments remain available for diagnostics
    and intentional one-off overrides.
    """
    if plan.stars.enabled:
        stars = rendered_star_geometry(
            rendering_result,
            sky=sky,
            star_layer=star_layer,
        )
        spherical = stars.spherical
        projected = stars.projected
        viewport = stars.viewport
        inputs = resolve_stellar_legend_inputs(
            resolved_detail,
            chart_style,
            effective_limit=effective_limit,
            area_scale=star_area_scale,
            color=star_color,
            alpha=star_alpha,
        )
    else:
        spherical = None
        projected = None
        viewport = rendering_result.viewport
        # Values are unused by the lower-level coordinator when disabled.
        inputs = None

    legend_options = dict(
        stellar_counts=stellar_counts,
    )
    if inputs is not None and inputs.magnitude_sizing is not None:
        legend_options["stellar_magnitude_sizing"] = (
            inputs.magnitude_sizing
        )
    return draw_planned_chart_legends(
        ax,
        chart,
        sky,
        chart_style,
        plan,
        star_spherical=spherical,
        star_projected=projected,
        viewport=viewport,
        effective_limit=(
            inputs.effective_limit if inputs is not None else 0.0
        ),
        star_area_scale=(
            inputs.area_scale if inputs is not None else 1.0
        ),
        star_color=inputs.color if inputs is not None else "black",
        star_alpha=inputs.alpha if inputs is not None else 1.0,
        footprint_contains=_resolved_footprint(chart, footprint_contains),
        stellar_legend_style=stellar_legend_style,
        grid=grid,
        object_title=object_title,
        context_lines=context_lines,
        include_objects=include_objects,
        include_context=include_context,
        symbol_labels=symbol_labels,
        stellar_title=stellar_title,
        stellar_reference_magnitude=stellar_reference_magnitude,
        stellar_label_suffix=stellar_label_suffix,
        resolved_detail=resolved_detail,
        **legend_options,
    )
