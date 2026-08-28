"""Single-face polar-planisphere disk geometry."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import ClassVar

import numpy as np

from wenu.charts.boundaries import (
    CircularGridLabelAnchor,
    apply_coordinate_label_anchor,
    circular_boundary,
    resolved_circular_boundary_style,
)
from wenu.charts.coordinate_frames import horizontal_to_equatorial
from wenu.charts.projection_selection import ProjectionSelection
from wenu.geometry.frame import SphericalFrame
from wenu.geometry.projected import ProjectedPoints
from wenu.geometry.spherical import SphericalPolygons
from wenu.geometry.viewport import Viewport
from wenu.rendering.preparation import clip_to_latitude
from wenu.rendering.label_placement import rotation_with_down_toward
from wenu.charts.polar_label_curation import (
    SOUTH_CONSTELLATION_LABEL_OFFSETS,
    SOUTH_DEEP_SKY_LABEL_OFFSETS,
    SOUTH_GLOBULAR_LABEL_FONTSIZE,
    SOUTH_GLOBULAR_MINIMUM_SIZE_ARCMIN,
    SOUTH_OPEN_CLUSTER_SYMBOL_STYLES,
)


def _merged_label_offsets(default, overrides):
    if isinstance(default, Mapping):
        return {**dict(default), **dict(overrides)}
    return {"__default__": default, **dict(overrides)}


def _with_entity_symbol_styles(render, overrides):
    """Return options that restyle only reviewed point identifiers."""
    configured = dict(render)

    def resolved(_spherical, projected):
        styles = []
        for index in range(len(projected)):
            identifiers = (
                values[index]
                for values in (
                    projected.ids,
                    projected.names,
                    projected.labels,
                )
                if values is not None
            )
            style = next(
                (
                    overrides[str(identifier)]
                    for identifier in identifiers
                    if str(identifier) in overrides
                ),
                None,
            )
            styles.append({} if style is None else dict(style))
        return {**configured, "styles": tuple(styles)}

    return resolved


@dataclass(frozen=True)
class PolarPlanisphereChart:
    """One equatorial polar disk bounded by a declination parallel."""

    chart_type: ClassVar[str] = "polar_planisphere"
    pole: str = "south"
    limiting_declination_deg: float | None = None
    projection_name: str = "polar_azimuthal_equidistant"
    position_angle_deg: float = 0.0
    projection_radius: float = 2.0
    physical_diameter_mm: float = 195.0
    flip_ew: bool = True
    boundary_samples: int = 721

    def __post_init__(self):
        pole = str(self.pole).strip().lower()
        if pole not in {"north", "south"}:
            raise ValueError("pole must be 'north' or 'south'.")
        projection_name = str(self.projection_name).strip().lower()
        if projection_name not in {
            "polar_azimuthal_equidistant",
            "stereographic",
        }:
            raise ValueError(
                "projection_name must be 'polar_azimuthal_equidistant' "
                "or 'stereographic'."
            )
        limit = self.limiting_declination_deg
        if limit is None:
            limit = 20.0 if pole == "south" else -20.0
        values = np.asarray(
            (
                limit,
                self.position_angle_deg,
                self.projection_radius,
                self.physical_diameter_mm,
            ),
            dtype=float,
        )
        if not np.all(np.isfinite(values)):
            raise ValueError("Polar-planisphere values must be finite.")
        limit = float(limit)
        if not -90.0 < limit < 90.0:
            raise ValueError(
                "limiting_declination_deg must be between -90 and 90."
            )
        if self.projection_radius <= 0.0:
            raise ValueError("projection_radius must be positive.")
        if self.physical_diameter_mm <= 0.0:
            raise ValueError("physical_diameter_mm must be positive.")
        if int(self.boundary_samples) < 16:
            raise ValueError("boundary_samples must be at least 16.")
        object.__setattr__(self, "pole", pole)
        object.__setattr__(self, "projection_name", projection_name)
        object.__setattr__(self, "limiting_declination_deg", limit)
        object.__setattr__(
            self, "position_angle_deg", float(self.position_angle_deg)
        )
        object.__setattr__(
            self, "projection_radius", float(self.projection_radius)
        )
        object.__setattr__(
            self, "physical_diameter_mm", float(self.physical_diameter_mm)
        )
        object.__setattr__(
            self, "boundary_samples", int(self.boundary_samples)
        )

    @property
    def pole_declination_deg(self):
        return -90.0 if self.pole == "south" else 90.0

    @property
    def angular_radius_deg(self):
        return abs(
            self.limiting_declination_deg - self.pole_declination_deg
        )

    @property
    def projection_selection(self):
        return ProjectionSelection(self.projection_name, "equatorial")

    @property
    def projection(self):
        geometry = {
            "radius": self.projection_radius,
            "flip_ew": self.flip_ew,
        }
        if self.projection_name == "polar_azimuthal_equidistant":
            geometry.update(
                pole=self.pole,
                position_angle_deg=self.position_angle_deg,
            )
        else:
            geometry["frame"] = SphericalFrame(
                pole_lon_deg=0.0,
                pole_lat_deg=self.pole_declination_deg,
                position_angle_deg=self.position_angle_deg,
            )
        return self.projection_selection.build(**geometry)

    @property
    def boundary_radius(self):
        return self.projection.projected_radius(self.angular_radius_deg)

    @property
    def boundary(self):
        return circular_boundary(
            self.boundary_radius,
            samples=self.boundary_samples,
            name=(
                "declination_"
                f"{self.limiting_declination_deg:g}"
            ),
        )

    @property
    def viewport(self):
        radius = self.boundary_radius
        return Viewport.centered(width=2.0 * radius, height=2.0 * radius)

    @property
    def coordinate_label_anchor(self):
        return CircularGridLabelAnchor(
            self.boundary,
            declination_at_left=True,
        )

    @property
    def chart_context(self):
        from wenu.charts.context import BoundaryKind, ChartContext

        radius = self.angular_radius_deg
        solid_angle = 2.0 * np.pi * (1.0 - np.cos(np.radians(radius)))
        return ChartContext(
            viewport=self.viewport,
            angular_width_deg=2.0 * radius,
            angular_height_deg=2.0 * radius,
            tangent_longitude_deg=0.0,
            tangent_latitude_deg=self.pole_declination_deg,
            boundary_kind=BoundaryKind.CIRCULAR,
            clip_boundary=self.boundary,
            visible_solid_angle_sq_deg=(
                solid_angle * (180.0 / np.pi) ** 2
            ),
            horizon_altitude_deg=-90.0,
        )

    def figure_size(self, width_inches=7.0):
        width = float(width_inches)
        if not np.isfinite(width) or width <= 0.0:
            raise ValueError("width_inches must be positive and finite.")
        return width, width

    def render(
        self,
        sky,
        renderer,
        *,
        observer=None,
        style=None,
        layer_options=None,
        boundary_style=None,
    ):
        """Render equatorial disk geometry through ``CelestialSphere``."""
        resolved_observer = (
            getattr(sky, "observer", None) if observer is None else observer
        )
        if resolved_observer is None:
            raise TypeError(
                "polar-planisphere rendering requires an observer."
            )
        resolved_style = style
        converter = getattr(style, "as_publication_style", None)
        if callable(converter):
            resolved_style = converter()
        options = (
            {}
            if resolved_style is None
            else resolved_style.layer_options(
                sky,
                horizon_altitude_deg=-90.0,
            )
        )
        if layer_options is not None:
            options.update(layer_options)
        options = self._inset_constellation_labels(sky, options)
        options = apply_coordinate_label_anchor(
            options, self.coordinate_label_anchor
        )
        set_background = getattr(renderer, "set_circular_background", None)
        canvas = getattr(style, "canvas", None)
        sky_color = getattr(canvas, "sky_color", None)
        if callable(set_background) and sky_color is not None:
            set_background(self.boundary, color=sky_color)
        set_boundary = getattr(renderer, "set_clip_boundary", None)
        if not callable(set_boundary):
            raise TypeError(
                "renderer must provide set_clip_boundary() for a "
                "polar-planisphere chart."
            )
        if boundary_style is None:
            boundary_style = resolved_circular_boundary_style(style)
        set_boundary(self.boundary, style=boundary_style or {})
        set_frame_visible = getattr(renderer, "set_axes_frame_visible", None)
        if callable(set_frame_visible):
            set_frame_visible(False)
        projection = self.projection

        def project(spherical):
            equatorial = horizontal_to_equatorial(
                spherical,
                resolved_observer,
            )
            return self.project_equatorial_geometry(equatorial)

        return sky.draw_chart(
            projection=projection,
            renderer=renderer,
            observer=resolved_observer,
            viewport=self.viewport,
            layer_options=options,
            project_geometry=project,
        )

    def project_equatorial_geometry(self, spherical):
        """Project geometry after clipping it to this face's sky cap."""
        projected = self.projection.project_geometry(spherical)
        if isinstance(spherical, SphericalPolygons):
            return projected
        if self.pole == "north":
            return clip_to_latitude(
                spherical,
                projected,
                minimum=self.limiting_declination_deg,
            )
        return clip_to_latitude(
            spherical,
            projected,
            minimum=-90.0,
            maximum=self.limiting_declination_deg,
        )

    def _inset_constellation_labels(self, sky, options):
        """Inset constellation labels and orient polar labels radially."""
        layer = getattr(sky, "constellation_labels", None)
        result = dict(options)
        if layer is not None and layer in options:
            configured = dict(options[layer])
            prepare = configured.get("prepare")
            radius = self.boundary_radius * 0.94

            def inset(spherical, projected):
                prepared = (
                    projected
                    if prepare is None
                    else prepare(spherical, projected)
                )
                if not isinstance(prepared, ProjectedPoints):
                    return prepared
                x = np.asarray(prepared.x, dtype=float).copy()
                y = np.asarray(prepared.y, dtype=float).copy()
                outside = np.hypot(x, y) > radius
                x[outside] = np.nan
                y[outside] = np.nan
                return ProjectedPoints(
                    x=x,
                    y=y,
                    metadata=prepared.metadata,
                    ids=prepared.ids,
                    labels=prepared.labels,
                    names=prepared.names,
                )

            configured["prepare"] = inset
            result[layer] = configured

        def polar_tangent_rotation(x, y):
            radial_angle = np.degrees(np.arctan2(y, x))
            return rotation_with_down_toward(
                radial_angle + 90.0,
                (x, y),
                (0.0, 0.0),
            )

        if layer is not None and layer in result:
            configured = dict(result[layer])
            render = dict(configured.get("render", {}))
            label_style = dict(render.get("label_style", {}))
            label_style.update(
                rotation=polar_tangent_rotation,
                rotation_mode="anchor",
            )
            render["label_style"] = label_style
            if self.pole == "south":
                render["label_offset"] = _merged_label_offsets(
                    render.get("label_offset", (0.0, 0.0)),
                    SOUTH_CONSTELLATION_LABEL_OFFSETS,
                )
            configured["render"] = render
            result[layer] = configured

        label_layers = (
            "nonstellar",
            "galaxies",
            "open_clusters",
            "globular_clusters",
            "planetary_nebulae",
        )
        for name in label_layers:
            current = getattr(sky, name, None)
            if current is None or current not in result:
                continue
            configured = dict(result[current])
            render = dict(configured.get("render", {}))
            label_style = dict(render.get("label_style", {}))
            label_style.update(
                rotation=polar_tangent_rotation,
                rotation_mode="anchor",
            )
            if self.pole == "south" and name == "globular_clusters":
                label_style["fontsize"] = SOUTH_GLOBULAR_LABEL_FONTSIZE
                geometry = dict(configured.get("geometry", {}))
                geometry["minimum_size_arcmin"] = (
                    SOUTH_GLOBULAR_MINIMUM_SIZE_ARCMIN
                )
                configured["geometry"] = geometry
            render["label_style"] = label_style
            if self.pole == "south":
                render["label_offset"] = _merged_label_offsets(
                    render.get("label_offset", (0.0, 0.0)),
                    SOUTH_DEEP_SKY_LABEL_OFFSETS.get(name, {}),
                )
                if name == "open_clusters":
                    render = _with_entity_symbol_styles(
                        render,
                        SOUTH_OPEN_CLUSTER_SYMBOL_STYLES,
                    )
            configured["render"] = render
            result[current] = configured
        return result

    def export(
        self,
        sky,
        renderer,
        path,
        *,
        observer=None,
        style=None,
        layer_options=None,
        export_options=None,
        legends=None,
        resolved_detail=None,
        composition=None,
        boundary_style=None,
        additional_furniture=None,
        svg_provenance=None,
    ):
        """Render and reproducibly save one polar-planisphere face."""
        if composition is not None:
            if (
                style is not None
                or legends is not None
                or resolved_detail is not None
            ):
                raise ValueError(
                    "composition cannot be combined with style, legends, "
                    "or resolved_detail."
                )
            from wenu.charts.export_workflow import export_composed_chart

            return export_composed_chart(
                self,
                sky,
                renderer,
                path,
                observer=observer,
                composition=composition,
                layer_options=layer_options,
                export_options=export_options,
                render_options={"boundary_style": boundary_style},
                additional_furniture=additional_furniture,
                svg_provenance=svg_provenance,
            )
        if additional_furniture is not None:
            raise ValueError(
                "additional_furniture requires a resolved composition."
            )
        result = self.render(
            sky,
            renderer,
            observer=observer,
            style=style,
            layer_options=layer_options,
            boundary_style=boundary_style,
        )
        if legends is not None:
            from wenu.charts.chart_legend_workflow import (
                draw_resolved_chart_legends,
            )

            result = draw_resolved_chart_legends(
                self,
                sky,
                renderer,
                style,
                result,
                resolved_detail,
                legends,
            )
        from wenu.charts.regional import ExportOptions

        options = (
            ExportOptions() if export_options is None else export_options
        )
        if svg_provenance is not None:
            from dataclasses import replace

            options = replace(options, svg_provenance=svg_provenance)
        output = options.save(renderer.ax.figure, path)
        return result, output
