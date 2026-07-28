"""Tests for the southern circumpolar atlas example."""

from pathlib import Path


EXAMPLE = Path("examples/circumpolar_atlas.py")


def test_circumpolar_atlas_example_exists():
    assert EXAMPLE.is_file()


def test_circumpolar_atlas_uses_j2000_minus_40_boundary():
    source = EXAMPLE.read_text(encoding="utf-8")
    assert "LIMITING_DECLINATION_DEG = -40.0" in source
    assert 'equinox=Time("J2000")' in source
    assert "declination_boundary(" in source
    assert "renderer.set_clip_boundary(" in source


def test_circumpolar_atlas_renders_the_complete_cap():
    source = EXAMPLE.read_text(encoding="utf-8")
    assert "horizon_altitude_deg=-90.0" in source
    assert "field_width_deg=100.0" in source
    assert "field_height_deg=100.0" in source


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
    assert "dec=(-75, -60, -45)" in source
