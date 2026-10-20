"""Legacy aliases for the shared kernel projected clipping services."""

from wenu_kernel.geometry.clipping import (
    _clip_polyline_to_viewport,
    clip_point_to_viewport,
    clip_curve_to_viewport,
    clip_polygon_to_convex_boundary,
    polygon_centroid,
    clip_polygon_to_viewport,
    clip_line_segment_to_viewport,
)

__all__ = ['clip_point_to_viewport', 'clip_curve_to_viewport', 'clip_polygon_to_convex_boundary', 'polygon_centroid', 'clip_polygon_to_viewport', 'clip_line_segment_to_viewport']
