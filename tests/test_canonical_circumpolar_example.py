"""Canonical circumpolar declaration contracts."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


def example():
    path = Path("examples/circumpolar.py")
    spec = importlib.util.spec_from_file_location("circumpolar", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_defining_geometry_is_explicit():
    module = example()
    source = Path("examples/circumpolar.py").read_text(encoding="utf-8")

    assert module.LIMITING_DECLINATION_DEG == pytest.approx(-69.75)
    assert 'pole="south"' in source
    assert "limiting_declination_deg=arguments.limiting_declination" in source
    assert 'projection="stereographic"' in source
    assert module.parser().parse_args([]).limiting_declination == pytest.approx(
        module.LIMITING_DECLINATION_DEG
    )


def test_limiting_declination_is_an_ordinary_framing_control(monkeypatch):
    module = example()
    captured = []
    sky = object()
    observer = SimpleNamespace(close=lambda: None)
    monkeypatch.setattr(module, "Observer", lambda **kwargs: observer)
    monkeypatch.setattr(
        module, "get_chart_view",
        lambda *args, **kwargs: captured.append((args, kwargs)) or object(),
    )

    module.chart_view(
        module.parser().parse_args(["--limiting-declination", "-30"]),
        sky=sky,
    )

    assert captured[0][0][:2] == (sky, observer)
    assert captured[0][1]["limiting_declination_deg"] == pytest.approx(-30.0)


def test_generation_retains_cartoon_content_and_closes_observer(
    monkeypatch, tmp_path
):
    module = example()
    closed = []
    output = tmp_path / "circumpolar.png"
    view = SimpleNamespace(
        observer=SimpleNamespace(close=lambda: closed.append(True))
    )
    captured = []
    monkeypatch.setattr(module, "chart_view", lambda arguments: view)
    monkeypatch.setattr(
        module, "draw_chart_view_from_arguments",
        lambda *args, **kwargs: captured.append(kwargs)
        or (SimpleNamespace(output=output),),
    )

    paths = module.generate(module.parser().parse_args([]))
    detail = captured[0]["product_details"]["cartoon"].detail

    assert paths == (output,)
    assert detail.star_magnitude_limit == pytest.approx(3.0)
    assert detail.enabled_layers == frozenset({
        "stars", "constellation_lines", "equatorial_grid",
        "milky_way", "magellanic_clouds",
    })
    assert closed == [True]
