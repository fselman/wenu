"""Compose chart legends from an existing chart-rendering result."""

from __future__ import annotations

from .legend_composition import draw_planned_chart_legends
from .legend_geometry import rendered_star_geometry
from .legend_inputs import resolve_stellar_legend_inputs


def draw_rendered_chart_legends(
    ax,
    chart,
    sky,
    chart_style,
    plan,
    rendering_result,
    *,
    resolved_detail=None,
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
        footprint_contains=footprint_contains,
        stellar_legend_style=stellar_legend_style,
        grid=grid,
        object_title=object_title,
        context_lines=context_lines,
        include_objects=include_objects,
        include_context=include_context,
        resolved_detail=resolved_detail,
    )
