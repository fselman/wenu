"""Tests for the southern circumpolar atlas example."""

from pathlib import Path


EXAMPLE = Path("examples/circumpolar_atlas.py")


def test_circumpolar_atlas_example_exists():
    assert EXAMPLE.is_file()


def test_circumpolar_atlas_places_boundary_through_lmc():
    source = EXAMPLE.read_text(encoding="utf-8")
    assert "LIMITING_DECLINATION_DEG = -69.75" in source
    assert "CircumpolarChart(" in source
    assert "limiting_declination_deg=LIMITING_DECLINATION_DEG" in source
    assert 'sky.add_magellanic_cloud_isophotes("lmc")' in source
    assert 'sky.add_magellanic_cloud_isophotes("smc")' not in source


def test_circumpolar_atlas_uses_circular_chart_clipping():
    source = EXAMPLE.read_text(encoding="utf-8")
    assert "horizon_altitude_deg=-90.0" in source
    assert "boundary_style={" in source
    assert "RegionalChart" not in source


def test_circumpolar_atlas_uses_atlas_style_and_double_resolution():
    source = EXAMPLE.read_text(encoding="utf-8")
    assert "AtlasChartStyle()" in source
    assert "ExportOptions(dpi=480)" in source
    assert "output/style-gallery/" in source


def test_circumpolar_grid_labels_anchor_to_the_circle():
    source = EXAMPLE.read_text(encoding="utf-8")
    assert "def polar_grid_label_anchor(" in source
    assert 'curve.name.startswith("right_ascension_")' in source
    assert "np.argmax(radius)" in source
    assert 'grid_render["label_anchor"]' in source


def test_circumpolar_grid_uses_two_hour_spacing_and_stops_at_minus_75():
    source = EXAMPLE.read_text(encoding="utf-8")
    assert "ra=tuple(range(0, 360, 30))" in source
    assert "meridian_dec_min=-75.0" in source
    assert "dec=(-85, -80, -75)" in source
