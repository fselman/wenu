"""Rendering backends and renderer-side helpers."""

from wenu.renderers.matplotlib import (
    render_curve,
    render_point,
    render_points,
    render_polygon,
    render_text,
)
from wenu.renderers.matplotlib_axes import apply_viewport
from wenu.renderers.matplotlib_renderer import MatplotlibRenderer

__all__ = [
    "MatplotlibRenderer",
    "apply_viewport",
    "render_curve",
    "render_point",
    "render_points",
    "render_polygon",
    "render_text",
]
