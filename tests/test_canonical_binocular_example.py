"""Canonical binocular example declaration contracts."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


def example():
    path = Path("examples/binocular_object.py")
    spec = importlib.util.spec_from_file_location("binocular_object", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_packaged_target_and_explicit_geometry_are_cli_data():
    module = example()
    arguments = module.parser().parse_args([
        "--target", "M57", "--field-diameter", "7.0"
    ])

    assert arguments.target == "M57"
    assert arguments.field_diameter == pytest.approx(7.0)
    assert module.parser().parse_args([]).field_diameter is None
    assert not hasattr(module, "TARGETS")


@pytest.mark.parametrize(
    ("families", "samples"),
    [({"globular_clusters"}, 73), ({"galaxies"}, 97)],
)
def test_target_family_selects_approved_binocular_detail(families, samples):
    module = example()
    target = SimpleNamespace(required_families=frozenset(families))
    details = module._details(SimpleNamespace(target=target))

    assert details["atlas"].detail.star_magnitude_limit == pytest.approx(11.0)
    assert details["atlas"].detail.extended_object_samples == samples
    assert families <= details["cartoon"].detail.enabled_layers
    assert details["cartoon"].detail.constellation_star_mode == "selected"


def test_generation_delegates_to_shared_view_drawing(monkeypatch, tmp_path):
    module = example()
    closed = []
    output = tmp_path / "m57.png"
    target = SimpleNamespace(
        display_name="Ring Nebula", primary_identifier="M57",
        required_families=frozenset({"planetary_nebulae"}),
    )
    view = SimpleNamespace(
        target=target,
        frame=SimpleNamespace(field_diameter_deg=6.5),
        observer=SimpleNamespace(close=lambda: closed.append(True)),
    )
    captured = []
    monkeypatch.setattr(module, "chart_view", lambda arguments: view)
    monkeypatch.setattr(
        module, "draw_chart_view_from_arguments",
        lambda *args, **kwargs: captured.append((args, kwargs))
        or (SimpleNamespace(output=output),),
    )

    paths = module.generate(module.parser().parse_args(["--target", "M57"]))

    assert paths == (output,)
    assert captured[0][0][0] is view
    assert captured[0][1]["title"] == "Ring Nebula (M57) — 6.5° binocular field"
    assert "planetary_nebulae" in (
        captured[0][1]["product_details"]["cartoon"].detail.enabled_layers
    )
    assert closed == [True]
