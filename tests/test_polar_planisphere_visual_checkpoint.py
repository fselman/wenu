from pathlib import Path


ROOT = Path(__file__).parents[1]
RUNNER = ROOT / "tools/render_48e2_polar_preview.py"


def test_visual_checkpoint_uses_canonical_sky_composition_and_rendering():
    source = RUNNER.read_text(encoding="utf-8")

    assert "generate_celestial_sphere()" in source
    assert "composition = compose_chart(" in source
    assert 'style="atlas"' in source
    assert 'mode="print"' in source
    assert "chart.render(" in source
    assert "PolarCalendarFurnitureRequest().resolve(pair)" in source
    assert ").save(figure, destination)" in source
    assert "polar-planisphere-south.png" not in source
    assert 'f"polar-planisphere-{name}.png"' in source


def test_visual_checkpoint_has_both_projection_choices_and_fixed_observer():
    source = RUNNER.read_text(encoding="utf-8")

    assert 'location="La Ligua"' in source
    assert 'time="2026-08-15 21:00"' in source
    assert '"polar_azimuthal_equidistant", "stereographic"' in source
    assert source.count("ExportOptions(") == 1


def test_visual_checkpoint_realizes_reviewed_calendar_and_references():
    source = RUNNER.read_text(encoding="utf-8")

    assert "tick.labeled_day" in source
    assert "fontsize=8.6" in source
    assert 'labeled("Celestial equator")' in source
    assert 'labeled("Ecliptic")' in source
    assert 'labeled("Galactic plane")' in source
    assert "draw_celestial_reference_furniture(" in source
