"""Canonical planisphere and regional declaration contracts."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


EXAMPLES = (
    Path("examples/planisphere.py"),
    Path("examples/regional_constellation_group.py"),
    Path("examples/regional_constellation.py"),
)


def load(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_single_regional_defaults_use_constellation_framing():
    module = load(EXAMPLES[2])
    arguments = module.parser().parse_args([])
    source = EXAMPLES[2].read_text(encoding="utf-8")

    assert arguments.constellations == ("Cru",)
    assert arguments.group is None
    assert arguments.field_width is None
    assert arguments.field_height is None
    assert arguments.position_angle == pytest.approx(0.0)
    assert arguments.mask is False
    assert "add_constellation_subject_arguments(" in source
    assert "chart_constellation_subject(" in source


def test_single_and_group_regional_examples_share_optional_field_overrides():
    for path in EXAMPLES[1:]:
        arguments = load(path).parser().parse_args([
            "--field-width", "30", "--field-height", "24",
        ])

        assert arguments.field_width == pytest.approx(30.0)
        assert arguments.field_height == pytest.approx(24.0)


@pytest.mark.parametrize("path", EXAMPLES)
def test_constellation_subject_examples_use_one_shared_parser(path):
    arguments = load(path).parser().parse_args([
        "--constellations", "Cru,Cyg,UMa"
    ])

    assert arguments.constellations == ("Cru", "Cyg", "UMa")
    assert arguments.group is None


def test_planisphere_accepts_optional_disjoint_mask_sets():
    module = load(EXAMPLES[0])
    arguments = module.parser().parse_args([
        "--constellations", "Cru,Cyg,UMa", "--mask"
    ])

    assert arguments.constellations == ("Cru", "Cyg", "UMa")
    assert arguments.mask is True


def test_group_example_defaults_to_an_arbitrary_adjacent_iau_set():
    module = load(EXAMPLES[1])
    arguments = module.parser().parse_args([])
    source = EXAMPLES[1].read_text(encoding="utf-8")

    assert arguments.constellations == ("Sgr", "Sco", "Oph", "Ser")
    assert arguments.group is None
    assert "GROUPS" not in source
    assert "add_constellation_subject_arguments(" in source
    assert "chart_constellation_subject(" in source


def test_group_example_retains_packaged_aliases_and_explicit_mask():
    module = load(EXAMPLES[1])
    arguments = module.parser().parse_args([
        "--group", "summer-triangle", "--mask"
    ])

    assert arguments.group == "summer-triangle"
    assert arguments.mask is True


@pytest.mark.parametrize(
    ("path", "limit"),
    [(EXAMPLES[0], 5.0), (EXAMPLES[1], 6.5), (EXAMPLES[2], 6.5)],
)
def test_atlas_stellar_limits_remain_explicit(path, limit):
    assert f"star_magnitude_limit={limit}" in path.read_text(encoding="utf-8")


@pytest.mark.parametrize("path", EXAMPLES)
def test_atlas_examples_use_adaptive_deep_sky_detail(path):
    source = path.read_text(encoding="utf-8")

    assert "AdaptiveDetailPolicy(" in source


@pytest.mark.parametrize("path", EXAMPLES)
def test_examples_use_the_shared_context_and_furniture_adapter(path):
    module = load(path)
    arguments = module.parser().parse_args([
        "--grid-references", "all", "--poles", "--pole-labels",
        "--legends", "--credits", "--location",
    ])

    assert arguments.grid_references == frozenset(
        {"equatorial", "ecliptic", "galactic"}
    )
    assert arguments.poles is True
    assert arguments.pole_labels is True
    assert arguments.legends is True
    assert arguments.credits is True
    assert arguments.location is True


def test_group_generation_uses_resolved_packaged_title(monkeypatch, tmp_path):
    module = load(EXAMPLES[1])
    output = tmp_path / "group.png"
    closed = []
    view = SimpleNamespace(
        constellations=SimpleNamespace(
            key="summer-triangle", display_name="The Summer Triangle"
        ),
        observer=SimpleNamespace(close=lambda: closed.append(True)),
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
    assert captured[0]["stem"] == "regional-summer-triangle"
    assert captured[0]["title"] == "The Summer Triangle"
    assert closed == [True]
