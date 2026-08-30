"""Production configuration for Galactic Mollweide all-sky charts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

import numpy as np

from wenu.charts.boundaries import (
    EllipticalGridLabelAnchor,
    apply_coordinate_label_anchor,
)
from wenu.charts.constellation_label_placement import (
    apply_visible_constellation_label_anchors,
)
from wenu.coordinate_service import CoordinateService
from wenu.geometry.projected import ProjectedCurve
from wenu.geometry.viewport import Viewport
from wenu.projections.mollweide import MollweideProjection


@dataclass(frozen=True)
class AllSkyChart:
    """A complete-sphere Galactic Mollweide chart."""

    chart_type: ClassVar[str] = "all_sky"
    central_longitude_deg: float = 0.0
    projection_radius: float = 1.0
    flip_ew: bool = True
    boundary_samples: int = 721
    boundary_color: str = "#707070"
    boundary_linewidth: float = 0.8
    outside_mask_constellations: tuple[str, ...] | None = None

    def __post_init__(self):
        values = np.asarray(
            (
                self.central_longitude_deg,
                self.projection_radius,
                self.boundary_linewidth,
            ),
            dtype=float,
        )
        if not np.all(np.isfinite(values)):
            raise ValueError("All-sky chart values must be finite.")
        if self.projection_radius <= 0.0:
            raise ValueError("projection_radius must be positive.")
        if self.boundary_samples < 16:
            raise ValueError("boundary_samples must be at least 16.")
        if self.boundary_linewidth < 0.0:
            raise ValueError("boundary_linewidth cannot be negative.")
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
    def selects_full_sphere(self):
        """Return whether catalogue selection covers the complete sphere."""
        return True

    @property
    def projection(self):
        """Return the coordinate-neutral Mollweide projection."""
        return MollweideProjection(
            central_longitude_deg=self.central_longitude_deg,
            flip_ew=self.flip_ew,
            radius=self.projection_radius,
        )

    @property
    def boundary(self):
        """Return the exact projected map ellipse."""
        angle = np.linspace(0.0, 2.0 * np.pi, self.boundary_samples)
        projection = self.projection
        return ProjectedCurve(
            x=projection.x_limit * np.cos(angle),
            y=projection.y_limit * np.sin(angle),
            closed=True,
            name="all_sky_boundary",
        )

    @property
    def viewport(self):
        projection = self.projection
        return Viewport(
            -projection.x_limit,
            projection.x_limit,
            -projection.y_limit,
            projection.y_limit,
        )

    @property
    def chart_context(self):
        from wenu.charts.context import BoundaryKind, ChartContext

        return ChartContext(
            viewport=self.viewport,
            angular_width_deg=360.0,
            angular_height_deg=180.0,
            tangent_longitude_deg=self.central_longitude_deg,
            tangent_latitude_deg=0.0,
            boundary_kind=BoundaryKind.ARBITRARY,
            clip_boundary=self.boundary,
            visible_solid_angle_sq_deg=(
                4.0 * np.pi * (180.0 / np.pi) ** 2
            ),
            horizon_altitude_deg=-90.0,
        )

    @property
    def coordinate_label_anchor(self):
        return EllipticalGridLabelAnchor(self.boundary)

    def figure_size(self, width_inches=7.0):
        width = float(width_inches)
        if not np.isfinite(width) or width <= 0.0:
            raise ValueError("width_inches must be positive and finite.")
        return width, width / self.viewport.aspect_ratio

    def render(
        self,
        sky,
        renderer,
        *,
        observer=None,
        realization_context=None,
        style=None,
        layer_options=None,
        horizon_mask=False,
    ):
        """Render the complete sphere through the canonical execution core."""
        resolved_observer = (
            getattr(sky, "observer", None) if observer is None else observer
        )
        if resolved_observer is None:
            raise TypeError("all-sky rendering requires an observer.")
        resolved_style = style
        boundary_style_factory = getattr(style, "chart_boundary_style", None)
        converter = getattr(style, "as_publication_style", None)
        if callable(converter):
            resolved_style = converter()
        canvas = getattr(style, "canvas", None)
        sky_color = getattr(canvas, "sky_color", None)
        if sky_color is None:
            sky_color = getattr(resolved_style, "sky_color", None)
        set_background = getattr(renderer, "set_boundary_background", None)
        if callable(set_background) and sky_color is not None:
            set_background(self.boundary, color=sky_color)

        options = (
            {}
            if resolved_style is None
            else resolved_style.layer_options(
                sky, horizon_altitude_deg=-90.0
            )
        )
        if layer_options is not None:
            options.update(layer_options)
        options = apply_coordinate_label_anchor(
            options, self.coordinate_label_anchor
        )
        transform = lambda spherical: CoordinateService().transform_observer_geometry(
            spherical,
            resolved_observer,
            "galactic",
        )
        options = apply_visible_constellation_label_anchors(
            options,
            sky=sky,
            projection=self.projection,
            viewport=self.viewport,
            boundary=self.boundary,
            observer=resolved_observer,
            transform_spherical=transform,
        )

        set_boundary = getattr(renderer, "set_clip_boundary", None)
        if not callable(set_boundary):
            raise TypeError(
                "renderer must provide set_clip_boundary() for an "
                "all-sky chart."
            )
        boundary_style = {
            "edgecolor": self.boundary_color,
            "linewidth": self.boundary_linewidth,
            "facecolor": "none",
        }
        if callable(boundary_style_factory):
            boundary_style.update(boundary_style_factory())
        set_boundary(self.boundary, style=boundary_style)
        set_frame_visible = getattr(renderer, "set_axes_frame_visible", None)
        if callable(set_frame_visible):
            set_frame_visible(False)

        projection = self.projection
        result = sky.draw_chart(
            projection=projection,
            renderer=renderer,
            observer=resolved_observer,
            realization_context=realization_context,
            viewport=self.viewport,
            layer_options=options,
            project_geometry=lambda spherical: projection.project_geometry(
                transform(spherical)
            ),
        )
        if self.outside_mask_constellations is not None or horizon_mask:
            from wenu.charts._masking import draw_composed_outside_mask

            from wenu.charts.styles import resolved_outside_mask_style

            mask_style = resolved_outside_mask_style(style)
            draw_composed_outside_mask(
                sky=sky,
                projection=projection,
                renderer=renderer,
                viewport=self.viewport,
                observer=resolved_observer,
                constellations=self.outside_mask_constellations,
                style=mask_style,
                transform_spherical=transform,
                horizon_mask=horizon_mask,
                boundary=self.boundary,
                complete_sphere=True,
            )
        return result

    def export(
        self,
        sky,
        renderer,
        path,
        *,
        observer=None,
        realization_context=None,
        style=None,
        layer_options=None,
        export_options=None,
        legends=None,
        resolved_detail=None,
        composition=None,
        horizon_mask=False,
        svg_provenance=None,
    ):
        """Render and reproducibly save an all-sky chart."""
        from wenu.charts.regional import ExportOptions

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
                realization_context=realization_context,
                composition=composition,
                layer_options=layer_options,
                export_options=export_options,
                render_options={"horizon_mask": horizon_mask},
                svg_provenance=svg_provenance,
            )

        result = self.render(
            sky,
            renderer,
            observer=observer,
            realization_context=realization_context,
            style=style,
            layer_options=layer_options,
            horizon_mask=horizon_mask,
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
        options = ExportOptions() if export_options is None else export_options
        if svg_provenance is not None:
            from dataclasses import replace

            options = replace(options, svg_provenance=svg_provenance)
        output = options.save(renderer.ax.figure, path)
        return result, output
