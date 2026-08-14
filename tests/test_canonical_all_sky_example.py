"""Canonical Galactic Mollweide example declaration contracts."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace

PATH = Path("examples/all_sky.py")


def example():
    spec = importlib.util.spec_from_file_location("all_sky", PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_geometry_is_explicit_and_detail_uses_shared_family_policy():
    module = example()
    source = PATH.read_text(encoding="utf-8")

    assert 'family="all_sky"' in source
    assert 'projection="mollweide"' in source
    assert 'coordinate_frame="galactic"' in source
    assert "position_angle_deg=0.0" in source
    assert "AdaptiveDetailPolicy" not in source
    assert "star_magnitude_limit" not in source
    assert module.parser().parse_args([]).mask is None


def test_optional_constellations_define_disjoint_mask_openings():
    arguments = example().parser().parse_args([
        "--constellations", "Cru,Cyg,UMa", "--mask"
    ])

    assert arguments.constellations == ("Cru", "Cyg", "UMa")
    assert arguments.group is None
    assert arguments.mask is True


def test_generation_uses_shared_drawing_and_closes_observer(
    monkeypatch, tmp_path
):
    module = example()
    closed = []
    output = tmp_path / "all-sky.png"
    view = SimpleNamespace(
        observer=SimpleNamespace(close=lambda: closed.append(True))
    )
    captured = []
    monkeypatch.setattr(module, "chart_view", lambda arguments: view)
    monkeypatch.setattr(
        module,
        "draw_chart_view_from_arguments",
        lambda *args, **kwargs: captured.append((args, kwargs))
        or (SimpleNamespace(output=output),),
    )

    paths = module.generate(module.parser().parse_args([]))

    assert paths == (output,)
    assert captured[0][0][0] is view
    assert captured[0][1]["stem"] == "all-sky"
    assert captured[0][1]["title"] == (
        "Galactic all-sky map — Mollweide projection"
    )
    assert "product_details" not in captured[0][1]
    assert closed == [True]
