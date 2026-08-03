"""Tests for the atlas-style Summer Triangle example."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "tests" / "fixtures" / "example_regressions" / "atlas_summer_triangle.py"


def source():
    return EXAMPLE.read_text(encoding="utf-8")


def test_example_selects_the_requested_constellations():
    text = source()
    for abbreviation in ("Cyg", "Lyr", "Vul", "Sge", "Aql"):
        assert f'"{abbreviation}"' in text


def test_example_uses_the_atlas_style_and_j2000_grid():
    text = source()
    assert "AtlasChartStyle()" in text
    assert "composition=composition" in text
    assert 'frame="fk5"' in text
    assert 'equinox="J2000"' in text


def test_example_keeps_deep_sky_catalogues_selective():
    text = source()
    assert "selected=OPEN_CLUSTERS" in text
    assert "selected=PLANETARY_NEBULAE" in text
    assert "selected=SUPERNOVA_REMNANTS" in text


def test_example_uses_high_resolution_output_directory():
    text = source()
    assert "output/style-gallery/atlas-summer-triangle.png" in text
    assert "PrintMode(width_inches=10.0, dpi=480)" in text
    assert "figure.savefig" not in text


def test_example_framing_contains_the_full_constellation_group():
    text = source()
    assert "angular_radius_deg=52.0" in text
    assert "crop_y=0.0" in text


def test_equatorial_atlas_field_is_not_clipped_at_observer_horizon():
    text = source()
    assert "horizon_altitude_deg=-90.0" in text
    assert "minimum_altitude_deg=-90.0" in text


def test_milky_way_is_clipped_before_far_side_projection():
    text = source()
    assert "clip_polygons_to_projection_cap" not in text
    assert "milky_way_options" not in text
    assert "layer_options=" not in text
