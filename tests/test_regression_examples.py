"""Defining contracts for test-local regression examples."""

import ast
from pathlib import Path

import pytest


FIXTURES = Path("tests/fixtures/example_regressions")
CIRCULAR = (
    FIXTURES / "circumpolar_atlas.py",
    FIXTURES / "la_ligua_planisphere.py",
)
CANONICAL_EXPORTS = (
    FIXTURES / "atlas_summer_triangle.py",
    FIXTURES / "cartoon_modes.py",
    FIXTURES / "cartoon_modes_explicit_labels.py",
    *CIRCULAR,
)


def source(path):
    return path.read_text(encoding="utf-8")


def calls_named(tree, name):
    return tuple(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and (
            isinstance(node.func, ast.Name)
            and node.func.id == name
            or isinstance(node.func, ast.Attribute)
            and node.func.attr == name
        )
    )


@pytest.mark.parametrize("path", CANONICAL_EXPORTS)
def test_regression_examples_use_one_canonical_export(path):
    tree = ast.parse(source(path), filename=str(path))
    exports = calls_named(tree, "export")

    assert len(exports) == 1
    assert any(
        keyword.arg == "composition"
        for keyword in exports[0].keywords
    )
    for prohibited in (
        "savefig",
        "draw_chart_legend",
        "layer_options",
    ):
        assert calls_named(tree, prohibited) == ()


@pytest.mark.parametrize("path", CIRCULAR)
def test_circular_regressions_delegate_grid_anchors_and_legends(path):
    text = source(path)
    assert "label_anchor" not in text
    assert "CircularGridLabelAnchor" not in text
    assert "legends=LegendOptions(" in text
    assert "objects=True" in text
    assert "stellar_magnitudes=False" in text
    assert "context=True" in text


def test_circumpolar_regression_preserves_defining_geometry():
    text = source(FIXTURES / "circumpolar_atlas.py")
    assert "LIMITING_DECLINATION_DEG = -69.75" in text
    assert "limiting_declination_deg=LIMITING_DECLINATION_DEG" in text
    assert "horizon_altitude_deg=-90.0" in text
    assert 'sky.add_magellanic_cloud_isophotes("lmc")' in text
    assert 'sky.add_magellanic_cloud_isophotes("smc")' not in text
    assert "ra=tuple(range(0, 360, 30))" in text
    assert "meridian_dec_min=-75.0" in text


def test_planisphere_regression_preserves_observer_and_horizon():
    text = source(FIXTURES / "la_ligua_planisphere.py")
    assert 'Observer(location="La Ligua", time=LOCAL_TIME)' in text
    assert 'LOCAL_TIME = "2026-08-15 21:00"' in text
    assert "horizon_altitude_deg=0.0" in text
    assert "context_lines=observer_context_lines(sky.observer)" in text
    assert "ra=tuple(range(0, 360, 30))" in text
    assert "meridian_dec_min=-75.0" in text


def test_summer_triangle_regression_preserves_field_and_content():
    text = source(FIXTURES / "atlas_summer_triangle.py")
    for abbreviation in ("Cyg", "Lyr", "Vul", "Sge", "Aql"):
        assert f'"{abbreviation}"' in text
    assert "selected=OPEN_CLUSTERS" in text
    assert "selected=PLANETARY_NEBULAE" in text
    assert "selected=SUPERNOVA_REMNANTS" in text
    assert "angular_radius_deg=52.0" in text
    assert "horizon_altitude_deg=-90.0" in text
    assert "minimum_altitude_deg=-90.0" in text


def test_explicit_cartoon_labels_remain_example_configuration():
    text = source(FIXTURES / "cartoon_modes_explicit_labels.py")
    assert "CONSTELLATION_LABEL_POSITIONS" in text
    assert "CONSTELLATION_LABEL_OFFSETS" in text
    assert "constellation_label_positions=" in text
    assert "constellation_label_offsets=" in text
