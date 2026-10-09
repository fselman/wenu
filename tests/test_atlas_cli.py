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
