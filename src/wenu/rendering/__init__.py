"""Geometry preparation and graphical rendering backends."""

from . import layers
from ._matplotlib_axes import apply_viewport
from ._matplotlib_primitives import (
    render_curve,
    render_point,
    render_points,
    render_polygon,
    render_text,
)
from .matplotlib import MatplotlibRenderer
from .symbols import DEFAULT_SYMBOLS, SymbolLibrary
from .preparation import (
    clip_to_latitude,
    magnitude_sizes,
    point_styles,
    radial_label_offset,
)

__all__ = [
    "MatplotlibRenderer",
    "SymbolLibrary",
    "DEFAULT_SYMBOLS",
    "apply_viewport",
    "render_curve",
    "render_point",
    "render_points",
    "render_polygon",
    "render_text",
    "clip_to_latitude",
    "magnitude_sizes",
    "point_styles",
    "radial_label_offset",
    "layers",
]
