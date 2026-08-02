"""Tests for the atlas-style La Ligua planisphere."""

from pathlib import Path


EXAMPLE = Path("examples/la_ligua_planisphere.py")


def test_la_ligua_planisphere_example_exists():
    assert EXAMPLE.is_file()


def test_planisphere_declares_location_date_and_local_time():
    source = EXAMPLE.read_text(encoding="utf-8")
    assert 'Observer(location="La Ligua", time=LOCAL_TIME)' in source
    assert 'LOCAL_TIME = "2026-08-15 21:00"' in source
    assert "context_lines=observer_context_lines(sky.observer)" in source


def test_planisphere_uses_visible_horizon_and_atlas_style():
    source = EXAMPLE.read_text(encoding="utf-8")
    assert "FullSkyChart(" in source
    assert "horizon_altitude_deg=0.0" in source
    assert 'style="atlas"' in source
    assert "PrintMode(width_inches=10.0, dpi=480)" in source
    assert "composition=composition" in source


def test_planisphere_grid_labels_use_the_horizon_circle():
    source = EXAMPLE.read_text(encoding="utf-8")
    assert "def circular_grid_label_anchor(" not in source
    assert "layer_options" not in source
    assert "CircularGridLabelAnchor" not in source


def test_planisphere_grid_uses_two_hour_spacing_and_stops_at_minus_75():
    source = EXAMPLE.read_text(encoding="utf-8")
    assert "ra=tuple(range(0, 360, 30))" in source
    assert "meridian_dec_min=-75.0" in source
    assert "dec=tuple(range(-75, 76, 15))" in source
