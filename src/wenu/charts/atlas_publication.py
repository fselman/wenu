"""Design-bound atlas planning and canonical chart-page publication."""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import math
import re
from pathlib import Path

from wenu.atlas_design import AtlasBandTiling, AtlasSheetGeometry, select_atlas_sheets


def _positive_integer(value, name):
    if type(value) is not int or value < 1:
        raise ValueError(f"{name} must be a positive integer.")


def _identity(value, name):
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{name} must be a nonempty trimmed string.")


@dataclass(frozen=True)
class AtlasPublicationBatchRequest:
    """Closed version-1 planning input for a later publication invocation."""

    publication_id: str
    revision: int
    design_id: str
    design_revision: int
    design_sha256: str
    charts: str
    jobs: int = 2

    def __post_init__(self):
        for name in ("publication_id", "design_id"):
            _identity(getattr(self, name), name)
        for name in ("revision", "design_revision", "jobs"):
            _positive_integer(getattr(self, name), name)
        if not isinstance(self.design_sha256, str) or not re.fullmatch(
                r"[0-9a-f]{64}", self.design_sha256):
            raise ValueError("design_sha256 must be a lowercase SHA-256 digest.")
        if not isinstance(self.charts, str) or not self.charts.strip():
            raise ValueError("charts must be a nonempty selector string.")

    @classmethod
    def from_dict(cls, data):
        required = {"schema_version", "document_kind", "publication_id",
                    "revision", "design_id", "design_revision", "design_sha256",
                    "charts"}
        if not isinstance(data, dict) or not required <= data.keys() or (
                data.keys() - required - {"jobs"}):
            raise ValueError("Invalid or unknown publication batch planning keys.")
        if type(data["schema_version"]) is not int or data["schema_version"] != 1:
            raise ValueError("Unsupported publication batch planning schema.")
        if data["document_kind"] != "wenu-atlas-publication-batch-request":
            raise ValueError("Unsupported publication batch planning kind.")
        return cls(**{name: data[name] for name in cls.__dataclass_fields__
                      if name in data})

    def resolve(self, design_bytes, *, charts=None, jobs=None):
        """Bind exact input bytes and resolve overrides before any sky loading.

        The caller reads a design once. Hash its original bytes, not a
        reserialization; whitespace changes therefore require a new binding.
        """
        if not isinstance(design_bytes, bytes):
            raise TypeError("design_bytes must be bytes.")
        digest = hashlib.sha256(design_bytes).hexdigest()
        if digest != self.design_sha256:
            raise ValueError("Design bytes do not match design_sha256.")
        requested_jobs = self.jobs if jobs is None else jobs
        _positive_integer(requested_jobs, "jobs")
        atlas = AtlasBandTiling.from_json(design_bytes.decode("utf-8"))
        if (atlas.geometry.design_id, atlas.geometry.revision) != (
                self.design_id, self.design_revision):
            raise ValueError("Design identity/revision does not match the request.")
        selector = self.charts if charts is None else charts
        sheets = select_atlas_sheets(atlas, selector)
        return AtlasPublicationBatchPlan(
            self, atlas, sheets, selector, requested_jobs)


@dataclass(frozen=True)
class AtlasPublicationBatchPlan:
    """Resolved sheets and worker budget, not an executed or complete atlas."""

    request: AtlasPublicationBatchRequest
    atlas: AtlasBandTiling
    sheets: tuple[AtlasSheetGeometry, ...]
    charts: str
    jobs: int

    def __post_init__(self):
        if not isinstance(self.request, AtlasPublicationBatchRequest):
            raise TypeError("request must be an AtlasPublicationBatchRequest.")
        _positive_integer(self.jobs, "jobs")
        selected = select_atlas_sheets(self.atlas, self.charts)
        if tuple(self.sheets) != selected:
            raise ValueError("Plan sheets disagree with its effective selector.")
        if (self.atlas.geometry.design_id, self.atlas.geometry.revision) != (
                self.request.design_id, self.request.design_revision):
            raise ValueError("Plan design identity disagrees with its request.")
        object.__setattr__(self, "sheets", selected)

    @property
    def worker_count(self):
        return min(self.jobs, len(self.sheets))

    @property
    def chart_numbers(self):
        return tuple(sheet.number for sheet in self.sheets)


@dataclass(frozen=True)
class AtlasSheetChart:
    """Native fixed-equatorial adapter over the canonical rectangular renderer."""

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
        from .boundaries import RectangularLabelAnchor
        return RectangularLabelAnchor()

    @property
    def chart_context(self):
        from .context import ChartContext
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
    legend_fontsize: float = 12.0
    messier_label_fontsize: float = 7.0
    grid_dec_label_scale: float = 0.8
    deep_sky_symbol_scale: float = 1.8
    cluster_face_color: str = "yellow"

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
                     "grid_label_fontsize", "grid_minor_label_scale", "grid_frame_width_scale", "legend_fontsize", "messier_label_fontsize", "deep_sky_symbol_scale"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and positive.")
        if self.grid_minor_label_scale > 1:
            raise ValueError("grid_minor_label_scale must be at most 1.")
        if type(self.grid_lines_visible) is not bool:
            raise ValueError("grid_lines_visible must be boolean.")
        if not math.isfinite(self.star_size_scale * self.star_size_scale):
            raise ValueError("star_size_scale squared must be finite.")
        if not math.isfinite(self.deep_sky_symbol_scale * self.deep_sky_symbol_scale):
            raise ValueError("deep_sky_symbol_scale squared must be finite.")
        from matplotlib.colors import is_color_like
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


_WORKER_SKY = None
_WORKER_CHART_COMMAND = None


def _initialize_atlas_worker(directory, digest, chart_command=None):
    import matplotlib
    matplotlib.use("Agg", force=True)
    from wenu.sky.native_snapshot import read_native_sky_snapshot
    global _WORKER_SKY, _WORKER_CHART_COMMAND
    _WORKER_CHART_COMMAND = chart_command
    _WORKER_SKY = read_native_sky_snapshot(directory,
        expected_manifest_sha256=digest).make_sky()


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
    if 'stars' not in composition.detail.enabled_layers:
        return None
    from .automatic_legends import draw_automatic_chart_legends
    from .legend_plan import ChartLegendPlan, LegendPlacement
    data = _atlas_report_data(chart, sky, composition, rendering)
    presentation = AtlasChartPresentation() if presentation is None else presentation
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


def _atlas_frame_widths(style, presentation):
    allowance = 2 * (style.canvas.grid_label_band_padding_points + style.canvas.grid_label_band_linewidth / 2)
    # A Dec string lies along its projected parallel, rather than along the
    # vertical edge. Budget its worst rotated extent once from the font.
    from matplotlib.backends.backend_agg import RendererAgg
    from matplotlib.font_manager import FontProperties
    font = FontProperties(size=presentation.grid_label_fontsize * presentation.grid_dec_label_scale)
    measure = RendererAgg(1, 1, 72)
    extent = max(math.hypot(*measure.get_text_width_height_descent(f'{value:+g}°', font, ismath=False)[:2])
                 for value in range(-80, 81, 10))
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


def _atlas_grid_layout(page, style, presentation):
    horizontal, vertical = _atlas_frame_widths(style, presentation)
    horizontal, vertical = horizontal * 25.4 / 72, vertical * 25.4 / 72
    factor = min(1 - 2 * vertical / page.useful_width_mm,
                 1 - 2 * horizontal / page.useful_height_mm)
    if factor <= 0:
        raise ValueError('Coordinate frame does not fit the useful page.')
    width, height = page.useful_width_mm * factor, page.useful_height_mm * factor
    bounds = ((page.inner_mm + (page.useful_width_mm-width)/2)/page.width_mm,
              (page.bottom_mm + (page.useful_height_mm-height)/2)/page.height_mm,
              width/page.width_mm, height/page.height_mm)
    return bounds, style


def _render_atlas_sheet(task, sky=None, *, chart_command=None):
    """Dispatch one immutable sheet through the supplied chart-command entry."""
    from .request_generation import AtlasSheetChartRequest, generate_chart_request
    sheet, page, presentation, directory = task
    command = chart_command if chart_command is not None else (_WORKER_CHART_COMMAND if sky is None else None)
    sky = _WORKER_SKY if sky is None else sky
    request = AtlasSheetChartRequest(sheet, page, presentation, Path(directory))
    if command is None:
        generate_chart_request(request, sky=sky)
    else:
        status = command(["atlas-sheet", "--chart-number", str(sheet.number),
            "--output-dir", str(directory), "--debug"],
            atlas_request=request, sky=sky, emit_outputs=False)
        if type(status) is not int or status != 0:
            raise RuntimeError(f"wenu_chart failed for chart {sheet.number}: {status}")
    return sheet.number


def _append_atlas_index(writer, reader, page):
    """Fit one supplied vector index into the physical atlas paper margins."""
    from pypdf import PdfWriter, Transformation
    with PdfWriter() as source:
        source.clone_document_from_reader(reader)
        index_page = source.pages[0]
        index_page.transfer_rotation_to_content()
        target = writer.add_blank_page(width=page.width_mm * 72 / 25.4,
                                      height=page.height_mm * 72 / 25.4)
        box = index_page.mediabox
        width, height = page.useful_width_mm * 72 / 25.4, page.useful_height_mm * 72 / 25.4
        scale = min(width / float(box.width), height / float(box.height))
        x = page.inner_mm * 72 / 25.4 + (width - float(box.width) * scale) / 2
        y = page.bottom_mm * 72 / 25.4 + (height - float(box.height) * scale) / 2
        transform = Transformation().translate(-float(box.left), -float(box.bottom)).scale(scale).translate(x, y)
        target.merge_transformed_page(index_page, transform)


def create_atlas(design_path, output_dir, *, presentation, charts="all", jobs=2,
                 save_sky=None, from_sky=None, index=None, chart_command=None):
    """Produce ordered chart pages with one preparation or explicit saved reuse.

    A manifest linked last commits the complete batch. Existing outputs and
    saved skies are preserved. Each chart has matching report-template products;
    an index PDF enables facing-page assembly. Object inventories and editorial
    curation remain separate.
    """
    from contextlib import ExitStack
    from dataclasses import asdict
    from pathlib import Path
    import json
    import multiprocessing
    import os
    import shutil
    import tempfile
    import time
    from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
    from pypdf import PdfReader, PdfWriter
    from wenu.sky.native_snapshot import prepare_native_sky_snapshot, read_native_sky_snapshot
    _positive_integer(jobs, "jobs")
    if chart_command is not None and not callable(chart_command):
        raise TypeError("chart_command must be callable or None.")
    if not isinstance(presentation, AtlasChartPresentation):
        raise TypeError("presentation must be AtlasChartPresentation.")
    if "svg" not in presentation.formats:
        from dataclasses import replace
        presentation = replace(presentation, formats=(*presentation.formats, "svg"))
    if save_sky is not None and from_sky is not None:
        raise ValueError("--save-sky and --from-sky are mutually exclusive.")
    raw = Path(design_path).read_bytes()
    atlas = AtlasBandTiling.from_json(raw.decode("utf-8"))
    if len({sheet.field_width_deg for sheet in atlas.geometry.sheets}) != 1:
        raise ValueError('Atlas charts require a common angular field and central scale; use a revised uniform-field design.')
    sheets = select_atlas_sheets(atlas, charts)
    index_bytes = None
    index_products = {}
    if index is not None:
        import io
        index_bytes = Path(index).read_bytes()
        try:
            index_reader = PdfReader(io.BytesIO(index_bytes))
            if index_reader.is_encrypted or len(index_reader.pages) != 1:
                raise ValueError("Index must be an unencrypted one-page PDF.")
            index_page = index_reader.pages[0]
            import math
            if any(not math.isfinite(float(value)) for value in index_page.mediabox) or min(
                    float(index_page.mediabox.width), float(index_page.mediabox.height)) <= 0:
                raise ValueError("Index PDF has an invalid page size.")
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError(f"Cannot read index PDF: {exc}") from exc
        for suffix in ('png', 'svg'):
            companion = Path(index).with_suffix('.' + suffix)
            if not companion.is_file():
                raise ValueError(f'Index requires its standalone {suffix.upper()} companion: {companion}')
            index_products[suffix] = companion.read_bytes()
    output_dir = Path(output_dir)
    if output_dir.exists() or output_dir.is_symlink() or not output_dir.parent.is_dir():
        raise ValueError("Choose a new output directory with an existing parent.")
    if from_sky is not None and Path(from_sky).resolve() in output_dir.resolve().parents:
        raise ValueError("Output must be outside the saved sky bundle.")
    if save_sky is not None:
        save_sky = Path(save_sky)
        if save_sky.exists() or save_sky.is_symlink() or not save_sky.parent.is_dir():
            raise ValueError("Choose a new saved-sky directory with an existing parent.")
        if save_sky.resolve() == output_dir.resolve() or output_dir.resolve() in save_sky.resolve().parents or save_sky.resolve() in output_dir.resolve().parents:
            raise ValueError("Saved sky and output directories must be independent.")
    started = time.perf_counter()
    worker_count = min(jobs, len(sheets))
    with ExitStack() as stack:
        cold_sky = None
        if from_sky is None:
            directory = save_sky or Path(stack.enter_context(tempfile.TemporaryDirectory(prefix="wenu-atlas-sky-"))) / "sky"
            digest, cold_sky = prepare_native_sky_snapshot(raw, directory, return_sky=True)
        else:
            directory = Path(from_sky)
        snapshot = read_native_sky_snapshot(directory)
        snapshot.require(layers=presentation.layers,
            star_magnitude_limit=presentation.star_magnitude_limit,
            design_sha256=hashlib.sha256(raw).hexdigest())
        digest = snapshot.manifest_sha256
        staging = Path(stack.enter_context(tempfile.TemporaryDirectory(prefix=".wenu-atlas-pages-", dir=output_dir.parent)))
        if index_bytes is not None:
            (staging/'atlas-index.pdf').write_bytes(index_bytes)
            for suffix, content in index_products.items():
                (staging/f'atlas-index.{suffix}').write_bytes(content)
        tasks = [(sheet, atlas.geometry.page, presentation, str(staging)) for sheet in sheets]
        if worker_count == 1:
            sky = cold_sky if cold_sky is not None else snapshot.make_sky()
            completed = [(_render_atlas_sheet(task, sky) if chart_command is None else
                          _render_atlas_sheet(task, sky, chart_command=chart_command)) for task in tasks]
        else:
            variables = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")
            previous = {key: os.environ.get(key) for key in variables}
            try:
                for key in variables:
                    os.environ[key] = "1"
                cold_sky = None
                pool = ProcessPoolExecutor(max_workers=worker_count,
                    mp_context=multiprocessing.get_context("spawn"),
                    initializer=_initialize_atlas_worker,
                    initargs=(str(directory), digest, chart_command))
                pending = {}
                remaining = iter(tasks)
                done_numbers = set()
                try:
                    for _ in range(worker_count):
                        task = next(remaining)
                        pending[pool.submit(_render_atlas_sheet, task)] = task[0].number
                    while pending:
                        finished, _ = wait(pending, return_when=FIRST_COMPLETED)
                        for future in finished:
                            number = pending.pop(future)
                            if future.result() != number:
                                raise RuntimeError(f"Chart {number} returned a different identity.")
                            done_numbers.add(number)
                            import sys
                            print(f"Completed chart {number} ({len(done_numbers)}/{len(sheets)})", file=sys.stderr)
                            task = next(remaining, None)
                            if task is not None:
                                pending[pool.submit(_render_atlas_sheet, task)] = task[0].number
                    completed = sorted(done_numbers)
                finally:
                    pool.shutdown(wait=True, cancel_futures=True)
            finally:
                for key, value in previous.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value
        if completed != [sheet.number for sheet in sheets]:
            raise RuntimeError("Incomplete atlas batch.")
        # Publish an analysis input manifest inside staging, never a partial
        # public batch. Charts and report records contain all diagnostic inputs.
        policies = [json.loads((staging / f"chart-{sheet.number:02d}_report_data.json").read_text())
                    ["stellar_sizing"] for sheet in sheets]
        if any(policy != policies[0] for policy in policies):
            raise ValueError("Atlas charts resolved different stellar sizing policies.")
        analysis_manifest = dict(document_kind="wenu-atlas-chart-batch",
            presentation=asdict(presentation), stellar_sizing=policies[0],
            page=asdict(atlas.geometry.page),
            products={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in staging.iterdir() if p.suffix == ".svg" or p.name.endswith("_report_data.json")})
        (staging / "manifest.json").write_text(json.dumps(analysis_manifest))
        from .stellar_sizing_report import analyze, render_catalogue_star_counts
        analyze([staging], staging / "stellar-sizing", atlas_report=True)
        count_report = None
        if "stars" in presentation.layers:
            catalogue_sky = sky if worker_count == 1 else snapshot.make_sky()
            count_report = render_catalogue_star_counts(catalogue_sky.stars,
                staging / "atlas-star-counts", magnitude_limit=presentation.star_magnitude_limit,
                page=atlas.geometry.page, dpi=presentation.dpi,
                provenance=dict(design_sha256=hashlib.sha256(raw).hexdigest(), snapshot_sha256=digest))
        with PdfWriter() as writer:
            writer.page_layout = '/TwoPageLeft'
            page_order = []
            if index_bytes is not None:
                _append_atlas_index(writer, index_reader, atlas.geometry.page)
                page_order.append(dict(page=1, kind="index"))
                writer.add_outline_item("Atlas index", 0)
                writer.add_blank_page(width=atlas.geometry.page.width_mm * 72 / 25.4,
                    height=atlas.geometry.page.height_mm * 72 / 25.4)
                page_order.append(dict(page=2, kind='blank'))
            for sheet in sheets:
                if index_bytes is not None:
                    writer.append(PdfReader(staging / f"chart-{sheet.number:02d}_report.pdf"))
                    page_order.append(dict(page=len(page_order) + 1, kind="report", chart=sheet.number))
                writer.append(PdfReader(staging / f"chart-{sheet.number:02d}.pdf"))
                page_order.append(dict(page=len(page_order) + 1, kind="chart", chart=sheet.number))
                writer.add_outline_item(f"Chart {sheet.number}", len(writer.pages) - 1)
            writer.append(PdfReader(staging / "stellar-sizing-report.pdf"))
            page_order.append(dict(page=len(page_order) + 1, kind="stellar_sizing_report"))
            writer.add_outline_item("Stellar sizing report", len(writer.pages) - 1)
            budget_pdf = staging / "stellar-sizing_area-budget.pdf"
            if budget_pdf.exists():
                writer.append(PdfReader(budget_pdf))
                page_order.append(dict(page=len(page_order) + 1, kind="stellar_area_budget"))
                writer.add_outline_item("Stellar area budget", len(writer.pages) - 1)
            if count_report is not None:
                writer.append(PdfReader(staging / "atlas-star-counts.pdf"))
                page_order.append(dict(page=len(page_order) + 1, kind="catalogue_star_counts"))
                writer.add_outline_item("Catalogue star counts", len(writer.pages) - 1)
            writer.write(staging / "atlas.pdf")
        for sheet in sheets:
            report_path = staging / f"chart-{sheet.number:02d}_report_data.json"
            report_data = json.loads(report_path.read_text(encoding="utf-8"))
            report_data.update(design_sha256=hashlib.sha256(raw).hexdigest(),
                snapshot_sha256=digest, presentation=asdict(presentation))
            report_path.write_text(json.dumps(report_data, indent=2, allow_nan=False) + "\n",
                                   encoding="utf-8")
        products = sorted(path for path in staging.iterdir() if path.name != "manifest.json")
        manifest = dict(schema_version=1, document_kind="wenu-atlas-chart-batch",
            design_sha256=hashlib.sha256(raw).hexdigest(),
            snapshot_sha256=digest, charts=completed, workers=worker_count,
            index_sha256=(None if index_bytes is None else hashlib.sha256(index_bytes).hexdigest()),
            report_content="reserved", page_order=page_order,
            presentation=asdict(presentation), elapsed_seconds=time.perf_counter() - started,
            stellar_sizing=policies[0], page=asdict(atlas.geometry.page),
            products={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in products})
        (staging / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        output_dir.mkdir()
        try:
            for path in products:
                os.link(path, output_dir / path.name)
            os.link(staging / "manifest.json", output_dir / "manifest.json")
        except BaseException:
            shutil.rmtree(output_dir)
            raise
    return output_dir / "manifest.json"

