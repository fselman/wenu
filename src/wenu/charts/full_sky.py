"""Production configuration and orchestration for full-sky charts."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from wenu.geometry.frame import SphericalFrame
from wenu.geometry.projected import ProjectedCurve
from wenu.geometry.viewport import Viewport
from wenu.projections.stereographic import StereographicProjection
from wenu.rendering.preparation import project_geometry_for_viewport


@dataclass(frozen=True)
class FullSkyChart:
    """A visible-hemisphere chart with an independent tangent point."""

    center_alt_deg: float = 90.0
    center_az_deg: float = 0.0
    horizon_altitude_deg: float = 0.0
    position_angle_deg: float = 0.0
    projection_radius: float = 2.0
    flip_ew: bool = True
    horizon_samples: int = 721
    horizon_color: str = "white"
    horizon_linewidth: float = 0.8

    def __post_init__(self):
        values = np.asarray(
            (
                self.center_alt_deg,
                self.center_az_deg,
                self.horizon_altitude_deg,
                self.position_angle_deg,
                self.projection_radius,
                self.horizon_linewidth,
            ),
            dtype=float,
        )
        if not np.all(np.isfinite(values)):
            raise ValueError("Full-sky chart values must be finite.")
        if not -90.0 <= self.center_alt_deg <= 90.0:
            raise ValueError(
                "center_alt_deg must be between -90 and 90."
            )
        if not -90.0 < self.horizon_altitude_deg < 90.0:
            raise ValueError(
                "horizon_altitude_deg must be between -90 and 90."
            )
        if self.center_alt_deg <= -self.horizon_altitude_deg:
            raise ValueError(
                "The tangent point must keep the visible region away "
                "from the stereographic antipode: center_alt_deg must "
                "be greater than -horizon_altitude_deg."
            )
        if self.projection_radius <= 0.0:
            raise ValueError("projection_radius must be positive.")
        if self.horizon_samples < 16:
            raise ValueError("horizon_samples must be at least 16.")
        if self.horizon_linewidth < 0.0:
            raise ValueError("horizon_linewidth cannot be negative.")

    @property
    def projection(self):
        """Return the configured coordinate-neutral projection."""
        return StereographicProjection(
            radius=self.projection_radius,
            flip_ew=self.flip_ew,
            frame=SphericalFrame(
                pole_lon_deg=self.center_az_deg,
                pole_lat_deg=self.center_alt_deg,
                position_angle_deg=self.position_angle_deg,
            ),
        )

    @property
    def horizon(self) -> ProjectedCurve:
        """Return the observer-horizontal limiting small circle."""
        azimuth = np.linspace(
            0.0,
            360.0,
            self.horizon_samples,
            endpoint=False,
        )
        altitude = np.full_like(
            azimuth,
            self.horizon_altitude_deg,
        )
        x, y = self.projection.project_spherical(azimuth, altitude)
        return ProjectedCurve(
            x=x,
            y=y,
            closed=True,
            name="horizon",
        )

    @property
    def viewport(self) -> Viewport:
        """Return exact bounds of the projected horizon circle."""
        horizon = self.horizon
        finite = horizon.finite
        if np.count_nonzero(finite) < 3:
            raise ValueError(
                "The projected horizon needs three finite samples."
            )
        x = horizon.x[finite]
        y = horizon.y[finite]
        design = np.column_stack((x, y, np.ones_like(x)))
        coefficients, *_ = np.linalg.lstsq(
            design,
            -(x * x + y * y),
            rcond=None,
        )
        center_x = -0.5 * coefficients[0]
        center_y = -0.5 * coefficients[1]
        radius_squared = (
            center_x * center_x
            + center_y * center_y
            - coefficients[2]
        )
        if not np.isfinite(radius_squared) or radius_squared <= 0.0:
            raise ValueError(
                "The projected horizon does not define a finite circle."
            )
        radius = float(np.sqrt(radius_squared))
        return Viewport(
            x_min=float(center_x - radius),
            x_max=float(center_x + radius),
            y_min=float(center_y - radius),
            y_max=float(center_y + radius),
        )

    @property
    def chart_context(self):
        """Return output-neutral geometry for composition."""
        from wenu.charts.context import BoundaryKind, ChartContext

        angular_radius = 90.0 - self.horizon_altitude_deg
        solid_angle_sr = 2.0 * np.pi * (
            1.0 - np.cos(np.radians(angular_radius))
        )
        square_degrees_per_steradian = (180.0 / np.pi) ** 2
        return ChartContext(
            viewport=self.viewport,
            angular_width_deg=2.0 * angular_radius,
            angular_height_deg=2.0 * angular_radius,
            tangent_longitude_deg=self.center_az_deg,
            tangent_latitude_deg=self.center_alt_deg,
            boundary_kind=BoundaryKind.CIRCULAR,
            clip_boundary=self.horizon,
            visible_solid_angle_sq_deg=(
                solid_angle_sr * square_degrees_per_steradian
            ),
        )

    def figure_size(self, width_inches=7.0):
        """Return a figure size matching the projected horizon bounds."""
        width_inches = float(width_inches)
        if not np.isfinite(width_inches) or width_inches <= 0.0:
            raise ValueError(
                "width_inches must be positive and finite."
            )
        return (
            width_inches,
            width_inches / self.viewport.aspect_ratio,
        )

    def render(
        self,
        sky,
        renderer,
        *,
        style=None,
        layer_options=None,
    ):
        """Render the visible hemisphere through ``CelestialSphere``."""
        options = (
            {}
            if style is None
            else style.layer_options(
                sky,
                horizon_altitude_deg=self.horizon_altitude_deg,
            )
        )
        if layer_options is not None:
            options.update(layer_options)

        set_boundary = getattr(renderer, "set_clip_boundary", None)
        if not callable(set_boundary):
            raise TypeError(
                "renderer must provide set_clip_boundary() for a "
                "full-sky chart."
            )
        set_boundary(
            self.horizon,
            style={
                "edgecolor": self.horizon_color,
                "linewidth": self.horizon_linewidth,
                "facecolor": "none",
            },
        )
        projection = self.projection
        viewport = self.viewport
        return sky.draw_chart(
            projection=projection,
            renderer=renderer,
            viewport=viewport,
            layer_options=options,
            project_geometry=lambda spherical: (
                project_geometry_for_viewport(
                    spherical,
                    projection=projection,
                    viewport=viewport,
                )
            ),
        )

    def export(
        self,
        sky,
        renderer,
        path,
        *,
        style=None,
        layer_options=None,
        export_options=None,
    ):
        """Render and reproducibly save a full-sky chart."""
        from wenu.charts.regional import ExportOptions

        result = self.render(
            sky,
            renderer,
            style=style,
            layer_options=layer_options,
        )
        options = (
            ExportOptions()
            if export_options is None
            else export_options
        )
        output = options.save(renderer.ax.figure, path)
        return result, output
