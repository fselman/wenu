"""Generic Matplotlib renderer for projected Cartesian geometry."""

from __future__ import annotations

from collections import Counter
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
from wenu.rendering.label_placement import CurveLabelPlacement
from wenu.rendering.preparation import cull_points_to_viewport
from wenu.rendering.paint_roles import paint_role_for_zorder
from wenu.svg_document import attach_semantic_svg_metadata
from wenu.chart_document import SemanticArtistRenderingResult


class MatplotlibRenderer:
    """Render projected geometry without astronomical knowledge."""

    def __init__(self, ax):
        self.ax = ax
        self._clip_patch = None
        self._viewport = None
        self._point_obstacles = []
        self._auto_labels = []
        self._area_labels = []
        self._curve_labels = []
        self.unresolved_label_collisions = ()
        self.suppressed_region_labels = ()
        self._label_rotations = {}
        self._gapped_lines = []
        self._grid_label_band = None
        self._grid_label_band_artist = None

    def _measure_curve_label(self, curve, *, boundary, label, font_size):
        """Supply display measurements to a backend-neutral anchor policy."""
        from matplotlib.font_manager import FontProperties
        from matplotlib.path import Path

        self.ax.apply_aspect()
        points = np.column_stack((curve.x, curve.y))
        inside = np.ones(len(points), dtype=bool)
        if boundary is not None:
            vertices = np.column_stack((boundary.x[boundary.finite],
                                        boundary.y[boundary.finite]))
            inside &= Path(np.vstack((vertices, vertices[0]))).contains_points(points)
        width, _, _ = self.ax.figure.canvas.get_renderer().get_text_width_height_descent(
            label, FontProperties(size=font_size), ismath=False,
        )
        return (self.ax.transData.transform(points), inside, width,
                self.ax.figure.dpi / 72.0)

    def set_grid_label_band(self, boundary, *, style):
        """Reserve exterior furniture around a chart-owned closed boundary."""
        if self._grid_label_band_artist is not None:
            self._grid_label_band_artist.remove()
            self._grid_label_band_artist = None
        previous = getattr(self, "_grid_label_band_frame", None)
        if previous is not None:
            previous.remove()
            self._grid_label_band_frame = None
        self._grid_label_band = None if style is None else (
            self._closed_boundary_path(boundary), dict(style),
        )

    def _finalize_grid_label_band(self):
        """Fit a circular or rectangular exterior band to physical text bounds."""
        if self._grid_label_band is None:
            return
        from matplotlib.path import Path
        from matplotlib.patches import PathPatch

        self.ax.figure.canvas.draw()
        renderer = self.ax.figure.canvas.get_renderer()
        path, style = self._grid_label_band
        inner = self.ax.transData.transform(path.vertices[:-1])
        low, high = inner.min(axis=0), inner.max(axis=0)
        centre = (low + high) / 2.0
        scale = self.ax.figure.dpi / 72.0
        padding = (style["padding_points"] + style["linewidth"] / 2.0) * scale
        labels = [text for text in self.ax.texts
                  if text.get_visible() and getattr(text, "_wenu_exterior_label", False)]
        for text in labels:
            text.set_color(style["label_color"])
            text.set_zorder(max(text.get_zorder(), 4.0))
        boxes = [text.get_window_extent(renderer) for text in labels]
        minimum = max([8.5, *(text.get_fontsize() for text in labels)]) * scale + 2.0 * padding
        radius = np.linalg.norm(inner - centre, axis=1)
        circular = len(inner) >= 16 and np.ptp(radius) < 1e-3 * np.mean(radius)
        from matplotlib.transforms import ScaledTranslation
        # Ordinary coordinate text remains below the reserved content sizing floor.
        # Keep its inner edge close to the boundary coordinate, with a
        # small physical clearance rather than half the ring width.
        for text in labels:
            attachment = getattr(text, "_wenu_exterior_attachment", None)
            if attachment is None:
                continue
            position, direction = attachment
            origin = self.ax.transData.transform(position)
            direction = self.ax.transData.transform(np.asarray(position) + direction) - origin
            direction /= np.linalg.norm(direction)
            text.set_transform(self.ax.transData)
            box = text.get_window_extent(renderer)
            support = (abs(direction[0]) * box.width + abs(direction[1]) * box.height) / 2.0
            clearance = 1.5 if not circular and direction[1] < -0.9 else 0.35
            offset = support + clearance * scale
            if circular:
                # Fit the upright text box to the curved inner rim.
                target = float(np.max(radius)) + 0.35 * scale
                lower, upper = 0.0, offset
                for _ in range(32):
                    trial = (lower + upper) / 2.0
                    shifted_low = np.array([box.x0, box.y0]) + direction * trial
                    shifted_high = np.array([box.x1, box.y1]) + direction * trial
                    nearest = np.clip(centre, shifted_low, shifted_high)
                    if np.linalg.norm(nearest - centre) < target:
                        lower = trial
                    else:
                        upper = trial
                offset = upper
            shift = direction * offset / self.ax.figure.dpi
            text.set_transform(self.ax.transData + ScaledTranslation(
                *shift, self.ax.figure.dpi_scale_trans,
            ))
        boxes = [text.get_window_extent(renderer) for text in labels]
        if circular:
            outer_radius = float(np.max(radius)) + minimum
            for text, box in zip(labels, boxes):
                clearance = (style["linewidth"] / 2.0 * scale
                             if hasattr(text, "_wenu_exterior_attachment") else padding)
                corners = np.array([[box.x0, box.y0], [box.x0, box.y1],
                                    [box.x1, box.y0], [box.x1, box.y1]])
                outer_radius = max(outer_radius, float(np.max(np.linalg.norm(corners - centre, axis=1))) + clearance)
            angle = np.linspace(0.0, 2.0 * np.pi, 721, endpoint=False)
            outer = centre + outer_radius * np.column_stack((np.cos(angle), np.sin(angle)))
        else:
            outer_low, outer_high = low - minimum, high + minimum
            for text, box in zip(labels, boxes):
                clearance = (style["linewidth"] / 2.0 * scale
                             if hasattr(text, "_wenu_exterior_attachment") else padding)
                outer_low = np.minimum(outer_low, (box.x0 - clearance, box.y0 - clearance))
                outer_high = np.maximum(outer_high, (box.x1 + clearance, box.y1 + clearance))
            outer = np.array([outer_low, [outer_high[0], outer_low[1]],
                              outer_high, [outer_low[0], outer_high[1]]])
        # Opposite winding leaves the sky interior as a genuine transparent hole.
        def closed(vertices):
            vertices = np.vstack((vertices, vertices[0]))
            codes = np.full(len(vertices), Path.LINETO, dtype=np.uint8)
            codes[0], codes[-1] = Path.MOVETO, Path.CLOSEPOLY
            return Path(self.ax.transData.inverted().transform(vertices), codes)
        signed_area = np.sum(inner[:, 0] * np.roll(inner[:, 1], -1)
                             - inner[:, 1] * np.roll(inner[:, 0], -1))
        hole = inner[::-1] if signed_area > 0 else inner
        band_path = Path.make_compound_path(closed(outer), closed(hole))
        if self._grid_label_band_artist is not None:
            self._grid_label_band_artist.remove()
        patch = PathPatch(band_path, facecolor=style["fill_color"], edgecolor="none",
                          clip_on=False, zorder=3.75)
        self.ax.add_patch(patch)
        # The exterior stroke is separate: never redraw the inner sky boundary.
        frame = PathPatch(closed(outer), facecolor="none", edgecolor=style["frame_color"],
                          linewidth=style["linewidth"], clip_on=False, zorder=3.85)
        previous = getattr(self, "_grid_label_band_frame", None)
        if previous is not None:
            previous.remove()
        self.ax.add_patch(frame)
        self._grid_label_band_artist = patch
        self._grid_label_band_frame = frame
        title = self.ax.title
        if title.get_visible() and title.get_text():
            from matplotlib.transforms import ScaledTranslation
            original = getattr(title, "_wenu_band_original_transform", title.get_transform())
            title._wenu_band_original_transform = original
            title.set_transform(original)
            box = title.get_window_extent(renderer)
            offset = max(0.0, float(np.max(outer[:, 1])) + padding - box.y0)
            title.set_transform(original + ScaledTranslation(
                0.0, offset / self.ax.figure.dpi, self.ax.figure.dpi_scale_trans,
            ))

    def set_axes_frame_visible(self, visible):
        """Show or hide the rectangular Matplotlib axes frame."""
        for spine in self.ax.spines.values():
            spine.set_visible(bool(visible))

    def set_boundary_background(self, boundary, *, color):
        """Paint a closed-boundary interior over a transparent canvas."""
        from matplotlib.path import Path
        from matplotlib.patches import PathPatch

        path = self._closed_boundary_path(boundary)
        self.ax.set_facecolor("none")
        self.ax.patch.set_visible(False)
        self.ax.figure.set_facecolor("none")
        patch = PathPatch(
            path,
            facecolor=color,
            edgecolor="none",
            zorder=-1000.0,
        )
        self.ax.add_patch(patch)
        self._boundary_background_patch = patch
        return patch

    def set_circular_background(self, boundary, *, color):
        """Paint a circular interior over a transparent canvas."""
        return self.set_boundary_background(boundary, color=color)

    def set_clip_boundary(self, boundary, *, style=None):
        """Set and draw a projected closed clipping boundary."""
        from matplotlib.patches import PathPatch

        path = self._closed_boundary_path(boundary)
        for spine in self.ax.spines.values():
            spine.set_visible(False)
        patch = PathPatch(
            path,
            **({} if style is None else dict(style)),
        )
        self.ax.add_patch(patch)
        self._clip_patch = patch
        return patch

    @staticmethod
    def _closed_boundary_path(boundary):
        """Return a Matplotlib path for a closed projected boundary."""
        from matplotlib.path import Path

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
        return Path(vertices, codes)

    @staticmethod
    def assign_semantic_identity(artists, identity):
        """Attach Wenu-owned SVG anchors without changing artist order."""
        flattened = []

        def collect(items):
            for artist in items:
                if isinstance(artist, (list, tuple)):
                    collect(artist)
                elif callable(getattr(artist, "set_gid", None)):
                    flattened.append(artist)

        collect(artists)
        existing_counts = Counter()
        figures = {
            getattr(artist, "get_figure", lambda: None)()
            for artist in flattened
        }
        for figure in figures - {None}:
            for existing_artist in figure.findobj():
                base_id = getattr(
                    existing_artist,
                    "_wenu_semantic_svg_base_id",
                    None,
                )
                if base_id is not None:
                    existing_counts[base_id] += 1
        identities = []
        entity_flags = []
        lock_owner_paths = []
        for artist in flattened:
            component = getattr(
                artist, "_wenu_semantic_component", None
            )
            artist_identity = (
                identity.component_identity(component)
                if component is not None
                else identity
            )
            entity_category = getattr(
                artist, "_wenu_semantic_entity_category", None
            )
            if entity_category is not None:
                artist_identity = artist_identity.category_identity(
                    entity_category
                )
            lock_owner_path = artist_identity.semantic_path
            entity_key = getattr(
                artist, "_wenu_semantic_entity_key", None
            )
            if entity_key is not None:
                artist_identity = artist_identity.entity_identity(
                    entity_key,
                    getattr(
                        artist,
                        "_wenu_semantic_entity_display_name",
                        entity_key,
                    ),
                )
            identities.append(artist_identity)
            entity_flags.append(entity_key is not None)
            lock_owner_paths.append(lock_owner_path)
        totals = Counter(item.svg_id for item in identities)
        positions = Counter(existing_counts)
        results = []
        for artist, artist_identity, is_entity, lock_owner_path in zip(
            flattened,
            identities,
            entity_flags,
            lock_owner_paths,
            strict=True,
        ):
            exact = bool(
                getattr(artist_identity, "exact_svg_id", False)
            )
            positions[artist_identity.svg_id] += 1
            total = (
                existing_counts[artist_identity.svg_id]
                + totals[artist_identity.svg_id]
            )
            width = max(4, len(str(total)))
            svg_id = (
                artist_identity.svg_id
                if (
                    (exact or is_entity)
                    and total == 1
                )
                else (
                    f"{artist_identity.svg_id}--"
                    f"{positions[artist_identity.svg_id]:0{width}d}"
                )
            )
            artist.set_gid(svg_id)
            setattr(
                artist,
                "_wenu_semantic_svg_base_id",
                artist_identity.svg_id,
            )
            zorder = float(artist.get_zorder())
            paint_role = paint_role_for_zorder(zorder)
            attach_semantic_svg_metadata(
                artist,
                layer=artist_identity.name,
                zorder=zorder,
                paint_role=paint_role,
                edit_policy=artist_identity.edit_policy,
                semantic_path=artist_identity.semantic_path,
                lock_owner_path=lock_owner_path,
                display_name=artist_identity.display_name,
                path_display_names=getattr(
                    artist_identity,
                    "path_display_names",
                    (),
                ),
                presentation_order=artist_identity.presentation_order,
                style_role=artist_identity.style_role,
            )
            results.append(
                SemanticArtistRenderingResult(
                    artist=artist,
                    svg_id=svg_id,
                    zorder=zorder,
                    paint_role=paint_role,
                    edit_policy=artist_identity.edit_policy,
                    semantic_path=artist_identity.semantic_path,
                    display_name=artist_identity.display_name,
                    presentation_order=artist_identity.presentation_order,
                    style_role=artist_identity.style_role,
                )
            )
        return tuple(results)

    def _apply_clip_patch(self, artists):
        if self._clip_patch is None:
            return artists
        for artist in artists:
            if isinstance(artist, (list, tuple)):
                self._apply_clip_patch(artist)
            elif getattr(artist, "_wenu_exterior_label", False):
                artist.set_clip_on(False)
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

        sizes = polygons.metadata.get("mask_opening_group_sizes")
        if sizes is None:
            sizes = (len(polygons),)
        if any(not isinstance(size, int) or size < 0 for size in sizes):
            raise ValueError(
                "Mask opening group sizes must be nonnegative integers."
            )
        if sum(sizes) != len(polygons):
            raise ValueError("Mask opening group sizes must match polygons.")
        offset = 0
        for size in sizes:
            add_ring(
                (
                    (viewport.x_min, viewport.y_min),
                    (viewport.x_max, viewport.y_min),
                    (viewport.x_max, viewport.y_max),
                    (viewport.x_min, viewport.y_max),
                ),
                clockwise=False,
            )
            for polygon in polygons.items[offset:offset + size]:
                add_ring(
                    np.column_stack((polygon.x, polygon.y)),
                    clockwise=True,
                )
            offset += size
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
        self._viewport = viewport

    def draw(
        self,
        geometry,
        *,
        style=None,
        styles=None,
        polygon_fill_style=None,
        polygon_outline_style=None,
        polygon_marker_style=None,
        compound_by=None,
        component_styles=None,
        component_label_styles=None,
        point_overlays=None,
        draw_markers=True,
        draw_labels=False,
        label_style=None,
        label_offset=(0.0, 0.0),
        label_formatter=None,
        label_anchor=None,
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
        polygon_markers = (
            None
            if polygon_marker_style is None
            else dict(polygon_marker_style)
        )
        if (
            isinstance(geometry, ProjectedPoints)
            and self._viewport is not None
        ):
            geometry = cull_points_to_viewport(
                geometry,
                self._viewport,
            )

        if isinstance(geometry, ProjectedPoint):
            artists = self._draw_point(
                geometry,
                common,
                draw_labels=draw_labels,
                label_style=labels,
                label_offset=label_offset,
                label_formatter=label_formatter,
            )
        elif isinstance(geometry, ProjectedPoints):
            artists = self._draw_points(
                geometry,
                common,
                styles=styles,
                point_overlays=point_overlays,
                draw_markers=draw_markers,
                draw_labels=draw_labels,
                label_style=labels,
                label_offset=label_offset,
                label_formatter=label_formatter,
            )
        elif isinstance(geometry, ProjectedCurve):
            artists = self._draw_curve(
                geometry,
                common,
                draw_labels=draw_labels,
                label_style=labels,
                label_offset=label_offset,
                label_formatter=label_formatter,
            )
        elif isinstance(geometry, ProjectedCurves):
            artists = self._draw_curves(
                geometry,
                common,
                styles=styles,
                draw_labels=draw_labels,
                label_style=labels,
                label_offset=label_offset,
                label_formatter=label_formatter,
            )
        elif isinstance(geometry, ProjectedGrid):
            artists = self._draw_grid(
                geometry,
                common,
                styles=styles,
                component_styles=component_styles,
                component_label_styles=component_label_styles,
                draw_labels=draw_labels,
                label_style=labels,
                label_offset=label_offset,
                label_formatter=label_formatter,
                label_anchor=label_anchor,
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
                label_formatter=label_formatter,
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
                marker_style=polygon_markers,
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
                label_formatter=label_formatter,
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
        label_formatter,
    ):
        if not point.finite:
            return []
        artists = [render_point(self.ax, point, **style)]
        label = point.name
        if label is not None and label_formatter is not None:
            label = label_formatter(label)
        if draw_labels and label is not None:
            artists.append(
                self._label(
                    point.x,
                    point.y,
                    label,
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
        draw_markers,
        draw_labels,
        label_style,
        label_offset,
        label_formatter,
    ):
        finite = points.finite
        artists = []
        label_style = dict(label_style)
        placement = label_style.pop("placement", "fixed")
        if placement not in {"fixed", "auto", "region"}:
            raise ValueError("point label placement must be fixed, auto, or region")
        if draw_markers:
            areas = np.broadcast_to(np.asarray(style.get("s", 1.0)), (len(points),)).copy()
            for index, entity_style in enumerate(self._entity_styles(styles, len(points))):
                areas[index] = entity_style.get("s", areas[index])
            for overlay in point_overlays or ():
                if "mask" not in overlay:
                    raise ValueError("Each point overlay must provide a mask.")
                overlay_mask = np.asarray(overlay["mask"], dtype=bool)
                if overlay_mask.shape != (len(points),):
                    raise ValueError("Point overlay masks must match the point collection.")
                overlay_areas = np.broadcast_to(np.asarray(overlay.get("style", {}).get("s", 1.0)), (len(points),))
                areas = np.maximum(areas, np.where(overlay_mask, overlay_areas, 0.0))
            self._point_obstacles.extend(
                (float(points.x[index]), float(points.y[index]), float(np.sqrt(areas[index]) / 2.0))
                for index in np.flatnonzero(finite)
            )
        if draw_markers:
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
                            label_formatter=None,
                        )
                    )

        if draw_markers and point_overlays is not None:
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
                            **self._mask_style(overlay_style, selected),
                        )
                    )

        if draw_labels:
            entity_styles = self._entity_styles(styles, len(points))
            for index in np.flatnonzero(finite):
                label = self._entity_label(points, index)
                if label is not None and label_formatter is not None:
                    label = label_formatter(label)
                if label is not None:
                    inherited = {
                        name: entity_styles[index][name]
                        for name in ("color", "alpha", "zorder")
                        if name in entity_styles[index]
                    }
                    label_artist = self._label(
                        points.x[index],
                        points.y[index],
                        label,
                        {**inherited, **label_style},
                        label_offset,
                    )
                    if placement == "auto":
                        self._auto_labels.append((label_artist, float(points.x[index]), float(points.y[index])))
                    elif placement == "region" or "label_regions" in points.metadata:
                        regions = points.metadata.get("label_regions")
                        self._area_labels.append((
                            label_artist, *label_artist.get_position(),
                            None if regions is None else regions[index],
                            placement == "region",
                        ))
                    self._attach_semantic_entity(
                        (label_artist,), points.metadata, index
                    )
                    artists.append(label_artist)
        return artists

    def _draw_curve(
        self,
        curve,
        style,
        *,
        draw_labels,
        label_style,
        label_offset,
        label_formatter,
    ):
        style = dict(style)
        original_curve = curve
        clearances = style.pop("endpoint_clearance_points", None)
        if clearances is not None:
            curve = self._trim_curve_endpoints(curve, clearances)
            if curve is None:
                return []
        if not np.any(curve.finite):
            return []
        artists = [render_curve(self.ax, curve, **style)]
        if clearances is not None:
            self._gapped_lines.append((artists[0], original_curve, tuple(clearances)))
        label = curve.name
        if label is not None and label_formatter is not None:
            label = label_formatter(label)
        if draw_labels and label is not None:
            anchor = self._anchor(curve.x, curve.y)
            if anchor is not None:
                artists.append(
                    self._label(
                        *anchor,
                        label,
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
        label_formatter,
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
            curve_artists = self._draw_curve(
                curve,
                {**style, **entity_styles[index]},
                draw_labels=draw_labels,
                label_style=label_style,
                label_offset=label_offset,
                label_formatter=label_formatter,
            )
            self._attach_semantic_entity(
                curve_artists, curves.metadata, index
            )
            artists.extend(curve_artists)
        return artists

    def _draw_grid(
        self,
        grid,
        style,
        *,
        styles,
        component_styles,
        component_label_styles,
        draw_labels,
        label_style,
        label_offset,
        label_formatter,
        label_anchor,
    ):
        component_styles = (
            {} if component_styles is None else component_styles
        )
        component_label_styles = (
            {} if component_label_styles is None
            else component_label_styles
        )
        per_component_styles = (
            {} if styles is None else styles
        )
        artists = []
        for name, curves in grid.components.items():
            line_artists = self._draw_curves(
                    curves,
                    {
                        **style,
                        **dict(component_styles.get(name, {})),
                    },
                    styles=per_component_styles.get(name),
                    draw_labels=False,
                    label_style=label_style,
                    label_offset=label_offset,
                    label_formatter=None,
                )
            for artist in line_artists:
                setattr(artist, "_wenu_semantic_component", "lines")
            artists.extend(line_artists)
            if draw_labels:
                for index, curve in enumerate(curves):
                    curve_name = curve.name
                    if curve_name is None:
                        curve_name = self._metadata_label(
                            curves.metadata,
                            index,
                        )
                    if curve_name is None:
                        continue
                    named_curve = ProjectedCurve(
                        curve.x,
                        curve.y,
                        closed=curve.closed,
                        name=curve_name,
                    )
                    if label_anchor is None:
                        anchor = self._anchor(curve.x, curve.y)
                    elif getattr(label_anchor, "near_ends", False):
                        anchor = label_anchor(
                            named_curve, self.ax, measure_curve=self._measure_curve_label,
                        )
                    else:
                        anchor = label_anchor(named_curve, self.ax)
                    if anchor is None:
                        continue
                    anchors = anchor if isinstance(anchor, list) and all(
                        isinstance(item, CurveLabelPlacement) for item in anchor
                    ) else (anchor,)
                    for anchor in anchors:
                        label_style_for_curve = {
                            **label_style,
                            **dict(component_label_styles.get(name, {})),
                        }
                        if isinstance(anchor, CurveLabelPlacement):
                            position = (anchor.x, anchor.y)
                            if anchor.horizontal_alignment is not None:
                                label_style_for_curve["ha"] = (
                                    anchor.horizontal_alignment
                                )
                            if anchor.vertical_alignment is not None:
                                label_style_for_curve["va"] = (
                                    anchor.vertical_alignment
                                )
                            if anchor.rotation_deg is not None:
                                label_style_for_curve = {
                                    **label_style_for_curve,
                                    "rotation": anchor.rotation_deg,
                                    "rotation_mode": "anchor",
                                }
                                if anchor.normal_offset_em and anchor.exterior_direction is None:
                                    from matplotlib.transforms import (
                                        ScaledTranslation,
                                    )

                                    fontsize = float(
                                        label_style_for_curve.get(
                                            "fontsize", 10.0
                                        )
                                    )
                                    angle = np.radians(anchor.rotation_deg)
                                    distance = (
                                        anchor.normal_offset_em * fontsize
                                    )
                                    dx = -np.sin(angle) * distance / 72.0
                                    dy = np.cos(angle) * distance / 72.0
                                    label_style_for_curve["transform"] = (
                                        self.ax.transData
                                        + ScaledTranslation(
                                            dx,
                                            dy,
                                            self.ax.figure.dpi_scale_trans,
                                        )
                                    )
                        else:
                            position = anchor
                        label = (
                            curve_name
                            if label_formatter is None
                            else label_formatter(curve_name)
                        )
                        label_artist = self._label(
                            *position,
                            label,
                            label_style_for_curve,
                            label_offset,
                        )
                        setattr(
                            label_artist,
                            "_wenu_semantic_component",
                            "labels",
                        )
                        if isinstance(anchor, CurveLabelPlacement) and anchor.exterior_direction is not None:
                            from matplotlib.transforms import ScaledTranslation

                            self.ax.apply_aspect()
                            direction = np.asarray(anchor.exterior_direction, dtype=float)
                            origin = self.ax.transData.transform((anchor.x, anchor.y))
                            direction = self.ax.transData.transform(
                                np.asarray((anchor.x, anchor.y)) + direction
                            ) - origin
                            direction /= np.linalg.norm(direction)
                            box = label_artist.get_window_extent(self.ax.figure.canvas.get_renderer())
                            fontsize = label_artist.get_fontsize()
                            distance = (abs(direction[0]) * box.width + abs(direction[1]) * box.height) / 2.0
                            distance += anchor.normal_offset_em * fontsize * self.ax.figure.dpi / 72.0
                            shift = direction * distance / self.ax.figure.dpi
                            label_artist.set_transform(self.ax.transData + ScaledTranslation(
                                *shift, self.ax.figure.dpi_scale_trans,
                            ))
                            label_artist.set_clip_on(False)
                            setattr(label_artist, "_wenu_exterior_label", True)
                            label_artist._wenu_exterior_attachment = (
                                (anchor.x, anchor.y),
                                np.asarray(anchor.exterior_direction, dtype=float),
                            )
                        candidate_factory = getattr(label_anchor, "candidates", None)
                        if isinstance(anchor, CurveLabelPlacement) and callable(candidate_factory):
                            per_anchor = getattr(label_anchor, "candidates_for_anchor", None)
                            candidates = tuple(
                                per_anchor(named_curve, anchor, self.ax) if callable(per_anchor)
                                else candidate_factory(named_curve, self.ax)
                            )
                            if candidates:
                                label_artist._wenu_reference_endpoint_label = bool(getattr(label_anchor, "near_ends", False))
                                self._curve_labels.append((label_artist, anchor, (anchor, *candidates)))
                        artists.append(label_artist)
        return artists

    def _apply_curve_label_placement(self, artist, placement):
        """Recompute a curve label's tangent and physical normal offset."""
        from matplotlib.transforms import ScaledTranslation

        artist.set_position((placement.x, placement.y))
        if placement.rotation_deg is not None:
            artist.set_rotation(placement.rotation_deg)
            artist.set_rotation_mode("anchor")
        if placement.horizontal_alignment is not None:
            artist.set_ha(placement.horizontal_alignment)
        if placement.vertical_alignment is not None:
            artist.set_va(placement.vertical_alignment)
        angle = np.radians(artist.get_rotation())
        distance = placement.normal_offset_em * artist.get_fontsize() / 72.0
        artist.set_transform(self.ax.transData + ScaledTranslation(
            -np.sin(angle) * distance, np.cos(angle) * distance,
            self.ax.figure.dpi_scale_trans,
        ))

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
        label_formatter,
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
        label = polygon.name
        if label is not None and label_formatter is not None:
            label = label_formatter(label)
        if draw_labels and label is not None:
            anchor = self._anchor(polygon.x, polygon.y)
            if anchor is not None:
                artists.append(
                    self._label(
                        *anchor,
                        label,
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
        label_formatter,
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
            polygon_artists = self._draw_polygon(
                polygon,
                {**style, **entity_styles[index]},
                fill_style=fill_style,
                outline_style=outline_style,
                draw_labels=draw_labels,
                label_style=label_style,
                label_offset=label_offset,
                label_formatter=label_formatter,
            )
            self._attach_semantic_entity(
                polygon_artists, polygons.metadata, index
            )
            artists.extend(polygon_artists)
        return artists

    def _draw_compound_polygons(
        self,
        polygons,
        style,
        *,
        compound_by,
        fill_style,
        outline_style,
        marker_style,
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
            group_indices = np.flatnonzero(groups == group)
            representative_index = int(group_indices[0])
            vertices = []
            codes = []
            for index in group_indices:
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

            def register(patch):
                self.ax.add_patch(patch)
                self._attach_semantic_entity(
                    (patch,),
                    polygons.metadata,
                    representative_index,
                )
                artists.append(patch)

            path = Path(
                np.asarray(vertices, dtype=float),
                np.asarray(codes, dtype=np.uint8),
            )
            if fill_style is None and outline_style is None:
                patch = PathPatch(path, **self._polygon_style(style))
                register(patch)
                continue
            if fill_style is not None:
                fill = {**style, **fill_style}
                fill.setdefault("edgecolor", "none")
                patch = PathPatch(path, **self._polygon_style(fill))
                register(patch)
            if outline_style is not None:
                outline = {**style, **outline_style}
                outline.setdefault("facecolor", "none")
                patch = PathPatch(path, **self._polygon_style(outline))
                register(patch)
        if marker_style is not None:
            for index, polygon in enumerate(polygons):
                marker_curve = ProjectedCurve(
                    polygon.x,
                    polygon.y,
                    closed=True,
                )
                marker_artist = render_curve(
                    self.ax,
                    marker_curve,
                    **marker_style,
                )
                self._attach_semantic_entity(
                    (marker_artist,), polygons.metadata, index
                )
                artists.append(marker_artist)
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

    def _trim_curve_endpoints(self, curve, clearances):
        """Trim visible graphical endpoints in physical points, never sky angles."""
        clearances = np.asarray(clearances, dtype=float)
        if clearances.shape != (2,) or np.any(~np.isfinite(clearances)) or np.any(clearances < 0.0):
            raise ValueError("endpoint clearances must be two finite nonnegative point distances")
        if curve.closed or not np.all(curve.finite) or len(curve.x) < 2:
            return curve
        xy = self.ax.transData.transform(np.column_stack((curve.x, curve.y)))
        obstacles = self.ax.transData.transform([(x, y) for x, y, _ in self._point_obstacles]) if self._point_obstacles else np.empty((0, 2))
        # A cap/viewport intersection is not a stellar endpoint; do not trim it.
        for index, endpoint in enumerate((xy[0], xy[-1])):
            if not len(obstacles) or np.min(np.linalg.norm(obstacles - endpoint, axis=1)) > 1e-4:
                clearances[index] = 0.0
        lengths = np.linalg.norm(np.diff(xy, axis=0), axis=1)
        distance = np.concatenate(([0.0], np.cumsum(lengths)))
        start, end = clearances * self.ax.figure.dpi / 72.0
        finish = distance[-1] - end
        if start >= finish:
            return None
        retained = (distance > start) & (distance < finish)
        anchors = np.column_stack((np.interp([start, finish], distance, xy[:, 0]),
                                   np.interp([start, finish], distance, xy[:, 1])))
        result = self.ax.transData.inverted().transform(np.vstack((anchors[0], xy[retained], anchors[1])))
        return ProjectedCurve(result[:, 0], result[:, 1], closed=curve.closed, name=curve.name)

    def finalize_graphics(self):
        """Resolve physical gaps and label positions after aspect/layout settles."""
        if not (self._gapped_lines or self._auto_labels or self._area_labels or self._curve_labels or self._grid_label_band):
            return
        self.ax.figure.canvas.draw()
        for line, curve, clearances in self._gapped_lines:
            shortened = self._trim_curve_endpoints(curve, clearances)
            if shortened is None:
                line.set_visible(False)
            else:
                line.set_data(shortened.x, shortened.y)
                self._apply_clip_patch([line])
        self.finalize_label_placement()
        self._finalize_grid_label_band()

    def finalize_label_placement(self):
        """Place compact labels with visible ownership in final display space.

        Point, area and curve candidates preserve their attachment policies.
        Boundary containment and text separation precede marker clearance,
        point ownership and cosmetic preferences. Coordinate descent plus
        bounded simultaneous pair moves revisit assignments as a group.
        """
        if not (self._auto_labels or self._area_labels or self._curve_labels):
            return
        self.ax.figure.canvas.draw()
        renderer = self.ax.figure.canvas.get_renderer()
        scale = self.ax.figure.dpi / 72.0
        centres = self.ax.transData.transform(
            [(x, y) for x, y, _ in self._point_obstacles]
        ) if self._point_obstacles else np.empty((0, 2))
        radii = np.asarray([radius * scale for _, _, radius in self._point_obstacles])
        auto_artists = {item[0] for item in (*self._auto_labels, *self._area_labels, *self._curve_labels)}
        fixed = [artist.get_window_extent(renderer) for artist in self.ax.texts
                 if artist not in auto_artists and artist.get_visible() and artist.get_text()]
        paths = [line.get_path().transformed(line.get_transform())
                 for line in self.ax.lines if line.get_visible()]
        bounds = self.ax.get_window_extent(renderer)
        boundary = (
            None if self._clip_patch is None
            else self._clip_patch.get_path().transformed(self._clip_patch.get_transform())
        )

        def outside_boundary(box):
            outside = max(0.0, box.width * box.height / scale**2 - overlap(box, bounds))
            if boundary is not None:
                corners = np.asarray(((box.x0, box.y0), (box.x0, box.y1),
                                      (box.x1, box.y0), (box.x1, box.y1)))
                inside = boundary.contains_points(corners)
                if not inside.all() or boundary.intersects_bbox(box, filled=False):
                    outside += box.width * box.height / scale**2
            return outside

        def overlap(first, second):
            return (max(0.0, min(first.x1, second.x1) - max(first.x0, second.x0))
                    * max(0.0, min(first.y1, second.y1) - max(first.y0, second.y0))) / scale**2

        def distances(box, points):
            return np.hypot(
                np.maximum(np.maximum(box.x0 - points[:, 0], points[:, 0] - box.x1), 0),
                np.maximum(np.maximum(box.y0 - points[:, 1], points[:, 1] - box.y1), 0),
            )

        def radius_at(anchor):
            if not len(centres):
                return 0.0
            near = np.linalg.norm(centres - anchor, axis=1) < 1e-4
            return np.max(radii[near], initial=0.0)

        point_labels = sorted(self._auto_labels, key=lambda item: (
            -radius_at(self.ax.transData.transform(item[1:])),
            -len(item[0].get_text()),
        ))
        labels = list(point_labels)
        label_anchors = self.ax.transData.transform([item[1:] for item in point_labels]) if point_labels else np.empty((0, 2))
        label_radii = np.asarray([radius_at(anchor) for anchor in label_anchors])
        choices = []
        for artist, x, y in point_labels:
            anchor = self.ax.transData.transform((x, y))
            radius = radius_at(anchor)
            artist.set_ha("left")
            artist.set_va("bottom")
            rotation = self._label_rotations.get(artist)
            if rotation is not None:
                artist.set_rotation(rotation(x, y))
            width, height = artist.get_window_extent(renderer).size
            # Sub-resolution companions share a visible anchor, not an identity.
            competitors = np.linalg.norm(label_anchors - anchor, axis=1) > 0.25 * scale
            offsets = label_anchors - anchor
            separations = np.linalg.norm(offsets, axis=1)
            neighbours = np.flatnonzero(separations > 0.25 * scale)
            lateral = False
            if len(neighbours):
                nearest = neighbours[np.argmin(separations[neighbours])]
                lateral = (separations[nearest] < 3 * height + radius
                           and abs(offsets[nearest, 1]) > 2 * abs(offsets[nearest, 0]))
            candidates = []
            directions = ((0, 1), (0, -1), (1, 1), (-1, 1),
                          (1, -1), (-1, -1), (1, 0), (-1, 0))
            extras = (0.0, 0.75, 1.5, 2.25) if lateral and width > 3 * height else (0.0, 0.75, 1.5)
            for extra in extras:
                clearance = radius + (0.75 + extra) * scale
                for preference, (dx, dy) in enumerate(directions):
                    offset = np.asarray((dx, dy), dtype=float)
                    offset *= clearance / np.linalg.norm(offset)
                    origin = anchor + offset
                    left = origin[0] - (width if dx < 0 else width / 2 if dx == 0 else 0)
                    bottom = origin[1] - (height if dy < 0 else height / 2 if dy == 0 else 0)
                    # Measure the actual rotated artist at each candidate.
                    # Re-evaluate position-dependent orientation after moving.
                    position = np.asarray((left, bottom))
                    rotation = self._label_rotations.get(artist)
                    for _ in range(4):
                        data_position = self.ax.transData.inverted().transform(position)
                        artist.set_position(data_position)
                        if rotation is not None:
                            artist.set_rotation(rotation(*data_position))
                        box = artist.get_window_extent(renderer)
                        correction = np.asarray((left - box.x0, bottom - box.y0))
                        if np.linalg.norm(correction) < 0.01:
                            break
                        position += correction
                    data_position = self.ax.transData.inverted().transform(position)
                    artist.set_position(data_position)
                    if rotation is not None:
                        artist.set_rotation(rotation(*data_position))
                    box = artist.get_window_extent(renderer)
                    padded = box.padded(0.75 * scale)
                    own_distance = distances(box, anchor.reshape(1, 2))[0]
                    attachment = np.clip(anchor, (box.x0, box.y0), (box.x1, box.y1))
                    own_gap = max(own_distance - radius, 0)
                    other_gaps = np.maximum(np.linalg.norm(label_anchors - attachment, axis=1) - label_radii, 0)
                    ambiguous = np.maximum(own_gap - other_gaps[competitors], 0).sum() / scale
                    marker_conflict = np.maximum(radii + 0.25 * scale - distances(padded, centres), 0).sum() / scale
                    fixed_conflict = sum(overlap(padded, other) for other in fixed)
                    outside = outside_boundary(padded)
                    alignment = float(lateral and dy != 0)
                    cosmetic = (0.35 * sum(path.intersects_bbox(padded, filled=False) for path in paths)
                                + 0.025 * preference + 0.05 * extra)
                    candidates.append((box, padded, (marker_conflict, ambiguous,
                                                      fixed_conflict, outside, alignment, cosmetic),
                                       tuple(data_position), artist.get_rotation(), artist.get_transform()))
            choices.append(candidates)

        def measured_choice(artist, *, movement=0.0):
            box = artist.get_window_extent(renderer)
            padded = box.padded(0.75 * scale)
            marker = np.maximum(radii + 0.25 * scale - distances(padded, centres), 0).sum() / scale
            static = (marker, 0.0, sum(overlap(padded, other) for other in fixed),
                      outside_boundary(padded), 0.0,
                      movement + .35 * sum(path.intersects_bbox(padded, filled=False) for path in paths))
            return (box, padded, static, artist.get_position(), artist.get_rotation(), artist.get_transform())

        suppressed = []
        for artist, x, y, regions, movable in self._area_labels:
            from matplotlib.path import Path

            artist.set_visible(True)
            artist.set_position((x, y))
            rotation = self._label_rotations.get(artist)
            if rotation is not None:
                artist.set_rotation(rotation(x, y))
            origin = self.ax.transData.transform((x, y))
            region_paths = None if regions is None else tuple(
                Path(np.vstack((np.column_stack((region.x, region.y)), (region.x[0], region.y[0])))).transformed(self.ax.transData)
                for region in regions
            )
            step = artist.get_fontsize() * scale
            offsets = [(0.0, 0.0)] + [(dx * distance, dy * distance)
                for distance in ((0.75, 1.5, 2.5, 4.0) if movable else ())
                for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, 1), (1, -1), (-1, -1))]
            # Add size-aware inward moves for anchors close to the rim.
            # Every candidate must fit its own region; narrow visible slivers
            # suppress their names instead of moving them into a neighbour.
            if boundary is not None and movable:
                inward = bounds.get_points().mean(axis=0) - origin
                length = np.linalg.norm(inward)
                if length > 0:
                    box = artist.get_window_extent(renderer)
                    reach = np.hypot(box.width, box.height) / step
                    offsets.extend(tuple(inward / length * reach * fraction)
                                   for fraction in (0.5, 1.0, 1.5))
            candidates = []
            for dx, dy in offsets:
                position = self.ax.transData.inverted().transform(origin + step * np.asarray((dx, dy)))
                artist.set_position(position)
                rotation = self._label_rotations.get(artist)
                if rotation is not None:
                    artist.set_rotation(rotation(*position))
                box = artist.get_window_extent(renderer)
                ink = box.padded(0.25 * scale)
                corners = ((ink.x0, ink.y0), (ink.x0, ink.y1),
                           (ink.x1, ink.y0), (ink.x1, ink.y1))
                allowed = region_paths is None or any(
                    path.contains_points(corners).all()
                    and not path.intersects_bbox(ink, filled=False)
                    for path in region_paths
                )
                if not allowed or outside_boundary(ink) > 1e-6:
                    continue
                candidates.append(measured_choice(artist, movement=0.025 * np.hypot(dx, dy)))
            if not candidates:
                artist.set_visible(False)
                suppressed.append(artist.get_text())
                continue
            labels.append((artist, x, y))
            choices.append(candidates)
        self.suppressed_region_labels = tuple(suppressed)

        for artist, original, placements in self._curve_labels:
            artist.set_visible(True)
            origin = self.ax.transData.transform((original.x, original.y))
            candidates = []
            for placement in placements:
                self._apply_curve_label_placement(artist, placement)
                if getattr(artist, "_wenu_reference_endpoint_label", False):
                    if outside_boundary(artist.get_window_extent(renderer).padded(.25 * scale)) > 1e-6:
                        continue
                movement = np.linalg.norm(self.ax.transData.transform((placement.x, placement.y)) - origin) / scale
                candidates.append(measured_choice(artist, movement=0.002 * movement))
            if not candidates:
                artist.set_visible(False)
                continue
            labels.append((artist, original.x, original.y))
            choices.append(candidates)

        candidate_bounds = [np.asarray([choice[1].extents for choice in candidates]) for candidates in choices]
        pair_overlaps = {}

        def pair_overlap(first, a, second, b):
            if first > second:
                return pair_overlap(second, b, first, a)
            key = first, second
            if key not in pair_overlaps:
                left, right = candidate_bounds[first], candidate_bounds[second]
                widths = np.maximum(0.0, np.minimum(left[:, None, 2], right[None, :, 2]) - np.maximum(left[:, None, 0], right[None, :, 0]))
                heights = np.maximum(0.0, np.minimum(left[:, None, 3], right[None, :, 3]) - np.maximum(left[:, None, 1], right[None, :, 1]))
                pair_overlaps[key] = widths * heights / scale**2
            return pair_overlaps[key][a, b]

        selected = []

        def score(index, candidate, assignments, *, exclude=None):
            static = choices[index][candidate][2]
            collisions = sum(pair_overlap(index, candidate, other, value)
                for other, value in enumerate(assignments) if other != index and other != exclude)
            return (static[3], static[2] + collisions, static[0], static[1], static[4], static[5])

        for index, candidates in enumerate(choices):
            selected.append(min(range(len(candidates)), key=lambda value: score(index, value, selected)))

        def descend():
            for _ in range(12):
                changed = False
                for index, candidates in enumerate(choices):
                    best = min(range(len(candidates)), key=lambda value: score(index, value, selected))
                    if score(index, best, selected) < score(index, selected[index], selected):
                        selected[index] = best
                        changed = True
                if not changed:
                    break

        def pair_score(i, a, j, b):
            left = score(i, a, selected, exclude=j)
            right = score(j, b, selected, exclude=i)
            combined = [x + y for x, y in zip(left, right)]
            combined[1] += pair_overlap(i, a, j, b)
            return tuple(combined)

        descend()
        # Simultaneous pair moves escape slots that a single-label move cannot.
        for _ in range(3):
            conflicts = sorted((-pair_overlap(i, selected[i], j, selected[j]), i, j)
                for i in range(len(labels)) for j in range(i + 1, len(labels))
                if pair_overlap(i, selected[i], j, selected[j]) > 1.0e-6)
            changed = False
            for _, i, j in conflicts[:64]:
                old = pair_score(i, selected[i], j, selected[j])
                left = np.asarray([score(i, a, selected, exclude=j) for a in range(len(choices[i]))])
                right = np.asarray([score(j, b, selected, exclude=i) for b in range(len(choices[j]))])
                combined = left[:, None, :] + right[None, :, :]
                matrix = pair_overlaps[min(i, j), max(i, j)]
                combined[:, :, 1] += matrix if i < j else matrix.T
                flat = combined.reshape(-1, combined.shape[-1])
                best = np.lexsort(tuple(flat[:, column] for column in range(5, -1, -1)))[0]
                a, b = np.unravel_index(best, combined.shape[:2])
                if pair_score(i, a, j, b) < old:
                    selected[i], selected[j] = a, b
                    changed = True
            if not changed:
                break
            descend()
        for index, (artist, _, _) in enumerate(labels):
            _, _, _, position, rotation, transform = choices[index][selected[index]]
            artist.set_position(position)
            artist.set_rotation(rotation)
            artist.set_transform(transform)
        all_text = [artist for artist in self.ax.texts if artist.get_visible() and artist.get_text()]
        self.unresolved_label_collisions = tuple(
            (first.get_text(), second.get_text())
            for i, first in enumerate(all_text) for second in all_text[i + 1:]
            if (first in auto_artists or second in auto_artists)
            and overlap(first.get_window_extent(renderer), second.get_window_extent(renderer)) > 0.01
        )

    def _label(self, x, y, label, style, offset):
        style = dict(style)
        rotation = style.get("rotation")
        if isinstance(offset, Mapping):
            offset = offset.get(
                str(label),
                offset.get("__default__", (0.0, 0.0)),
            )
        dx, dy = offset(x, y) if callable(offset) else offset
        if callable(rotation):
            style["rotation"] = rotation(x + dx, y + dy)
        artist = render_text(
            self.ax,
            x + dx,
            y + dy,
            str(label),
            **style,
        )
        if callable(rotation):
            self._label_rotations[artist] = rotation
        return artist

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
    def _attach_semantic_entity(artists, metadata, index):
        """Carry optional source entity identity without domain knowledge."""
        keys = metadata.get("semantic_entity_keys")
        names = metadata.get("semantic_entity_display_names")
        categories = metadata.get("semantic_entity_categories")
        if keys is None and names is None and categories is None:
            return
        if keys is None or names is None:
            raise ValueError(
                "Semantic entity keys and display names must be paired."
            )
        if len(keys) != len(names):
            raise ValueError(
                "Semantic entity keys and display names must align."
            )
        if categories is not None and len(categories) != len(keys):
            raise ValueError(
                "Semantic entity categories must align with entities."
            )
        for artist in artists:
            setattr(
                artist,
                "_wenu_semantic_entity_key",
                keys[index],
            )
            setattr(
                artist,
                "_wenu_semantic_entity_display_name",
                names[index],
            )
            if categories is not None:
                setattr(
                    artist,
                    "_wenu_semantic_entity_category",
                    categories[index],
                )

    @staticmethod
    def _anchor(x, y):
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
        finite = np.isfinite(x) & np.isfinite(y)
        if not np.any(finite):
            return None
        return float(np.mean(x[finite])), float(np.mean(y[finite]))
