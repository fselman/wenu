"""Production configuration and orchestration for full-sky charts."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from wenu.charts.boundaries import (
    CircularGridLabelAnchor,
    apply_coordinate_label_anchor,
)
from wenu.charts.constellation_label_placement import (
    apply_visible_constellation_label_anchors,
)
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
    outside_mask_constellations: tuple[str, ...] | None = None

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
        if self.outside_mask_constellations is not None:
            names = tuple(
                str(name).strip()
                for name in self.outside_mask_constellations
            )
            if not names or any(not name for name in names):
                raise ValueError(
                    "outside_mask_constellations must contain names."
                )
            object.__setattr__(
                self, "outside_mask_constellations", names
            )

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

    @property
    def coordinate_label_anchor(self):
        """Return the coordinate-grid anchor for the horizon circle."""
        return CircularGridLabelAnchor(self.horizon)

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
        observer=None,
        style=None,
        layer_options=None,
    ):
        """Render the visible hemisphere through ``CelestialSphere``."""
        resolved_style = style
        boundary_style_factory = getattr(
            style,
            "chart_boundary_style",
            None,
        )
        converter = getattr(style, "as_publication_style", None)
        if callable(converter):
            resolved_style = converter()
        canvas = getattr(style, "canvas", None)
        sky_color = getattr(canvas, "sky_color", None)
        if sky_color is None:
            sky_color = getattr(resolved_style, "sky_color", None)
        set_circular_background = getattr(
            renderer, "set_circular_background", None
        )
        if callable(set_circular_background) and sky_color is not None:
            set_circular_background(
                self.horizon,
                color=sky_color,
            )
        options = (
            {}
            if resolved_style is None
            else resolved_style.layer_options(
                sky,
                horizon_altitude_deg=self.horizon_altitude_deg,
            )
        )
        if layer_options is not None:
            options.update(layer_options)
        options = apply_coordinate_label_anchor(
            options,
            self.coordinate_label_anchor,
        )
        options = apply_visible_constellation_label_anchors(
            options,
            sky=sky,
            projection=self.projection,
            viewport=self.viewport,
            boundary=self.horizon,
            observer=observer,
        )

        set_boundary = getattr(renderer, "set_clip_boundary", None)
        if not callable(set_boundary):
            raise TypeError(
                "renderer must provide set_clip_boundary() for a "
                "full-sky chart."
            )
        boundary_style = {
            "edgecolor": self.horizon_color,
            "linewidth": self.horizon_linewidth,
            "facecolor": "none",
        }
        if callable(boundary_style_factory):
            boundary_style.update(boundary_style_factory())
        set_boundary(
            self.horizon,
            style=boundary_style,
        )
        set_frame_visible = getattr(
            renderer, "set_axes_frame_visible", None
        )
        if callable(set_frame_visible):
            set_frame_visible(False)
        projection = self.projection
        viewport = self.viewport
        result = sky.draw_chart(
            projection=projection,
            renderer=renderer,
            observer=observer,
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
        if self.outside_mask_constellations is not None:
            from wenu.charts._masking import (
                draw_constellation_outside_mask,
            )

            mask_style = (
                {
                    "facecolor": "black",
                    "edgecolor": "none",
                    "alpha": 0.35,
                    "zorder": 20.0,
                }
                if style is None
                else resolved_style.outside_mask_style()
            )
            draw_constellation_outside_mask(
                sky=sky,
                projection=projection,
                renderer=renderer,
                viewport=viewport,
                observer=observer,
                constellations=self.outside_mask_constellations,
                style=mask_style,
            )
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
    ):
        """Render and reproducibly save a full-sky chart."""
        from wenu.charts.regional import ExportOptions

        if composition is not None:
            if style is not None or legends is not None or resolved_detail is not None:
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
            )

        result = self.render(
            sky,
            renderer,
            observer=observer,
            style=style,
            layer_options=layer_options,
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
        options = (
            ExportOptions()
            if export_options is None
            else export_options
        )
        output = options.save(renderer.ax.figure, path)
        return result, output
