"""Generic Matplotlib renderer for projected Cartesian geometry."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np

from wenu.geometry.projected import (
    ProjectedCurve,
    ProjectedCurves,
    ProjectedGrid,
    ProjectedPoint,
    ProjectedPoints,
    ProjectedPolygon,
    ProjectedPolygons,
)
from wenu.rendering._matplotlib_axes import apply_viewport
from wenu.rendering._matplotlib_primitives import (
    render_curve,
    render_point,
    render_points,
    render_polygon,
    render_text,
)


class MatplotlibRenderer:
    """Render projected geometry without astronomical knowledge."""

    def __init__(self, ax):
        self.ax = ax
        self._clip_patch = None

    def set_clip_boundary(self, boundary, *, style=None):
        """Set and draw a projected closed clipping boundary."""
        from matplotlib.path import Path
        from matplotlib.patches import PathPatch

        if not isinstance(boundary, ProjectedCurve):
            raise TypeError("boundary must be a ProjectedCurve.")
        if not boundary.closed:
            raise ValueError("The clipping boundary must be closed.")
        finite = boundary.finite
        if np.count_nonzero(finite) < 3:
            raise ValueError(
                "The clipping boundary needs three finite vertices."
            )
        vertices = np.column_stack(
            (boundary.x[finite], boundary.y[finite])
        )
        vertices = np.vstack((vertices, vertices[0]))
        codes = np.full(len(vertices), Path.LINETO, dtype=np.uint8)
        codes[0] = Path.MOVETO
        codes[-1] = Path.CLOSEPOLY
        patch = PathPatch(
            Path(vertices, codes),
            **({} if style is None else dict(style)),
        )
        self.ax.add_patch(patch)
        self._clip_patch = patch
        return patch

    def _apply_clip_patch(self, artists):
        if self._clip_patch is None:
            return artists
        for artist in artists:
            if isinstance(artist, (list, tuple)):
                self._apply_clip_patch(artist)
            elif callable(getattr(artist, "set_clip_path", None)):
                artist.set_clip_on(True)
                artist.set_clip_path(self._clip_patch)
        return artists

    def draw_outside_mask(
        self,
        polygons,
        *,
        viewport,
        style=None,
    ):
        """Shade the viewport except for holes defined by polygons."""
        from matplotlib.path import Path
        from matplotlib.patches import PathPatch

        if not isinstance(polygons, ProjectedPolygons):
            raise TypeError("polygons must be ProjectedPolygons.")
        if not polygons.items:
            raise ValueError("At least one mask opening is required.")

        vertices = []
        codes = []

        def add_ring(points, *, clockwise):
            points = np.asarray(points, dtype=float)
            if points.ndim != 2 or points.shape[1] != 2:
                raise ValueError("Mask rings must contain x/y vertices.")
            points = points[np.all(np.isfinite(points), axis=1)]
            if len(points) < 3:
                return
            if np.allclose(points[0], points[-1]):
                points = points[:-1]
            if len(points) < 3:
                return
            area = 0.5 * np.sum(
                points[:, 0] * np.roll(points[:, 1], -1)
                - np.roll(points[:, 0], -1) * points[:, 1]
            )
            is_clockwise = area < 0.0
            if is_clockwise != clockwise:
                points = points[::-1]
            ring = np.vstack((points, points[0]))
            ring_codes = np.full(
                len(ring),
                Path.LINETO,
                dtype=np.uint8,
            )
            ring_codes[0] = Path.MOVETO
            ring_codes[-1] = Path.CLOSEPOLY
            vertices.extend(ring)
            codes.extend(ring_codes)

        add_ring(
            (
                (viewport.x_min, viewport.y_min),
                (viewport.x_max, viewport.y_min),
                (viewport.x_max, viewport.y_max),
                (viewport.x_min, viewport.y_max),
            ),
            clockwise=False,
        )
        for polygon in polygons:
            add_ring(
                np.column_stack((polygon.x, polygon.y)),
                clockwise=True,
            )
        if len(vertices) <= 5:
            raise ValueError(
                "No finite polygon opening could be constructed."
            )

        mask_style = {
            "facecolor": "black",
            "edgecolor": "none",
            "alpha": 0.35,
            "zorder": 20.0,
        }
        if style is not None:
            mask_style.update(style)
        patch = PathPatch(
            Path(
                np.asarray(vertices, dtype=float),
                np.asarray(codes, dtype=np.uint8),
            ),
            **mask_style,
        )
        self.ax.add_patch(patch)
        self._apply_clip_patch([patch])
        return patch

    def apply_viewport(self, viewport, *, equal_aspect=True):
        """Apply projected chart bounds to this renderer's axes."""
        apply_viewport(
            self.ax,
            viewport,
            equal_aspect=equal_aspect,
        )

    def draw(
        self,
        geometry,
        *,
        style=None,
        styles=None,
        polygon_fill_style=None,
        polygon_outline_style=None,
        compound_by=None,
        component_styles=None,
        point_overlays=None,
        draw_labels=False,
        label_style=None,
        label_offset=(0.0, 0.0),
    ):
        """Draw a supported projected geometry object."""
        common = {} if style is None else dict(style)
        labels = {} if label_style is None else dict(label_style)
        polygon_fill = (
            None
            if polygon_fill_style is None
            else dict(polygon_fill_style)
        )
        polygon_outline = (
            None
            if polygon_outline_style is None
            else dict(polygon_outline_style)
        )

        if isinstance(geometry, ProjectedPoint):
            artists = self._draw_point(
                geometry,
                common,
                draw_labels=draw_labels,
                label_style=labels,
                label_offset=label_offset,
            )
        elif isinstance(geometry, ProjectedPoints):
            artists = self._draw_points(
                geometry,
                common,
                styles=styles,
                point_overlays=point_overlays,
                draw_labels=draw_labels,
                label_style=labels,
                label_offset=label_offset,
            )
        elif isinstance(geometry, ProjectedCurve):
            artists = self._draw_curve(
                geometry,
                common,
                draw_labels=draw_labels,
                label_style=labels,
                label_offset=label_offset,
            )
        elif isinstance(geometry, ProjectedCurves):
            artists = self._draw_curves(
                geometry,
                common,
                styles=styles,
                draw_labels=draw_labels,
                label_style=labels,
                label_offset=label_offset,
            )
        elif isinstance(geometry, ProjectedGrid):
            artists = self._draw_grid(
                geometry,
                common,
                styles=styles,
                component_styles=component_styles,
                draw_labels=draw_labels,
                label_style=labels,
                label_offset=label_offset,
            )
        elif isinstance(geometry, ProjectedPolygon):
            artists = self._draw_polygon(
                geometry,
                common,
                fill_style=polygon_fill,
                outline_style=polygon_outline,
                draw_labels=draw_labels,
                label_style=labels,
                label_offset=label_offset,
            )
        elif (
            isinstance(geometry, ProjectedPolygons)
            and compound_by is not None
        ):
            artists = self._draw_compound_polygons(
                geometry,
                common,
                compound_by=compound_by,
                fill_style=polygon_fill,
                outline_style=polygon_outline,
            )
        elif isinstance(geometry, ProjectedPolygons):
            artists = self._draw_polygons(
                geometry,
                common,
                styles=styles,
                fill_style=polygon_fill,
                outline_style=polygon_outline,
                draw_labels=draw_labels,
                label_style=labels,
                label_offset=label_offset,
            )
        else:
            raise TypeError(
                "Unsupported projected geometry type: "
                f"{type(geometry).__name__}."
            )
        return self._apply_clip_patch(artists)


    def _draw_point(
        self,
        point,
        style,
        *,
        draw_labels,
        label_style,
        label_offset,
    ):
        if not point.finite:
            return []
        artists = [render_point(self.ax, point, **style)]
        if draw_labels and point.name is not None:
            artists.append(
                self._label(
                    point.x,
                    point.y,
                    point.name,
                    label_style,
                    label_offset,
                )
            )
        return artists

    def _draw_points(
        self,
        points,
        style,
        *,
        styles,
        point_overlays,
        draw_labels,
        label_style,
        label_offset,
    ):
        finite = points.finite
        artists = []
        if styles is None:
            if np.any(finite):
                artists.append(
                    render_points(
                        self.ax,
                        points.x[finite],
                        points.y[finite],
                        **self._mask_style(style, finite),
                    )
                )
        else:
            entity_styles = self._entity_styles(
                styles,
                len(points),
            )
            for index in np.flatnonzero(finite):
                point = ProjectedPoint(
                    points.x[index],
                    points.y[index],
                    name=self._entity_label(points, index),
                )
                artists.extend(
                    self._draw_point(
                        point,
                        {**style, **entity_styles[index]},
                        draw_labels=False,
                        label_style={},
                        label_offset=(0.0, 0.0),
                    )
                )

        if point_overlays is not None:
            for overlay in point_overlays:
                overlay = dict(overlay)
                if "mask" not in overlay:
                    raise ValueError(
                        "Each point overlay must provide a mask."
                    )
                mask = np.asarray(overlay.pop("mask"), dtype=bool)
                if mask.shape != (len(points),):
                    raise ValueError(
                        "Point overlay masks must match the point collection."
                    )
                overlay_style = dict(overlay.pop("style", {}))
                if overlay:
                    raise ValueError(
                        "Unsupported point overlay options: "
                        + ", ".join(sorted(overlay))
                    )
                selected = finite & mask
                if np.any(selected):
                    artists.append(
                        render_points(
                            self.ax,
                            points.x[selected],
                            points.y[selected],
                            **overlay_style,
                        )
                    )

        if draw_labels:
            entity_styles = self._entity_styles(styles, len(points))
            for index in np.flatnonzero(finite):
                label = self._entity_label(points, index)
                if label is not None:
                    inherited = {
                        name: entity_styles[index][name]
                        for name in ("color", "alpha", "zorder")
                        if name in entity_styles[index]
                    }
                    artists.append(
                        self._label(
                            points.x[index],
                            points.y[index],
                            label,
                            {**inherited, **label_style},
                            label_offset,
                        )
                    )
        return artists

    def _draw_curve(
        self,
        curve,
        style,
        *,
        draw_labels,
        label_style,
        label_offset,
    ):
        if not np.any(curve.finite):
            return []
        artists = [render_curve(self.ax, curve, **style)]
        if draw_labels and curve.name is not None:
            anchor = self._anchor(curve.x, curve.y)
            if anchor is not None:
                artists.append(
                    self._label(
                        *anchor,
                        curve.name,
                        label_style,
                        label_offset,
                    )
                )
        return artists

    def _draw_curves(
        self,
        curves,
        style,
        *,
        styles,
        draw_labels,
        label_style,
        label_offset,
    ):
        entity_styles = self._entity_styles(
            styles,
            len(curves),
        )
        artists = []
        for index, curve in enumerate(curves):
            name = curve.name
            if name is None:
                name = self._metadata_label(curves.metadata, index)
                if name is not None:
                    curve = ProjectedCurve(
                        curve.x,
                        curve.y,
                        closed=curve.closed,
                        name=name,
                    )
            artists.extend(
                self._draw_curve(
                    curve,
                    {**style, **entity_styles[index]},
                    draw_labels=draw_labels,
                    label_style=label_style,
                    label_offset=label_offset,
                )
            )
        return artists

    def _draw_grid(
        self,
        grid,
        style,
        *,
        styles,
        component_styles,
        draw_labels,
        label_style,
        label_offset,
    ):
        component_styles = (
            {} if component_styles is None else component_styles
        )
        per_component_styles = (
            {} if styles is None else styles
        )
        artists = []
        for name, curves in grid.components.items():
            artists.extend(
                self._draw_curves(
                    curves,
                    {
                        **style,
                        **dict(component_styles.get(name, {})),
                    },
                    styles=per_component_styles.get(name),
                    draw_labels=draw_labels,
                    label_style=label_style,
                    label_offset=label_offset,
                )
            )
        return artists

    def _draw_polygon(
        self,
        polygon,
        style,
        *,
        fill_style,
        outline_style,
        draw_labels,
        label_style,
        label_offset,
    ):
        if not np.any(polygon.finite):
            return []
        if fill_style is None and outline_style is None:
            artists = [
                render_polygon(
                    self.ax,
                    polygon,
                    **self._polygon_style(style),
                )
            ]
        else:
            artists = []
            if fill_style is not None:
                fill = {**style, **fill_style}
                fill.setdefault("edgecolor", "none")
                artists.append(
                    render_polygon(
                        self.ax,
                        polygon,
                        **self._polygon_style(fill),
                    )
                )
            if outline_style is not None:
                outline = {**style, **outline_style}
                outline.setdefault("facecolor", "none")
                artists.append(
                    render_polygon(
                        self.ax,
                        polygon,
                        **self._polygon_style(outline),
                    )
                )
        if draw_labels and polygon.name is not None:
            anchor = self._anchor(polygon.x, polygon.y)
            if anchor is not None:
                artists.append(
                    self._label(
                        *anchor,
                        polygon.name,
                        label_style,
                        label_offset,
                    )
                )
        return artists

    def _draw_polygons(
        self,
        polygons,
        style,
        *,
        styles,
        fill_style,
        outline_style,
        draw_labels,
        label_style,
        label_offset,
    ):
        entity_styles = self._entity_styles(
            styles,
            len(polygons),
        )
        artists = []
        for index, polygon in enumerate(polygons):
            name = polygon.name
            if name is None:
                name = self._metadata_label(
                    polygons.metadata,
                    index,
                )
                if name is not None:
                    polygon = ProjectedPolygon(
                        polygon.x,
                        polygon.y,
                        name=name,
                    )
            artists.extend(
                self._draw_polygon(
                    polygon,
                    {**style, **entity_styles[index]},
                    fill_style=fill_style,
                    outline_style=outline_style,
                    draw_labels=draw_labels,
                    label_style=label_style,
                    label_offset=label_offset,
                )
            )
        return artists

    def _draw_compound_polygons(
        self,
        polygons,
        style,
        *,
        compound_by,
        fill_style,
        outline_style,
    ):
        """Draw grouped rings as compound paths with interior holes."""
        from matplotlib.path import Path
        from matplotlib.patches import PathPatch

        groups = polygons.metadata.get(compound_by)
        if groups is None:
            raise ValueError(
                f"Missing compound polygon metadata: {compound_by!r}."
            )
        groups = np.asarray(groups, dtype=object)
        if groups.ndim != 1 or groups.size != len(polygons):
            raise ValueError(
                "Compound polygon metadata must contain one group "
                "identifier per ring."
            )
        is_hole = polygons.metadata.get(
            "is_hole",
            np.zeros(len(polygons), dtype=bool),
        )
        is_hole = np.asarray(is_hole, dtype=bool)
        if is_hole.shape != groups.shape:
            raise ValueError(
                "is_hole must contain one value per polygon ring."
            )

        ordered_groups = tuple(dict.fromkeys(groups.tolist()))
        artists = []
        for group in ordered_groups:
            vertices = []
            codes = []
            for index in np.flatnonzero(groups == group):
                polygon = polygons[index]
                finite = polygon.finite
                points = np.column_stack(
                    (polygon.x[finite], polygon.y[finite])
                )
                if len(points) > 1 and np.allclose(
                    points[0], points[-1]
                ):
                    points = points[:-1]
                if len(points) < 3:
                    continue
                area = 0.5 * np.sum(
                    points[:, 0] * np.roll(points[:, 1], -1)
                    - np.roll(points[:, 0], -1) * points[:, 1]
                )
                want_clockwise = bool(is_hole[index])
                if (area < 0.0) != want_clockwise:
                    points = points[::-1]
                ring = np.vstack((points, points[0]))
                ring_codes = np.full(
                    len(ring), Path.LINETO, dtype=np.uint8
                )
                ring_codes[0] = Path.MOVETO
                ring_codes[-1] = Path.CLOSEPOLY
                vertices.extend(ring)
                codes.extend(ring_codes)
            if not vertices:
                continue
            path = Path(
                np.asarray(vertices, dtype=float),
                np.asarray(codes, dtype=np.uint8),
            )
            if fill_style is None and outline_style is None:
                patch = PathPatch(path, **self._polygon_style(style))
                self.ax.add_patch(patch)
                artists.append(patch)
                continue
            if fill_style is not None:
                fill = {**style, **fill_style}
                fill.setdefault("edgecolor", "none")
                patch = PathPatch(path, **self._polygon_style(fill))
                self.ax.add_patch(patch)
                artists.append(patch)
            if outline_style is not None:
                outline = {**style, **outline_style}
                outline.setdefault("facecolor", "none")
                patch = PathPatch(path, **self._polygon_style(outline))
                self.ax.add_patch(patch)
                artists.append(patch)
        return artists

    @staticmethod
    def _polygon_style(style):
        """Translate independent edge/face alpha into RGBA colors."""
        from matplotlib.colors import to_rgba

        result = dict(style)
        edge_alpha = result.pop("edge_alpha", None)
        face_alpha = result.pop("face_alpha", None)
        if (
            "alpha" in result
            and (edge_alpha is not None or face_alpha is not None)
        ):
            raise ValueError(
                "Polygon alpha cannot be combined with edge_alpha or "
                "face_alpha."
            )

        color = result.pop("color", None)
        if color is not None:
            result.setdefault("edgecolor", color)
            result.setdefault("facecolor", color)

        def alpha_value(value, name):
            value = float(value)
            if not np.isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1.")
            return value

        if edge_alpha is not None:
            edge_alpha = alpha_value(edge_alpha, "edge_alpha")
            edgecolor = result.get("edgecolor", "black")
            result["edgecolor"] = to_rgba(
                edgecolor,
                alpha=edge_alpha,
            )
        if face_alpha is not None:
            face_alpha = alpha_value(face_alpha, "face_alpha")
            facecolor = result.get("facecolor", "none")
            result["facecolor"] = to_rgba(
                facecolor,
                alpha=face_alpha,
            )
        return result

    def _label(self, x, y, label, style, offset):
        dx, dy = offset(x, y) if callable(offset) else offset
        return render_text(
            self.ax,
            x + dx,
            y + dy,
            str(label),
            **style,
        )

    @staticmethod
    def _entity_styles(styles, length):
        if styles is None:
            return tuple({} for _ in range(length))
        if not isinstance(styles, Sequence) or isinstance(
            styles,
            (str, bytes),
        ):
            raise TypeError("styles must be a sequence of mappings.")
        if len(styles) != length:
            raise ValueError("styles must contain one mapping per entity.")
        if not all(isinstance(item, Mapping) for item in styles):
            raise TypeError("every entity style must be a mapping.")
        return tuple(dict(item) for item in styles)

    @staticmethod
    def _mask_style(style, mask):
        masked = {}
        for name, value in style.items():
            array = np.asarray(value)
            if array.ndim == 1 and array.size == mask.size:
                masked[name] = array[mask]
            else:
                masked[name] = value
        return masked

    @staticmethod
    def _entity_label(points, index):
        for values in (points.labels, points.names, points.ids):
            if values is not None and values[index] is not None:
                return values[index]
        return None

    @staticmethod
    def _metadata_label(metadata, index):
        for name in ("labels", "names", "ids"):
            values = metadata.get(name)
            if values is not None and values[index] is not None:
                return values[index]
        return None

    @staticmethod
    def _anchor(x, y):
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
        finite = np.isfinite(x) & np.isfinite(y)
        if not np.any(finite):
            return None
        return float(np.mean(x[finite])), float(np.mean(y[finite]))

