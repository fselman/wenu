"""Single-face polar-planisphere disk geometry."""

from __future__ import annotations

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
from wenu.geometry.viewport import Viewport


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
            limit = 10.0 if pole == "south" else -10.0
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
        options = apply_coordinate_label_anchor(
            options, self.coordinate_label_anchor
        )
        transform = lambda spherical: horizontal_to_equatorial(
            spherical, resolved_observer
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
        return sky.draw_chart(
            projection=projection,
            renderer=renderer,
            observer=resolved_observer,
            viewport=self.viewport,
            layer_options=options,
            project_geometry=lambda spherical: projection.project_geometry(
                transform(spherical)
            ),
        )

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
        output = options.save(renderer.ax.figure, path)
        return result, output
