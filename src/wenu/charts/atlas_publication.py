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
        return sheet.number
    except Exception as exc:
        raise RuntimeError(f"Chart {sheet.number} failed: {exc}") from exc
    finally:
        plt.close(figure)


def create_atlas(design_path, output_dir, *, presentation, charts="all", jobs=2,
                 save_sky=None, from_sky=None):
    """Produce ordered chart pages with one preparation or explicit saved reuse.

    A manifest linked last commits the complete batch. Existing outputs and
    saved skies are preserved. Facing reports and editorial curation are separate.
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
    from pypdf import PdfWriter
    from wenu.sky.native_snapshot import prepare_native_sky_snapshot, read_native_sky_snapshot
    _positive_integer(jobs, "jobs")
    if not isinstance(presentation, AtlasChartPresentation):
        raise TypeError("presentation must be AtlasChartPresentation.")
    if save_sky is not None and from_sky is not None:
        raise ValueError("--save-sky and --from-sky are mutually exclusive.")
    raw = Path(design_path).read_bytes()
    atlas = AtlasBandTiling.from_json(raw.decode("utf-8"))
    sheets = select_atlas_sheets(atlas, charts)
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
            for sheet in sheets:
                writer.append(staging / f"chart-{sheet.number:02d}.pdf")
            writer.write(staging / "atlas.pdf")
        products = sorted(staging.iterdir())
        manifest = dict(schema_version=1, document_kind="wenu-atlas-chart-batch",
            design_sha256=hashlib.sha256(raw).hexdigest(),
            snapshot_sha256=digest, charts=completed, workers=worker_count,
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
