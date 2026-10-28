"""Atlas request-file admission, installed route and JSON publication."""

from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
import hashlib
import os
from pathlib import Path
import subprocess
import sys

import pytest
from stellar_catalogue_fixtures import native_table

from wenu.atlas_design import AtlasBandTiling, AtlasDesignRequest
from wenu.cli import atlas as cli
from wenu.charts.atlas_publication import AtlasPublicationBatchRequest


@pytest.mark.parametrize('name,count,interior', [('b4-landscape-five-band',34,5),('b4-portrait',36,3), ('b4-hemispheres',2,0)])
def test_installed_layout_and_style_are_independent_cli_inputs(tmp_path, monkeypatch, name, count, interior):
    from wenu.resources import configuration_preset_path
    from wenu.charts import atlas_publication
    path = configuration_preset_path(name, kind='atlas-layout')
    atlas = AtlasBandTiling.from_json(path.read_text())
    assert len(atlas.geometry.sheets) == count
    assert len(atlas.bands) == interior + 2
    assert len({s.field_width_deg for s in atlas.geometry.sheets}) == 1
    output = tmp_path/'design.json'
    assert cli.design_main(['--layout',name,'--output',str(output)]) == 0
    assert output.read_bytes() == path.read_bytes()
    calls = []
    def capture(design, directory, **kwargs):
        calls.append((design,kwargs)); return tmp_path/'manifest.json'
    monkeypatch.setattr(atlas_publication,'create_atlas',capture)
    assert cli.create_main(['--layout',name,'--charts','1','--output-dir',str(tmp_path/'atlas')]) == 0
    design, kwargs = calls[0]
    assert design == path
    presentation = kwargs['presentation']
    assert presentation.star_magnitude_limit == 7.5
    assert presentation.star_size_scale == 1.7
    assert presentation.stellar_magnitude_sizing.algorithm == 'quadratic'
    assert presentation.report_label_scale == 3
    assert presentation.chart_number_box_visible
    assert presentation.open_cluster_angular_sizes
    assert presentation.chart_legend_visible
    assert {'open_clusters', 'planetary_nebulae'} <= set(presentation.layers)
    assert cli.create_main(['--layout',name,'--charts','1','--magnitude-limit','7',
        '--star-size-scale','2','--output-dir',str(tmp_path/'override')]) == 0
    assert calls[1][1]['presentation'].star_magnitude_limit == 7
    assert calls[1][1]['presentation'].star_size_scale == 2
    assert calls[1][0] == path
    assert cli.create_main(['--layout',name,'--no-legend','--no-planetary-nebulae',
        '--output-dir',str(tmp_path/'hidden')]) == 0
    hidden = calls[2][1]['presentation']
    assert hidden.chart_legend_visible is False
    assert set(hidden.layers) == set(presentation.layers) - {'planetary_nebulae'}
    from dataclasses import asdict
    # Persist both settings through the existing closed presentation schema.
    data = asdict(hidden)
    del data['stellar_magnitude_sizing']
    data.update(schema_version=1, document_kind='wenu-atlas-chart-presentation')
    assert atlas_publication.AtlasChartPresentation.from_dict(data).chart_legend_visible is False
    config = tmp_path/'hidden.toml'
    config.write_text('schema_version = 1\ndocument_kind = "wenu-atlas-chart-presentation"\n'
        'chart_legend_visible = false\nlayers = ["stars"]\n')
    assert cli.create_main(['--layout',name,'--config',str(config),
        '--output-dir',str(tmp_path/'inherited')]) == 0
    assert calls[3][1]['presentation'].chart_legend_visible is False
    assert calls[3][1]['presentation'].layers == ('stars',)
    assert cli.create_main(['--layout',name,'--config',str(config),'--legend','--planetary-nebulae',
        '--output-dir',str(tmp_path/'shown')]) == 0
    assert calls[4][1]['presentation'].chart_legend_visible is True
    assert calls[4][1]['presentation'].layers == ('stars','planetary_nebulae')
    assert cli.create_main(['--layout',name,'--exclude-layer','nonstellar',
        '--exclude-layer','planetary_nebulae','--planetary-nebulae',
        '--output-dir',str(tmp_path/'excluded')]) == 0
    excluded = calls[5][1]['presentation']
    assert set(excluded.layers) == set(presentation.layers) - {'nonstellar','planetary_nebulae'}
    assert excluded.chart_legend_visible is True


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples/atlas_design_request_v1.toml"


@pytest.mark.parametrize('style_name,show_features', [
    ('atlas-v6',True), ('atlas-hemispheres-v2',True), ('atlas-hemispheres-v2',False)])
def test_hemispheric_atlas_uses_all_three_commands_and_curated_catalogue_seams(tmp_path, monkeypatch, style_name, show_features):
    """Synthetic catalogue evidence; real design, index, chart and book routes."""
    import json
    import numpy as np
    import pandas as pd
    from astropy.table import Table
    from pypdf import PdfReader
    from xml.etree import ElementTree
    from wenu import CelestialSphere
    from wenu.objects.stars import Stars
    from wenu.sky import native_snapshot
    from wenu.charts import atlas_index, export_workflow
    from wenu import resources

    design = tmp_path / 'hemispheres_v1.json'
    assert cli.design_main(['--config', str(ROOT/'examples/atlas_design_hemispheres_v1.toml'),
                            '--output', str(design)]) == 0
    original_design = design.read_bytes()
    # Exercise the installed index preset without loading unrelated sky catalogues.
    monkeypatch.setattr(atlas_index, 'index_sky', lambda *a, **k: CelestialSphere(None))
    prefix = tmp_path/'index_v1'
    assert cli.plot_main(['--design', str(design), '--output-prefix', str(prefix)]) == 0
    elements = list(ElementTree.parse(prefix.with_suffix('.svg')).getroot().iter())
    ids = [e.get('id') for e in elements if e.get('id')]
    assert len(ids) == len(set(ids))
    assert {int(e.get('data-chart-number')) for e in elements
            if e.get('data-role') == 'number_label'} == {1, 2}

    sky = CelestialSphere(None)
    sky.add_equatorial_grid(frame='icrs', equinox='J2000', include_equator=True)
    sources = {}
    for domain, add in (('open_clusters', sky.add_open_clusters),
                        ('planetary_nebulae', sky.add_planetary_nebulae)):
        path = tmp_path/f'synthetic_curated_{domain}_v1.ecsv'
        Table(dict(identifier=[f'{domain} south', f'{domain} north'],
            ra_deg=[60., 60.], dec_deg=[-30., 30.],
            apparent_diameter_arcmin=[10., 10.],
            major_axis_arcmin=[10., 10.], minor_axis_arcmin=[10., 10.],
            object_type=['open cluster' if domain == 'open_clusters' else 'planetary nebula']*2,
            selection_fixture=['synthetic']*2)).write(path, format='ascii.ecsv')
        add(filename=path)
        sources[domain] = path
    stars = Stars(None, magnitude_limit=11)
    stars.source_catalog = pd.DataFrame(dict(ra_hours=[4., 4.], ra_degrees=[60., 60.],
        dec_degrees=[-30., 30.], magnitude=[1., 2.], is_constellation_vertex=[False]*2), index=[11, 12])
    stars.source_catalog = native_table(stars.source_catalog)
    stars.catalog = stars.source_catalog.copy()
    sky.stars = sky.add(stars)
    bundles = []
    def bundle(domain):
        bundles.append(domain)
        if domain not in sources:
            return None
        return dict(catalogue=sources[domain], criteria=())
    monkeypatch.setattr(resources, 'curated_catalogue_bundle', bundle)
    profiles = []
    def prepare(raw, directory, **kwargs):
        assert raw == original_design
        profiles.append(kwargs['profile'])
        return 'synthetic-digest', sky
    monkeypatch.setattr(native_snapshot, 'prepare_native_sky_snapshot', prepare)
    snapshot = type('SyntheticSnapshot', (), {
        'manifest_sha256': 'synthetic-digest', 'require': lambda self, **kw: None})()
    monkeypatch.setattr(native_snapshot, 'read_native_sky_snapshot', lambda *a, **k: snapshot)
    exports = []
    export = export_workflow.export_composed_chart
    def capture(chart, *args, **kwargs):
        result = export(chart, *args, **kwargs)
        style = result.composition.style
        assert not style.stars.draw_bright_symbols
        assert style.stars.color == '#151515'
        assert style.deep_sky.planetary_nebula_color == '#24552b'
        small = style_name == 'atlas-hemispheres-v2'
        assert result.composition.detail.star_magnitude_limit == (5 if small else 7.5)
        assert style.stars.area_scale == pytest.approx((0.85 if small else 1.7)**2)
        from wenu.charts.presets import AtlasChartStyle
        expected_cluster_area = AtlasChartStyle().deep_sky.open_cluster_symbol_size * (1.8*(0.5 if small else 1))**2
        assert style.deep_sky.globular_cluster_symbol_size == pytest.approx(expected_cluster_area)
        assert ('planetary_nebulae' in result.composition.detail.enabled_layers) is show_features
        assert any(record.layer is sky.planetary_nebulae for record in result.rendering.layers) is show_features
        renderer = args[1]
        outer = renderer._grid_label_band_frame
        bounds = outer.get_path().transformed(outer.get_transform()).get_extents()
        scale = 25.4 / renderer.ax.figure.dpi
        # Polygonal display rims approximate the fixed circle to < 2 microns.
        assert bounds.width * scale == pytest.approx(chart.page.useful_width_mm, abs=.002)
        assert bounds.height * scale == pytest.approx(bounds.width * scale, abs=.002)
        for record in result.rendering.layers:
            if record.layer in (sky.stars, sky.open_clusters, sky.planetary_nebulae):
                assert np.isfinite(record.projected.x).sum() == 1
        exports.append(result)
        return result
    monkeypatch.setattr(export_workflow, 'export_composed_chart', capture)
    output = tmp_path/'atlas_v1'
    assert cli.create_main(['--design', str(design), '--config', style_name,
        '--jobs', '1', '--index', str(prefix.with_suffix('.pdf')),
        '--output-dir', str(output),
        *([] if show_features else ['--no-legend','--no-planetary-nebulae'])]) == 0
    assert len(exports) == 2 and len(profiles) == 1
    assert profiles[0].open_cluster_filename == sources['open_clusters']
    assert profiles[0].planetary_nebula_filename == (sources['planetary_nebulae'] if show_features else None)
    assert 'open_clusters' in bundles
    assert ('planetary_nebulae' in bundles) is show_features
    frames, scales = [], []
    for number in (1, 2):
        data = json.loads((output/f'chart-{number:02d}_report_data.json').read_text())
        assert data['stars']['statistics']['visible_count'] == 1
        frames.append(data['layout']['chart_sky_frame'])
        scales.append(data['layout']['central_scale_mm_per_degree'])
        assert frames[-1]['width'] == pytest.approx(frames[-1]['height'])
        assert data['stellar_area_budget']['chart_area_mm2'] == pytest.approx(
            np.pi * frames[-1]['width'] * frames[-1]['height'] / 4)
        root = ElementTree.parse(output/f'chart-{number:02d}.svg').getroot()
        texts = [''.join(e.itertext()) for e in root.iter() if e.tag.endswith('}text')]
        assert {f'{hour}ʰ' for hour in range(0, 24, 2)} <= set(texts)
        assert any(text.endswith('°') for text in texts)
        assert ('Stars' in texts) is show_features
    assert scales[0] == pytest.approx(scales[1])
    assert frames[0] == frames[1]
    book = PdfReader(output/'atlas.pdf')
    assert 'Chart 1' in book.pages[2].extract_text()
    assert 'Chart 2' in book.pages[4].extract_text()
    assert not book.pages[1].extract_text().strip()
    manifest = json.loads((output/'manifest.json').read_text())
    assert len(book.pages) == len(manifest['page_order'])
    assert design.read_bytes() == original_design


@pytest.fixture
def request_data():
    return cli.tomllib.loads(EXAMPLE.read_text(encoding="utf-8"))


def _batch_input(request_data):
    atlas = AtlasDesignRequest.from_dict(request_data).resolve()
    raw = atlas.to_json().encode("utf-8")
    return raw, dict(schema_version=1,
                    document_kind="wenu-atlas-publication-batch-request",
                    publication_id="book", revision=1,
                    design_id=atlas.geometry.design_id,
                    design_revision=atlas.geometry.revision,
                    design_sha256=hashlib.sha256(raw).hexdigest(),
                    charts="S,20..21", jobs=2)


def test_publication_batch_binds_exact_bytes_and_retains_effective_overrides(request_data, monkeypatch):
    from wenu import Observer, CelestialSphere, MatplotlibRenderer
    from wenu.objects.stars import Stars
    import socket
    raw, data = _batch_input(request_data)

    def forbidden(*args, **kwargs):
        raise AssertionError("Batch planning must not load scientific or render resources")
    for owner in (Observer, CelestialSphere, MatplotlibRenderer, Stars):
        monkeypatch.setattr(owner, "__init__", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)
    request = AtlasPublicationBatchRequest.from_dict(data)
    plan = request.resolve(raw, charts="34,3..6,20..21", jobs=100)
    assert plan.chart_numbers == (3, 4, 5, 6, 20, 21, 34)
    assert plan.worker_count == 7
    assert plan.charts == "34,3..6,20..21" and plan.jobs == 100
    assert plan.request is request and request.charts == "S,20..21"
    assert request.resolve(raw).chart_numbers == (*range(1, 14), 20, 21)
    assert request.resolve(raw, charts="E", jobs=1).worker_count == 1
    assert plan.atlas.to_json().encode() == raw
    with pytest.raises(FrozenInstanceError):
        plan.jobs = 1
    with pytest.raises(ValueError, match="disagree"):
        replace(plan, sheets=plan.sheets[:-1])
    missing_jobs = dict(data)
    del missing_jobs["jobs"]
    assert AtlasPublicationBatchRequest.from_dict(missing_jobs).jobs == 2


def test_publication_batch_rejects_closed_input_faults(request_data):
    raw, original = _batch_input(request_data)
    faults = dict(schema_version=True, document_kind="wenu-atlas-publication-request",
                  publication_id=" ", revision=0, design_revision=True,
                  design_id=" other ", design_sha256="A" * 64, charts=None,
                  jobs=True, surprise="ignored")
    for key, value in faults.items():
        data = dict(original)
        assert key not in data or data[key] != value or type(data[key]) is not type(value)
        data[key] = value
        with pytest.raises(ValueError):
            AtlasPublicationBatchRequest.from_dict(data)
    for key in original.keys() - {"jobs"}:
        data = dict(original)
        del data[key]
        with pytest.raises(ValueError):
            AtlasPublicationBatchRequest.from_dict(data)
    request = AtlasPublicationBatchRequest.from_dict(original)
    for charts, jobs in (("35", 1), ("N,", 1), ("", 1), (True, 1),
                         ("all", 0), ("all", True), ("all", "2")):
        with pytest.raises(ValueError):
            request.resolve(raw, charts=charts, jobs=jobs)
    changed = raw + b"\n"
    assert hashlib.sha256(changed).hexdigest() != original["design_sha256"]
    with pytest.raises(ValueError, match="bytes"):
        request.resolve(changed)
    with pytest.raises(ValueError, match="identity"):
        replace(request, design_id="another").resolve(raw)
    with pytest.raises(TypeError):
        request.resolve(raw.decode())


def test_publication_batch_cannot_admit_corrupted_bound_design(request_data):
    raw, data = _batch_input(request_data)
    # A correct checksum does not replace the existing semantic JSON validator.
    import json
    content = json.loads(raw)
    content["geometry"]["coordinate_frame"] = "fk5"
    corrupted = json.dumps(content).encode()
    assert corrupted != raw
    data["design_sha256"] = hashlib.sha256(corrupted).hexdigest()
    with pytest.raises(ValueError):
        AtlasPublicationBatchRequest.from_dict(data).resolve(corrupted)


def test_request_units_and_cli_reproduce_the_accepted_layout(request_data, tmp_path, monkeypatch, capsys):
    from wenu import Observer, CelestialSphere, MatplotlibRenderer
    from wenu.objects.stars import Stars
    import socket

    def forbidden(*args, **kwargs):
        raise AssertionError("Designer must not load sky, observer or renderer resources")
    for owner in (Observer, CelestialSphere, MatplotlibRenderer, Stars):
        monkeypatch.setattr(owner, "__init__", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)
    original = EXAMPLE.read_bytes()
    hours = AtlasDesignRequest.from_dict(request_data).resolve()
    degrees = deepcopy(request_data)
    degrees["overview"]["join_ra_deg"] = degrees["overview"].pop("join_ra_hours") * 15
    degrees["tiling"]["seed_ra_deg"] = degrees["tiling"].pop("seed_ra_hours") * 15
    assert AtlasDesignRequest.from_dict(degrees).resolve().to_json() == hours.to_json()
    output = tmp_path / "atlas_design_v1.json"
    assert cli.design_main(["--config", str(EXAMPLE), "--output", str(output)]) == 0
    assert output.read_text() == hours.to_json()
    read = AtlasBandTiling.read_json(output)
    assert [len(b.sheet_ids) for b in read.bands] == [1, 5, 7, 8, 7, 5, 1]
    assert read.validation()["coverage_status"] == "validated_analytic_rectangle_bound"
    assert set(p.name for p in tmp_path.iterdir()) == {output.name}
    assert EXAMPLE.read_bytes() == original
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("section,key,value", [
    (None, "schema_version", True),
    (None, "schema_version", 2),
    (None, "projection", "gnomonic"),
    (None, "coordinate_frame", "fk5"),
    (None, "revision", 0),
    (None, "stars", []),
    ("page", "width_mm", "353"),
    ("page", "outer_mm", 400),
    ("overview", "join_ra_hours", 24),
    ("overview", "join_ra_hours", float("nan")),
    ("overview", "join_ra_deg", 82.5),
    ("tiling", "seed_ra_hours", True),
    ("tiling", "algorithm", "unknown"),
    ("tiling", "field_width_deg", float("inf")),
    ("tiling", "overlap_deg", -1),
    ("tiling", "max_sheets", 4097),
    ("tiling", "max_sheets", 33),
    ("tiling", "middle_boundary_dec_deg", 85),
    ("tiling", "equatorial_half_height_deg", None),
])
def test_request_faults_fail_before_returning_a_design(request_data, section, key, value):
    target = request_data if section is None else request_data[section]
    assert key not in target or type(target[key]) is not type(value) or target[key] != value
    target[key] = value
    with pytest.raises(ValueError):
        AtlasDesignRequest.from_dict(request_data).resolve()


def test_cap_layout_and_unknown_or_missing_nested_keys(request_data):
    tiling = request_data["tiling"]
    tiling.update(algorithm="cap_bands", field_width_deg=40, overlap_deg=2)
    # A five-band profile must not silently apply to the cap algorithm.
    with pytest.raises(ValueError):
        AtlasDesignRequest.from_dict(request_data)
    del tiling["equatorial_half_height_deg"], tiling["middle_boundary_dec_deg"]
    assert len(AtlasDesignRequest.from_dict(request_data).resolve().geometry.sheets) == 128
    del request_data["page"]["top_mm"]
    with pytest.raises(ValueError):
        AtlasDesignRequest.from_dict(request_data)


@pytest.mark.parametrize("case", ["existing", "symlink", "syntax", "unknown", "missing", "suffix", "parent"])
def test_cli_errors_preserve_input_and_existing_destinations(tmp_path, capsys, case):
    config = tmp_path / "request_v1.toml"
    text = EXAMPLE.read_text()
    if case == "syntax":
        text += '\nschema_version = 1\nschema_version = 2\n'
    if case == "unknown":
        text += '\nunknown = true\n'
    config.write_text(text)
    output = tmp_path / "design_v1.json"
    if case == "existing":
        output.write_text("preserved")
    if case == "symlink":
        output.symlink_to(tmp_path / "absent.json")
    if case == "missing":
        config.unlink()
    if case == "suffix":
        output = tmp_path / "design_v1.png"
    if case == "parent":
        output = tmp_path / "absent" / "design_v1.json"
    with pytest.raises(SystemExit) as exc:
        cli.design_main(["--config", str(config), "--output", str(output)])
    assert exc.value.code == 2
    assert "error:" in capsys.readouterr().err
    assert not list(tmp_path.glob(".wenu-atlas-*.tmp"))
    if case == "existing":
        assert output.read_text() == "preserved"
    elif case == "symlink":
        assert output.is_symlink() and not output.exists()
    else:
        assert not output.exists()


@pytest.mark.parametrize("fault", ["fsync", "race", "interrupt"])
def test_atomic_publication_failure_and_interruption_clean_temporary_files(tmp_path, monkeypatch, fault):
    output = tmp_path / "design_v1.json"
    def failed(*args):
        if fault == "interrupt":
            raise KeyboardInterrupt
        if fault == "race":
            output.write_text("concurrent winner")
            raise FileExistsError("Destination appeared during publication")
        raise OSError("Synthetic flush failure")
    monkeypatch.setattr(cli.os, "fsync" if fault == "fsync" else "link", failed)
    args = ["--config", str(EXAMPLE), "--output", str(output)]
    if fault == "interrupt":
        assert cli.design_main(args) == 130
    else:
        with pytest.raises(SystemExit) as exc:
            cli.design_main(args)
        assert exc.value.code == 2
    assert not list(tmp_path.glob(".wenu-atlas-*.tmp"))
    if fault == "race":
        assert output.read_text() == "concurrent winner"
    else:
        assert not output.exists()


def test_module_route_and_installed_entry_point(tmp_path):
    data = cli.tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert data["project"]["scripts"]["wenu_design_atlas"] == "wenu.cli.atlas:design_main"
    output = tmp_path / "design_v1.json"
    result = subprocess.run(
        [sys.executable, "-m", "wenu.cli.atlas", "--config", str(EXAMPLE),
         "--output", str(output)], text=True, capture_output=True,
        env=os.environ.copy(), timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    assert len(AtlasBandTiling.read_json(output).geometry.sheets) == 34


@pytest.fixture
def index_data():
    return cli.tomllib.loads((ROOT / "examples/atlas_index_style_v1.toml").read_text())


@pytest.mark.parametrize("group,key,value", [
    (None, "schema_version", True), (None, "schema_version", 2),
    (None, "document_kind", "chart"), (None, "unknown", 1),
    ("layout", "joined", "true"), ("layout", "width_mm", 0),
    ("layout", "height_mm", float("nan")), ("layout", "join_ra_hours", 5.5),
    ("content", "layers", ["planets"]), ("content", "layers", ["stars", "stars"]),
    ("content", "layers", ["constellation_boundaries"]),
    ("content", "star_magnitude_limit", "4.5"),
    ("content", "milky_way_levels", ["ol9"]),
    ("typography", "number_size_pt", True),
    ("colours", "ink_color", "not-a-colour"),
    ("export", "formats", []), ("export", "formats", ["png", "png"]),
    ("export", "formats", ["eps"]), ("export", "dpi", 160.5),
    ("export", "transparent", 1),
])
def test_index_request_rejects_unsupported_inputs(index_data, group, key, value):
    from wenu.charts.atlas_index import AtlasIndexPresentation
    data = deepcopy(index_data)
    (data if group is None else data[group])[key] = value
    with pytest.raises(ValueError):
        AtlasIndexPresentation.from_dict(data)


@pytest.mark.parametrize('orientation', ['landscape', 'portrait'])
def test_plot_cli_geometry_is_unchanged_and_exports_selected_formats(index_data, request_data, tmp_path, monkeypatch, capsys, orientation):
    from wenu.charts import atlas_index as index
    from dataclasses import replace
    from PIL import Image
    from xml.etree import ElementTree
    import wenu.atlas_design as geometry
    atlas = geometry.AtlasDesignRequest.from_dict(request_data).resolve()
    design = atlas.write_json(tmp_path / "design_v1.json")
    before = design.read_bytes()
    def forbidden(*args, **kwargs):
        raise AssertionError("Plotter must not design, observe or load sky in geometry-only mode")
    monkeypatch.setattr(geometry, "design_five_band_atlas", forbidden)
    monkeypatch.setattr(geometry, "design_band_atlas", forbidden)
    monkeypatch.setattr(index, "index_sky", forbidden)
    presentation = replace(index.AtlasIndexPresentation.from_dict(index_data),
        layers=(), milky_way_levels=(), transparent=True, number_size_pt=13,
        ink_color="#551177", paper_color="#f0e0c0", orientation=orientation)
    figures = []
    original = index.ExportOptions.save
    def capture(self, figure, path):
        if not figures:
            figures.append(figure)
        return original(self, figure, path)
    monkeypatch.setattr(index.ExportOptions, "save", capture)
    paths = index.plot_overview(design, tmp_path / "index_v1", presentation=presentation)
    assert {p.suffix for p in paths} == {".png", ".pdf", ".svg"}
    with Image.open(paths[0]) as image:
        assert image.size == ((2240, 1280) if orientation == 'landscape' else (1280, 2240))
        assert image.convert("RGBA").getpixel((0, 0))[3] == 0
    svg = ElementTree.parse(paths[2]).getroot()
    assert svg.get("width") == ('1008pt' if orientation == 'landscape' else '576pt')
    assert paths[1].read_bytes().startswith(b"%PDF-")
    number_labels = [t for ax in figures[0].axes for t in ax.texts if t.get_text().isdigit()]
    assert {int(t.get_text()) for t in number_labels} == set(range(1, 35))
    assert all(t.get_fontsize() == 13 and t.get_color() == "#551177" for t in number_labels)
    if orientation == 'portrait':
        assert figures[0].axes[0].get_position().y0 > figures[0].axes[1].get_position().y0
        assert [ax.get_gid() for ax in figures[0].axes] == ['atlas-index-south', 'atlas-index-north']
        assert any('south' in artist.get('id', '') for artist in svg.iter())
    assert design.read_bytes() == before
    with pytest.raises(FileExistsError):
        index.plot_overview(design, tmp_path / "index_v1", presentation=presentation)
    assert not list(tmp_path.glob(".wenu-index-*"))
    assert 'wenu_plot_atlas = "wenu.cli.atlas:plot_main"' in (ROOT / "pyproject.toml").read_text()


@pytest.mark.parametrize("layers,levels", [
    (("stars",), ()), (("milky_way",), ("ol3",)),
    (("constellation_lines", "constellation_labels"), ()),
    (("magellanic_clouds",), ()),
])
def test_index_selects_native_layers_without_observer(layers, levels, request_data, tmp_path, monkeypatch):
    from dataclasses import replace
    from wenu.charts import atlas_index as index
    from wenu.observer import Observer
    from wenu.coordinate_service import CoordinateService
    atlas = AtlasDesignRequest.from_dict(request_data).resolve()
    design = atlas.write_json(tmp_path / "design_v1.json")
    def forbidden(*args, **kwargs):
        raise AssertionError("Native index requested observation or an observer")
    monkeypatch.setattr(Observer, "__init__", forbidden)
    monkeypatch.setattr(CoordinateService, "transform_observer_geometry", forbidden)
    results = []
    original = index.CelestialSphere.draw_chart
    def capture(self, **kwargs):
        result = original(self, **kwargs)
        results.append(result)
        return result
    monkeypatch.setattr(index.CelestialSphere, "draw_chart", capture)
    config = replace(index.AtlasIndexPresentation(), layers=layers,
                     milky_way_levels=levels, formats=("svg",))
    index.plot_overview(design, tmp_path / "native_v1", presentation=config)
    assert len(results) == 2
    expected = {"milky_way_isophotes" if v == "milky_way" else
                "magellanic_cloud_isophotes" if v == "magellanic_clouds" else v for v in layers}
    for result in results:
        assert {r.layer.layer_name for r in result.layers} == expected
        assert all(r.spherical.coordinate_spec.frame == "icrs" for r in result.layers)
        for r in result.layers:
            if r.layer.layer_name == "milky_way_isophotes":
                assert set(r.spherical.metadata["level"]) == set(levels)


@pytest.mark.parametrize("fault", ["render", "publication", "interrupt"])
def test_index_failed_batch_removes_only_its_outputs(fault, request_data, tmp_path, monkeypatch):
    from wenu.charts import atlas_index as index
    atlas = AtlasDesignRequest.from_dict(request_data).resolve()
    design = atlas.write_json(tmp_path / "design_v1.json")
    save = index.ExportOptions.save
    link = index.os.link
    count = 0
    def fail_save(self, figure, path):
        nonlocal count
        count += 1
        if count == 2:
            raise OSError("export failed")
        return save(self, figure, path)
    def fail_link(source, destination):
        nonlocal count
        count += 1
        if count == 2:
            if fault == "interrupt":
                raise KeyboardInterrupt()
            Path(destination).write_bytes(b"concurrent winner")
            raise FileExistsError("concurrent winner")
        return link(source, destination)
    monkeypatch.setattr(index.ExportOptions, "save", fail_save if fault == "render" else save)
    monkeypatch.setattr(index.os, "link", fail_link if fault != "render" else link)
    with pytest.raises(KeyboardInterrupt if fault == "interrupt" else OSError):
        index.plot_overview(design, tmp_path / "index_v1", presentation=index.AtlasIndexPresentation())
    assert not (tmp_path / "index_v1.png").exists()
    assert not (tmp_path / "index_v1.svg").exists()
    if fault == "publication":
        assert (tmp_path / "index_v1.pdf").read_bytes() == b"concurrent winner"
    else:
        assert not (tmp_path / "index_v1.pdf").exists()
    assert not list(tmp_path.glob(".wenu-index-*"))


def test_plot_cli_example_and_closed_errors(request_data, tmp_path, capsys):
    atlas = AtlasDesignRequest.from_dict(request_data).resolve()
    design = atlas.write_json(tmp_path / "design_v1.json")
    config = ROOT / "examples/atlas_index_style_v1.toml"
    arguments = ["--design", str(design), "--config", str(config),
                 "--output-prefix", str(tmp_path / "index_v1")]
    assert cli.plot_main(arguments) == 0
    assert len(capsys.readouterr().out.splitlines()) == 3
    with pytest.raises(SystemExit) as exc:
        cli.plot_main(arguments)
    assert exc.value.code == 2
    with pytest.raises(SystemExit):
        cli.plot_main(arguments + ["--position-angle", "10"])
    assert not list(tmp_path.glob(".wenu-index-*"))


@pytest.mark.parametrize("change", [
    {"enabled": "true"}, {"color": "unknown-colour"}, {"opacity": True},
    {"opacity": -0.1}, {"opacity": 1.1}, {"opacity": float("nan")},
    {"extra": 1},
])
def test_veil_admission_is_closed_and_finite(index_data, change):
    from wenu.charts.atlas_index import AtlasIndexPresentation
    index_data["veil"] = {"enabled": True, "color": "white", "opacity": 0.55}
    index_data["veil"].update(change)
    with pytest.raises(ValueError):
        AtlasIndexPresentation.from_dict(index_data)


@pytest.mark.parametrize("enabled,opacity,expected", [(False, 0.55, False),
    (True, 0, False), (True, 0.55, True), (True, 1, True)])
def test_veil_is_between_native_objects_and_index_borders_and_numbers(
        request_data, enabled, opacity, expected, monkeypatch):
    from dataclasses import replace
    from wenu.charts import atlas_index as index
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.colors import to_rgba
    atlas = AtlasDesignRequest.from_dict(request_data).resolve()
    figure = Figure(figsize=(14, 8))
    FigureCanvasAgg(figure)
    ax = figure.add_subplot()
    celestial = []
    original = index.PolarPlanisphereChart.render
    def capture(self, sky, renderer, **kwargs):
        result = original(self, sky, renderer, **kwargs)
        celestial.extend(a for a in (*ax.lines, *ax.patches, *ax.collections, *ax.texts)
                         if getattr(a, "_wenu_svg_semantics", None))
        return result
    monkeypatch.setattr(index.PolarPlanisphereChart, "render", capture)
    sky = index.index_sky(4.5, layers=("stars",))
    presentation = replace(index.AtlasIndexPresentation(), layers=("stars",),
        veil_enabled=enabled, veil_color="#ffeedd", veil_opacity=opacity)
    face = index.overview_face(atlas.geometry.overview, "north")
    index._draw_face(ax, atlas, face, footprints=True, sky=sky,
                    presentation=presentation, star_magnitude_limit=4.5)
    veils = [p for p in ax.patches if p.get_gid() == "atlas-index-veil-north"]
    assert bool(veils) == expected
    assert {int(t.get_text()) for t in ax.texts if t.get_text().isdigit()} >= {34}
    if expected:
        veil = veils[0]
        assert veil.get_alpha() == opacity
        assert veil.get_facecolor() == to_rgba("#ffeedd", opacity)
        assert all(a.get_zorder() < veil.get_zorder() for a in celestial)
        overlay = [a for a in (*ax.lines, *ax.patches, *ax.collections, *ax.texts)
                   if a not in celestial and a is not veil]
        assert overlay and all(a.get_zorder() > veil.get_zorder() for a in overlay)
        index._join_faces(figure, (ax, figure.add_subplot()), atlas)
        assert veil.get_clip_box() is not None


def test_veil_example_exports_svg_without_modifying_design(request_data, tmp_path):
    from wenu.charts.atlas_index import AtlasIndexPresentation
    from xml.etree import ElementTree
    old = cli.tomllib.loads((ROOT / "examples/atlas_index_style_v1.toml").read_text())
    assert not AtlasIndexPresentation.from_dict(old).veil_enabled
    config = ROOT / "examples/atlas_index_style_v2.toml"
    data = cli.tomllib.loads(config.read_text())
    assert AtlasIndexPresentation.from_dict(data).veil_opacity == 0.55
    design = AtlasDesignRequest.from_dict(request_data).resolve().write_json(tmp_path / "design_v1.json")
    before = design.read_bytes()
    assert cli.plot_main(["--design", str(design), "--config", str(config),
        "--output-prefix", str(tmp_path / "veiled_index_v2")]) == 0
    svg = ElementTree.parse(tmp_path / "veiled_index_v2.svg")
    ids = {e.get("id") for e in svg.getroot().iter()}
    assert {"atlas-index-veil-north", "atlas-index-veil-south"} <= ids
    elements = list(svg.getroot().iter())
    all_ids = [e.get("id") for e in elements if e.get("id")]
    assert len(all_ids) == len(set(all_ids))
    by_id = {e.get("id"): e for e in elements}
    parent_of = {child: parent for parent in elements for child in parent}
    label_attr = "{http://www.inkscape.org/namespaces/inkscape}label"
    assert by_id["atlas-index"].get(label_attr) == "Atlas Index"
    for pole in ("north", "south"):
        disk = by_id[f"atlas-index-{pole}"]
        assert disk.get(label_attr) == f"{pole.capitalize()} Disk"
        folders = {e.get(label_attr): e for e in disk}
        assert {"Stars", "Constellations", "Milky Way", "Veil", "Guides", "Charts", "Heading"} <= folders.keys()
        assert not {"Chart", "Atlas Index", "Celestial content", "Atlas Charts"} & folders.keys()
        charts = folders["Charts"]
        chart_names = [e.get(label_attr) for e in charts]
        assert len(chart_names) == len(set(chart_names))
        for chart in charts:
            assert chart.get(label_attr).startswith("Chart ")
            assert {e.get(label_attr) for e in chart} <= {"Label", "Primary Boundary", "Full Footprint"}
        assert all(e.get("id", "").startswith("star-hip-") or e.tag.endswith("}defs")
                   for e in folders["Stars"])
        veil_position = elements.index(by_id[f"atlas-index-veil-{pole}"])
        numbers = [e for e in elements if e.get("data-role") == "number_label"
                   and e.get("id", "").endswith(pole)]
        boundaries = [e for e in elements if e.get("data-role") in {"primary_boundary", "footprint"}
                      and e.get("id", "").endswith(pole)]
        assert numbers and boundaries
        assert all(elements.index(e) > veil_position for e in numbers + boundaries)
        for e in numbers + boundaries:
            number = int(e.get("data-chart-number"))
            assert f"chart_{number:02d}" in e.get("data-wenu-semantic-path")
            assert parent_of[e].get(label_attr) == f"Chart {number}"
            assert parent_of[parent_of[e]] is charts
            if e.get("data-role") != "number_label":
                assert e.tag.endswith("}path")
            else:
                assert {child.get(label_attr) for child in e} == {"Background", "Text"}
        stars = [e for e in elements if e.get("id", "").startswith("star-hip-")
                 and (e.get("id").endswith(pole) or f"-{pole}-overlay-" in e.get("id"))]
        assert stars and all(elements.index(e) < veil_position for e in stars)
        assert all(e.get("data-wenu-display-name", "").startswith("HIP ") for e in stars)
        primary = by_id[f"chart-14-primary-boundary-{pole}"]
        clip = by_id[primary.get("clip-path")[5:-1]]
        rectangle = next(iter(clip))
        assert rectangle.tag.endswith("}rect")
        assert float(rectangle.get("x")) == pytest.approx(0 if pole == "north" else 504)
        assert float(rectangle.get("width")) == pytest.approx(504)
        assert rectangle.get("clip-path") is not None
    assert {int(e.get("data-chart-number")) for e in elements
            if e.get("data-role") == "number_label"} == set(range(1, 35))
    assert "chart-14-number-label-north" in ids
    assert "chart-14-number-label-south" in ids
    assert "chart-34-footprint-south" not in ids
    assert "chart-01-footprint-north" not in ids
    assert design.read_bytes() == before


def test_chart_presentation_is_closed_and_rejects_nonstatic_inputs():
    from wenu.charts.atlas_publication import AtlasChartPresentation
    data = cli.tomllib.loads((ROOT / 'examples/atlas_chart_style_v1.toml').read_text())
    assert AtlasChartPresentation.from_dict(data).formats == ('png', 'pdf', 'svg')
    for change in ({'observer': 'La Ligua'}, {'dpi': True}, {'dpi': 0},
                   {'star_magnitude_limit': 12}, {'layers': ['satellites']},
                   {'star_size_scale': 0}, {'star_size_scale': True},
                   {'star_size_scale': float('inf')}, {'star_size_scale': 1e200},
                   {'layers': 'stars'}, {'formats': ['png']},
                   {'formats': ['pdf', 'pdf']}, {'schema_version': True},
                   {'report_label_scale': 0}, {'report_label_scale': float('nan')},
                   {'report_label_family': ''}, {'report_label_weight': 'invalid'},
                   {'report_label_color': 'invalid-color'}, {'report_separator_width': -1},
                   {'report_separator_gap_mm': True}, {'chart_number_box_visible': 1},
                   {'chart_number_box_location': 'outside'}, {'chart_number_box_alpha': 2},
                   {'chart_number_box_padding': -1}, {'chart_number_box_facecolor': 'invalid'},
                   {'magnitude_veil_alpha': -1}, {'magnitude_veil_alpha': 1.1},
                   {'magnitude_veil_alpha': True}, {'magnitude_veil_color': 'invalid'},
                   {'planetary_nebula_symbol_scale': 0}, {'planetary_nebula_symbol_scale': 1e200},
                   {'planetary_nebula_color': 'invalid'}, {'planetary_nebula_linewidth': -1}):
        with pytest.raises(ValueError):
            AtlasChartPresentation.from_dict(dict(data, **change))


def test_sheet_adapter_preserves_exact_json_projection_viewport_and_paper(request_data):
    import numpy as np
    from wenu.charts.atlas_publication import AtlasSheetChart
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    atlas = AtlasDesignRequest.from_dict(request_data).resolve()
    for sheet in atlas.geometry.sheets:
        chart = AtlasSheetChart(sheet, atlas.geometry.page)
        assert chart.viewport == sheet.viewport(atlas.geometry.page)
        np.testing.assert_array_equal(chart.projection.frame.rotation_matrix,
                                      sheet.frame.rotation_matrix)
        x, y = chart.projection.project_spherical(sheet.center_ra_deg, sheet.center_dec_deg)
        np.testing.assert_array_equal([x, y], sheet.projection.project_spherical(sheet.center_ra_deg, sheet.center_dec_deg))
        assert chart.chart_context.tangent_longitude_deg == sheet.center_ra_deg
        with pytest.raises(ValueError, match='native ICRS'):
            chart.render(None, None)
        with pytest.raises(ValueError, match='observer'):
            chart.render(None, None, observer=object(),
                         realization_context=LayerRealizationContext(NATIVE_ICRS_SPEC))


def test_atlas_create_cli_rejects_selector_before_preparation(request_data, tmp_path, monkeypatch):
    from wenu.sky import native_snapshot
    atlas = AtlasDesignRequest.from_dict(request_data).resolve()
    design = tmp_path / 'design.json'
    design.write_text(atlas.to_json())
    def forbidden(*args, **kwargs):
        raise AssertionError('Invalid requests must not prepare the sky')
    monkeypatch.setattr(native_snapshot, 'prepare_native_sky_snapshot', forbidden)
    for extra in (['--charts', '0'], ['--jobs', '0'],
                  ['--mag-a', '0.5'], ['--mag-algorithm', 'taki'],
                  ['--mag-algorithm', 'asinh', '--mag-dmin', '0'],
                  ['--mag-algorithm', 'asinh', '--mag-size-reference', '5'],
                  ['--magnitude-limit', '12'], ['--magnitude-limit', 'nan'],
                  ['--save-sky', str(tmp_path/'sky'), '--from-sky', 'other'],
                  ['--index', str(tmp_path/'missing.pdf')]):
        with pytest.raises(SystemExit) as exc:
            cli.create_main(['--design', str(design), '--config', str(ROOT/'examples/atlas_chart_style_v1.toml'),
                             '--output-dir', str(tmp_path/'output'), *extra])
        assert exc.value.code == 2
    assert not (tmp_path/'output').exists()
    from wenu.atlas_design import AtlasBandTiling
    mixed = ROOT/'examples/atlas_design_36charts_v1.json'
    assert len({s.field_width_deg for s in AtlasBandTiling.from_json(mixed.read_text()).geometry.sheets}) == 2
    with pytest.raises(SystemExit):
        cli.create_main(['--design',str(mixed),'--config',str(ROOT/'examples/atlas_chart_style_v1.toml'),
                         '--output-dir',str(tmp_path/'output')])


def test_atlas_cli_passes_sizing_overrides_without_building_a_sky(tmp_path, monkeypatch):
    from wenu.charts import atlas_publication
    calls = []
    def capture(*args, **kwargs):
        calls.append(kwargs)
        return tmp_path/'manifest.json'
    monkeypatch.setattr(atlas_publication, 'create_atlas', capture)
    assert cli.create_main(['--design', 'design.json', '--config', str(ROOT/'examples/atlas_chart_style_v1.toml'),
        '--output-dir', str(tmp_path/'atlas'), '--from-sky', 'saved-sky', '--magnitude-limit', '8',
        '--mag-algorithm', 'asinh', '--mag-a', '.4', '--mag-b', '2', '--mag-dmin', '.3',
        '--mag-size-reference', '8', '--star-size-scale', '1', '--style', 'cartoon',
        '--mode', 'presentation', '--open-cluster-size', 'fixed']) == 0
    presentation = calls[0]['presentation']
    assert presentation.stellar_magnitude_sizing.algorithm == 'asinh'
    assert presentation.stellar_magnitude_sizing.a_mm == .4
    assert presentation.stellar_magnitude_sizing.b_mag == 2
    assert presentation.star_magnitude_limit == 8
    assert presentation.star_size_scale == 1
    assert presentation.mode == 'presentation' and presentation.style == 'cartoon'
    assert presentation.open_cluster_angular_sizes is False
    assert calls[0]['from_sky'] == Path('saved-sky')
    from wenu.cli.chart import main as chart_command
    assert calls[0]['chart_command'] is chart_command


def test_atlas_index_rejects_multiple_pages_before_preparation(request_data, tmp_path, monkeypatch):
    from pypdf import PdfWriter
    from wenu.charts.atlas_publication import AtlasChartPresentation, create_atlas
    from wenu.sky import native_snapshot
    design = tmp_path/'design.json'
    design.write_text(AtlasDesignRequest.from_dict(request_data).resolve().to_json())
    index = tmp_path/'two-pages.pdf'
    with PdfWriter() as writer:
        writer.add_blank_page(width=100,height=100)
        writer.add_blank_page(width=100,height=100)
        writer.write(index)
    def forbidden(*args, **kwargs):
        raise AssertionError('Invalid index must fail before sky preparation')
    monkeypatch.setattr(native_snapshot,'prepare_native_sky_snapshot',forbidden)
    with pytest.raises(ValueError,match='one-page'):
        create_atlas(design,tmp_path/'output',presentation=AtlasChartPresentation(),index=index)
    assert not (tmp_path/'output').exists()


@pytest.mark.parametrize('typography', [{}, dict(report_label_scale=2, report_label_family='serif',
    report_label_weight='bold', report_label_color='#005577', report_separator_width=1.2,
    report_separator_gap_mm=5)])
@pytest.mark.parametrize('dimensions', [(353,250),(250,353)])
@pytest.mark.parametrize('stars', [True,False])
@pytest.mark.parametrize('polar', [False,True])
def test_reserved_report_mirrors_binding_margin_and_keeps_legends_at_right(typography, dimensions, stars, polar, tmp_path, monkeypatch):
    from types import SimpleNamespace
    import matplotlib.pyplot as plt
    import numpy as np
    from wenu.atlas_design import AtlasPageGeometry
    from wenu.charts.atlas_publication import _render_atlas_report, AtlasChartPresentation
    presentation = AtlasChartPresentation(**typography)
    from wenu.charts import automatic_legends
    from wenu.charts.regional import ExportOptions
    page = AtlasPageGeometry(*dimensions,top_mm=18,bottom_mm=15,inner_mm=25,outer_mm=12)
    from wenu.geometry.viewport import Viewport
    chart = SimpleNamespace(page=page,sheet=SimpleNamespace(number=14,
        sheet_id='test-sheet',boundary_kind='rectangle',center_ra_deg=0 if polar else 82.5,
        center_dec_deg=90 if polar else 0,pole_meridian_ra_deg=82.5 if polar else None))
    from wenu.charts.presets import AtlasChartStyle
    composition = SimpleNamespace(style=replace(AtlasChartStyle(), legend=replace(
        AtlasChartStyle().legend, title_fontsize=6.5)),detail=SimpleNamespace(star_magnitude_limit=6,
                                  enabled_layers={'stars'} if stars else {'galaxies'}),
                                  mode=SimpleNamespace(dpi=150))
    star_layer = object()
    sky = SimpleNamespace(stars=star_layer)
    rendering = SimpleNamespace(viewport=Viewport.centered(width=2,height=2), layers=(
        SimpleNamespace(layer=star_layer,
            spherical=SimpleNamespace(metadata={'magnitude': np.array([1.1,5.8,-1.5])}),
            projected=SimpleNamespace(x=np.array([0,0,3]),y=np.array([0,0,0]))),))
    calls = []
    def legend(ax, actual_chart, sky, style, result, **options):
        assert actual_chart is chart and result is rendering
        assert style.legend.fontsize == presentation.legend_fontsize
        assert style.legend.title_fontsize == presentation.legend_fontsize
        assert options['resolved_detail'] is composition.detail
        assert options['include_context'] is True
        if polar:
            assert options['object_title'] == 'Centre: ICRS\nRA undefined (pole)\nDec +90d00m00s\nMeridian 05h30m00s'
        else:
            assert options['object_title'] == 'Centre: ICRS\nRA 05h30m00s\nDec +00d00m00s'
        assert options['stellar_reference_range'] == (-2,8)
        assert options['stellar_report_range'] is True
        assert options['object_marker_scale'] == presentation.deep_sky_symbol_scale
        assert options['stellar_title'] == ('Star magnitude (2)' if stars else 'Star magnitude')
        assert options['plan'].objects.location == 'upper right'
        assert options['plan'].stars.location == 'lower right'
        assert options['plan'].stars.enabled is stars
        calls.append(1)
        artist = ax.legend([], [], title=options['object_title'], loc='upper right', title_fontsize=6.5)
        return SimpleNamespace(artists=(artist,), legends=SimpleNamespace(objects=artist))
    def save(self, figure, destination):
        assert destination.stem == 'chart-14_report' and self.bbox_inches is None
        assert destination.suffix in ('.png','.pdf','.svg')
        np.testing.assert_allclose(figure.get_size_inches(), np.array(dimensions)/25.4)
        ax = figure.axes[0]
        np.testing.assert_allclose(ax.get_position().bounds,
            [page.outer_mm/page.width_mm,page.bottom_mm/page.height_mm,
             page.useful_width_mm/page.width_mm,page.useful_height_mm/page.height_mm])
        assert all(spine.get_visible() for spine in ax.spines.values())
        ax = figure.axes[1]
        np.testing.assert_allclose(ax.get_position().bounds[:3],
            [(page.outer_mm+0.68*page.useful_width_mm)/page.width_mm,
             (page.bottom_mm+4)/page.height_mm,(0.32*page.useful_width_mm-4)/page.width_mm])
        legend = ax.get_legend()
        heading = legend._wenu_heading
        assert heading.get_text() == 'Chart 14' and heading.get_fontsize() == 6.5 * presentation.report_label_scale
        assert heading.get_color() == presentation.report_label_color
        assert heading.get_fontfamily() == [presentation.report_label_family]
        assert heading.get_fontweight() == presentation.report_label_weight
        separator = legend._wenu_separator
        assert separator.get_linewidth() == presentation.report_separator_width
        assert separator.get_color() == presentation.report_label_color
        renderer = figure.canvas.get_renderer()
        frame_bounds = legend.get_frame().get_window_extent(renderer)
        heading_bounds = heading.get_window_extent(renderer)
        separator_bounds = separator.get_window_extent(renderer)
        metadata_bounds = legend.get_title().get_window_extent(renderer)
        assert frame_bounds.contains(heading_bounds.x0, heading_bounds.y1)
        assert frame_bounds.contains(separator_bounds.x1, separator_bounds.y0)
        assert heading_bounds.y0 > separator_bounds.y0 > metadata_bounds.y1
        assert ax.get_window_extent(renderer).contains(frame_bounds.x0, frame_bounds.y0)
        assert figure.texts[0].get_position()[0] == page.outer_mm/page.width_mm
    monkeypatch.setattr(automatic_legends,'draw_automatic_chart_legends',legend)
    monkeypatch.setattr(ExportOptions,'save',save)
    before = plt.get_fignums()
    _render_atlas_report(chart,sky,composition,rendering,tmp_path,presentation=presentation)
    assert calls == [1] and plt.get_fignums() == before
    import json
    data = json.loads((tmp_path/'chart-14_report_data.json').read_text())
    assert data['chart_number'] == 14 and data['center']['ra_deg'] == (0 if polar else 82.5)
    assert data['center']['ra_defined'] is (not polar)
    assert data['report']['inventory_status'] == 'not_generated'
    assert data['report']['sections'] == []
    if stars:
        assert data['stars']['reference_range'] == [1,6]
        assert data['stars']['statistics']['visible_count'] == 2
        assert data['stars']['statistics']['brightest_magnitude'] == 1.1


@pytest.mark.parametrize('dimensions', [(353,250),(250,353)])
def test_atlas_index_keeps_vector_text_and_paper_orientation(dimensions):
    import io
    import matplotlib.pyplot as plt
    import numpy as np
    from pypdf import PdfReader, PdfWriter
    from wenu.atlas_design import AtlasPageGeometry
    from wenu.charts.atlas_publication import _append_atlas_index
    raw = io.BytesIO()
    figure = plt.figure(figsize=(14,8))
    figure.text(0.5,0.5,'Vector index')
    figure.savefig(raw,format='pdf')
    plt.close(figure)
    reader = PdfReader(raw)
    reader.pages[0].rotate(90)
    page = AtlasPageGeometry(*dimensions,top_mm=18,bottom_mm=15,inner_mm=25,outer_mm=12)
    with PdfWriter() as writer:
        _append_atlas_index(writer,reader,page)
        output = io.BytesIO()
        writer.write(output)
    final = PdfReader(output).pages[0]
    assert final.rotation == 0 and reader.pages[0].rotation == 90
    assert 'Vector index' in final.extract_text()
    np.testing.assert_allclose([float(final.mediabox.width),float(final.mediabox.height)],
                              np.array(dimensions)*72/25.4)
    assert not final.images


@pytest.mark.parametrize("location", ["upper right", "upper left", "lower right", "lower left"])
def test_atlas_number_box_is_inside_and_flush_with_selected_frame_corner(location):
    from types import SimpleNamespace
    import numpy as np
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from wenu.charts.atlas_publication import AtlasChartPresentation, _draw_atlas_chart_number
    figure = Figure(figsize=(353 / 25.4, 250 / 25.4))
    FigureCanvasAgg(figure)
    ax = figure.add_axes((0.1, 0.1, 0.8, 0.8))
    style = SimpleNamespace(legend=SimpleNamespace(title_fontsize=6.5))
    presentation = AtlasChartPresentation(chart_number_box_location=location)
    artist = _draw_atlas_chart_number(ax, 10, style, presentation)
    figure.canvas.draw()
    renderer = figure.canvas.get_renderer()
    frame = ax.get_window_extent(renderer)
    box = artist.patch.get_window_extent(renderer)
    np.testing.assert_allclose(box.x1 if "right" in location else box.x0,
                               frame.x1 if "right" in location else frame.x0)
    np.testing.assert_allclose(box.y1 if "upper" in location else box.y0,
                               frame.y1 if "upper" in location else frame.y0)
    assert box.x0 >= frame.x0 - 1e-8 and box.x1 <= frame.x1 + 1e-8
    assert box.y0 >= frame.y0 - 1e-8 and box.y1 <= frame.y1 + 1e-8
    assert artist.txt.get_text() == "10" and artist.txt._text.get_fontsize() == 19.5
    assert not figure.texts
    assert _draw_atlas_chart_number(ax, 10, style,
        AtlasChartPresentation(chart_number_box_visible=False)) is None


@pytest.mark.parametrize("orientation", ["portrait", "landscape", "portrait_32charts"])
def test_automatic_request_retains_geometry_inputs_and_computed_layout(tmp_path, orientation):
    data = cli.tomllib.loads((ROOT / "examples/atlas_design_request_v2.toml").read_text())
    independent = orientation == "portrait_32charts"
    if independent:
        orientation = "portrait"
        data["tiling"].pop("field_width_deg")
        data["tiling"].update(field_height_deg=55, polar_primary_diameter_deg=40)
    data["page"]["orientation"] = orientation
    request = AtlasDesignRequest.from_dict(data)
    atlas = request.resolve()
    result = atlas.to_dict()
    assert result["design_request"]["page"]["orientation"] == orientation
    assert "algorithm" not in result["design_request"]["tiling"]
    assert result["layout"]["orientation"] == orientation
    assert sum(result["layout"]["charts_per_band"]) == len(atlas.geometry.sheets)
    assert atlas.validation()["shared_boundary_overlap_lower_bound_deg"] >= 0.25
    assert AtlasBandTiling.from_json(atlas.to_json()) == atlas
    if independent:
        assert result["layout"]["charts_per_band"] == [1, 10, 10, 10, 1]
        assert result["layout"]["field_height_deg"] == pytest.approx(55)
        assert result["layout"]["polar_primary_diameter_deg"] == pytest.approx(40)
        changed = deepcopy(result)
        changed["design_request"]["tiling"]["polar_primary_diameter_deg"] = 42
        with pytest.raises(ValueError, match="does not match"):
            AtlasBandTiling.from_dict(changed)
    # A loaded design is validated, not silently retiled; redundant summary
    # and request geometry must agree with the persisted scientific geometry.
    changed = deepcopy(result)
    changed["layout"]["interior_band_count"] += 2
    with pytest.raises(ValueError):
        AtlasBandTiling.from_dict(changed)
    changed = deepcopy(result)
    changed["design_request"]["tiling"]["field_width_deg"] = 60
    with pytest.raises(ValueError):
        AtlasBandTiling.from_dict(changed)
    changed = deepcopy(data)
    changed["tiling"]["max_sheets"] = 5
    with pytest.raises(ValueError, match="No polar-first"):
        AtlasDesignRequest.from_dict(changed).resolve()
    for section, key, value in (("page", "orientation", "sideways"),
                                ("page", "paper_size", "unknown"),
                                ("tiling", "algorithm", "five_band")):
        changed = deepcopy(data)
        changed[section][key] = value
        with pytest.raises(ValueError):
            AtlasDesignRequest.from_dict(changed)

@pytest.mark.parametrize("polar", [False, "south", "north"])
@pytest.mark.parametrize("lines_visible", [False, True])
@pytest.mark.parametrize("orientation", ["landscape", "portrait"])
@pytest.mark.parametrize("minute_labels_visible", [False, True])
def test_atlas_coordinate_grid_uses_canonical_native_route_and_reserved_frame(
        request_data, polar, lines_visible, orientation, minute_labels_visible, tmp_path, monkeypatch):
    import matplotlib.pyplot as plt
    import numpy as np
    from wenu import CelestialSphere
    from wenu.charts.atlas_publication import (AtlasSheetChart, AtlasChartPresentation,
        _atlas_grid_options, _atlas_grid_layout, _atlas_tick_options, _atlas_frame_widths,
        _draw_atlas_magnitude_scale)
    from wenu.charts.composition import compose_chart
    from wenu.charts.detail import DetailOverrides
    from wenu.charts.modes import PrintMode
    from wenu.charts.export_workflow import export_composed_chart
    from wenu.charts.regional import ExportOptions
    from wenu.rendering.matplotlib import MatplotlibRenderer
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    request_data = deepcopy(request_data)
    if orientation == 'portrait':
        request_data['page'].update(width_mm=250,height_mm=353)
    atlas = AtlasDesignRequest.from_dict(request_data).resolve()
    page = atlas.geometry.page
    sheet = atlas.geometry.sheets[0 if polar == 'south' else -1 if polar == 'north' else 13]
    chart = AtlasSheetChart(sheet,page)
    presentation = AtlasChartPresentation(layers=("equatorial_grid",),grid_lines_visible=lines_visible,
        grid_minute_labels_visible=minute_labels_visible)
    sky = CelestialSphere(None)
    layer = sky.add_equatorial_grid(frame="icrs",equinox="J2000",include_equator=True)
    composition = compose_chart(chart,style="atlas",mode=PrintMode(
        width_inches=page.width_mm/25.4,height_inches=page.height_mm/25.4,dpi=150),
        detail_overrides=DetailOverrides(enabled_layers=frozenset({"equatorial_grid"})))
    bounds, style = _atlas_grid_layout(page,composition.style,presentation)
    assert bounds[2]*page.width_mm/page.useful_width_mm == pytest.approx(
        bounds[3]*page.height_mm/page.useful_height_mm)
    assert bounds[2] < page.useful_width_mm/page.width_mm
    assert chart.viewport == sheet.viewport(page)
    # Definition of the 50% wider band is explicit and physically reproducible.
    baseline = 12+2*(composition.style.canvas.grid_label_band_padding_points+
        composition.style.canvas.grid_label_band_linewidth/2)
    horizontal, vertical = _atlas_frame_widths(style, presentation)
    assert horizontal == pytest.approx(baseline*1.5)
    composition = replace(composition,style=style)
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    # Match production atlas-sheet physical geometry. A GUI manager can round
    # set_size_inches() to device pixels (observed on Mac landscape pages).
    # Keep every margin, attachment, collision and tick assertion strict.
    def refuse_gui_figure(*args, **kwargs):
        raise AssertionError("Physical atlas layout must not depend on pyplot GUI sizing.")
    monkeypatch.setattr(plt, "figure", refuse_gui_figure)
    fig = Figure(figsize=(page.width_mm / 25.4, page.height_mm / 25.4), dpi=100)
    FigureCanvasAgg(fig)
    assert fig.canvas.manager is None
    renderer = MatplotlibRenderer(fig.add_axes(bounds))
    renderer.configure_grid_label_frame(horizontal_points=horizontal,
        vertical_points=vertical, polar=bool(polar))
    result = export_composed_chart(chart,sky,renderer,tmp_path/'grid.svg',
        composition=composition,layer_options=_atlas_grid_options(chart,presentation),
        realization_context=LayerRealizationContext(NATIVE_ICRS_SPEC),
        export_options=ExportOptions(dpi=150,bbox_inches=None),
        additional_furniture=lambda **options: _draw_atlas_magnitude_scale(**options, presentation=presentation))
    assert layer.ra is None and layer.dec is None
    rendered = result.rendering.layers[0]
    assert rendered.spherical.coordinate_spec.frame == 'icrs'
    assert len(rendered.spherical.components['meridians']) == (12 if polar else 24)
    assert len(rendered.spherical.components['parallels']) == 17
    ticks = [a for a in rendered.artists if getattr(a,'_wenu_semantic_component',None)=='ticks']
    lines = [a for a in rendered.artists if getattr(a,'_wenu_semantic_component',None)=='lines']
    texts = [t for t in renderer.ax.texts if t.get_visible()]
    assert ticks and texts
    assert all(t.get_text().endswith(('ʰ','ᵐ','°')) for t in texts)
    assert all(t.get_fontsize()==pytest.approx(9 if t.get_text().endswith('ᵐ') else 9.6 if t.get_text().endswith('°') else 12) for t in texts)
    assert all(a.get_linewidth()==0 for a in lines) == (not lines_visible)
    assert all(a.get_alpha()==0.65 for a in lines)
    if polar:
        # A meridian meets a polar sheet boundary once. The antipode must not
        # add a spurious second crossing through the chart.
        from collections import Counter
        assert all(count==1 for count in Counter(t.get_text() for t in texts
                   if t.get_text().endswith('ʰ')).values())
    assert 'ticks' in (tmp_path/'grid.svg').read_text()
    fig.canvas.draw()
    outer = renderer._grid_label_band_frame.get_path().transformed(renderer._grid_label_band_frame.get_transform())
    for text in texts:
        if text.get_text().endswith('°') and not hasattr(text, '_wenu_polar_grid_anchor'):
            matching=[mark for mark in ticks if np.allclose(mark.get_xydata()[0],text.get_position(),atol=1e-12)]
            direction=np.array([np.cos(np.radians(text.get_rotation())),np.sin(np.radians(text.get_rotation()))])
            assert matching and any(abs(np.cross(direction,
                np.diff(renderer.ax.transData.transform(mark.get_xydata()),axis=0)[0])) < 1e-7
                for mark in matching)
        box = text.get_window_extent(fig.canvas.get_renderer())
        if hasattr(text, '_wenu_exterior_attachment'):
            position, direction = text._wenu_exterior_attachment
            edge = renderer.ax.transData.transform(position)
            axis = 1 if text._wenu_grid_edge_horizontal else 0
            gap = ((box.y0-edge[1] if direction[1] > 0 else edge[1]-box.y1)
                   if axis == 1 else
                   (box.x0-edge[0] if direction[0] > 0 else edge[0]-box.x1))
            assert gap*72/fig.dpi >= (style.canvas.grid_label_band_padding_points +
                style.canvas.grid_label_band_linewidth/2) - 1e-7
        if hasattr(text, '_wenu_polar_grid_anchor'):
            sky_box = renderer.ax.get_window_extent()
            assert sky_box.contains(box.x0,box.y0) and sky_box.contains(box.x1,box.y1)
        assert outer.contains_points([[box.x0,box.y0],[box.x1,box.y1]]).all()
        assert not any(box.overlaps(other.get_window_extent(fig.canvas.get_renderer()))
                       for other in texts if other is not text)
    outer_mm = outer.vertices * 25.4 / fig.dpi
    assert outer_mm[:,0].min() >= page.inner_mm-1e-6
    assert outer_mm[:,0].max() <= page.width_mm-page.outer_mm+1e-6
    assert outer_mm[:,1].min() >= page.bottom_mm-1e-6
    assert outer_mm[:,1].max() <= page.height_mm-page.top_mm+1e-6
    sky_box = renderer.ax.get_window_extent()
    assert (outer_mm[:,0].max()-outer_mm[:,0].min()-sky_box.width*25.4/fig.dpi) == pytest.approx(2*vertical*25.4/72)
    assert (outer_mm[:,1].max()-outer_mm[:,1].min()-sky_box.height*25.4/fig.dpi) == pytest.approx(2*horizontal*25.4/72)
    for minutes in range(60):
        if minutes%10:
            continue
        rule = _atlas_tick_options(f'right_ascension_{15+minutes/4}',minor_scale=.75)
        assert rule['label']==('1ʰ' if minutes==0 else None)
    plt.close(fig)


@pytest.mark.parametrize("number", [1, 6, 7, 12, 15, 16, 28, 32, 36])
def test_requested_portrait_review_sheets_render_through_chart_command(number, tmp_path):
    """Actual uniform-scale 36-chart execution with synthetic grid content."""
    from xml.etree import ElementTree
    from wenu import CelestialSphere
    from wenu.charts.atlas_publication import AtlasChartPresentation
    from wenu.charts.request_generation import AtlasSheetChartRequest
    from wenu.cli.chart import main
    from wenu.atlas_design import AtlasBandTiling
    atlas = AtlasBandTiling.from_json((ROOT/'examples/atlas_design_36charts_v3.json').read_text())
    assert len(atlas.geometry.sheets) == 36
    assert len({s.field_width_deg for s in atlas.geometry.sheets}) == 1
    sheet = atlas.geometry.sheets[number-1]
    sky = CelestialSphere(None)
    sky.add_equatorial_grid(frame='icrs', equinox='J2000', include_equator=True)
    request = AtlasSheetChartRequest(sheet, atlas.geometry.page,
        AtlasChartPresentation(layers=('equatorial_grid',), grid_frame_width_scale=1.0), tmp_path/'sheet')
    assert main(['atlas-sheet', '--chart-number', str(number), '--output-dir', str(request.output_dir),
        '--debug'], atlas_request=request, sky=sky, emit_outputs=False) == 0
    assert {path.suffix for path in request.output_dir.glob(f'chart-{number:02d}.*')} == {'.png','.pdf','.svg'}
    root = ElementTree.parse(request.output_dir/f'chart-{number:02d}.svg').getroot()
    texts = [''.join(element.itertext()) for element in root.iter() if element.tag.endswith('}text')]
    assert any(text.endswith('ʰ') for text in texts)
    assert any(text.endswith('°') for text in texts)
    assert any('ticks' in element.get('id','') for element in root.iter())
    import json
    from wenu.charts.atlas_publication import _atlas_grid_layout, _atlas_frame_widths
    from wenu.charts.presets import AtlasChartStyle
    report = json.loads((request.output_dir/f'chart-{number:02d}_report_data.json').read_text())
    page = atlas.geometry.page
    bounds, _ = _atlas_grid_layout(page, AtlasChartStyle(), request.presentation)
    frame = report['layout']['chart_sky_frame']
    assert frame['width'] == pytest.approx(bounds[2] * page.width_mm)
    assert frame['height'] == pytest.approx(bounds[3] * page.height_mm)
    horizontal, vertical = _atlas_frame_widths(AtlasChartStyle(), request.presentation)
    # The fixed sheet aspect is fitted inside both frame allowances. Font
    # metrics can make one dimension limiting; the other need not fill it.
    available_width = page.useful_width_mm - 2*vertical*25.4/72
    available_height = page.useful_height_mm - 2*horizontal*25.4/72
    assert frame['width'] == pytest.approx(min(available_width, available_height*page.aspect_ratio))
    assert frame['height'] == pytest.approx(frame['width']/page.aspect_ratio)
    assert frame['width'] <= available_width + 1e-9
    assert frame['height'] <= available_height + 1e-9
    assert report['layout']['central_scale_mm_per_degree'] == pytest.approx(
        frame['width'] / sheet.viewport(page).width * sheet.projection.projected_radius(1e-5)/1e-5)


def test_atlas_ir_embedded_filter_reaches_canonical_chart_layer(request_data, tmp_path, monkeypatch):
    from astropy.table import Table
    from wenu import CelestialSphere
    from wenu.charts.atlas_publication import AtlasChartPresentation
    from wenu.charts.request_generation import AtlasSheetChartRequest
    from wenu.cli.chart import main
    atlas = AtlasDesignRequest.from_dict(request_data).resolve()
    sheet, page = atlas.geometry.sheets[13], atlas.geometry.page
    table = Table(dict(identifier=['synthetic ordinary','synthetic IR','synthetic E','synthetic V'],
        ra_deg=[sheet.center_ra_deg]*4, dec_deg=[sheet.center_dec_deg]*4,
        apparent_diameter_arcmin=[10.]*4, object_type=['open cluster']*4,
        source_type_flag=['','IR','E','V']))
    source = tmp_path/'synthetic_open_clusters.ecsv'
    table.write(source, format='ascii.ecsv')
    sky = CelestialSphere(None); layer = sky.add_open_clusters(filename=source)
    counts = []
    from wenu.charts import export_workflow
    original = export_workflow.export_composed_chart
    def capture(*args, **kwargs):
        result = original(*args, **kwargs)
        counts.append(len(next(record.spherical for record in result.rendering.layers if record.layer is layer)))
        return result
    monkeypatch.setattr(export_workflow, 'export_composed_chart', capture)
    for exclude in (False, True):
        directory = tmp_path/str(exclude)
        request = AtlasSheetChartRequest(sheet, page, AtlasChartPresentation(
            layers=('open_clusters',), dpi=36, formats=('pdf', 'svg'),
            open_cluster_exclude_infrared_embedded=exclude), directory)
        assert main(['atlas-sheet','--chart-number',str(sheet.number),
            '--output-dir',str(directory),'--debug'], atlas_request=request,
            sky=sky, emit_outputs=False) == 0
    assert counts == [4,2] and len(layer.catalog) == 4


@pytest.mark.parametrize("field,value", [("grid_lines_visible",1), ("chart_legend_visible",1),
    ("grid_label_fontsize",float('nan')),("grid_minor_label_scale",1.1),
    ("grid_frame_width_scale",0), ("grid_ra_step_hours",5), ("grid_polar_ra_step_hours",5),
    ("open_cluster_exclude_infrared_embedded", 1),
    ("grid_minute_labels_visible",1), ("milky_way_color","invalid"), ("legend_fontsize",0),
    ("messier_label_fontsize",0), ("deep_sky_symbol_scale",0),
    ("cluster_symbol_scale",0), ("cluster_symbol_scale",True),
    ("cluster_symbol_scale",float("inf")),
    ("cluster_face_color","invalid"), ("grid_dec_label_scale",0)])
def test_atlas_coordinate_presentation_rejects_invalid_values(field,value):
    from wenu.charts.atlas_publication import AtlasChartPresentation
    with pytest.raises(ValueError):
        AtlasChartPresentation(**{field:value})


@pytest.mark.parametrize('hours', [1, 2, 4])
@pytest.mark.parametrize('minutes_visible', [False, True])
def test_atlas_grid_ra_spacing_and_minute_label_switch(hours, minutes_visible):
    from wenu.charts.request_grids import equatorial_grid_tick_options, equatorial_grid_mark_options
    from wenu.charts.atlas_publication import AtlasChartPresentation
    from wenu import RegionalChart
    presentation = AtlasChartPresentation(grid_ra_step_hours=hours,
        grid_minute_labels_visible=minutes_visible)
    options = equatorial_grid_mark_options(RegionalChart(45,180,50,40), presentation)
    assert options['equatorial_grid']['geometry']['ra'] == tuple(range(0,360,15*hours))
    for minutes in (20,40):
        rule = equatorial_grid_tick_options(f'right_ascension_{minutes/4}', minor_scale=.75,
            minute_labels_visible=minutes_visible)
        assert rule['label'] == (f'{minutes}ᵐ' if minutes_visible else None)
        assert rule['length_points'] > 0


def test_index_optional_mw_colour_keeps_v1_admission_and_reaches_typed_presentation(index_data):
    from wenu.charts.atlas_index import AtlasIndexPresentation
    assert AtlasIndexPresentation.from_dict(index_data).milky_way_color == '#87CEFA'
    data = deepcopy(index_data)
    data['colours']['milky_way_color'] = '#88aaff'
    assert AtlasIndexPresentation.from_dict(data).milky_way_color == '#88aaff'
    data['colours']['milky_way_color'] = 'invalid'
    with pytest.raises(ValueError):
        AtlasIndexPresentation.from_dict(data)

def test_atlas_stellar_area_budget_uses_reduced_rendered_sky(request_data):
    """Synthetic completed star geometry isolates the report denominator seam."""
    from types import SimpleNamespace
    import matplotlib.pyplot as plt
    import numpy as np
    from wenu.charts.atlas_publication import (AtlasSheetChart, AtlasChartPresentation,
        _atlas_grid_layout, _atlas_report_data)
    from wenu.charts.composition import compose_chart
    from wenu.charts.detail import DetailOverrides
    from wenu.rendering.matplotlib import MatplotlibRenderer
    atlas = AtlasDesignRequest.from_dict(request_data).resolve()
    page = atlas.geometry.page
    chart = AtlasSheetChart(atlas.geometry.sheets[13],page)
    composition = compose_chart(chart,style='atlas',
        detail_overrides=DetailOverrides(enabled_layers=frozenset({'stars'}),star_magnitude_limit=6))
    bounds,style = _atlas_grid_layout(page,composition.style,AtlasChartPresentation())
    style = replace(style,stars=replace(style.stars,draw_bright_symbols=False))
    composition = replace(composition,style=style)
    fig = plt.figure(figsize=(page.width_mm/25.4,page.height_mm/25.4),dpi=150)
    renderer = MatplotlibRenderer(fig.add_axes(bounds))
    renderer.apply_viewport(chart.viewport)
    star_layer = object()
    rendering = SimpleNamespace(renderer=renderer,viewport=chart.viewport,layers=(
        SimpleNamespace(layer=star_layer,
            spherical=SimpleNamespace(metadata={'magnitude':np.array([1.,2.])}),
            projected=SimpleNamespace(x=np.array([0.,0.]),y=np.array([0.,0.]))),))
    sky = SimpleNamespace(stars=star_layer)
    data = _atlas_report_data(chart,sky,composition,rendering)
    box = renderer.ax.get_window_extent()
    area = box.width*box.height*(25.4/fig.dpi)**2
    budget = data['stellar_area_budget']
    assert budget['chart_area_mm2'] == pytest.approx(area)
    assert area < page.useful_width_mm*page.useful_height_mm
    frame = data['layout']['chart_sky_frame']
    assert frame['width']*frame['height'] == pytest.approx(area)
    assert sum(row['chart_fraction'] for row in budget['bins']) == pytest.approx(
        budget['total_area_mm2']/area)
    from wenu.charts.atlas_publication import _draw_atlas_magnitude_scale
    for size in (12.0, 14.0):
        legends = _draw_atlas_magnitude_scale(chart=chart, sky=sky, renderer=renderer,
            composition=composition, rendering=rendering,
            presentation=AtlasChartPresentation(legend_fontsize=size))
        texts = legends.legends.stars.artist.get_texts()
        assert texts and all(text.get_fontsize()==size for text in texts)
    assert _draw_atlas_magnitude_scale(chart=chart, sky=sky, renderer=renderer,
        composition=composition, rendering=rendering,
        presentation=AtlasChartPresentation(chart_legend_visible=False)) is None
    plt.close(fig)

def test_atlas_sheet_worker_invokes_chart_entry_and_reuses_worker_sky(request_data, tmp_path, monkeypatch):
    from wenu.charts import atlas_publication as publication
    from wenu.sky import native_snapshot
    atlas = AtlasDesignRequest.from_dict(request_data).resolve()
    sky = object()
    calls = []
    monkeypatch.setattr(native_snapshot,'read_native_sky_snapshot',
        lambda *args,**kwargs: type('SyntheticSnapshot',(),{'make_sky':lambda self:sky})())
    def command(argv,**kwargs):
        calls.append((argv,kwargs))
        return 0
    monkeypatch.setattr(publication,'_WORKER_SKY',None)
    monkeypatch.setattr(publication,'_WORKER_CHART_COMMAND',None)
    publication._initialize_atlas_worker('synthetic-snapshot','synthetic-digest',command)
    for sheet in atlas.geometry.sheets[:2]:
        assert publication._render_atlas_sheet((sheet,atlas.geometry.page,
            publication.AtlasChartPresentation(),str(tmp_path))) == sheet.number
    assert len(calls)==2 and all(kwargs['sky'] is sky for argv,kwargs in calls)
    assert all(argv[0]=='atlas-sheet' and kwargs['emit_outputs'] is False for argv,kwargs in calls)
    assert all(kwargs['atlas_request'].sheet.number==int(argv[2]) for argv,kwargs in calls)


def test_atlas_sheet_command_runs_in_spawn_workers_without_an_observer(request_data, tmp_path):
    import multiprocessing
    from concurrent.futures import ProcessPoolExecutor
    from wenu import CelestialSphere
    from wenu.cli.chart import main as chart_command
    from wenu.charts.atlas_publication import _render_atlas_sheet,AtlasChartPresentation
    from pypdf import PdfReader
    atlas = AtlasDesignRequest.from_dict(request_data).resolve()
    sky = CelestialSphere(None)
    sky.add_equatorial_grid(frame='icrs',equinox='J2000',include_equator=True)
    presentation = AtlasChartPresentation(layers=('equatorial_grid',),formats=('pdf','svg'))
    sheets = (atlas.geometry.sheets[0],atlas.geometry.sheets[13])
    with ProcessPoolExecutor(max_workers=2,mp_context=multiprocessing.get_context('spawn')) as pool:
        futures=[pool.submit(_render_atlas_sheet,(sheet,atlas.geometry.page,presentation,str(tmp_path)),
            sky,chart_command=chart_command) for sheet in sheets]
        assert [future.result(timeout=60) for future in futures]==[sheet.number for sheet in sheets]
    for sheet in sheets:
        assert (tmp_path/f'chart-{sheet.number:02d}.svg').exists()
        assert (tmp_path/f'chart-{sheet.number:02d}_report_data.json').exists()
        page=PdfReader(tmp_path/f'chart-{sheet.number:02d}.pdf').pages[0]
        assert float(page.mediabox.width)==pytest.approx(atlas.geometry.page.width_mm*72/25.4)


def test_atlas_producer_uses_real_chart_command_and_prepares_sky_once(request_data, tmp_path, monkeypatch):
    """Synthetic source admission; actual CLI, sheet exports and book publication."""
    import json
    from wenu import CelestialSphere
    from wenu.cli import chart
    from wenu.sky import native_snapshot
    atlas = AtlasDesignRequest.from_dict(request_data).resolve()
    design = tmp_path/'design.json'
    design.write_text(atlas.to_json())
    config = tmp_path/'presentation.toml'
    config.write_text('schema_version=1\ndocument_kind="wenu-atlas-chart-presentation"\n'
        'layers=["stars","equatorial_grid","galaxies","nonstellar"]\nformats=["pdf","svg"]\n')
    sky = CelestialSphere(None)
    sky.add_equatorial_grid(frame='icrs', equinox='J2000', include_equator=True)
    # Co-located synthetic galaxy and Messier designation exercise both native
    # inherited galaxy realization and catalogue-label-only sheet execution.
    from astropy.table import Table
    sheet = atlas.geometry.sheets[13]
    table = Table(dict(name=['M synthetic'], ra_deg=[sheet.center_ra_deg],
        dec_deg=[sheet.center_dec_deg], magnitude=[5.0], object_type=['Galaxy'],
        major_axis_arcmin=[10.0], minor_axis_arcmin=[5.0], position_angle_deg=[30.0]))
    catalogue = tmp_path/'synthetic_dso.ecsv';table.write(catalogue,format='ascii.ecsv')
    sky.add_galaxies(filename=catalogue)
    sky.add_nonstellar(filename=catalogue)
    from wenu.objects.stars import Stars
    import pandas as pd
    stars = Stars(None, magnitude_limit=6)
    stars.source_catalog = pd.DataFrame(dict(
        ra_hours=[sheet.center_ra_deg / 15]*3,
        ra_degrees=[sheet.center_ra_deg]*3,
        dec_degrees=[sheet.center_dec_deg, -80, 0],
        magnitude=[-1.0, 5.0, 9.0], is_constellation_vertex=[False]*3), index=[11,12,13])
    stars.source_catalog = native_table(stars.source_catalog)
    stars.catalog = stars.source_catalog[stars.source_catalog.magnitude <= 6].copy()
    sky.stars = sky.add(stars)
    preparations, dispatches, profiles = [], [], []
    def prepare(raw, directory, **kwargs):
        preparations.append(raw)
        profiles.append(kwargs.get("profile"))
        return 'synthetic-digest', sky
    snapshot = type('SyntheticSnapshot', (), {
        'manifest_sha256':'synthetic-digest', 'require':lambda self, **kwargs:None,
        'make_sky':lambda self: (_ for _ in ()).throw(AssertionError('Cold sky must be reused'))})()
    monkeypatch.setattr(native_snapshot,'prepare_native_sky_snapshot',prepare)
    monkeypatch.setattr(native_snapshot,'read_native_sky_snapshot',lambda *args, **kwargs:snapshot)
    command = chart.main
    def dispatch(argv, **kwargs):
        dispatches.append((argv, kwargs['sky']))
        return command(argv, **kwargs)
    monkeypatch.setattr(chart,'main',dispatch)
    output=tmp_path/'batch'
    import matplotlib.pyplot as plt
    index = tmp_path/'index.pdf'
    figure = plt.figure(figsize=(14,8))
    figure.text(.5,.5,'Synthetic index')
    for suffix in ('png', 'svg', 'pdf'):
        figure.savefig(index.with_suffix('.'+suffix))
    plt.close(figure)
    from wenu.charts.regional import ExportOptions
    original_save = ExportOptions.save
    def check_axis(options, figure, path):
        if path.stem == 'atlas-star-counts':
            assert figure.axes[0].xaxis_inverted()
            assert figure.axes[0].lines[0].get_xdata().tolist() == [-1., 5.]
        return original_save(options, figure, path)
    monkeypatch.setattr(ExportOptions, 'save', check_axis)
    selected_catalogue=tmp_path/'selected_clusters.ecsv'
    selected_catalogue.write_text('synthetic; profile propagation is tested at preparation seam')
    selector=tmp_path/'open_star_clusters.ecsv';selector.symlink_to(selected_catalogue.name)
    selected_planetary_catalogue=tmp_path/'selected_planetary_nebulae.ecsv'
    selected_planetary_catalogue.write_text('synthetic; profile propagation is tested at preparation seam')
    planetary_selector=tmp_path/'planetary_nebulae.ecsv';planetary_selector.symlink_to(selected_planetary_catalogue.name)
    import hashlib
    criteria = tmp_path/'criteria_v1.json'
    criteria_data = dict(schema_version=1, document_kind='wenu-catalogue-selection-criteria',
        catalogue=dict(file=selected_planetary_catalogue.name,
            sha256=hashlib.sha256(selected_planetary_catalogue.read_bytes()).hexdigest()),
        pages=[dict(file=index.name, title='Synthetic selection plot',
            sha256=hashlib.sha256(index.read_bytes()).hexdigest())])
    criteria.write_text(json.dumps(criteria_data))
    assert cli.create_main(['--design',str(design),'--config',str(config),
        '--open-cluster-catalogue',str(selector), '--planetary-nebula-catalogue',str(planetary_selector),
        '--selection-criteria',str(criteria),
        '--charts','1,14','--jobs','1','--index',str(index),'--output-dir',str(output)])==0
    assert preparations == [design.read_bytes()]
    from dataclasses import replace
    from wenu.sky.maximal_sphere import CANONICAL_MAXIMAL_SPHERE_PROFILE
    assert profiles == [replace(CANONICAL_MAXIMAL_SPHERE_PROFILE,
        open_cluster_filename=selected_catalogue.resolve(),
        planetary_nebula_filename=selected_planetary_catalogue.resolve())]
    with pytest.raises(SystemExit):
        cli.create_main(["--design",str(design),"--config",str(config),"--output-dir",str(tmp_path/"invalid"),
            "--from-sky",str(tmp_path/"old-sky"),"--open-cluster-catalogue",str(selector)])
    assert not (tmp_path/"invalid").exists()
    with pytest.raises(SystemExit):
        cli.create_main(["--design",str(design),"--config",str(config),"--output-dir",str(tmp_path/"invalid_pn"),
            "--from-sky",str(tmp_path/"old-sky"),"--planetary-nebula-catalogue",str(planetary_selector)])
    assert not (tmp_path/"invalid_pn").exists()
    assert len(dispatches)==2 and all(argv[0]=='atlas-sheet' and reused is sky for argv,reused in dispatches)
    manifest=json.loads((output/'manifest.json').read_text())
    assert manifest['charts']==[1,14] and manifest['workers']==1
    assert (output/'atlas.pdf').is_file()
    from pypdf import PdfReader
    book = PdfReader(output/'atlas.pdf')
    assert book.page_layout == '/TwoPageLeft'
    assert not book.pages[1].extract_text().strip()
    assert [entry['kind'] for entry in manifest['page_order'][:6]] == ['index','blank','report','chart','report','chart']
    for suffix in ('png', 'svg', 'pdf'):
        assert (output/f'atlas-index.{suffix}').read_bytes() == index.with_suffix('.'+suffix).read_bytes()
    reports = [json.loads((output/f'chart-{number:02d}_report_data.json').read_text()) for number in (1,14)]
    assert reports[0]['layout']['chart_sky_frame'] == pytest.approx(reports[1]['layout']['chart_sky_frame'])
    assert reports[0]['layout']['central_scale_mm_per_degree'] == pytest.approx(reports[1]['layout']['central_scale_mm_per_degree'])
    counts=json.loads((output/'atlas-star-counts.json').read_text())
    assert counts['selected_count']==2 and counts['cumulative_count']==[1,2]
    assert counts['magnitude']==[-1.0,5.0]
    assert counts['provenance']['snapshot_sha256']=='synthetic-digest'
    assert manifest['page_order'][-2]['kind']=='catalogue_star_counts'
    assert manifest['page_order'][-1]['kind']=='selection_criteria'
    assert book.pages[-1].extract_text().strip() == 'Synthetic index'
    assert manifest['selection_criteria'][0]['catalogue_sha256'] == criteria_data['catalogue']['sha256']
    assert manifest['selection_criteria'][0]['criteria_sha256'] == hashlib.sha256(criteria.read_bytes()).hexdigest()
    from wenu.charts.atlas_publication import _read_selection_criteria
    with pytest.raises(ValueError, match='explicit atlas catalogue'):
        _read_selection_criteria([criteria], [selected_catalogue])
    original_digest = criteria_data['pages'][0]['sha256']
    criteria_data['pages'][0]['sha256'] = '0'*64
    assert criteria_data['pages'][0]['sha256'] != original_digest
    criteria.write_text(json.dumps(criteria_data))
    with pytest.raises(SystemExit):
        cli.create_main(['--design',str(design),'--config',str(config),
            '--planetary-nebula-catalogue',str(planetary_selector),
            '--selection-criteria',str(criteria),'--output-dir',str(tmp_path/'bad_criteria')])
    assert preparations == [design.read_bytes()] and not (tmp_path/'bad_criteria').exists()
    assert all((output/f'atlas-star-counts.{suffix}').is_file() for suffix in ('png','svg','pdf'))
    from xml.etree import ElementTree
    root = ElementTree.parse(output/'chart-14.svg').getroot()
    texts = [''.join(element.itertext()) for element in root.iter() if element.tag.endswith('}text')]
    assert texts.count('M synthetic') == 1
    designation = next(element for element in root.iter()
        if element.tag.endswith('}text') and ''.join(element.itertext()) == 'M synthetic')
    assert '7px' in designation.get('style', '')
    # An installed default supplies its matching criteria without CLI paths.
    from wenu import resources
    criteria_data['pages'][0]['sha256'] = original_digest
    criteria.write_text(json.dumps(criteria_data))
    config.write_text(config.read_text().replace('"nonstellar"]', '"nonstellar","planetary_nebulae"]'))
    monkeypatch.setattr(resources, 'curated_catalogue_bundle', lambda domain:
        dict(catalogue=selected_planetary_catalogue, criteria=(criteria,))
        if domain == 'planetary_nebulae' else None)
    automatic = tmp_path / 'automatic'
    assert cli.create_main(['--design',str(design),'--config',str(config),
        '--charts','14','--jobs','1','--output-dir',str(automatic)]) == 0
    default_manifest = json.loads((automatic / 'manifest.json').read_text())
    assert default_manifest['page_order'][-1]['kind'] == 'selection_criteria'
    assert default_manifest['selection_criteria'][0]['catalogue_sha256'] == criteria_data['catalogue']['sha256']
    assert len(preparations) == 2
    assert profiles[-1] == replace(CANONICAL_MAXIMAL_SPHERE_PROFILE,
        planetary_nebula_filename=selected_planetary_catalogue.resolve())



def test_atlas_catalogue_counts_use_unique_actual_photometry_and_finite_positions():
    import pandas as pd
    import numpy as np
    from types import SimpleNamespace
    from wenu.charts.stellar_sizing_report import catalogue_star_counts
    source = pd.DataFrame(dict(magnitude=[-1,-1,0,2,7,1],
        ra_hours=[0,0,2,3,4,np.nan], dec_degrees=[0]*6), index=[1,1,2,3,4,5])
    before=source.copy(deep=True)
    from wenu.geometry.spherical import SphericalPoints
    from wenu.coordinates import GENERIC_SPHERICAL_SPEC
    geometry = SphericalPoints(source.ra_hours.to_numpy()*15, source.dec_degrees.to_numpy(),
        ids=source.index.to_numpy(), metadata={"magnitude": source.magnitude.to_numpy()},
        coordinate_spec=GENERIC_SPHERICAL_SPEC)
    data, identifiers, values=catalogue_star_counts(SimpleNamespace(native_positions=lambda: geometry),6)
    assert identifiers.tolist()==[1,2,3] and values.tolist()==[-1,0,2]
    assert data['selected_count']==3 and data['cumulative_count']==[1,2,3]
    assert data['invalid_count']==1 and data['fainter_count']==1
    np.testing.assert_allclose(data['log10_cumulative_count'],np.log10([1,2,3]))
    pd.testing.assert_frame_equal(source,before)


@pytest.mark.parametrize('symbol_scale',[1.0,0.5])
@pytest.mark.parametrize('angular',[True,False])
def test_atlas_cluster_diameters_match_reported_central_scale(request_data,tmp_path,monkeypatch,angular,symbol_scale):
    from wenu import CelestialSphere
    from astropy.table import Table
    from wenu.charts.atlas_publication import AtlasChartPresentation
    from wenu.charts.request_generation import AtlasSheetChartRequest,generate_chart_request
    from wenu.rendering import MatplotlibRenderer
    from matplotlib.collections import PathCollection
    import numpy as np
    import json
    atlas=AtlasDesignRequest.from_dict(request_data).resolve()
    sheet=atlas.geometry.sheets[13]
    path=tmp_path/'clusters.ecsv'
    Table(dict(identifier=['Small','Large','Missing'],ra_deg=[sheet.center_ra_deg]*3,
        dec_deg=[sheet.center_dec_deg]*3,object_type=['Open Cluster']*3,
        apparent_diameter_arcmin=[.1,120,np.nan])).write(path)
    sky=CelestialSphere(None);sky.add_open_clusters(filename=path)
    pn_path=tmp_path/'pn.ecsv'
    Table(dict(identifier=['PN synthetic'],ra_deg=[sheet.center_ra_deg],
        dec_deg=[sheet.center_dec_deg],object_type=['Planetary Nebula'])).write(pn_path)
    sky.add_planetary_nebulae(filename=pn_path)
    planetary=[]
    measured=[]
    original=MatplotlibRenderer.draw
    def capture(renderer,geometry,**kwargs):
        result=original(renderer,geometry,**kwargs)
        if geometry.metadata.get('symbol')=='open_cluster':
            measured.extend(a.get_sizes() for a in result if isinstance(a,PathCollection))
        if geometry.metadata.get('symbol')=='planetary_nebula':
            planetary.extend(a for a in result if isinstance(a,PathCollection))
        return result
    monkeypatch.setattr(MatplotlibRenderer,'draw',capture)
    presentation=AtlasChartPresentation(layers=('open_clusters','planetary_nebulae'),formats=('pdf','svg'),open_cluster_angular_sizes=angular,
        cluster_symbol_scale=symbol_scale, planetary_nebula_symbol_scale=1.25*symbol_scale)
    generate_chart_request(AtlasSheetChartRequest(sheet,atlas.geometry.page,presentation,tmp_path/'charts'),sky=sky)
    report=json.loads((tmp_path/'charts/chart-14_report_data.json').read_text())
    areas=np.broadcast_to(measured[0],(3,))
    from wenu.charts.presets import AtlasChartStyle
    from matplotlib.colors import to_rgba
    expected = AtlasChartStyle().deep_sky.planetary_nebula_symbol_size * 1.8**2 * (1.25*symbol_scale)**2
    assert planetary[0].get_sizes()[0] == pytest.approx(expected)
    np.testing.assert_allclose(planetary[0].get_edgecolors()[0], to_rgba('#24552b'))
    assert planetary[0].get_linewidths()[0] == pytest.approx(1.1)
    assert areas[0]==pytest.approx(areas[2])
    assert areas[0] == pytest.approx(AtlasChartStyle().deep_sky.open_cluster_symbol_size * (1.8*symbol_scale)**2)
    if angular:
        mm=2*report['layout']['central_scale_mm_per_degree']*symbol_scale
        assert np.sqrt(areas[1])*25.4/72==pytest.approx(mm)
        assert areas[1]>areas[0]
    else:
        np.testing.assert_allclose(areas,[areas[0]]*3)
    with pytest.raises(ValueError): AtlasChartPresentation(open_cluster_angular_sizes='yes')



@pytest.mark.parametrize("worker", [False, True])
@pytest.mark.parametrize("status", [0, 1, True])
def test_atlas_sheet_default_route_uses_wenu_chart(request_data, tmp_path, monkeypatch, worker, status):
    """No injected command must still use the ordinary chart command entry."""
    from wenu.charts import atlas_publication as publication
    from wenu.cli import chart

    atlas = AtlasDesignRequest.from_dict(request_data).resolve()
    sheet = atlas.geometry.sheets[0]
    presentation = publication.AtlasChartPresentation()
    sky = object()
    calls = []
    monkeypatch.setattr(publication, "_WORKER_SKY", sky)
    monkeypatch.setattr(publication, "_WORKER_CHART_COMMAND", None)

    def command(argv, **options):
        request = options["atlas_request"]
        assert request.sheet is sheet and request.page is atlas.geometry.page
        assert request.presentation is presentation and request.output_dir == tmp_path
        assert options["sky"] is sky and options["emit_outputs"] is False
        assert argv == ["atlas-sheet", "--chart-number", str(sheet.number),
                        "--output-dir", str(tmp_path), "--debug"]
        calls.append(request)
        return status

    monkeypatch.setattr(chart, "main", command)
    task = (sheet, atlas.geometry.page, presentation, str(tmp_path))
    if type(status) is int and status == 0:
        assert publication._render_atlas_sheet(task, **({} if worker else {"sky": sky})) == sheet.number
    else:
        with pytest.raises(RuntimeError, match="wenu_chart failed"):
            publication._render_atlas_sheet(task, **({} if worker else {"sky": sky}))
    assert len(calls) == 1


@pytest.mark.parametrize("refuse", (False, True))
def test_sheet_executor_consumes_public_render_result_and_preserves_scope(request_data, tmp_path, monkeypatch, refuse):
    import pickle
    from wenu import CelestialSphere
    from wenu.charts import atlas_sheet as publication
    from wenu.charts import request_generation as generation
    from wenu.charts.export_workflow import ChartExportResult
    from wenu.charts.atlas_publication import AtlasSheetChartRequest as legacy
    assert generation.AtlasSheetChartRequest is publication.AtlasSheetChartRequest is legacy
    atlas = AtlasDesignRequest.from_dict(request_data).resolve()
    request = publication.AtlasSheetChartRequest(atlas.geometry.sheets[0], atlas.geometry.page,
        publication.AtlasChartPresentation(layers=("equatorial_grid",), formats=("pdf",)), tmp_path/'sheet')
    assert pickle.loads(pickle.dumps(request)) == request
    sky = CelestialSphere(None)
    marker = object()
    calls = []
    def render(staged, actual_sky):
        calls.append(staged)
        assert actual_sky is sky and sky._active_chart_request_state is not None
        assert staged.sheet is request.sheet and staged.presentation is request.presentation
        assert staged.output_dir != request.output_dir
        if refuse:
            raise RuntimeError("synthetic public sheet refusal")
        output = staged.output_dir/'chart-01.pdf'
        report = staged.output_dir/'chart-01_report_data.json'
        output.write_bytes(b'synthetic sheet result')
        report.write_bytes(b'synthetic report result')
        return ChartExportResult(marker, output, marker, {}, marker, report_outputs=(report,))
    monkeypatch.setattr(publication, "render_atlas_sheet", render)
    if refuse:
        with pytest.raises(RuntimeError, match="public sheet refusal"):
            generation.generate_chart_request(request, sky=sky)
        assert not request.output_dir.exists()
    else:
        result = generation.generate_chart_request(request, sky=sky)
        assert result.exports[0].rendering is marker
        assert tuple(p.name for p in result.outputs) == ('chart-01.pdf','chart-01_report_data.json')
        assert [p.read_bytes() for p in result.outputs] == [b'synthetic sheet result', b'synthetic report result']
    assert len(calls) == 1
    assert not hasattr(sky, '_active_chart_request_state')
    assert not list(tmp_path.glob('.wenu-chart-*'))


def test_catalogue_counts_consume_returned_native_rows_and_propagate_refusal():
    import numpy as np
    from types import SimpleNamespace
    from wenu.coordinates import GENERIC_SPHERICAL_SPEC
    from wenu.geometry.spherical import SphericalPoints
    from wenu.charts.stellar_sizing_report import catalogue_star_counts
    geometry = SphericalPoints([10.,20.], [30.,40.], ids=[11,12],
        metadata={"magnitude": [1.,2.]}, coordinate_spec=GENERIC_SPHERICAL_SPEC)
    stars = SimpleNamespace(native_positions=lambda: geometry)
    assert catalogue_star_counts(stars,6)[1].tolist() == [11,12]
    geometry = replace(geometry, lon_deg=np.asarray([np.nan,20.]))
    data, ids, values = catalogue_star_counts(stars,6)
    assert ids.tolist() == [12] and values.tolist() == [2.]
    assert data['selected_count'] == 1 and data['invalid_count'] == 1
    def refuse():
        raise RuntimeError('synthetic native count refusal')
    stars.native_positions = refuse
    with pytest.raises(RuntimeError, match='native count refusal'):
        catalogue_star_counts(stars,6)


def test_index_and_catalogue_appendix_use_real_kernel_results_and_refuse(request_data, monkeypatch):
    import numpy as np
    import pandas as pd
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from wenu import CelestialSphere
    from wenu.objects.stars import Stars
    from wenu.charts import atlas_index as index
    from wenu.charts.stellar_sizing_report import catalogue_star_counts
    from wenu.catalogue_state import _unit_direction
    from wenu_kernel import KernelSession
    stars = Stars(None, magnitude_limit=6)
    stars.source_catalog = native_table(pd.DataFrame(dict(ra_hours=[1.], dec_degrees=[30.],
        magnitude=[2.], is_constellation_vertex=[False]),index=[11]))
    stars.catalog = stars.source_catalog.copy()
    sky = CelestialSphere(None); sky.stars = sky.add(stars)
    evaluate = KernelSession.evaluate
    def shifted(session, query):
        batch = evaluate(session, query)
        return replace(batch, states=tuple(replace(state, vector=_unit_direction(45.,50.)) for state in batch.states))
    monkeypatch.setattr(KernelSession, 'evaluate', shifted)
    atlas = AtlasDesignRequest.from_dict(request_data).resolve()
    face = index.overview_face(atlas.geometry.overview, 'north')
    presentation = replace(index.AtlasIndexPresentation(), layers=('stars',), veil_enabled=False)
    realized = []
    realize = stars.realize
    def capture(*args, **kwargs):
        result = realize(*args, **kwargs); realized.append(result); return result
    monkeypatch.setattr(stars, 'realize', capture)
    def draw():
        figure = Figure(); FigureCanvasAgg(figure)
        index._draw_face(figure.add_subplot(), atlas, face, footprints=False, sky=sky,
            presentation=presentation, star_magnitude_limit=6)
    draw()
    assert realized and realized[0].ids.tolist() == [11]
    np.testing.assert_allclose(realized[0].lon_deg,[45.])
    np.testing.assert_allclose(realized[0].lat_deg,[50.])
    assert catalogue_star_counts(stars,6)[1].tolist() == [11]
    def refuse(*a, **k):
        raise RuntimeError('synthetic atlas kernel refusal')
    monkeypatch.setattr(KernelSession, 'evaluate', refuse)
    with pytest.raises(RuntimeError, match='atlas kernel refusal'):
        draw()
    with pytest.raises(RuntimeError, match='atlas kernel refusal'):
        catalogue_star_counts(stars,6)



def test_atlas_motion_config_uses_existing_publication_execution_owner(tmp_path, monkeypatch):
    from wenu.charts import atlas_publication
    calls = []
    def capture(design, output, **kwargs):
        calls.append(kwargs)
        return tmp_path/'manifest.json'
    monkeypatch.setattr(atlas_publication, 'create_atlas', capture)
    motion = tmp_path/'motion-v1.toml'
    assert cli.create_main(['--layout','b4-portrait','--stellar-motion-config',str(motion),
        '--jobs','2','--output-dir',str(tmp_path/'atlas')]) == 0
    assert calls[0]['stellar_motion_config'] == motion
    assert calls[0]['jobs'] == 2
    assert callable(calls[0]['chart_command'])


def _atlas_frame_document(axes='mean-equator-equinox', year=-8000):
    from fractions import Fraction
    day=Fraction(2451545)+(Fraction(year)-2000)*Fraction('365.25')
    whole=(day+Fraction(1,2)).__floor__();small=float(day-whole)
    return (f'schema_version = 1\ndocument_kind = "wenu-atlas-frame"\naxes = "{axes}"\n'
        'model_policy = "vcw2011-2012-erfa"\n'
        f'[equinox]\njd1 = {whole}\njd2 = {small}\nscale = "tt"\n'
        '[start]\njd1 = -1200956\njd2 = 0.0\nscale = "tt"\n'
        '[stop]\njd1 = 2451546\njd2 = 0.0\nscale = "tt"\n').encode()


def _dated_atlas_test_sky():
    """Constructed local inputs; no source fixture or ephemeris acquisition."""
    import pandas as pd
    from astropy.coordinates import BarycentricMeanEcliptic
    from astropy.time import Time
    from wenu import CelestialSphere
    from wenu.objects.stars import Stars
    stars=Stars(None,magnitude_limit=6)
    stars.source_catalog=native_table(pd.DataFrame(dict(ra_hours=[1.,15.],dec_degrees=[30.,-60.],
        magnitude=[2.,4.],is_constellation_vertex=[False,False]),index=[11,12]))
    stars.catalog=stars.source_catalog.copy()
    sky=CelestialSphere(None);sky.stars=sky.add(stars)
    sky.add_equatorial_grid(frame='icrs',equinox='J2000',samples=73,include_equator=True)
    sky.add_ecliptic_grid(equinox='J2000',samples=73,include_ecliptic=True)
    points=sky.add_points();ecliptic=BarycentricMeanEcliptic(equinox=Time('J2000'))
    for pole in ('north','south'):
        points.add_equatorial_pole(pole).add_ecliptic_pole(pole,frame=ecliptic)
    points.add_ecliptic_cardinal_points(frame=ecliptic)
    return sky


def _dated_atlas_test_worker(directory,digest,command,motion_input,design_sha256,frame_input):
    """Replace synthetic snapshot decoding only; real frame binding and workers."""
    from wenu.sky import native_snapshot
    from wenu.charts import atlas_publication as publication
    class SyntheticSnapshot:
        manifest_sha256=digest
        def require(self,**kwargs): assert kwargs['design_sha256']==design_sha256
        def make_sky(self):return _dated_atlas_test_sky()
    original=native_snapshot.read_native_sky_snapshot
    native_snapshot.read_native_sky_snapshot=lambda *a,**k:SyntheticSnapshot()
    try:
        publication._initialize_atlas_worker(directory,digest,command,motion_input,design_sha256,frame_input)
    finally:
        native_snapshot.read_native_sky_snapshot=original


def _dated_atlas_drop_frame_command(argv,**kwargs):
    from wenu.cli.chart import main
    kwargs['atlas_request']=replace(kwargs['atlas_request'],orientation=None,frame_input=None)
    return main(argv,**kwargs)


def test_atlas_frame_document_capture_rejects_wrong_scale_domain_bytes_and_backend(tmp_path,monkeypatch):
    import erfa, numpy as np
    from wenu.charts.atlas_sheet import AtlasFrameExecutionInput,load_atlas_frame
    from wenu_kernel.errors import KernelError
    path=tmp_path/'frame.toml';path.write_bytes(_atlas_frame_document())
    captured,frame=AtlasFrameExecutionInput.capture(path,design_bytes=b'original design bytes',snapshot_sha256='b'*64)
    path.write_bytes(_atlas_frame_document(year=2000))
    assert captured.admit(design_sha256=hashlib.sha256(b'original design bytes').hexdigest(),snapshot_sha256='b'*64)==frame
    for bad in (replace(captured,document=path.read_bytes()),replace(captured,design_sha256='c'*64)):
        with pytest.raises(ValueError,match='identity mismatch'):
            bad.admit(design_sha256=hashlib.sha256(b'original design bytes').hexdigest(),snapshot_sha256='b'*64)
    for content in (_atlas_frame_document().replace(b'"tt"',b'"tcb"',1),
                    _atlas_frame_document(year=-9000),_atlas_frame_document()+b'unknown = true\n'):
        with pytest.raises((ValueError,KernelError)):
            load_atlas_frame(content)
    evaluate=erfa.ltpb
    def fault(year):
        angle=.01
        return np.array([[np.cos(angle),-np.sin(angle),0],[np.sin(angle),np.cos(angle),0],[0,0,1]])@evaluate(year)
    monkeypatch.setattr(erfa,'ltpb',fault)
    with pytest.raises(ValueError,match='backend/matrix'):
        captured.admit(design_sha256=hashlib.sha256(b'original design bytes').hexdigest(),snapshot_sha256='b'*64)


@pytest.mark.parametrize('axes',['mean-equator-equinox','mean-ecliptic-equinox'])
@pytest.mark.parametrize('year',[2000,-8000])
def test_dated_sheet_cli_and_python_share_frame_geometry_reports_and_pixels(tmp_path,monkeypatch,axes,year):
    import json,numpy as np
    from PIL import Image
    from wenu.resources import configuration_preset_path
    from wenu.charts.atlas_sheet import AtlasSheetChartRequest,AtlasChartPresentation,load_atlas_frame
    from wenu.charts.request_generation import generate_chart_request
    from wenu.cli.chart import main
    from wenu.sky import native_snapshot
    from wenu.sky.celestial_sphere import CelestialSphere
    design=configuration_preset_path('b4-portrait',kind='atlas-layout');raw=design.read_bytes()
    atlas=AtlasBandTiling.from_json(raw.decode());digest=hashlib.sha256(raw).hexdigest()
    frame_path=tmp_path/'frame.toml';frame_path.write_bytes(_atlas_frame_document(axes,year))
    presentation=AtlasChartPresentation(layers=('stars','equatorial_grid','ecliptic_grid','celestial_points'),
        dpi=36,legend_fontsize=6,report_label_scale=1)
    config=tmp_path/'style.toml';config.write_text('schema_version=1\ndocument_kind="wenu-atlas-chart-presentation"\n'
        'layers=["stars","equatorial_grid","ecliptic_grid","celestial_points"]\n'
        'dpi=36\nlegend_fontsize=6\nreport_label_scale=1\n')
    sky=_dated_atlas_test_sky();original=sky.stars.source_catalog.copy(deep=True)
    class SyntheticSnapshot:
        manifest_sha256='b'*64
        def require(self,**kwargs):assert kwargs['design_sha256']==digest
        def make_sky(self):return sky
    monkeypatch.setattr(native_snapshot,'read_native_sky_snapshot',lambda *a,**k:SyntheticSnapshot())
    rendered=[];draw=CelestialSphere.draw_chart
    def capture(self,**kwargs):
        result=draw(self,**kwargs);rendered.append(result);return result
    monkeypatch.setattr(CelestialSphere,'draw_chart',capture)
    # Polar and ordinary fields exercise different boundary/furniture owners.
    for number in (1,13):
        out=tmp_path/f'cli-{number}'
        assert main(['atlas-sheet','--design',str(design),'--config',str(config),
            '--from-sky',str(tmp_path/'synthetic-snapshot'),'--atlas-frame-config',str(frame_path),
            '--chart-number',str(number),'--output-dir',str(out),'--debug'])==0
        request=AtlasSheetChartRequest(atlas.geometry.sheets[number-1],atlas.geometry.page,
            presentation,tmp_path/f'python-{number}',orientation=load_atlas_frame(frame_path.read_bytes()),design_sha256=digest,design_bytes=raw)
        generate_chart_request(request,sky=sky)
        stem=f'chart-{number:02d}'
        for suffix in ('','_report'):
            with Image.open(out/(stem+suffix+'.png')) as a,Image.open(request.output_dir/(stem+suffix+'.png')) as b:
                np.testing.assert_array_equal(np.asarray(a),np.asarray(b))
        report=json.loads((out/(stem+'_report_data.json')).read_text())
        assert report['center']['coordinate_system']==axes
        assert report['center']['equinox_tt']['scale']=='tt'
        assert report['derived_view']['source_design_sha256']==digest
        assert report['derived_view']['source_sheet_id']==request.sheet.sheet_id
        assert report['sheet_id']!=request.sheet.sheet_id
        assert 'ra_deg' not in report['center'] and 'stellar_realization' not in report
    assert all(r.spherical.coordinate_spec.frame==axes for result in rendered for r in result.layers)
    import pandas as pd
    pd.testing.assert_frame_equal(sky.stars.source_catalog,original)
    assert not hasattr(sky.stars,'_stellar_realization')


@pytest.mark.parametrize('jobs',[1,2])
@pytest.mark.parametrize('axes',['mean-equator-equinox','mean-ecliptic-equinox'])
def test_dated_atlas_publication_without_motion_keeps_counts_and_validates_frame(tmp_path,monkeypatch,jobs,axes):
    import json
    from wenu.charts import atlas_publication as publication
    from wenu.charts.atlas_sheet import AtlasChartPresentation,atlas_frame_record,load_atlas_frame
    from wenu.resources import configuration_preset_path
    from wenu.sky import native_snapshot
    from wenu.charts.stellar_sizing_report import catalogue_star_counts
    design=configuration_preset_path('b4-portrait',kind='atlas-layout')
    digest=hashlib.sha256(design.read_bytes()).hexdigest();sky=_dated_atlas_test_sky()
    class SyntheticSnapshot:
        manifest_sha256='b'*64
        def require(self,**kwargs):assert kwargs['design_sha256']==digest
        def make_sky(self):return sky
    monkeypatch.setattr(native_snapshot,'read_native_sky_snapshot',lambda *a,**k:SyntheticSnapshot())
    if jobs==2:monkeypatch.setattr(publication,'_initialize_atlas_worker',_dated_atlas_test_worker)
    frame_path=tmp_path/'frame.toml';frame_path.write_bytes(_atlas_frame_document(axes))
    frame=load_atlas_frame(frame_path.read_bytes())
    presentation=AtlasChartPresentation(layers=('stars','equatorial_grid','ecliptic_grid','celestial_points'),
        formats=('png','pdf','svg'),dpi=36,legend_fontsize=6,report_label_scale=1)
    expected=catalogue_star_counts(sky.stars,presentation.star_magnitude_limit)[0]
    path=publication.create_atlas(design,tmp_path/'book',presentation=presentation,
        charts='1,13',jobs=jobs,from_sky=tmp_path/'synthetic',atlas_frame_config=frame_path)
    data=json.loads(path.read_text());assert data['atlas_frame']==atlas_frame_record(frame)
    counts=json.loads((path.parent/'atlas-star-counts.json').read_text())
    assert counts['selected_count']==expected['selected_count']==2
    assert counts['provenance']['atlas_frame']==data['atlas_frame']
    assert 'stellar_realization' not in data
    assert data['charts']==[1,13] and len(data['derived_views'])==2
    with pytest.raises(ValueError):
        publication.create_atlas(design,path.parent,presentation=presentation,charts='1',
            jobs=1,from_sky=tmp_path/'synthetic',atlas_frame_config=frame_path)


@pytest.mark.parametrize('jobs',[1,2])
def test_dated_atlas_dropped_worker_frame_refuses_completion(tmp_path,monkeypatch,jobs):
    from wenu.charts import atlas_publication as publication
    from wenu.charts.atlas_sheet import AtlasChartPresentation
    from wenu.resources import configuration_preset_path
    from wenu.sky import native_snapshot
    design=configuration_preset_path('b4-portrait',kind='atlas-layout')
    digest=hashlib.sha256(design.read_bytes()).hexdigest();sky=_dated_atlas_test_sky()
    class SyntheticSnapshot:
        manifest_sha256='b'*64
        def require(self,**kwargs):assert kwargs['design_sha256']==digest
        def make_sky(self):return sky
    monkeypatch.setattr(native_snapshot,'read_native_sky_snapshot',lambda *a,**k:SyntheticSnapshot())
    if jobs==2:monkeypatch.setattr(publication,'_initialize_atlas_worker',_dated_atlas_test_worker)
    frame=tmp_path/'frame.toml';frame.write_bytes(_atlas_frame_document())
    with pytest.raises(ValueError,match='different frame or derived layout'):
        publication.create_atlas(design,tmp_path/'failed',
            presentation=AtlasChartPresentation(layers=('stars',),dpi=36,legend_fontsize=6,report_label_scale=1),
            charts='1,13',jobs=jobs,from_sky=tmp_path/'synthetic',atlas_frame_config=frame,
            chart_command=_dated_atlas_drop_frame_command)
    assert not (tmp_path/'failed').exists()
    assert not hasattr(sky.stars,'_stellar_realization')


def test_atlas_frame_worker_scope_refuses_snapshot_mismatch_and_clears_frame(tmp_path,monkeypatch):
    from wenu.charts import atlas_publication as publication
    from wenu.charts.atlas_sheet import AtlasFrameExecutionInput
    from wenu.sky import native_snapshot
    frame=tmp_path/'frame.toml';frame.write_bytes(_atlas_frame_document())
    captured,_=AtlasFrameExecutionInput.capture(frame,design_bytes=b'original design bytes',snapshot_sha256='b'*64)
    class SyntheticSnapshot:
        manifest_sha256='b'*64
        def require(self,**kwargs):pass
        def make_sky(self):return _dated_atlas_test_sky()
    monkeypatch.setattr(native_snapshot,'read_native_sky_snapshot',lambda *a,**k:SyntheticSnapshot())
    try:
        publication._initialize_atlas_worker(tmp_path,'b'*64,None,None,hashlib.sha256(b'original design bytes').hexdigest(),captured)
        assert publication._WORKER_FRAME.model.configuration_digest
        with pytest.raises(ValueError,match='identity mismatch'):
            publication._initialize_atlas_worker(tmp_path,'b'*64,None,None,'c'*64,captured)
        assert publication._WORKER_FRAME is None and publication._WORKER_SKY is None
    finally:publication._close_atlas_worker()


def test_empty_stellar_svg_requires_checksum_bound_zero_report(tmp_path):
    import json
    from wenu.charts.stellar_sizing_report import analyze
    svg=tmp_path/'chart-01.svg'
    svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="100mm" height="100mm" viewBox="0 0 100 100"/>')
    report=tmp_path/'chart-01_report_data.json'
    def bind(count):
        report.write_text(json.dumps({'stars':{'statistics':{'visible_count':count}}}))
        manifest=dict(document_kind='wenu-atlas-chart-batch',presentation={'layers':['stars']},
            products={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (svg,report)})
        (tmp_path/'manifest.json').write_text(json.dumps(manifest))
    bind(1)
    with pytest.raises(ValueError,match='No Wenu stellar semantic layer'):
        analyze([svg],tmp_path/'bad',show_magnitudes=False)
    bind(0)
    report.write_text(report.read_text()+' ')
    with pytest.raises(ValueError,match='No Wenu stellar semantic layer'):
        analyze([svg],tmp_path/'tampered',show_magnitudes=False)
    bind(0)
    analyze([svg],tmp_path/'empty',show_magnitudes=False)
    assert (tmp_path/'empty_summary.json').exists()


def test_dated_request_binds_exact_design_sheet_page_and_primary_tick_units(tmp_path):
    from wenu.charts.atlas_sheet import (AtlasSheetChartRequest,AtlasChartPresentation,
        load_atlas_frame,_ecliptic_tick_options)
    from wenu.resources import configuration_preset_path
    raw=configuration_preset_path('b4-portrait',kind='atlas-layout').read_bytes()
    atlas=AtlasBandTiling.from_json(raw.decode())
    request=AtlasSheetChartRequest(atlas.geometry.sheets[0],atlas.geometry.page,
        AtlasChartPresentation(),tmp_path,orientation=load_atlas_frame(_atlas_frame_document()),design_bytes=raw)
    assert request.design_sha256==hashlib.sha256(raw).hexdigest()
    for fields in (dict(design_sha256='a'*64),dict(design_bytes=None),
                   dict(sheet=replace(request.sheet,position_angle_deg=1.)),
                   dict(page=replace(request.page,width_mm=request.page.width_mm+1))):
        with pytest.raises(ValueError):replace(request,**fields)
    tick=_ecliptic_tick_options('ecliptic_longitude_30',minor_scale=.75,latitude_scale=.8)
    assert tick['label']=='30°' and 'ʰ' not in tick['label']



def test_atlas_epoch_config_routes_to_publication_and_refuses_live_combination(tmp_path, monkeypatch):
    from wenu.charts import atlas_publication
    calls=[]
    monkeypatch.setattr(atlas_publication, 'create_atlas', lambda *a,**k: calls.append(k) or tmp_path/'manifest.json')
    epoch=tmp_path/'epoch-query.toml'
    assert cli.create_main(['--layout','b4-portrait','--stellar-epoch-config',str(epoch),
        '--output-dir',str(tmp_path/'atlas')]) == 0
    assert calls[0]['stellar_epoch_config'] == epoch
    assert calls[0]['stellar_motion_config'] is None
    with pytest.raises(SystemExit):
        cli.create_main(['--layout','b4-portrait','--stellar-epoch-config',str(epoch),
            '--stellar-motion-config','live.toml','--output-dir',str(tmp_path/'atlas')])
