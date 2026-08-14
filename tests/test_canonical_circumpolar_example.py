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

    assert "limiting_declination_deg=arguments.limiting_declination" in source
    assert 'projection="stereographic"' in source
    assert module.parser().parse_args([]).limiting_declination is None
    assert "configuration=configuration" in source


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


def test_generation_uses_shared_detail_and_closes_observer(
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
    assert paths == (output,)
    assert "product_details" not in captured[0]
    assert closed == [True]
