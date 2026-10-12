"""Atlas request-file admission, installed route and JSON publication."""

from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
import hashlib
import os
from pathlib import Path
import subprocess
import sys

import pytest

from wenu.atlas_design import AtlasBandTiling, AtlasDesignRequest
from wenu.cli import atlas as cli
from wenu.charts.atlas_publication import AtlasPublicationBatchRequest


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples/atlas_design_request_v1.toml"


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


def test_plot_cli_geometry_is_unchanged_and_exports_selected_formats(index_data, request_data, tmp_path, monkeypatch, capsys):
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
        ink_color="#551177", paper_color="#f0e0c0")
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
        assert image.size == (2240, 1280)
        assert image.convert("RGBA").getpixel((0, 0))[3] == 0
    svg = ElementTree.parse(paths[2]).getroot()
    assert svg.get("width") == "1008pt"
    assert paths[1].read_bytes().startswith(b"%PDF-")
    number_labels = [t for ax in figures[0].axes for t in ax.texts if t.get_text().isdigit()]
    assert {int(t.get_text()) for t in number_labels} == set(range(1, 35))
    assert all(t.get_fontsize() == 13 and t.get_color() == "#551177" for t in number_labels)
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
                   {'magnitude_veil_alpha': True}, {'magnitude_veil_color': 'invalid'}):
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
        '--mode', 'presentation']) == 0
    presentation = calls[0]['presentation']
    assert presentation.stellar_magnitude_sizing.algorithm == 'asinh'
    assert presentation.stellar_magnitude_sizing.a_mm == .4
    assert presentation.stellar_magnitude_sizing.b_mag == 2
    assert presentation.star_magnitude_limit == 8
    assert presentation.star_size_scale == 1
    assert presentation.mode == 'presentation' and presentation.style == 'cartoon'
    assert calls[0]['from_sky'] == Path('saved-sky')


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
        sheet_id='test-sheet',center_ra_deg=0 if polar else 82.5,
        center_dec_deg=90 if polar else 0,pole_meridian_ra_deg=82.5 if polar else None))
    from wenu.charts.presets import AtlasChartStyle
    composition = SimpleNamespace(style=SimpleNamespace(stars=AtlasChartStyle().stars, legend=SimpleNamespace(title_fontsize=6.5)),detail=SimpleNamespace(star_magnitude_limit=6,
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
        assert style is composition.style and options['resolved_detail'] is composition.detail
        assert options['include_context'] is True
        if polar:
            assert options['object_title'] == 'Centre: ICRS\nRA undefined (pole)\nDec +90d00m00s\nMeridian 05h30m00s'
        else:
            assert options['object_title'] == 'Centre: ICRS\nRA 05h30m00s\nDec +00d00m00s'
        assert options['stellar_reference_range'] == (-2,8)
        assert options['stellar_report_range'] is True
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


@pytest.mark.parametrize("orientation", ["portrait", "landscape"])
def test_automatic_request_retains_geometry_inputs_and_computed_layout(tmp_path, orientation):
    data = cli.tomllib.loads((ROOT / "examples/atlas_design_request_v2.toml").read_text())
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
