"""Rendering backends and renderer-side helpers."""

from wenu.renderers.matplotlib import (
    render_curve,
    render_point,
    render_points,
    render_polygon,
)
from wenu.renderers.matplotlib_axes import apply_viewport

__all__ = [
    "apply_viewport",
    "render_curve",
    "render_point",
    "render_points",
    "render_polygon",
]
