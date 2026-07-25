"""Generic Matplotlib renderer for projected Cartesian geometry."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np

from wenu.projected import (
    ProjectedCurve,
    ProjectedCurves,
    ProjectedGrid,
    ProjectedPoint,
    ProjectedPoints,
    ProjectedPolygon,
    ProjectedPolygons,
)
from wenu.renderers.matplotlib import (
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

    def draw(
        self,
        geometry,
        *,
        style=None,
        styles=None,
        component_styles=None,
        draw_labels=False,
        label_style=None,
        label_offset=(0.0, 0.0),
    ):
        """Draw a supported projected geometry object.

        Parameters are renderer-facing only. ``style`` applies to the whole
        object, ``styles`` optionally supplies one style per entity, and
        ``component_styles`` supplies overrides for named grid components.
        """
        common = {} if style is None else dict(style)
        labels = {} if label_style is None else dict(label_style)

        if isinstance(geometry, ProjectedPoint):
            return self._draw_point(
                geometry,
                common,
                draw_labels=draw_labels,
                label_style=labels,
                label_offset=label_offset,
            )
        if isinstance(geometry, ProjectedPoints):
            return self._draw_points(
                geometry,
                common,
                styles=styles,
                draw_labels=draw_labels,
                label_style=labels,
                label_offset=label_offset,
            )
        if isinstance(geometry, ProjectedCurve):
            return self._draw_curve(
                geometry,
                common,
                draw_labels=draw_labels,
                label_style=labels,
                label_offset=label_offset,
            )
        if isinstance(geometry, ProjectedCurves):
            return self._draw_curves(
                geometry,
                common,
                styles=styles,
                draw_labels=draw_labels,
                label_style=labels,
                label_offset=label_offset,
            )
        if isinstance(geometry, ProjectedGrid):
            return self._draw_grid(
                geometry,
                common,
                styles=styles,
                component_styles=component_styles,
                draw_labels=draw_labels,
                label_style=labels,
                label_offset=label_offset,
            )
        if isinstance(geometry, ProjectedPolygon):
            return self._draw_polygon(
                geometry,
                common,
                draw_labels=draw_labels,
                label_style=labels,
                label_offset=label_offset,
            )
        if isinstance(geometry, ProjectedPolygons):
            return self._draw_polygons(
                geometry,
                common,
                styles=styles,
                draw_labels=draw_labels,
                label_style=labels,
                label_offset=label_offset,
            )
        raise TypeError(
            "Unsupported projected geometry type: "
            f"{type(geometry).__name__}."
        )

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

        if draw_labels:
            for index in np.flatnonzero(finite):
                label = self._entity_label(points, index)
                if label is not None:
                    artists.append(
                        self._label(
                            points.x[index],
                            points.y[index],
                            label,
                            label_style,
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
        draw_labels,
        label_style,
        label_offset,
    ):
        if not np.any(polygon.finite):
            return []
        artists = [render_polygon(self.ax, polygon, **style)]
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
                    draw_labels=draw_labels,
                    label_style=label_style,
                    label_offset=label_offset,
                )
            )
        return artists

    def _label(self, x, y, label, style, offset):
        dx, dy = offset
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

