"""Design-bound atlas planning and canonical chart-page publication."""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import math
import re
from pathlib import Path

from wenu.atlas_design import AtlasBandTiling, AtlasSheetGeometry, select_atlas_sheets

# Legacy aliases preserve existing imports and pickle GLOBAL lookups.
from .atlas_sheet import (
    _identity,
    AtlasSheetChart,
    AtlasChartPresentation,
    AtlasSheetChartRequest,
    _atlas_report_data,
    _atlas_full_magnitude_range,
    _render_atlas_report,
    _draw_atlas_chart_number,
    _draw_atlas_magnitude_scale,
    _atlas_grid_marks,
    _atlas_tick_options,
    _atlas_grid_options,
    _atlas_frame_widths,
    _draw_polar_declination_labels,
    _atlas_grid_layout,
    render_atlas_sheet,
)


def _positive_integer(value, name):
    if type(value) is not int or value < 1:
        raise ValueError(f"{name} must be a positive integer.")


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


def _render_atlas_sheet(task, sky=None, *, chart_command=None):
    """Dispatch one immutable sheet through the shared chart-command entry."""
    sheet, page, presentation, directory = task
    command = chart_command if chart_command is not None else (_WORKER_CHART_COMMAND if sky is None else None)
    sky = _WORKER_SKY if sky is None else sky
    request = AtlasSheetChartRequest(sheet, page, presentation, Path(directory))
    if command is None:
        from wenu.cli.chart import main as command
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


def _read_selection_criteria(paths, catalogues):
    """Admit immutable, catalogue-bound PDF pages before preparing any sky."""
    import io
    import json
    from pypdf import PdfReader
    admitted = {Path(p).resolve(strict=True): hashlib.sha256(Path(p).read_bytes()).hexdigest()
                for p in catalogues if p is not None}
    records = []
    seen = set()
    for path in paths:
        path = Path(path).resolve(strict=True)
        raw = path.read_bytes()
        data = json.loads(raw)
        if (not isinstance(data, dict) or type(data.get('schema_version')) is not int or data.get('schema_version') != 1 or
                data.get('document_kind') != 'wenu-catalogue-selection-criteria'):
            raise ValueError('Unsupported selection-criteria manifest.')
        catalogue = data.get('catalogue')
        if (not isinstance(catalogue, dict) or set(catalogue) != {'file', 'sha256'} or
                not isinstance(catalogue['file'], str) or Path(catalogue['file']).name != catalogue['file']):
            raise ValueError('Invalid criteria catalogue filename.')
        target = path.parent / catalogue['file']
        if (target.resolve(strict=True) not in admitted or
                admitted[target.resolve()] != catalogue['sha256']):
            raise ValueError('Selection criteria do not match an explicit atlas catalogue.')
        if not isinstance(data.get('pages'), list) or not data['pages']:
            raise ValueError('Selection criteria require pages.')
        for page in data['pages']:
            if not isinstance(page, dict) or set(page) != {'file', 'title', 'sha256'} or not isinstance(page['file'], str):
                raise ValueError('Invalid selection PDF record.')
            name = page['file']
            if Path(name).name != name or Path(name).suffix != '.pdf' or name in seen:
                raise ValueError('Invalid or duplicate selection PDF filename.')
            content = (path.parent / name).read_bytes()
            if hashlib.sha256(content).hexdigest() != page['sha256']:
                raise ValueError('Selection PDF checksum mismatch: ' + name)
            reader = PdfReader(io.BytesIO(content))
            if reader.is_encrypted or len(reader.pages) != 1:
                raise ValueError('Selection PDF must contain one unencrypted page.')
            box = reader.pages[0].mediabox
            if any(not math.isfinite(float(v)) for v in box) or min(float(box.width), float(box.height)) <= 0:
                raise ValueError('Invalid selection PDF page size.')
            _identity(page['title'], 'Selection page title')
            seen.add(name)
            records.append(dict(file=f'selection-criteria-{len(records)+1:03d}.pdf', source_file=name,
                title=page['title'], content=content,
                sha256=page['sha256'], catalogue_sha256=catalogue['sha256'],
                criteria_file=path.name, criteria_sha256=hashlib.sha256(raw).hexdigest()))
    return records


def create_atlas(design_path, output_dir, *, presentation, charts="all", jobs=2,
                 save_sky=None, from_sky=None, index=None, chart_command=None,
                 open_cluster_catalogue=None, planetary_nebula_catalogue=None,
                 selection_criteria=()):
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
    if from_sky is not None and (open_cluster_catalogue is not None or planetary_nebula_catalogue is not None):
        raise ValueError("A catalogue override requires a new sky; omit --from-sky.")
    criteria_catalogues = dict(open_cluster_filename=open_cluster_catalogue,
        planetary_nebula_filename=planetary_nebula_catalogue)
    criteria_paths = list(selection_criteria)
    if from_sky is None:
        from wenu.resources import curated_catalogue_bundle
        for layer, domain, field in (
                ('nonstellar', 'messier', 'nonstellar_filename'),
                ('galaxies', 'galaxies', 'galaxy_filename'),
                ('open_clusters', 'open_clusters', 'open_cluster_filename'),
                ('globular_clusters', 'globular_clusters', 'globular_cluster_filename'),
                ('supernova_remnants', 'supernova_remnants', 'supernova_remnant_filename'),
                ('planetary_nebulae', 'planetary_nebulae', 'planetary_nebula_filename')):
            if criteria_catalogues.get(field) is not None or layer not in presentation.layers:
                continue
            bundle = curated_catalogue_bundle(domain)
            if bundle is None:
                continue
            criteria_catalogues[field] = bundle['catalogue']
            if not selection_criteria and bundle['criteria']:
                def revision(path):
                    match = re.search(r'_v(\d+(?:\.\d+)*)\.json$', path.name)
                    if match is None:
                        raise ValueError('Installed criteria require an explicit version.')
                    return tuple(map(int, match[1].split('.')))
                criteria_paths.append(max(bundle['criteria'], key=revision))
    criteria = _read_selection_criteria(criteria_paths, criteria_catalogues.values())
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
            if all(catalogue is None for catalogue in criteria_catalogues.values()):
                digest, cold_sky = prepare_native_sky_snapshot(raw, directory, return_sky=True)
            else:
                from dataclasses import replace
                from wenu.sky.maximal_sphere import CANONICAL_MAXIMAL_SPHERE_PROFILE
                # Resolve the selector once; all workers reuse the hashed snapshot.
                overrides = {}
                for field, catalogue in criteria_catalogues.items():
                    if catalogue is not None:
                        overrides[field] = Path(catalogue).resolve(strict=True)
                profile = replace(CANONICAL_MAXIMAL_SPHERE_PROFILE, **overrides)
                digest, cold_sky = prepare_native_sky_snapshot(raw, directory,
                    profile=profile, return_sky=True)
        else:
            directory = Path(from_sky)
        snapshot = read_native_sky_snapshot(directory)
        snapshot.require(layers=presentation.layers,
            star_magnitude_limit=presentation.star_magnitude_limit,
            design_sha256=hashlib.sha256(raw).hexdigest())
        digest = snapshot.manifest_sha256
        staging = Path(stack.enter_context(tempfile.TemporaryDirectory(prefix=".wenu-atlas-pages-", dir=output_dir.parent)))
        for record in criteria:
            (staging / record['file']).write_bytes(record['content'])
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
            for record in criteria:
                first_page = len(writer.pages)
                reader = PdfReader(staging / record['file'])
                _append_atlas_index(writer, reader, atlas.geometry.page)
                page_order.append(dict(page=first_page + 1, kind="selection_criteria",
                    title=record['title'], file=record['file'],
                    catalogue_sha256=record['catalogue_sha256']))
                writer.add_outline_item(record['title'], first_page)
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
            selection_criteria=[{k: v for k, v in record.items() if k != 'content'} for record in criteria],
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
