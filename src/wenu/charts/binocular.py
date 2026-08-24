"""Circular binocular-field chart type."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from wenu.charts.boundaries import (
    CircularLabelAnchor,
    apply_coordinate_label_anchor,
    circular_boundary,
    resolved_circular_boundary_style,
    viewport_from_boundary,
)
from wenu.charts.context import BoundaryKind, ChartContext
from wenu.charts.constellation_label_placement import (
    apply_visible_constellation_label_anchors,
)
from wenu.charts.regional import (
    ExportOptions,
    RegionalChart,
    ResolvedChartOrientation,
)


@dataclass(frozen=True)
class BinocularChart:
    """A circular regional chart representing a binocular field stop."""

    center_alt_deg: float
    center_az_deg: float
    field_diameter_deg: float = 6.5
    position_angle_deg: float = 0.0
    resolved_orientation: ResolvedChartOrientation | None = None
    projection_radius: float = 2.0
    flip_ew: bool = True
    boundary_samples: int = 721
    label_selection: tuple[str, ...] | None = None
    target_ra_deg: float | None = None
    target_dec_deg: float | None = None

    def __post_init__(self):
        values = np.asarray(
            (
                self.center_alt_deg,
                self.center_az_deg,
                self.field_diameter_deg,
                self.position_angle_deg,
                self.projection_radius,
            ),
            dtype=float,
        )
        if not np.all(np.isfinite(values)):
            raise ValueError("Binocular chart values must be finite.")
        if not -90.0 <= self.center_alt_deg <= 90.0:
            raise ValueError("center_alt_deg must be between -90 and 90.")
        if not 0.0 < self.field_diameter_deg < 180.0:
            raise ValueError(
                "field_diameter_deg must be between 0 and 180."
            )
        if self.projection_radius <= 0.0:
            raise ValueError("projection_radius must be positive.")
        if int(self.boundary_samples) < 9:
            raise ValueError("boundary_samples must be at least 9.")
        if (self.target_ra_deg is None) != (self.target_dec_deg is None):
            raise ValueError(
                "target_ra_deg and target_dec_deg must be supplied together."
            )
        if self.target_ra_deg is not None:
            if not np.isfinite((self.target_ra_deg, self.target_dec_deg)).all():
                raise ValueError("Target coordinates must be finite.")
            if not -90.0 <= float(self.target_dec_deg) <= 90.0:
                raise ValueError("target_dec_deg must be between -90 and 90.")

    @classmethod
    def from_coordinate(
        cls,
        observer,
        coordinate,
        *,
        field_diameter_deg=6.5,
        orientation=None,
        position_angle_deg=None,
        boundary_samples=721,
        **kwargs,
    ):
        """Create a binocular chart centered on an Astropy coordinate."""
        regional = RegionalChart.from_coordinate(
            observer,
            coordinate,
            field_width_deg=field_diameter_deg,
            field_height_deg=field_diameter_deg,
            orientation=orientation,
            position_angle_deg=position_angle_deg,
            **kwargs,
        )
        icrs = coordinate.icrs
        return cls(
            center_alt_deg=regional.center_alt_deg,
            center_az_deg=regional.center_az_deg,
            field_diameter_deg=field_diameter_deg,
            position_angle_deg=regional.position_angle_deg,
            resolved_orientation=regional.resolved_orientation,
            projection_radius=regional.projection_radius,
            flip_ew=regional.flip_ew,
            boundary_samples=boundary_samples,
            label_selection=regional.label_selection,
            target_ra_deg=float(icrs.ra.deg),
            target_dec_deg=float(icrs.dec.deg),
        )

    @property
    def regional_chart(self):
        """Return the equivalent square regional chart."""
        return RegionalChart(
            center_alt_deg=self.center_alt_deg,
            center_az_deg=self.center_az_deg,
            field_width_deg=self.field_diameter_deg,
            field_height_deg=self.field_diameter_deg,
            position_angle_deg=self.position_angle_deg,
            resolved_orientation=self.resolved_orientation,
            projection_radius=self.projection_radius,
            flip_ew=self.flip_ew,
            label_selection=self.label_selection,
        )

    @property
    def projection(self):
        return self.regional_chart.projection

    @property
    def field_stop(self):
        radius = self.projection.projected_radius(
            self.field_diameter_deg / 2.0
        )
        return circular_boundary(
            radius,
            samples=self.boundary_samples,
            name="binocular_field_stop",
        )

    @property
    def viewport(self):
        return viewport_from_boundary(self.field_stop)

    @property
    def coordinate_label_anchor(self):
        return CircularLabelAnchor(self.field_stop)

    @property
    def chart_context(self):
        angular_radius = self.field_diameter_deg / 2.0
        solid_angle_sr = 2.0 * np.pi * (
            1.0 - np.cos(np.radians(angular_radius))
        )
        return ChartContext(
            viewport=self.viewport,
            angular_width_deg=self.field_diameter_deg,
            angular_height_deg=self.field_diameter_deg,
            tangent_longitude_deg=self.center_az_deg,
            tangent_latitude_deg=self.center_alt_deg,
            boundary_kind=BoundaryKind.CIRCULAR,
            clip_boundary=self.field_stop,
            visible_solid_angle_sq_deg=(
                solid_angle_sr * (180.0 / np.pi) ** 2
            ),
        )

    def figure_size(self, width_inches=7.0):
        width_inches = float(width_inches)
        if not np.isfinite(width_inches) or width_inches <= 0.0:
            raise ValueError("width_inches must be positive and finite.")
        return width_inches, width_inches

    def render(
        self,
        sky,
        renderer,
        *,
        observer=None,
        style=None,
        layer_options=None,
        boundary_style=None,
        coordinate_label_anchor=None,
        horizon_mask=False,
    ):
        """Render and clip every artist to the circular field stop."""
        if boundary_style is None:
            boundary_style = resolved_circular_boundary_style(style)
        resolved_style = style
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
                self.field_stop,
                color=sky_color,
            )
        options = (
            {}
            if resolved_style is None
            else resolved_style.layer_options(sky)
        )
        if layer_options is not None:
            options.update(layer_options)
        options = apply_coordinate_label_anchor(
            options,
            (
                self.coordinate_label_anchor
                if coordinate_label_anchor is None
                else coordinate_label_anchor
            ),
        )
        options = apply_visible_constellation_label_anchors(
            options,
            sky=sky,
            projection=self.projection,
            viewport=self.viewport,
            boundary=self.field_stop,
            observer=observer,
        )
        renderer.set_clip_boundary(
            self.field_stop,
            style=(
                {"facecolor": "none", "edgecolor": "none"}
                if boundary_style is None
                else dict(boundary_style)
            ),
        )
        set_frame_visible = getattr(
            renderer, "set_axes_frame_visible", None
        )
        if callable(set_frame_visible):
            set_frame_visible(False)
        from wenu.charts.styles import resolved_outside_mask_style

        return self.regional_chart.render(
            sky,
            renderer,
            observer=observer,
            style=None,
            layer_options=options,
            horizon_mask=horizon_mask,
            mask_boundary=self.field_stop,
            mask_style=(
                None
                if not horizon_mask
                else resolved_outside_mask_style(style)
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
        boundary_style=None,
        export_options=None,
        legends=None,
        resolved_detail=None,
        composition=None,
        horizon_mask=False,
    ):
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
                render_options={
                    "boundary_style": boundary_style,
                    "horizon_mask": horizon_mask,
                },
            )
        result = self.render(
            sky,
            renderer,
            observer=observer,
            style=style,
            layer_options=layer_options,
            boundary_style=boundary_style,
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
        options = (
            ExportOptions(transparent=True, facecolor="none")
            if export_options is None
            else export_options
        )
        output = options.save(renderer.ax.figure, path)
        return result, output
