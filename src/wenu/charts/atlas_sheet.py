"""Single-sheet atlas contract, composition, furniture and report service.

Batch planning, worker scheduling and book publication stay with atlas_publication;
request scope and atomic file publication stay with request_generation.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import math
from pathlib import Path

from wenu.atlas_design import AtlasSheetGeometry


def _identity(value, name):
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{name} must be a nonempty trimmed string.")



@dataclass(frozen=True)
class AtlasSheetChart:
    """Native fixed-equatorial adapter over canonical rectangular/polar owners."""

    sheet: AtlasSheetGeometry
    page: object
    label_selection: tuple | None = None
    outside_mask_constellations: tuple | None = None

    @property
    def projection(self):
        return self.sheet.projection

    @property
    def viewport(self):
        return self.sheet.viewport(self.page)

    @property
    def coordinate_label_anchor(self):
        if self.sheet.boundary_kind == 'hemisphere':
            return self.polar_chart.coordinate_label_anchor
        from .boundaries import RectangularLabelAnchor
        return RectangularLabelAnchor()

    @property
    def polar_chart(self):
        from .polar_planisphere import PolarPlanisphereChart
        return PolarPlanisphereChart(
            pole='south' if self.sheet.center_dec_deg < 0 else 'north',
            limiting_declination_deg=0, projection_name='stereographic',
            position_angle_deg=self.sheet.position_angle_deg + math.copysign(
                self.sheet.pole_meridian_ra_deg, self.sheet.center_dec_deg),
            projection_radius=self.sheet.projection_radius, flip_ew=self.sheet.flip_ew,
            reviewed_label_curation=False)

    @property
    def chart_context(self):
        from .context import ChartContext
        if self.sheet.boundary_kind == 'hemisphere':
            return self.polar_chart.chart_context
        return ChartContext(self.viewport, self.sheet.field_width_deg,
            self.sheet.field_height_deg(self.page), self.sheet.center_ra_deg,
            self.sheet.center_dec_deg)

    def render(self, sky, renderer, **options):
        from .regional import RegionalChart
        from wenu.sky.realization import LayerRealizationContext
        context = options.get("realization_context")
        if not isinstance(context, LayerRealizationContext) or not context.is_native_icrs:
            raise ValueError("Atlas sheets require explicit native ICRS realization.")
        if options.get("observer") is not None:
            raise ValueError("Atlas sheets do not admit an observer.")
        if self.sheet.boundary_kind == 'hemisphere':
            return self.polar_chart.render(sky, renderer, **options)
        return RegionalChart.render(self, sky, renderer, **options)



@dataclass(frozen=True)
class AtlasChartPresentation:
    """Independent, closed chart-page input; geometry belongs to the design."""

    style: str = "atlas"
    mode: str = "print"
    dpi: int = 150
    star_magnitude_limit: float = 6.0
    star_size_scale: float = 1.0
    stellar_magnitude_sizing: object | None = None
    layers: tuple = ("stars", "constellation_lines", "constellation_labels",
        "constellation_boundaries", "milky_way", "magellanic_clouds",
        "nonstellar", "galaxies", "open_clusters", "globular_clusters",
        "supernova_remnants", "planetary_nebulae", "equatorial_grid")
    formats: tuple = ("png", "pdf", "svg")
    report_label_scale: float = 3.0
    report_label_family: str = "sans-serif"
    report_label_weight: str = "normal"
    report_label_color: str = "black"
    report_separator_width: float = 0.8
    report_separator_gap_mm: float = 3.0
    magnitude_veil_color: str = "white"
    magnitude_veil_alpha: float = 0.65
    chart_number_box_visible: bool = True
    chart_number_box_location: str = "upper right"
    chart_number_box_facecolor: str = "white"
    chart_number_box_edgecolor: str = "#777777"
    chart_number_box_alpha: float = 0.9
    chart_number_box_padding: float = 0.4
    chart_number_box_borderpad: float = 0.0
    grid_lines_visible: bool = True
    grid_label_fontsize: float = 12.0
    grid_minor_label_scale: float = 0.75
    grid_frame_width_scale: float = 1.5
    grid_ra_step_hours: int = 1
    grid_polar_ra_step_hours: int = 2
    grid_minute_labels_visible: bool = False
    milky_way_color: str = "#87CEFA"
    chart_legend_visible: bool = True
    legend_fontsize: float = 12.0
    messier_label_fontsize: float = 7.0
    grid_dec_label_scale: float = 0.8
    deep_sky_symbol_scale: float = 1.8
    cluster_symbol_scale: float = 1.0
    planetary_nebula_symbol_scale: float = 1.25
    planetary_nebula_color: str = "#24552b"
    planetary_nebula_linewidth: float = 1.1
    cluster_face_color: str = "yellow"
    open_cluster_exclude_infrared_embedded: bool = False
    open_cluster_angular_sizes: bool = True

    def __post_init__(self):
        import math
        _atlas_grid_marks(self)
        from .style_components import EquatorialGridMarks
        EquatorialGridMarks(grid_ra_step_hours=self.grid_polar_ra_step_hours)
        from wenu.sky.native_snapshot import LAYERS
        if self.style not in {"atlas", "cartoon"}:
            raise ValueError("style must be atlas or cartoon.")
        if self.mode not in {"print", "presentation"}:
            raise ValueError("mode must be print or presentation.")
        from .style_components import StellarMagnitudeSizing
        if self.stellar_magnitude_sizing is not None and not isinstance(self.stellar_magnitude_sizing, StellarMagnitudeSizing):
            raise TypeError("stellar_magnitude_sizing must be StellarMagnitudeSizing.")
        if type(self.dpi) is not int or not 36 <= self.dpi <= 1200:
            raise ValueError("dpi must be an integer from 36 to 1200.")
        limit = self.star_magnitude_limit
        if isinstance(limit, bool) or not isinstance(limit, (int, float)) or not math.isfinite(limit) or not -2 <= limit <= 11:
            raise ValueError("star_magnitude_limit must be finite between -2 and 11.")
        if (self.stellar_magnitude_sizing is not None
                and self.stellar_magnitude_sizing.algorithm != "legacy"
                and limit > self.stellar_magnitude_sizing.size_reference_magnitude):
            raise ValueError("Magnitude limit must not exceed the sizing reference.")
        for name in ("star_size_scale", "report_label_scale", "report_separator_width", "report_separator_gap_mm",
                     "grid_label_fontsize", "grid_minor_label_scale", "grid_frame_width_scale", "legend_fontsize", "messier_label_fontsize", "deep_sky_symbol_scale", "cluster_symbol_scale", "planetary_nebula_symbol_scale", "planetary_nebula_linewidth"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and positive.")
        if self.grid_minor_label_scale > 1:
            raise ValueError("grid_minor_label_scale must be at most 1.")
        if type(self.chart_legend_visible) is not bool:
            raise ValueError("chart_legend_visible must be boolean.")
        if type(self.grid_lines_visible) is not bool:
            raise ValueError("grid_lines_visible must be boolean.")
        if type(self.open_cluster_angular_sizes) is not bool:
            raise ValueError("open_cluster_angular_sizes must be boolean.")
        if type(self.open_cluster_exclude_infrared_embedded) is not bool:
            raise ValueError('open_cluster_exclude_infrared_embedded must be boolean.')
        if not math.isfinite(self.star_size_scale * self.star_size_scale):
            raise ValueError("star_size_scale squared must be finite.")
        if not math.isfinite(self.deep_sky_symbol_scale * self.deep_sky_symbol_scale):
            raise ValueError("deep_sky_symbol_scale squared must be finite.")
        cluster_scale = self.deep_sky_symbol_scale * self.cluster_symbol_scale
        if not math.isfinite(cluster_scale * cluster_scale):
            raise ValueError("Cluster symbol area must be finite.")
        from matplotlib.colors import is_color_like
        if not isinstance(self.planetary_nebula_color, str) or not is_color_like(self.planetary_nebula_color):
            raise ValueError("Invalid planetary_nebula_color.")
        pn_scale = self.deep_sky_symbol_scale * self.planetary_nebula_symbol_scale
        if not math.isfinite(pn_scale * pn_scale):
            raise ValueError("Planetary-nebula symbol area must be finite.")
        if not isinstance(self.cluster_face_color, str) or not is_color_like(self.cluster_face_color):
            raise ValueError("Invalid cluster_face_color.")
        _identity(self.report_label_family, "report_label_family")
        if not isinstance(self.report_label_weight, str) or self.report_label_weight not in {"normal", "bold", "light", "medium", "semibold", "heavy", "black"}:
            raise ValueError("Invalid report_label_weight.")
        from matplotlib.colors import is_color_like
        if not isinstance(self.milky_way_color, str) or not is_color_like(self.milky_way_color):
            raise ValueError("Invalid milky_way_color.")
        if not isinstance(self.report_label_color, str) or not is_color_like(self.report_label_color):
            raise ValueError("Invalid report_label_color.")
        if type(self.chart_number_box_visible) is not bool:
            raise ValueError("chart_number_box_visible must be boolean.")
        if not isinstance(self.chart_number_box_location, str) or self.chart_number_box_location not in {
                "upper right", "upper left", "lower right", "lower left"}:
            raise ValueError("Invalid chart_number_box_location.")
        for name in ("chart_number_box_facecolor", "chart_number_box_edgecolor", "magnitude_veil_color"):
            if not isinstance(getattr(self, name), str) or not is_color_like(getattr(self, name)):
                raise ValueError(f"Invalid {name}.")
        for name in ("chart_number_box_alpha", "chart_number_box_padding", "chart_number_box_borderpad", "magnitude_veil_alpha"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError(f"Invalid {name}.")
        if self.magnitude_veil_alpha > 1:
            raise ValueError("magnitude_veil_alpha must be at most 1.")
        if self.chart_number_box_alpha > 1:
            raise ValueError("chart_number_box_alpha must be at most 1.")
        for name, allowed in (("layers", set(LAYERS)), ("formats", {"png", "pdf", "svg"})):
            values = getattr(self, name)
            if not isinstance(values, (list, tuple)) or not values or any(not isinstance(v, str) for v in values) or len(set(values)) != len(values) or not set(values) <= allowed:
                raise ValueError(f"Invalid or duplicate {name}.")
            object.__setattr__(self, name, tuple(values))
        if "pdf" not in self.formats:
            raise ValueError("pdf is required for ordered atlas assembly.")

    @classmethod
    def from_dict(cls, data):
        required = {"schema_version", "document_kind"}
        if not isinstance(data, dict) or not required <= data.keys() or data.keys() - required - set(cls.__dataclass_fields__):
            raise ValueError("Unknown or missing atlas chart presentation keys.")
        if type(data["schema_version"]) is not int or data["schema_version"] != 1 or data["document_kind"] != "wenu-atlas-chart-presentation":
            raise ValueError("Unsupported atlas chart presentation schema/kind.")
        values = {k: v for k, v in data.items() if k not in required}
        if isinstance(values.get("stellar_magnitude_sizing"), dict):
            from .style_components import StellarMagnitudeSizing
            values["stellar_magnitude_sizing"] = StellarMagnitudeSizing(**values["stellar_magnitude_sizing"])
        return cls(**values)



@dataclass(frozen=True)
class AtlasSheetChartRequest:
    """Validated fixed-ICRS sheet input for the shared chart execution owner."""

    sheet: object
    page: object
    presentation: object
    output_dir: object

    def __post_init__(self):
        from pathlib import Path
        from wenu.atlas_design import AtlasSheetGeometry, AtlasPageGeometry
        if not isinstance(self.sheet, AtlasSheetGeometry) or not isinstance(self.page, AtlasPageGeometry):
            raise TypeError("Atlas sheet requests require validated sheet/page geometry.")
        if not isinstance(self.presentation, AtlasChartPresentation):
            raise TypeError("Atlas sheet requests require AtlasChartPresentation.")
        object.__setattr__(self, "output_dir", Path(self.output_dir))



def _atlas_report_data(chart, sky, composition, rendering):
    """Describe the report template from the existing rendered star geometry."""
    from dataclasses import asdict
    import math
    from .legend_geometry import rendered_star_geometry
    from .magnitude_legend import visible_star_statistics, visible_star_mask
    page = chart.page
    sky_area_mm2 = page.useful_width_mm * page.useful_height_mm
    renderer = getattr(rendering, "renderer", None)
    sky_frame = None
    if renderer is not None:
        renderer.ax.apply_aspect()
        box = renderer.ax.get_window_extent()
        scale = 25.4 / renderer.ax.figure.dpi
        sky_frame = dict(x=box.x0 * scale, y=box.y0 * scale,
                         width=box.width * scale, height=box.height * scale)
        sky_area_mm2 = sky_frame["width"] * sky_frame["height"]
    if chart.sheet.boundary_kind == 'hemisphere':
        sky_area_mm2 *= math.pi / 4
    statistics = None
    reference_range = None
    budget = None
    if "stars" in composition.detail.enabled_layers:
        stars = rendered_star_geometry(rendering, sky=sky)
        statistics = visible_star_statistics(stars.spherical, stars.projected,
            stars.viewport, effective_limit=composition.detail.star_magnitude_limit)
        if statistics.has_visible_stars:
            # The first reference must be at least as bright as every plotted star.
            reference_range = (math.floor(statistics.brightest_magnitude),
                               math.ceil(statistics.faintest_magnitude))
    from .stellar_sizing_report import resolved_sizing_record, magnitude_area_budget
    sizing_record = resolved_sizing_record(composition.style.stars, composition.detail.star_magnitude_limit)
    if statistics is not None and not sizing_record["draw_bright_symbols"]:
        import numpy as np
        mask = visible_star_mask(stars.spherical, stars.projected, stars.viewport,
                                effective_limit=composition.detail.star_magnitude_limit)
        budget = magnitude_area_budget(np.asarray(stars.spherical.metadata["magnitude"])[mask],
            sizing_record, sky_area_mm2)
    return dict(schema_version=1, document_kind="wenu-atlas-chart-report",
        stellar_sizing=sizing_record, stellar_area_budget=budget,
        chart_number=chart.sheet.number, sheet_id=chart.sheet.sheet_id,
        center=dict(coordinate_system="ICRS", ra_deg=chart.sheet.center_ra_deg,
                    dec_deg=chart.sheet.center_dec_deg,
                    ra_defined=abs(chart.sheet.center_dec_deg) != 90,
                    pole_meridian_ra_deg=chart.sheet.pole_meridian_ra_deg),
        page=dict(width_mm=page.width_mm, height_mm=page.height_mm),
        layout=dict(units="mm", origin="bottom-left",
            chart_sky_frame=sky_frame,
            central_scale_mm_per_degree=(None if sky_frame is None else
                sky_frame['width'] / chart.viewport.width * chart.sheet.projection_radius * math.pi / 360),
            frame=dict(x=page.outer_mm, y=page.bottom_mm,
                width=page.useful_width_mm, height=page.useful_height_mm),
            report=dict(x=page.outer_mm + 4, y=page.bottom_mm + 4,
                width=page.useful_width_mm * 0.68 - 8,
                height=page.useful_height_mm - 8),
            legends=dict(x=page.outer_mm + page.useful_width_mm * 0.68,
                y=page.bottom_mm + 4, width=page.useful_width_mm * 0.32 - 4,
                height=page.useful_height_mm - 8)),
        stars=dict(statistics=None if statistics is None else asdict(statistics),
                   reference_range=reference_range),
        report=dict(status="reserved", sections=[], inventory_status="not_generated"))



def _atlas_full_magnitude_range(composition, data):
    """Full atlas reference scale, widened for any plotted exceptional star."""
    import math
    sizing = getattr(composition.style.stars, 'magnitude_sizing', None)
    end = (sizing.size_reference_magnitude if sizing is not None and
           sizing.algorithm != 'legacy' else max(8, composition.detail.star_magnitude_limit))
    visible = data['stars']['reference_range']
    return (min(-2, visible[0]) if visible else -2,
            max(math.ceil(end), visible[1]) if visible else math.ceil(end))



def _render_atlas_report(chart, sky, composition, rendering, directory,
                         formats=("png", "pdf", "svg"), presentation=None):
    """Reserved left-hand page with canonical legends from the existing render."""
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from .automatic_legends import draw_automatic_chart_legends
    from .legend_plan import ChartLegendPlan, LegendPlacement
    from .regional import ExportOptions
    from astropy.coordinates import Angle
    import astropy.units as u
    import json
    presentation = AtlasChartPresentation() if presentation is None else presentation
    data = _atlas_report_data(chart, sky, composition, rendering)
    page = chart.page
    # Measure physical layout without a GUI window rounding the paper to pixels.
    figure = Figure(figsize=(page.width_mm / 25.4, page.height_mm / 25.4))
    FigureCanvasAgg(figure)
    left = page.outer_mm / page.width_mm
    bottom = page.bottom_mm / page.height_mm
    width = page.useful_width_mm / page.width_mm
    height = page.useful_height_mm / page.height_mm
    frame = figure.add_axes((left, bottom, width, height))
    frame.set_xticks([])
    frame.set_yticks([])
    frame.set_gid(f"chart-{chart.sheet.number:02d}-report-frame")
    # Reserve the wider column for later object reports; keep the key by the fold.
    box = data["layout"]["legends"]
    ax = figure.add_axes((box["x"] / page.width_mm, box["y"] / page.height_mm,
                         box["width"] / page.width_mm, box["height"] / page.height_mm))
    ax.set_axis_off()
    figure.text(left, 1 - page.top_mm / (2 * page.height_mm),
        f"Chart {chart.sheet.number} — Object report", va="center", fontsize=10)
    report = data["layout"]["report"]
    figure.text(report["x"] / page.width_mm,
        (report["y"] + report["height"]) / page.height_mm,
        "Reserved for the object report", va="top", fontsize=10, color="0.45")
    try:
        ra = Angle(chart.sheet.center_ra_deg * u.deg).to_string(
            unit=u.hourangle, sep="hms", precision=0, pad=True)
        dec = Angle(chart.sheet.center_dec_deg * u.deg).to_string(
            unit=u.deg, sep="dms", precision=0, pad=True, alwayssign=True)
        title = f"Centre: ICRS\nRA {ra}\nDec {dec}"
        if not data["center"]["ra_defined"]:
            meridian = Angle(chart.sheet.pole_meridian_ra_deg * u.deg).to_string(
                unit=u.hourangle, sep="hms", precision=0, pad=True)
            title = ("Centre: ICRS\nRA undefined (pole)"
                     f"\nDec {dec}\nMeridian {meridian}")
        plan = ChartLegendPlan("regional",
            LegendPlacement(location="upper right"),
            LegendPlacement(enabled="stars" in composition.detail.enabled_layers,
                location="lower right"))
        report_style = replace(composition.style, legend=replace(composition.style.legend,
            fontsize=presentation.legend_fontsize, title_fontsize=presentation.legend_fontsize))
        if not getattr(report_style.legend, "visible", True):
            report_style = replace(report_style,
                legend=replace(report_style.legend, visible=True, frame=True))
        legends = draw_automatic_chart_legends(ax, chart, sky, report_style,
            rendering, resolved_detail=composition.detail, plan=plan,
            include_context=True, object_title=title,
            object_marker_scale=presentation.deep_sky_symbol_scale,
            stellar_title="Star magnitude" + (f" ({data['stars']['statistics']['visible_count']:,})"
                if data['stars']['statistics'] is not None else ""),
            stellar_reference_range=_atlas_full_magnitude_range(composition, data),
            stellar_report_range=True, stellar_veil_color=presentation.magnitude_veil_color,
            stellar_veil_alpha=presentation.magnitude_veil_alpha)
        stellar_result = getattr(legends.legends, 'stars', None)
        if stellar_result is not None and stellar_result.scale is not None:
            from dataclasses import asdict
            data['stars']['legend_entries'] = [asdict(entry) for entry in stellar_result.scale.entries]
            data['stars']['interval_policy'] = '[m,m+1); counts are chart appearances, not discrete rendered sizes'
            data['stars']['reference_policy'] = 'Symbol evaluated at bright interval bound m; star diameters remain continuous'

        from .legend import add_legend_heading
        heading, separator = add_legend_heading(legends.legends.objects,
            f"Chart {chart.sheet.number}",
            fontsize=composition.style.legend.title_fontsize * presentation.report_label_scale,
            family=presentation.report_label_family, weight=presentation.report_label_weight,
            color=presentation.report_label_color,
            separator_width=presentation.report_separator_width,
            gap_mm=presentation.report_separator_gap_mm,
            gid=f"chart-{chart.sheet.number:02d}-report")
        for artist in legends.artists:
            artist.borderaxespad = 0
        # Detect legend overflow rather than silently cropping it into the report.
        figure.canvas.draw()
        renderer = figure.canvas.get_renderer()
        bounds = ax.get_window_extent(renderer)
        extents = [artist.get_window_extent(renderer) for artist in legends.artists]
        for name, artist in (("heading", heading), ("separator", separator)):
            extent = artist.get_window_extent(renderer)
            factor = 25.4 / figure.dpi
            data["layout"][name] = dict(x=extent.x0 * factor, y=extent.y0 * factor,
                width=extent.width * factor, height=extent.height * factor)
        for extent in extents:
            if (extent.x0 < bounds.x0 - 1 or extent.x1 > bounds.x1 + 1
                    or extent.y0 < bounds.y0 - 1 or extent.y1 > bounds.y1 + 1):
                raise ValueError("Legends do not fit the facing-page column.")
        if len(extents) == 2 and extents[0].overlaps(extents[1]):
            raise ValueError("Facing-page legends overlap.")
        stem = f"chart-{chart.sheet.number:02d}_report"
        export = ExportOptions(dpi=composition.mode.dpi, bbox_inches=None)
        for suffix in formats:
            export.save(figure, Path(directory) / f"{stem}.{suffix}")
        (Path(directory) / f"{stem}_data.json").write_text(
            json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    finally:
        plt.close(figure)



def _draw_atlas_chart_number(ax, number, style, presentation):
    """Place the chart number inside the selected frame corner."""
    if presentation.chart_number_box_visible:
        from matplotlib.offsetbox import AnchoredText
        number_box = AnchoredText(str(number),
            loc=presentation.chart_number_box_location, frameon=True,
            pad=presentation.chart_number_box_padding, borderpad=presentation.chart_number_box_borderpad,
            prop=dict(size=style.legend.title_fontsize * presentation.report_label_scale,
                family=presentation.report_label_family, weight=presentation.report_label_weight,
                color=presentation.report_label_color))
        number_box.patch.set_facecolor(presentation.chart_number_box_facecolor)
        number_box.patch.set_edgecolor(presentation.chart_number_box_edgecolor)
        number_box.patch.set_alpha(presentation.chart_number_box_alpha)
        number_box.set_gid(f"chart-{number:02d}-number-box")
        number_box.set_zorder(200)
        ax.add_artist(number_box)
        return number_box
    return None



def _draw_atlas_magnitude_scale(*, chart, sky, renderer, composition, rendering, presentation=None):
    """Minimal in-frame scale through the existing rendered-legend owner."""
    if abs(chart.sheet.center_dec_deg) == 90:
        _draw_polar_declination_labels(chart, renderer, presentation or AtlasChartPresentation(), rendering)
    presentation = AtlasChartPresentation() if presentation is None else presentation
    if not presentation.chart_legend_visible or 'stars' not in composition.detail.enabled_layers:
        return None
    from .automatic_legends import draw_automatic_chart_legends
    from .legend_plan import ChartLegendPlan, LegendPlacement
    data = _atlas_report_data(chart, sky, composition, rendering)
    style = replace(composition.style, legend=replace(composition.style.legend,
        fontsize=presentation.legend_fontsize, title_fontsize=presentation.legend_fontsize))
    legends = draw_automatic_chart_legends(renderer.ax, chart, sky, style,
        rendering, resolved_detail=composition.detail,
        plan=ChartLegendPlan('regional', LegendPlacement(enabled=False),
                             LegendPlacement(location='lower right')),
        include_context=False, stellar_reference_range=data['stars']['reference_range'])
    from types import SimpleNamespace
    from wenu.chart_document import assign_furniture_semantics
    assign_furniture_semantics(renderer, SimpleNamespace(legends=legends))
    return legends



def _atlas_grid_marks(presentation):
    from .style_components import EquatorialGridMarks
    return EquatorialGridMarks(**{name: getattr(presentation, name)
        for name in EquatorialGridMarks.__dataclass_fields__})



def _atlas_tick_options(name, *, minor_scale):
    from .request_grids import equatorial_grid_tick_options
    return equatorial_grid_tick_options(name, minor_scale=minor_scale)



def _atlas_grid_options(chart, presentation):
    from .request_grids import equatorial_grid_mark_options
    marks = replace(_atlas_grid_marks(presentation), grid_ra_step_hours=
        presentation.grid_polar_ra_step_hours if abs(chart.sheet.center_dec_deg) == 90 else presentation.grid_ra_step_hours)
    return equatorial_grid_mark_options(chart, marks)



def _atlas_frame_widths(style, presentation, *, circular=False):
    allowance = 2 * (style.canvas.grid_label_band_padding_points + style.canvas.grid_label_band_linewidth / 2)
    # A Dec string lies along its projected parallel, rather than along the
    # vertical edge. Budget its worst rotated extent once from the font.
    from matplotlib.backends.backend_agg import RendererAgg
    from matplotlib.font_manager import FontProperties
    font = FontProperties(size=presentation.grid_label_fontsize * presentation.grid_dec_label_scale)
    measure = RendererAgg(1, 1, 72)
    extent = max(math.hypot(*measure.get_text_width_height_descent(f'{value:+g}°', font, ismath=False)[:2])
                 for value in range(-80, 81, 10))
    if circular:
        # Radial RA labels rotate around the rim. Their display bounding boxes
        # require at most width + height in the radial direction, once per atlas.
        ra_font = FontProperties(size=presentation.grid_label_fontsize)
        ra_extent = max(sum(measure.get_text_width_height_descent(f'{hour}ʰ', ra_font, ismath=False)[:2])
                        for hour in range(24))
        thickness = (max(extent, ra_extent) + allowance) * presentation.grid_frame_width_scale
        return thickness, thickness
    return ((presentation.grid_label_fontsize + allowance) * presentation.grid_frame_width_scale,
            (extent + allowance) * presentation.grid_frame_width_scale)



def _draw_polar_declination_labels(chart, renderer, presentation, rendering):
    """Interior Dec text on the actual grid meridian nearest page vertical."""
    if 'equatorial_grid' not in presentation.layers or getattr(renderer, '_grid_label_band', None) is None:
        return
    import numpy as np
    pole = chart.sheet.center_dec_deg
    declination = pole - math.copysign(10, pole)
    ras = np.arange(0, 360, 15. * presentation.grid_polar_ra_step_hours)
    x, y = chart.projection.project_spherical(ras, np.full(len(ras), declination))
    candidates = np.flatnonzero(y > 0)
    chosen = min(candidates, key=lambda i: (round(abs(x[i]) / abs(y[i]), 12), ras[i]))
    ra = ras[chosen]
    from wenu.geometry.projected import ProjectedPoints
    decs = np.arange(-80, 81, 10.)
    x, y = chart.projection.project_spherical(np.full(len(decs), ra), decs)
    view = chart.viewport
    from wenu.sky.semantic_identity import semantic_layer_identity
    grid_layer = next(record.layer for record in rendering.layers
        if getattr(record.layer, 'coordinate_system', None) == 'equatorial')
    identity = semantic_layer_identity(grid_layer)
    keep = np.isfinite(x) & np.isfinite(y) & (x > view.x_min) & (x < view.x_max) & (y > view.y_min) & (y < view.y_max)
    for px, py, dec in zip(x[keep], y[keep], decs[keep]):
        tangent = chart.projection.project_spherical(np.array([ra-.01, ra+.01]), np.array([dec, dec]))
        direction = np.diff(renderer.ax.transData.transform(np.column_stack(tangent)), axis=0)[0]
        angle = (np.degrees(np.arctan2(direction[1], direction[0])) + 90) % 180 - 90
        artists = renderer.draw(ProjectedPoints(np.array([px]), np.array([py]), names=(f'{dec:+g}°',)),
            draw_markers=False, draw_labels=True, label_offset=(0, 0),
            label_style=dict(fontsize=presentation.grid_label_fontsize * presentation.grid_dec_label_scale,
                color='black', rotation=angle, ha='center', va='center'))
        for artist in artists:
            artist._wenu_semantic_component = 'labels'
            artist.set_gid(f'atlas-polar-dec-{int(dec)}')
            artist._wenu_polar_grid_anchor = (float(px), float(py), float(ra))
            from matplotlib.transforms import ScaledTranslation
            centre = renderer.ax.transData.transform((0, 0))
            direction = centre - renderer.ax.transData.transform((px, py))
            direction /= np.linalg.norm(direction)
            bounds = renderer.ax.get_window_extent()
            for _ in range(3):
                box = artist.get_window_extent(renderer.ax.figure.canvas.get_renderer())
                if bounds.contains(box.x0, box.y0) and bounds.contains(box.x1, box.y1):
                    break
                distance = max(bounds.x0-box.x0, box.x1-bounds.x1,
                               bounds.y0-box.y0, box.y1-bounds.y1, 0) + 1
                shift = direction * distance / renderer.ax.figure.dpi
                artist.set_transform(artist.get_transform() + ScaledTranslation(
                    *shift, renderer.ax.figure.dpi_scale_trans))
        renderer.assign_semantic_identity(artists, identity)



def _atlas_grid_layout(page, style, presentation, *, circular=False):
    horizontal, vertical = _atlas_frame_widths(style, presentation, circular=circular)
    horizontal, vertical = horizontal * 25.4 / 72, vertical * 25.4 / 72
    available_width = page.useful_width_mm - 2 * vertical
    available_height = page.useful_height_mm - 2 * horizontal
    width = min(available_width, available_height * page.aspect_ratio)
    height = width / page.aspect_ratio
    if width <= 0 or height <= 0:
        raise ValueError('Coordinate frame does not fit the useful page.')
    bounds = ((page.inner_mm + (page.useful_width_mm-width)/2)/page.width_mm,
              (page.bottom_mm + (page.useful_height_mm-height)/2)/page.height_mm,
              width/page.width_mm, height/page.height_mm)
    return bounds, style



def render_atlas_sheet(request, sky):
    """Render a validated native sheet and return one ChartExportResult.

    The result owns its first output plus all other format/report paths in
    report_outputs. The request executor owns scope, staging and publication;
    this service renders into the caller-provided directory without publishing.
    """
    if not isinstance(request, AtlasSheetChartRequest):
        raise TypeError("request must be AtlasSheetChartRequest.")
    if sky is None or getattr(sky, "observer", None) is not None:
        raise ValueError("Atlas sheets require an observer-free prepared sky.")
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from pathlib import Path
    from .composition import compose_chart
    from functools import partial
    from .style_overrides import ChartStyleOverrides
    from .detail import DetailOverrides
    from .export_workflow import export_composed_chart
    from .modes import PrintMode, PresentationMode
    from .regional import ExportOptions
    from wenu.rendering.matplotlib import MatplotlibRenderer
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    sheet, page, presentation, directory = request.sheet, request.page, request.presentation, request.output_dir
    chart = AtlasSheetChart(sheet, page)
    composition = compose_chart(chart, style=presentation.style,
        style_overrides=ChartStyleOverrides(star_size_scale=presentation.star_size_scale,
            stellar_magnitude_sizing=presentation.stellar_magnitude_sizing),
        mode=(PrintMode if presentation.mode == "print" else PresentationMode)(width_inches=page.width_mm / 25.4,
            height_inches=page.height_mm / 25.4, dpi=presentation.dpi),
        detail_overrides=DetailOverrides(
            star_magnitude_limit=presentation.star_magnitude_limit,
            enabled_layers=frozenset("nonstellar_objects" if name == "nonstellar" else name
                for name in presentation.layers),
            constellation_star_mode="none"))
    composition = replace(composition, style=replace(composition.style,
        isophotes=replace(composition.style.isophotes,
            milky_way_color=presentation.milky_way_color,
            lmc_color=presentation.milky_way_color, smc_color=presentation.milky_way_color)))
    deep = composition.style.deep_sky
    area_scale = presentation.deep_sky_symbol_scale ** 2
    cluster_area_scale = area_scale * presentation.cluster_symbol_scale ** 2
    composition = replace(composition, style=replace(composition.style,
        deep_sky=replace(deep,
            open_cluster_symbol_name="cluster_circle", open_cluster_color="black",
            open_cluster_face_color=presentation.cluster_face_color,
            open_cluster_diameter_scale=presentation.cluster_symbol_scale,
            open_cluster_symbol_size=deep.open_cluster_symbol_size * cluster_area_scale,
            globular_cluster_symbol_name="globular_cluster", globular_cluster_color="black",
            globular_cluster_face_color=presentation.cluster_face_color,
            globular_cluster_symbol_size=deep.open_cluster_symbol_size * cluster_area_scale,
            planetary_nebula_symbol_size=deep.planetary_nebula_symbol_size * area_scale * presentation.planetary_nebula_symbol_scale ** 2,
            planetary_nebula_color=presentation.planetary_nebula_color,
            planetary_nebula_linewidth=presentation.planetary_nebula_linewidth,
            planetary_nebula_alpha=1.0)))
    circular = sheet.boundary_kind == 'hemisphere'
    axes_bounds, grid_style = _atlas_grid_layout(page, composition.style, presentation,
                                               circular=circular)
    grid_options = {}
    if 'open_clusters' in presentation.layers:
        grid_options['open_clusters'] = dict(geometry=dict(
            exclude_infrared_embedded=presentation.open_cluster_exclude_infrared_embedded))
        if presentation.open_cluster_angular_sizes:
            import math
            grid_options['open_clusters']['render'] = dict(
                point_diameter_metadata_key="apparent_diameter_arcmin",
                point_diameter_scale=sheet.projection_radius * math.pi / 21600 * presentation.cluster_symbol_scale)

    if "supernova_remnants" in presentation.layers:
        grid_options["supernova_remnants"] = dict(
            render=dict(curve_size_scale=presentation.deep_sky_symbol_scale))
    if "nonstellar" in presentation.layers:
        grid_options["nonstellar"] = dict(geometry=dict(labels_only=True),
            render=dict(draw_markers=False, draw_labels=True,
                label_style=dict(fontsize=presentation.messier_label_fontsize, color="black", alpha=1.0)))
    if "equatorial_grid" in presentation.layers:
        composition = replace(composition, style=grid_style)
        grid_options.update(_atlas_grid_options(chart, presentation))
    # Keep the existing 100-dpi layout metrics independent of GUI/Retina scaling.
    # Raster export resolution remains presentation.dpi; no global backend change.
    figure = Figure(figsize=(page.width_mm / 25.4, page.height_mm / 25.4), dpi=100)
    FigureCanvasAgg(figure)
    ax = figure.add_axes(axes_bounds)
    ax.set_xticks([])
    ax.set_yticks([])
    _draw_atlas_chart_number(ax, sheet.number, composition.style, presentation)
    try:
        renderer = MatplotlibRenderer(ax)
        horizontal, vertical = _atlas_frame_widths(composition.style, presentation,
                                                  circular=circular)
        renderer.configure_grid_label_frame(horizontal_points=horizontal,
            vertical_points=vertical, polar=abs(sheet.center_dec_deg) == 90)
        first = presentation.formats[0]
        result = export_composed_chart(chart, sky, renderer,
            Path(directory) / f"chart-{sheet.number:02d}.{first}",
            composition=composition,
            layer_options=grid_options,
            realization_context=LayerRealizationContext(NATIVE_ICRS_SPEC),
            export_options=ExportOptions(dpi=presentation.dpi, bbox_inches=None),
            additional_furniture=partial(_draw_atlas_magnitude_scale, presentation=presentation))
        for suffix in presentation.formats[1:]:
            result.export_options.save(figure, Path(directory) / f"chart-{sheet.number:02d}.{suffix}")
        _render_atlas_report(chart, sky, composition, result.rendering, directory,
                             formats=presentation.formats, presentation=presentation)
        other_outputs = tuple(Path(directory) / f"chart-{sheet.number:02d}.{suffix}"
            for suffix in presentation.formats[1:])
        report_outputs = tuple(Path(directory) / f"chart-{sheet.number:02d}_report.{suffix}"
            for suffix in presentation.formats) + (Path(directory) / f"chart-{sheet.number:02d}_report_data.json",)
        return replace(result, report_outputs=(*other_outputs, *report_outputs))
    except Exception as exc:
        raise RuntimeError(f"Chart {sheet.number} failed: {exc}") from exc
    finally:
        plt.close(figure)

