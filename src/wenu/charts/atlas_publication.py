"""Design-bound atlas planning and canonical chart-page publication."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
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
    dpi: int = 150
    star_magnitude_limit: float = 6.0
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

    def __post_init__(self):
        import math
        from wenu.sky.native_snapshot import LAYERS
        if self.style not in {"atlas", "cartoon"}:
            raise ValueError("style must be atlas or cartoon.")
        if type(self.dpi) is not int or not 36 <= self.dpi <= 1200:
            raise ValueError("dpi must be an integer from 36 to 1200.")
        limit = self.star_magnitude_limit
        if isinstance(limit, bool) or not isinstance(limit, (int, float)) or not math.isfinite(limit) or not -2 <= limit <= 11:
            raise ValueError("star_magnitude_limit must be finite between -2 and 11.")
        for name in ("report_label_scale", "report_separator_width", "report_separator_gap_mm"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and positive.")
        _identity(self.report_label_family, "report_label_family")
        if not isinstance(self.report_label_weight, str) or self.report_label_weight not in {"normal", "bold", "light", "medium", "semibold", "heavy", "black"}:
            raise ValueError("Invalid report_label_weight.")
        from matplotlib.colors import is_color_like
        if not isinstance(self.report_label_color, str) or not is_color_like(self.report_label_color):
            raise ValueError("Invalid report_label_color.")
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
        return cls(**{k: v for k, v in data.items() if k not in required})


_WORKER_SKY = None


def _initialize_atlas_worker(directory, digest):
    import matplotlib
    matplotlib.use("Agg", force=True)
    from wenu.sky.native_snapshot import read_native_sky_snapshot
    global _WORKER_SKY
    _WORKER_SKY = read_native_sky_snapshot(directory,
        expected_manifest_sha256=digest).make_sky()


def _atlas_report_data(chart, sky, composition, rendering):
    """Describe the report template from the existing rendered star geometry."""
    from dataclasses import asdict
    import math
    from .legend_geometry import rendered_star_geometry
    from .magnitude_legend import visible_star_statistics
    page = chart.page
    statistics = None
    reference_range = None
    if "stars" in composition.detail.enabled_layers:
        stars = rendered_star_geometry(rendering, sky=sky)
        statistics = visible_star_statistics(stars.spherical, stars.projected,
            stars.viewport, effective_limit=composition.detail.star_magnitude_limit)
        if statistics.has_visible_stars:
            # The first reference must be at least as bright as every plotted star.
            reference_range = (math.floor(statistics.brightest_magnitude),
                               math.floor(statistics.faintest_magnitude))
    return dict(schema_version=1, document_kind="wenu-atlas-chart-report",
        chart_number=chart.sheet.number, sheet_id=chart.sheet.sheet_id,
        center=dict(coordinate_system="ICRS", ra_deg=chart.sheet.center_ra_deg,
                    dec_deg=chart.sheet.center_dec_deg,
                    ra_defined=abs(chart.sheet.center_dec_deg) != 90,
                    pole_meridian_ra_deg=chart.sheet.pole_meridian_ra_deg),
        page=dict(width_mm=page.width_mm, height_mm=page.height_mm),
        layout=dict(units="mm", origin="bottom-left",
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
        # A separate heading lets its type grow without enlarging centre metadata.
        heading = figure.text((box["x"] + box["width"]) / page.width_mm,
            (box["y"] + box["height"]) / page.height_mm,
            f"Chart {chart.sheet.number}", ha="right", va="top",
            fontsize=composition.style.legend.title_fontsize * presentation.report_label_scale,
            fontfamily=presentation.report_label_family,
            fontweight=presentation.report_label_weight,
            color=presentation.report_label_color)
        heading.set_gid(f"chart-{chart.sheet.number:02d}-report-heading")
        figure.canvas.draw()
        bounds = heading.get_window_extent(figure.canvas.get_renderer())
        heading_height = bounds.height / figure.dpi * 25.4
        heading_width = bounds.width / figure.dpi * 25.4
        gap = presentation.report_separator_gap_mm
        separator_y = box["y"] + box["height"] - heading_height - gap
        legend_height = separator_y - gap - box["y"]
        if heading_width > box["width"] or legend_height <= 0:
            raise ValueError("Report heading does not fit the facing-page column.")
        from matplotlib.lines import Line2D
        separator = Line2D([box["x"] / page.width_mm,
            (box["x"] + box["width"]) / page.width_mm],
            [separator_y / page.height_mm] * 2, transform=figure.transFigure,
            color=presentation.report_label_color, linewidth=presentation.report_separator_width)
        separator.set_gid(f"chart-{chart.sheet.number:02d}-report-separator")
        figure.add_artist(separator)
        ax.set_position((box["x"] / page.width_mm, box["y"] / page.height_mm,
                         box["width"] / page.width_mm, legend_height / page.height_mm))
        data["layout"]["heading"] = dict(x=box["x"], y=separator_y + gap,
            width=box["width"], height=heading_height)
        data["layout"]["separator"] = dict(x=box["x"], y=separator_y, width=box["width"])
        data["layout"]["legends"] = dict(box, height=legend_height)
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
        legends = draw_automatic_chart_legends(ax, chart, sky, composition.style,
            rendering, resolved_detail=composition.detail, plan=plan,
            include_context=True, object_title=title,
            stellar_reference_range=data["stars"]["reference_range"])
        for artist in legends.artists:
            artist.borderaxespad = 0
        # Detect legend overflow rather than silently cropping it into the report.
        figure.canvas.draw()
        renderer = figure.canvas.get_renderer()
        bounds = ax.get_window_extent(renderer)
        extents = [artist.get_window_extent(renderer) for artist in legends.artists]
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


def _render_atlas_sheet(task, sky=None):
    """One isolated figure, canonical composition/export, all requested formats."""
    import matplotlib.pyplot as plt
    from .composition import compose_chart
    from .detail import DetailOverrides
    from .export_workflow import export_composed_chart
    from .modes import PrintMode
    from .regional import ExportOptions
    from wenu.rendering.matplotlib import MatplotlibRenderer
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    sheet, page, presentation, directory = task
    sky = _WORKER_SKY if sky is None else sky
    chart = AtlasSheetChart(sheet, page)
    composition = compose_chart(chart, style=presentation.style,
        mode=PrintMode(width_inches=page.width_mm / 25.4,
            height_inches=page.height_mm / 25.4, dpi=presentation.dpi),
        detail_overrides=DetailOverrides(
            star_magnitude_limit=presentation.star_magnitude_limit,
            enabled_layers=frozenset("nonstellar_objects" if name == "nonstellar" else name
                for name in presentation.layers),
            constellation_star_mode="none"))
    figure = plt.figure(figsize=(page.width_mm / 25.4, page.height_mm / 25.4))
    ax = figure.add_axes((page.inner_mm / page.width_mm,
        page.bottom_mm / page.height_mm, page.useful_width_mm / page.width_mm,
        page.useful_height_mm / page.height_mm))
    ax.set_xticks([])
    ax.set_yticks([])
    figure.text(page.inner_mm / page.width_mm, 1 - page.top_mm / (2 * page.height_mm),
        f"Chart {sheet.number}", va="center", fontsize=10)
    try:
        renderer = MatplotlibRenderer(ax)
        first = presentation.formats[0]
        result = export_composed_chart(chart, sky, renderer,
            Path(directory) / f"chart-{sheet.number:02d}.{first}",
            composition=composition,
            realization_context=LayerRealizationContext(NATIVE_ICRS_SPEC),
            export_options=ExportOptions(dpi=presentation.dpi, bbox_inches=None))
        for suffix in presentation.formats[1:]:
            result.export_options.save(figure, Path(directory) / f"chart-{sheet.number:02d}.{suffix}")
        _render_atlas_report(chart, sky, composition, result.rendering, directory,
                             formats=presentation.formats, presentation=presentation)
        return sheet.number
    except Exception as exc:
        raise RuntimeError(f"Chart {sheet.number} failed: {exc}") from exc
    finally:
        plt.close(figure)


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
                 save_sky=None, from_sky=None, index=None):
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
    if not isinstance(presentation, AtlasChartPresentation):
        raise TypeError("presentation must be AtlasChartPresentation.")
    if save_sky is not None and from_sky is not None:
        raise ValueError("--save-sky and --from-sky are mutually exclusive.")
    raw = Path(design_path).read_bytes()
    atlas = AtlasBandTiling.from_json(raw.decode("utf-8"))
    sheets = select_atlas_sheets(atlas, charts)
    index_bytes = None
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
        tasks = [(sheet, atlas.geometry.page, presentation, str(staging)) for sheet in sheets]
        if worker_count == 1:
            sky = cold_sky if cold_sky is not None else snapshot.make_sky()
            completed = [_render_atlas_sheet(task, sky) for task in tasks]
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
                    initargs=(str(directory), digest))
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
        with PdfWriter() as writer:
            page_order = []
            if index_bytes is not None:
                _append_atlas_index(writer, index_reader, atlas.geometry.page)
                page_order.append(dict(page=1, kind="index"))
                writer.add_outline_item("Atlas index", 0)
            for sheet in sheets:
                if index_bytes is not None:
                    writer.append(staging / f"chart-{sheet.number:02d}_report.pdf")
                    page_order.append(dict(page=len(page_order) + 1, kind="report", chart=sheet.number))
                writer.append(staging / f"chart-{sheet.number:02d}.pdf")
                page_order.append(dict(page=len(page_order) + 1, kind="chart", chart=sheet.number))
                writer.add_outline_item(f"Chart {sheet.number}", len(writer.pages) - 1)
            writer.write(staging / "atlas.pdf")
        for sheet in sheets:
            report_path = staging / f"chart-{sheet.number:02d}_report_data.json"
            report_data = json.loads(report_path.read_text(encoding="utf-8"))
            report_data.update(design_sha256=hashlib.sha256(raw).hexdigest(),
                snapshot_sha256=digest, presentation=asdict(presentation))
            report_path.write_text(json.dumps(report_data, indent=2, allow_nan=False) + "\n",
                                   encoding="utf-8")
        products = sorted(staging.iterdir())
        manifest = dict(schema_version=1, document_kind="wenu-atlas-chart-batch",
            design_sha256=hashlib.sha256(raw).hexdigest(),
            snapshot_sha256=digest, charts=completed, workers=worker_count,
            index_sha256=(None if index_bytes is None else hashlib.sha256(index_bytes).hexdigest()),
            report_content="reserved", page_order=page_order,
            presentation=asdict(presentation), elapsed_seconds=time.perf_counter() - started,
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
