"""Atlas request-file admission, installed route and JSON publication."""

from copy import deepcopy
import os
from pathlib import Path
import subprocess
import sys

import pytest

from wenu.atlas_design import AtlasBandTiling, AtlasDesignRequest
from wenu.cli import atlas as cli


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples/atlas_design_request_v1.toml"


@pytest.fixture
def request_data():
    return cli.tomllib.loads(EXAMPLE.read_text(encoding="utf-8"))


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
        celestial.extend((*ax.lines, *ax.patches, *ax.collections, *ax.texts))
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
    assert design.read_bytes() == before
